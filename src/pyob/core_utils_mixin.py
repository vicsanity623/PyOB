from typing import Callable, Optional
import json
import logging
import os
import re
import select
import shutil
import subprocess
import sys
import textwrap
import time

class CoreUtilsMixin:
    target_dir: str
    memory_path: str
    key_cooldowns: dict[str, float]
    _workspace_cache: dict[str, tuple[float, str]]

    def generate_pr_summary(self, rel_path: str, diff_text: str) -> dict:
        """Analyzes a git diff and returns a professional title and body for the PR."""
        # ... (rest of the method remains the same)

    def stream_gemini(
        self, prompt: str, api_key: str, on_chunk: Callable[[], None]
    ) -> str:
        return stream_gemini(prompt, api_key, on_chunk)

    def stream_ollama(self, prompt: str, on_chunk: Callable[[], None]) -> str:
        return str(stream_ollama(prompt, on_chunk))

    def stream_github_models(
        self, prompt: str, on_chunk: Callable[[], None], model_name: str = "Llama-3"
    ) -> str:
        return str(stream_github_models(prompt, on_chunk, model_name))

    def _stream_single_llm(
        self,
        prompt: str,
        key: Optional[str] = None,
        context: str = "",
        gh_model: str = "Llama-3",
    ) -> str:
        return str(stream_single_llm(prompt, key, context, gh_model))

    def get_user_approval(self, prompt_text: str, timeout: int = 220) -> str:
        # ... (rest of the method remains the same)

    def _get_input_with_timeout(self, timeout: int) -> str:
        # ... (rest of the method remains the same)

    def _win32_input(self, start_time: float, timeout: int) -> str:
        # ... (rest of the method remains the same)

    def _unix_input(self, start_time: float, timeout: int) -> str:
        # ... (rest of the method remains the same)

    def _open_editor_for_content(
        self,
        initial_content: str,
        file_suffix: str = ".txt",
        log_message: str = "Opening editor",
        error_message: str = "Using original content.",
    ) -> str:
        # ... (rest of the method remains the same)

    def _launch_external_code_editor(
        self, initial_content: str, file_suffix: str = ".py"
    ) -> str:
        return self._open_editor_for_content(
            initial_content,
            file_suffix,
            log_message="Opening prompt augmentation editor",
            error_message="Using original content.",
        )

    def _edit_prompt_with_external_editor(self, initial_prompt: str) -> str:
        return self._open_editor_for_content(
            initial_prompt,
            log_message="Opening prompt in editor",
            error_message="Using original prompt.",
        )

    def backup_workspace(self) -> dict[str, str]:
        # ... (rest of the method remains the same)

    def restore_workspace(self, state: dict[str, str]):
        # ... (rest of the method remains the same)

    def load_memory(self) -> str:
        # ... (rest of the method remains the same)

    def get_valid_llm_response(
        self, prompt: str, validator: Callable[[str], bool], context: str = ""
    ) -> str:
        # ... (rest of the method remains the same)

    def _find_entry_file(self) -> str | None:
        # ... (rest of the method remains the same)

    def display_menu(self) -> None:
        print("Available options:")
        print("1. Generate PR summary")
        print("2. Stream Gemini")
        print("3. Stream Ollama")
        print("4. Stream GitHub models")
        print("5. Get user approval")
        print("6. Backup workspace")
        print("7. Restore workspace")
        print("8. Load memory")
        print("9. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            rel_path = input("Enter relative path: ")
            diff_text = input("Enter diff text: ")
            print(self.generate_pr_summary(rel_path, diff_text))
        elif choice == "2":
            prompt = input("Enter prompt: ")
            api_key = input("Enter API key: ")
            print(self.stream_gemini(prompt, api_key, lambda: None))
        elif choice == "3":
            prompt = input("Enter prompt: ")
            print(self.stream_ollama(prompt, lambda: None))
        elif choice == "4":
            prompt = input("Enter prompt: ")
            model_name = input("Enter model name: ")
            print(self.stream_github_models(prompt, lambda: None, model_name))
        elif choice == "5":
            prompt_text = input("Enter prompt text: ")
            print(self.get_user_approval(prompt_text))
        elif choice == "6":
            print(self.backup_workspace())
        elif choice == "7":
            state = input("Enter state: ")
            self.restore_workspace(json.loads(state))
        elif choice == "8":
            print(self.load_memory())
        elif choice == "9":
            print("Exiting...")
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    mixin = CoreUtilsMixin()
    while True:
        mixin.display_menu()