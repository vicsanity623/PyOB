import ast
import os
import subprocess
import sys
import time

from .core_utils import (
    ANALYSIS_FILE,
    FAILED_FEATURE_FILE_NAME,
    FAILED_PR_FILE_NAME,
    FEATURE_FILE_NAME,
    GEMINI_API_KEYS,
    HISTORY_FILE,
    MEMORY_FILE_NAME,
    PR_FILE_NAME,
    SYMBOLS_FILE,
    CoreUtilsMixin,
    logger,
)
from .feature_mixins import FeatureOperationsMixin
from .get_valid_edit import GetValidEditMixin
from .prompts_and_memory import PromptsAndMemoryMixin
from .reviewer_mixins import ValidationMixin
from .scanner_mixins import ScannerMixin
from .xml_mixin import ApplyXMLMixin


class AutoReviewer(
    CoreUtilsMixin,
    PromptsAndMemoryMixin,
    ValidationMixin,
    FeatureOperationsMixin,
    ScannerMixin,
    GetValidEditMixin,
    ApplyXMLMixin,
):
    _shared_cooldowns: dict[str, float] | None = None
    DASHBOARD_BASE_URL: str = os.environ.get(
        "PYOB_DASHBOARD_URL", "http://localhost:8000"
    )
    MODULARITY_THRESHOLD_LINES: int = 800
    DASHBOARD_POLL_INTERVAL_SECONDS: int = 2
    DASHBOARD_MAX_RETRIES: int = 3
    DASHBOARD_REQUEST_TIMEOUT_SECONDS: int = 5

    def __init__(self, target_dir: str):
        self.target_dir = os.path.abspath(target_dir)
        self.pyob_dir = os.path.join(self.target_dir, ".pyob")
        os.makedirs(self.pyob_dir, exist_ok=True)
        self.pr_file = os.path.join(self.pyob_dir, PR_FILE_NAME)
        self.feature_file = os.path.join(self.pyob_dir, FEATURE_FILE_NAME)
        self.failed_pr_file = os.path.join(self.pyob_dir, FAILED_PR_FILE_NAME)
        self.failed_feature_file = os.path.join(self.pyob_dir, FAILED_FEATURE_FILE_NAME)
        self.memory_path = os.path.join(self.pyob_dir, MEMORY_FILE_NAME)
        self.analysis_path = os.path.join(self.pyob_dir, ANALYSIS_FILE)
        self.history_path = os.path.join(self.pyob_dir, HISTORY_FILE)
        self.symbols_path = os.path.join(self.pyob_dir, SYMBOLS_FILE)
        self.memory = self.load_memory()
        self.session_context: list[str] = []
        self.manual_target_file: str | None = None
        self._ensure_prompt_files()
        if AutoReviewer._shared_cooldowns is None:
            AutoReviewer._shared_cooldowns = {
                key: 0.0 for key in GEMINI_API_KEYS if key.strip()
            }

        self.key_cooldowns = AutoReviewer._shared_cooldowns

    def get_language_info(self, filepath: str) -> tuple[str, str]:
        ext = os.path.splitext(filepath)[1].lower()
        mapping = {
            ".py": ("Python", "python"),
            ".js": ("JavaScript", "javascript"),
            ".ts": ("TypeScript", "typescript"),
            ".html": ("HTML", "html"),
            ".css": ("CSS", "css"),
            ".json": ("JSON", "json"),
            ".sh": ("Bash", "bash"),
            ".md": ("Markdown", "markdown"),
        }
        return mapping.get(ext, ("Code", ""))

    def scan_for_lazy_code(self, filepath: str, content: str) -> list[str]:
        issues = []
        lines = content.splitlines()

        if len(lines) > 800:
            issues.append(
                f"Architectural Bloat: File has {len(lines)} lines. This exceeds the 800-line modularity threshold. Priority: HIGH. Action: Split into smaller modules."
            )

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return [f"SyntaxError during AST parse: {e}"]
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "Any":
                issues.append("Found use of 'Any' type hint.")
            elif isinstance(node, ast.Attribute) and node.attr == "Any":
                issues.append("Found use of 'typing.Any'.")
        return issues

    def _get_user_decision(self, prompt_message: str, allow_delete: bool) -> str:
        """
        Initiates an interactive CLI review process for pending proposals.
        """
        is_cloud = (
            os.environ.get("GITHUB_ACTIONS") == "true"
            or os.environ.get("CI") == "true"
            or "GITHUB_RUN_ID" in os.environ
        )
        if is_cloud or not sys.stdin.isatty():
            logger.info("Headless environment detected: Auto-approving proposal.")
            return "PROCEED"

        logger.info("==================================================")
        logger.info(" ACTION REQUIRED: Interactive Proposal Review")
        logger.info("==================================================")

        if os.path.exists(self.pr_file):
            logger.info(f"\n--- {PR_FILE_NAME} ---")
            with open(self.pr_file, "r", encoding="utf-8") as f:
                print(f.read())

        if os.path.exists(self.feature_file):
            logger.info(f"\n--- {FEATURE_FILE_NAME} ---")
            with open(self.feature_file, "r", encoding="utf-8") as f:
                print(f.read())

        logger.info("==================================================")

        while True:
            try:
                user_decision = input(f"{prompt_message}: ").strip().upper()
                if user_decision == "":
                    return "PROCEED"
                if user_decision not in ["PROCEED", "SKIP"] and (
                    not allow_delete or user_decision != "DELETE"
                ):
                    logger.warning(
                        f"Invalid input '{user_decision}'. Please try again."
                    )
                else:
                    return user_decision
            except EOFError:
                logger.warning(
                    "EOFError caught during input. Auto-approving to prevent crash."
                )
                return "PROCEED"

    def set_manual_target_file(self, filepath: str | None):
        if filepath:
            if not os.path.exists(filepath):
                logger.warning(
                    f"Manual target file '{filepath}' does not exist. Ignoring."
                )
                self.manual_target_file = None
            else:
                self.manual_target_file = os.path.abspath(filepath)
                logger.info(f"Manual target file set to: {self.manual_target_file}")
        else:
            self.manual_target_file = None
            logger.info("Manual target file cleared. Reverting to directory scan.")

    def run_linters(self, filepath: str) -> tuple[str, str]:

        ruff_out, mypy_out = "", ""
        try:
            ruff_out = subprocess.run(
                ["ruff", "check", filepath], capture_output=True, text=True
            ).stdout.strip()
        except FileNotFoundError:
            pass
        try:
            res = subprocess.run(["mypy", filepath], capture_output=True, text=True)
            mypy_out = res.stdout.strip()
        except FileNotFoundError:
            pass
        return ruff_out, mypy_out

    def build_patch_prompt(
        self,
        lang_name: str,
        lang_tag: str,
        content: str,
        ruff_out: str,
        mypy_out: str,
        custom_issues: list[str],
    ) -> str:
        memory_section = self._get_rich_context(query_text=content)
        ruff_section = f"### Ruff Errors:\n{ruff_out}\n\n" if ruff_out else ""
        mypy_section = f"### Mypy Errors:\n{mypy_out}\n\n" if mypy_out else ""

        strict_typing_directives = (
            "### STRICT TYPING DIRECTIVES (CRITICAL)\n"
            "This repository operates under `mypy --strict`. You MUST follow these rules:\n"
            "1. **Complete Signatures:** Every new or modified function must have explicit argument types and a return type (e.g., `def foo(x: int) -> str:`).\n"
            "2. **Unimported Modules:** If your edit causes a `[no-any-unimported]` error due to an external library, you MUST append `# type: ignore` to that specific import line.\n"
            "3. **No Implicit Any:** Avoid using `Any` unless strictly necessary. If used, ensure `typing.Any` is imported.\n\n"
        )

        custom_issues_section = (
            "### Code Quality Issues:\n"
            + "\n".join(f"- {i}" for i in custom_issues)
            + "\n\n"
            if custom_issues
            else ""
        )

        combined_issues = strict_typing_directives + custom_issues_section

        return str(
            self.load_prompt(
                "PP.md",
                lang_name=lang_name,
                lang_tag=lang_tag,
                content=content,
                memory_section=memory_section,
                ruff_section=ruff_section,
                mypy_section=mypy_section,
                custom_issues_section=combined_issues,  # Pass the combined string here
            )
        )

    def _handle_pending_proposals(
        self, prompt_message: str, allow_delete: bool
    ) -> bool:
        """
        Handles user approval for pending PR/feature files, applies them,
        manages rollback on failure, or deletes them.
        Returns True if proposals were successfully applied or deleted,
        False if skipped or failed to apply.
        """
        if not (os.path.exists(self.pr_file) or os.path.exists(self.feature_file)):
            return False

        user_input = self._get_user_decision(prompt_message, allow_delete)

        if user_input == "PROCEED":
            backup_state = self.backup_workspace()
            success = True
            if os.path.exists(self.pr_file):
                with open(self.pr_file, "r", encoding="utf-8") as f:
                    if not self.implement_pr(f.read()):
                        success = False
            if success and os.path.exists(self.feature_file):
                with open(self.feature_file, "r", encoding="utf-8") as f:
                    if not self.implement_feature(f.read()):
                        success = False
            if not success:
                self.restore_workspace(backup_state)
                logger.warning("Rollback performed due to unfixable errors.")
                self.session_context.append(
                    "CRITICAL: The last refactor/feature attempt FAILED and was ROLLED BACK. "
                    "The files on disk have NOT changed. Check FAILED_FEATURE.md for error logs."
                )

                failure_report = f"\n\n### FAILURE ATTEMPT LOGS ({time.strftime('%Y-%m-%d %H:%M:%S')})\n"
                failure_report += self.session_context[-1]
                if len(self.session_context) > 1:
                    failure_report += "\n" + "\n".join(self.session_context[-3:-1])

                if os.path.exists(self.pr_file):
                    with open(self.pr_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    with open(self.failed_pr_file, "w") as f:
                        f.write(content + failure_report)
                    os.remove(self.pr_file)

                if os.path.exists(self.feature_file):
                    with open(self.feature_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    with open(self.failed_feature_file, "w") as f:
                        f.write(content + failure_report)
                    os.remove(self.feature_file)
                return False
            return True
        elif allow_delete and user_input == "DELETE":
            if os.path.exists(self.pr_file):
                os.remove(self.pr_file)
            if os.path.exists(self.feature_file):
                os.remove(self.feature_file)
            logger.info("Deleted pending proposal files. Starting fresh scan...")
            return True
        else:
            logger.info(
                "Changes not applied manually. They will remain for the next loop iteration."
            )
            return False

    def run_pipeline(self, current_iteration: int):
        changes_made = False
        try:
            if os.path.exists(self.pr_file) or os.path.exists(self.feature_file):
                logger.info("==================================================")
                logger.info(
                    f"Found pending {PR_FILE_NAME} and/or {FEATURE_FILE_NAME} from a previous run."
                )
                proposals_handled = self._handle_pending_proposals(
                    "Hit ENTER to PROCEED, type 'SKIP' to ignore",
                    allow_delete=True,
                )
                if not proposals_handled:
                    logger.info(
                        "Pending proposals were not applied or deleted. Halting current pipeline iteration to await user action."
                    )
                    return
                changes_made = True

            if not changes_made:
                logger.info("==================================================")
                logger.info("PHASE 1: Initial Assessment & Codebase Scan")
                logger.info("==================================================")
                if self.manual_target_file:
                    if os.path.exists(self.manual_target_file):
                        all_files = [self.manual_target_file]
                        logger.info(
                            f"Manual target file override active: {self.manual_target_file}"
                        )
                    else:
                        logger.warning(
                            f"Manual target file '{self.manual_target_file}' not found. Reverting to full scan."
                        )
                        self.manual_target_file = None
                        all_files = self.scan_directory()
                else:
                    all_files = self.scan_directory()

                    # Incremental Analysis: Only analyze changed files + direct dependencies
                    try:
                        res = subprocess.run(
                            ["git", "diff", "--name-only", "HEAD"],
                            cwd=self.target_dir,
                            capture_output=True,
                            text=True,
                        )
                        changed_files = [
                            os.path.abspath(os.path.join(self.target_dir, f))
                            for f in res.stdout.strip().splitlines()
                            if f
                        ]

                        # Add dependencies based on symbols (if we changed a definition, re-analyze files that reference it)
                        if changed_files and hasattr(self, "ledger"):
                            deps = set(changed_files)
                            for c_file in changed_files:
                                rel_c = os.path.relpath(c_file, self.target_dir)
                                # Find definitions in this changed file
                                defs_here = [
                                    k
                                    for k, v in self.ledger.get(
                                        "definitions", {}
                                    ).items()
                                    if v == rel_c
                                ]
                                # Find files that reference these definitions
                                for ref_file, refs in self.ledger.get(
                                    "references", {}
                                ).items():
                                    if any(d in refs for d in defs_here):
                                        deps.add(
                                            os.path.abspath(
                                                os.path.join(self.target_dir, ref_file)
                                            )
                                        )

                            all_files = [f for f in all_files if f in deps]
                            if not all_files:
                                logger.info(
                                    "Incremental Analysis: No relevant file changes detected. Sleeping..."
                                )
                                return
                        elif not changed_files:
                            # If no git changes, maybe we just analyze a random subset instead of all to save tokens
                            import random

                            all_files = random.sample(all_files, min(3, len(all_files)))

                    except Exception as e:
                        logger.warning(f"Failed to perform incremental analysis: {e}")

                if not all_files:
                    return logger.warning("No supported source files found.")
                for idx, filepath in enumerate(all_files, start=1):
                    self.analyze_file(filepath, idx, len(all_files))
                logger.info("==================================================")
                logger.info(" Phase 1 Complete.")
                logger.info("==================================================")
                if os.path.exists(self.pr_file):
                    logger.info(
                        "Skipping Phase 2 (Feature Proposal) because Phase 1 found bugs."
                    )
                    logger.info("Applying fixes first to prevent code collisions...")
                elif all_files:
                    logger.info("Moving to Phase 2: Generating Feature Proposal...")
                    self.propose_feature(random.choice(all_files))
                if os.path.exists(self.pr_file) or os.path.exists(self.feature_file):
                    print("\n" + "=" * 50)
                    print(" ACTION REQUIRED: Proposals Generated")
                    self._handle_pending_proposals(
                        "Hit ENTER to PROCEED, or type 'SKIP' to cancel",
                        allow_delete=False,
                    )
                else:
                    logger.info("\nNo issues found, no features proposed.")
        finally:
            self.update_memory()
            if current_iteration % 2 == 0:
                self.refactor_memory()
            logger.info("Pipeline iteration complete.")


if __name__ == "__main__":
    print("Please run `python entrance.py` instead to use the targeted memory flow.")
    sys.exit(0)
