import ast
import json
import logging
import os
import re
import select
import shutil
import subprocess
import sys
import termios
import textwrap
import threading
import time
import tty
import requests

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

env_keys = os.environ.get("PYOB_GEMINI_KEYS") or os.environ.get("INPUT_GEMINI_KEYS", "")
GEMINI_API_KEYS = [k.strip() for k in env_keys.split(",") if k.strip()]
GEMINI_MODEL = os.environ.get("PYOB_GEMINI_MODEL", "gemini-2.5-flash")
LOCAL_MODEL = os.environ.get("PYOB_LOCAL_MODEL", "qwen3-coder:30b")

IGNORE_DIRS = {".git", ".github", ".pyob", "build_env", "venv", ".venv", "dist", "build", "__pycache__"}
IGNORE_FILES = {"package-lock.json", "action.yml", "Dockerfile", "index.html", "observer.html", "check.sh"}
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".html", ".css", ".json"}

class CyberpunkFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        prefix = f"{time.strftime('%H:%M:%S')} | "
        color = "\033[92m" if record.levelno == logging.INFO else "\033[93m"
        if record.levelno >= logging.ERROR: color = "\033[91m"
        return f"\033[94m{prefix}\033[0m{color}{record.getMessage()}\033[0m"

logger = logging.getLogger("PyOuroBoros")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(CyberpunkFormatter())
logger.addHandler(handler)
logger.propagate = False

class CoreUtilsMixin:
    target_dir: str
    memory_file: str
    key_cooldowns: dict[str, float]

    def get_user_approval(self, prompt_text: str, timeout: int = 220) -> str:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            return "PROCEED"
        print(f"\n{prompt_text}")
        return "PROCEED"

    def stream_gemini(self, prompt: str, api_key: str, on_chunk) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent?alt=sse&key={api_key.strip()}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1}}
        try:
            response = requests.post(url, headers=headers, json=data, stream=True, timeout=120)
            if response.status_code != 200:
                return f"ERROR_CODE_{response.status_code}"
            full_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        chunk = json.loads(line[6:])
                        text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                        on_chunk()
                        full_text += text
                    except Exception: pass
            return full_text
        except Exception as e:
            return f"ERROR_CODE_EXCEPTION: {e}"

    def stream_github_models(self, prompt: str, on_chunk) -> str:
        token = os.environ.get("GITHUB_TOKEN")
        if not token: return "ERROR_CODE_TOKEN_MISSING"
        endpoint = "https://models.inference.ai.azure.com/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = {"messages": [{"role": "user", "content": prompt}], "model": "Phi-4", "stream": True}
        try:
            res = requests.post(endpoint, headers=headers, json=data, stream=True, timeout=120)
            if res.status_code != 200: return f"ERROR_CODE_{res.status_code}"
            full_text = ""
            for line in res.iter_lines():
                if line:
                    decoded = line.decode("utf-8").replace("data: ", "")
                    if decoded == "[DONE]": break
                    try:
                        content = json.loads(decoded)["choices"][0]["delta"].get("content", "")
                        if content:
                            full_text += content
                            on_chunk()
                    except Exception: continue
            return full_text
        except Exception as e: return "ERROR_CODE_GH_FAILED"

    def _stream_single_llm(self, prompt: str, key: str = None, context: str = "") -> str:
        first_chunk = [False]
        start = time.time()
        is_cloud = os.environ.get("GITHUB_ACTIONS") == "true"
        
        def on_chunk():
            if not first_chunk[0]:
                first_chunk[0] = True
                source = f"Gemini ...{key[-4:]}" if key else "GitHub Models"
                print(f"🤖 AI Output ({source}): ", end="", flush=True)

        if key:
            res = self.stream_gemini(prompt, key, on_chunk)
        elif is_cloud:
            res = self.stream_github_models(prompt, on_chunk)
        else:
            return "ERROR_CODE_CLOUD_BLOCKED" # Failsafe: Ollama is completely disconnected here.

        print(f"\n[✅ Done: {len(res)//4} tokens in {time.time()-start:.1f}s]")
        return res

    def get_valid_llm_response(self, prompt: str, validator, context: str = "") -> str:
        attempts = 0
        is_cloud = os.environ.get("GITHUB_ACTIONS") == "true"
        
        while True:
            key = None
            now = time.time()
            available_keys = [k for k, cd in self.key_cooldowns.items() if now > cd]

            # 1. ENGINE SELECTION
            if available_keys:
                key = available_keys[attempts % len(available_keys)]
                logger.info(f"Attempting Gemini Key {attempts % len(available_keys) + 1}/{len(available_keys)}")
            elif is_cloud:
                logger.warning("⏳ Gemini keys out. Pivoting to GitHub Models (Phi-4)...")
            else:
                logger.error("❌ No engines available. Sleeping 60s.")
                time.sleep(60)
                continue

            # 2. EXECUTION
            response = self._stream_single_llm(prompt, key, context)

            # 3. RATE LIMITS & ERRORS
            if not response or "ERROR_CODE" in response:
                if "429" in response and key:
                    self.key_cooldowns[key] = now + 1200
                    logger.warning(f"⚠️ Key {key[-4:]} banned. 20m timeout.")
                
                wait = 60 if is_cloud else 10
                logger.warning(f"⚠️ API Error/Empty. Mandatory {wait}s sleep to refill tokens...")
                time.sleep(wait)
                attempts += 1
                continue

            # 4. VALIDATION
            if validator(response):
                if is_cloud: time.sleep(5)
                return response
            
            logger.warning("⚠️ Invalid output format. Backing off 20s...")
            time.sleep(20)
            attempts += 1
            
    def backup_workspace(self) -> dict:
        state = {}
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                if f in IGNORE_FILES: continue
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as f_obj: state[path] = f_obj.read()
                except: pass
        return state

    def restore_workspace(self, state: dict):
        for path, content in state.items():
            try:
                with open(path, 'w', encoding='utf-8') as f: f.write(content)
            except: pass

    def load_memory(self):
        return ""

    def save_ledger(self):
        pass

    def apply_xml_edits(self, source_code: str, llm_response: str) -> tuple:
        thought_match = re.search(r"<THOUGHT>(.*?)</THOUGHT>", llm_response, re.DOTALL | re.IGNORECASE)
        explanation = thought_match.group(1).strip() if thought_match else "No explanation."
        new_code = source_code
        pattern = re.compile(r"<EDIT>\s*<SEARCH>(.*?)</SEARCH>\s*<REPLACE>(.*?)</REPLACE>\s*</EDIT>", re.DOTALL | re.IGNORECASE)
        matches = list(pattern.finditer(llm_response))
        if not matches: return new_code, explanation, True
        success = True
        for m in matches:
            search, replace = m.group(1).strip(), m.group(2).strip()
            if search in new_code: new_code = new_code.replace(search, replace, 1)
            else: success = False
        return new_code, explanation, success
