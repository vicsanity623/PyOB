import os
import re

from pyob.core_utils import logger
from pyob.prompts import SYSTEM_PROMPTS


class SearchAndFilterMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_query = ""
        self.filter_date = ""

    def handle_search(self, search_query):

        if not hasattr(self, "search_query"):
            self.search_query = ""
        self.search_query = search_query

    def handle_filter(self, filter_date):
        if not hasattr(self, "filter_date"):
            self.filter_date = ""
        self.filter_date = filter_date


class PromptsAndMemoryMixin(SearchAndFilterMixin):
    target_dir: str
    history_path: str
    analysis_path: str
    memory_path: str
    memory: str

    def _ensure_prompt_files(self) -> None:
        data_dir = os.path.join(self.target_dir, ".pyob")
        os.makedirs(data_dir, exist_ok=True)
        for filename, content in SYSTEM_PROMPTS.items():
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        if f.read() == content:
                            continue
                except Exception:
                    pass
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

    def load_prompt(self, filename: str, **kwargs: str) -> str:
        # Use a consistent path resolution
        data_dir = os.path.join(self.target_dir, ".pyob")

        # A/B Testing Logic
        base_name, ext = os.path.splitext(filename)
        path_a = os.path.join(data_dir, f"{base_name}.vA{ext}")
        path_b = os.path.join(data_dir, f"{base_name}.vB{ext}")

        if os.path.exists(path_a) and os.path.exists(path_b):
            import random

            chosen_version = random.choice(["vA", "vB"])
            filepath = path_a if chosen_version == "vA" else path_b
            logger.info(f"A/B Testing: Selected {chosen_version} for prompt {filename}")
        else:
            filepath = os.path.join(data_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                template = f.read()
            for key, value in kwargs.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
        except Exception as e:
            logger.error(f"Failed to load prompt {filename} from {filepath}: {e}")
            return ""

    def _get_impactful_history(self) -> str:
        if not os.path.exists(self.history_path):
            return "No prior history."
        with open(self.history_path, "r", encoding="utf-8") as f:
            full_history = f.read()
        entries = [
            e.strip()
            for e in re.split(r"## \d{4}-\d{2}-\d{2}", full_history)
            if e.strip()
        ]
        recent_entries = entries[-3:]
        summary = "### Significant Recent Architecture Changes:\n"
        for entry in recent_entries:
            lines = entry.split("\n")
            if lines and lines[0].strip():
                summary += f"- {lines[0].strip()}\n"
        return summary

    def _get_rich_context(self, query_text: str = "") -> str:
        context = ""
        if os.path.exists(self.analysis_path):
            with open(self.analysis_path, "r", encoding="utf-8") as f:
                content = f.read()
                header_parts = content.split("## File Directory")
                header = header_parts[0].strip() if header_parts else ""
                context += f"### Project Goal:\n{header}\n\n"

        if os.path.exists(self.history_path):
            with open(self.history_path, "r", encoding="utf-8") as f:
                hist = f.read()
                headers = [line for line in hist.split("\n") if line.startswith("## ")]
                context += (
                    "### Recent Edit History:\n" + "\n".join(headers[-3:]) + "\n\n"
                )

        if self.memory:
            mem_str = self.memory.strip()
            # Simple keyword-based RAG if query_text is provided
            if query_text and len(mem_str) > 1500:
                query_words = set(re.findall(r"\b\w{4,}\b", query_text.lower()))
                paragraphs = mem_str.split("\n\n")
                scored_paragraphs = []
                for p in paragraphs:
                    p_words = set(re.findall(r"\b\w{4,}\b", p.lower()))
                    score = len(query_words.intersection(p_words))
                    scored_paragraphs.append((score, p))

                # Sort by score descending and take top N paragraphs
                scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
                top_paragraphs = [p for score, p in scored_paragraphs[:5] if score > 0]

                if top_paragraphs:
                    mem_str = "\n\n".join(top_paragraphs)
                    mem_str = f"[RAG FILTERED MEMORY]\n{mem_str}"
                else:
                    mem_str = (
                        mem_str[:500]
                        + "\n\n... [OLDER MEMORY TRUNCATED FOR CONTEXT LIMITS] ...\n\n"
                        + mem_str[-800:]
                    )
            elif len(mem_str) > 1500:
                mem_str = (
                    mem_str[:500]
                    + "\n\n... [OLDER MEMORY TRUNCATED FOR CONTEXT LIMITS] ...\n\n"
                    + mem_str[-800:]
                )

            context += f"### Logic Memory:\n{mem_str}\n\n"

        return context

    def update_memory(self) -> None:
        session_context: list[str] = getattr(self, "session_context", [])
        if not session_context:
            return
        logger.info("\nPHASE 5: Updating MEMORY.md with session context...")
        session_summary = "\n".join(f"- {item}" for item in session_context)
        prompt = self.load_prompt(
            "UM.md",
            current_memory=self.memory if self.memory else "No previous memory.",
            session_summary=session_summary,
        )

        def validator(text: str) -> bool:
            return bool(text.strip())

        llm_response = self.get_valid_llm_response(
            prompt, validator, context="Memory Update"
        )
        raw_response = llm_response.strip()
        clean_memory = re.sub(
            r"^```[a-zA-Z]*\r?\n", "", raw_response, flags=re.MULTILINE
        )
        clean_memory = re.sub(r"\r?\n```\s*$", "", clean_memory, flags=re.MULTILINE)
        if clean_memory:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                f.write(clean_memory)
            self.memory = clean_memory

    def refactor_memory(self) -> None:
        if not self.memory:
            return
        logger.info(
            "\nPHASE 6: Cleanup! Summarizing and refactoring MEMORY.md (Rolling Summary)..."
        )

        # Pull in recent history and analysis for dense summarization
        history_excerpt = self._get_impactful_history()
        analysis_excerpt = ""
        if os.path.exists(self.analysis_path):
            try:
                with open(self.analysis_path, "r", encoding="utf-8") as f:
                    analysis_excerpt = f.read()[
                        :1000
                    ]  # Just the high-level project summary
            except Exception:
                pass

        prompt = self.load_prompt(
            "RM.md",
            current_memory=self.memory,
            history=history_excerpt,
            analysis=analysis_excerpt,
        )

        def validator(text: str) -> bool:
            return bool(text.strip())

        llm_response = self.get_valid_llm_response(
            prompt, validator, context="Memory Refactor"
        )
        raw_response = llm_response.strip()
        clean_memory = re.sub(
            r"^```[a-zA-Z]*\r?\n", "", raw_response, flags=re.MULTILINE
        )
        clean_memory = re.sub(r"\r?\n```\s*$", "", clean_memory, flags=re.MULTILINE)
        if clean_memory and len(clean_memory) > 50:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                f.write(clean_memory)
            self.memory = clean_memory
