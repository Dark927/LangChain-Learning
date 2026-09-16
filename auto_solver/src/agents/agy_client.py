import subprocess
import time
import re
from core.config import config

# Maximum seconds to wait for an agy subprocess before killing it and retrying
_AGENT_TIMEOUT_SEC: int = 45
# Maximum characters of screen text sent to the agent to keep prompts lean
_SCREEN_TEXT_MAX_CHARS: int = 3000

# Global cache to prevent reloading the massive GGUF model files into RAM on every call
_LOCAL_MODEL_CACHE = {
    "filename": None,
    "instance": None
}


def _get_cached_local_model(filename: str):
    """
    Returns the loaded GPT4All instance for the given filename.
    Loads it if not already in memory, or if the requested model changed.
    """
    if _LOCAL_MODEL_CACHE["filename"] == filename and _LOCAL_MODEL_CACHE["instance"]:
        return _LOCAL_MODEL_CACHE["instance"]
    
    # Clean up old instance if exists
    if _LOCAL_MODEL_CACHE["instance"]:
        del _LOCAL_MODEL_CACHE["instance"]
        _LOCAL_MODEL_CACHE["instance"] = None
        
    from gpt4all import GPT4All
    from agents.local_models import get_models_dir
    
    mdl = GPT4All(filename, model_path=get_models_dir(), allow_download=False)
    
    _LOCAL_MODEL_CACHE["filename"] = filename
    _LOCAL_MODEL_CACHE["instance"] = mdl
    return mdl



def _run_agy(prompt: str, check_abort=None, live_log_callback=None) -> str:
    """
    Spawns a single agy subprocess, polls until it exits, and returns stdout.
    Kills the process if stop is requested or the call exceeds _AGENT_TIMEOUT_SEC.
    Returns empty string on any failure.
    """
    import sys
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    # Strip the UI display prefix before passing the model name to the CLI
    agy_model_name = re.sub(r"^Antigravity\s*[-—]\s*|^Antigravity\s+", "", config.model).strip()
    proc = subprocess.Popen(
        ["agy", "--print", prompt, "--model", agy_model_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
        creationflags=creationflags
    )
    
    import queue
    import threading
    q = queue.Queue()
    
    def reader(pipe, q):
        for line in iter(pipe.readline, ''):
            q.put(line)
        pipe.close()
        
    t = threading.Thread(target=reader, args=(proc.stdout, q))
    t.daemon = True
    t.start()

    deadline = time.monotonic() + _AGENT_TIMEOUT_SEC
    output_lines = []
    
    while True:
        try:
            line = q.get(timeout=0.1)
            output_lines.append(line)
            if live_log_callback:
                live_log_callback(line.rstrip('\n'))
        except queue.Empty:
            if proc.poll() is not None:
                break
            if check_abort and check_abort():
                proc.kill()
                return ""
            if time.monotonic() > deadline:
                proc.kill()
                msg = f"[Agent] Timed out after {_AGENT_TIMEOUT_SEC}s — killed."
                if live_log_callback:
                    live_log_callback(msg)
                print(msg)
                return ""

    # Drain remaining
    while not q.empty():
        line = q.get()
        output_lines.append(line)
        if live_log_callback:
            live_log_callback(line.rstrip('\n'))

    if proc.returncode != 0:
        err = "".join(output_lines).strip()[:200]
        print(f"[Agent] Error: {err}")
        return ""

    return "".join(output_lines).strip()


def _extract_options(question_text: str) -> list[str]:
    """
    Parses all answer options from a question block.
    Handles formats: 'a. text', 'a) text', '(a) text', 'a: text'
    Returns a list of bare option texts (without the letter prefix).
    """
    pattern = re.compile(
        r"(?:^|\n)\s*(?:\([a-dA-D]\)|[a-dA-D][.):\s])\s*(.+?)(?=\n\s*(?:\([a-dA-D]\)|[a-dA-D][.):\s])|$)",
        re.DOTALL
    )
    return [m.group(1).strip() for m in pattern.finditer(question_text)]


def _resolve_local_answer(raw: str, question_text: str) -> str:
    """
    Maps the local model's raw response to exactly one of the answer options
    extracted from the question text.

    Strategy (in priority order):
    1. Check if raw is a single letter (a-d) — look up the matching option directly.
    2. Check if raw starts with 'letter. text' pattern — strip the prefix.
    3. Strip common preamble phrases ('the correct answer is ...', 'answer: ...').
    4. Find which extracted option is a substring of the raw response (case-insensitive).
    5. Use difflib to find the closest matching option.
    6. Return the stripped raw as a last resort.
    """
    import difflib

    options = _extract_options(question_text)
    raw_stripped = raw.strip()

    # 1. Single bare letter
    if re.match(r"^[a-dA-D]\.?$", raw_stripped):
        letter = raw_stripped[0].lower()
        idx = ord(letter) - ord("a")
        if 0 <= idx < len(options):
            return options[idx]

    # 2. Starts with letter prefix: 'b. Led by...' or '(b) Led by...'
    m = re.match(r"^\(?([a-dA-D])\)?[.):\s]+(.+)", raw_stripped, re.DOTALL)
    if m:
        letter = m.group(1).lower()
        text_after = m.group(2).strip().splitlines()[0].strip()
        idx = ord(letter) - ord("a")
        if 0 <= idx < len(options):
            return options[idx]
        # Fallback: use stripped text after the letter
        raw_stripped = text_after

    # 3. Strip common model preamble phrases
    preamble = re.compile(
        r"^(?:the\s+(?:correct\s+)?answer\s+is|answer\s*:|correct\s*:|option\s*:)\s*",
        re.IGNORECASE
    )
    cleaned = preamble.sub("", raw_stripped).strip()
    # Strip letter prefix that may appear after preamble ('b. Led by...')
    m2 = re.match(r"^\(?([a-dA-D])\)?[.):\s]+(.+)", cleaned, re.DOTALL)
    if m2:
        letter = m2.group(1).lower()
        idx = ord(letter) - ord("a")
        if 0 <= idx < len(options):
            return options[idx]
        cleaned = m2.group(2).strip().splitlines()[0].strip()
    else:
        cleaned = cleaned.splitlines()[0].strip()

    if not options:
        return cleaned if len(cleaned) >= 3 else ""

    # 4. Exact substring containment (case-insensitive)
    cleaned_lower = cleaned.lower()
    for opt in options:
        if opt.lower() in cleaned_lower or cleaned_lower in opt.lower():
            return opt

    # 5. Difflib closest match
    best = difflib.get_close_matches(cleaned, options, n=1, cutoff=0.4)
    if best:
        return best[0]

    # 6. Last resort — return whatever was cleaned up if it's long enough
    return cleaned if len(cleaned) >= 3 else ""


def _mask_failed_options(question_text: str, failed_answers: list[str]) -> str:
    """
    Physically replaces the text of known wrong answers from the question block
    so the model cannot possibly select or read them.
    """
    if not failed_answers:
        return question_text
        
    import difflib
    
    lines = question_text.split('\n')
    filtered_lines = []
    
    for line in lines:
        is_wrong = False
        line_clean = line.strip().lower()
        if len(line_clean) > 3:
            for fa in failed_answers:
                fa_clean = fa.strip().lower()
                
                char_sim = difflib.SequenceMatcher(None, fa_clean, line_clean).ratio()
                
                words1 = set(re.findall(r'\w+', line_clean))
                words2 = set(re.findall(r'\w+', fa_clean))
                word_sim = len(words1.intersection(words2)) / len(words1.union(words2)) if words1 or words2 else 0.0
                
                if max(char_sim, word_sim) > 0.50 or fa_clean in line_clean or line_clean in fa_clean:
                    is_wrong = True
                    break
        
        if not is_wrong:
            filtered_lines.append(line)
            
    return '\n'.join(filtered_lines)


def _run_local_model(prompt: str, live_log_callback=None, max_tokens: int = 120, system_prompt: str = None) -> str:
    """Runs a locally installed GPT4All model and returns its text response."""
    from agents.local_models import get_installed_models, get_models_dir
    model_pretty = config.model.replace("Local: ", "")
    model_filename = None
    for m in get_installed_models():
        if m["name"] == model_pretty:
            model_filename = m["filename"]
            break

    if not model_filename:
        if live_log_callback: live_log_callback(f"[Local Agent] Model file not found for '{model_pretty}'")
        return ""

    if live_log_callback: live_log_callback(f"[Local Agent] Running {model_pretty}...")
    try:
        mdl = _get_cached_local_model(model_filename)
        chat_kwargs = {"system_prompt": system_prompt} if system_prompt else {}
        with mdl.chat_session(**chat_kwargs):
            raw = mdl.generate(prompt, max_tokens=max_tokens)
        if live_log_callback: live_log_callback("[Local Agent] Done.")
        return raw.strip() if raw else ""
    except Exception as e:
        if live_log_callback: live_log_callback(f"[Local Agent] Error: {e}")
        return ""


def _try_local_models_fallback(prompt: str, question_text: str, live_log_callback=None, max_tokens: int = 120, system_prompt: str = None) -> str:
    """
    Iterates over all installed local models and tries each one until a non-empty
    answer is produced. Used as a last-resort fallback when every API model fails.
    Only runs when config.use_local_as_fallback is True.
    """
    if not getattr(config, "use_local_as_fallback", True):
        return ""

    from agents.local_models import get_installed_models, get_models_dir
    installed = get_installed_models()
    if not installed:
        return ""

    if live_log_callback:
        live_log_callback(f"[Local Fallback] Trying {len(installed)} local model(s)...")

    for m in installed:
        try:
            if live_log_callback:
                live_log_callback(f"[Local Fallback] Trying {m['name']}...")
            mdl = _get_cached_local_model(m["filename"])
            chat_kwargs = {"system_prompt": system_prompt} if system_prompt else {}
            with mdl.chat_session(**chat_kwargs):
                raw = mdl.generate(prompt, max_tokens=max_tokens)
            if raw and raw.strip():
                resolved = _resolve_local_answer(raw.strip(), question_text)
                if live_log_callback:
                    live_log_callback(f"[Local Fallback] Got answer from {m['name']}: {resolved}")
                return resolved
        except Exception as e:
            if live_log_callback:
                live_log_callback(f"[Local Fallback] {m['name']} failed: {e}")
    return ""


def ask_agent(question_text: str, check_abort=None, live_log_callback=None, failed_answers=None) -> str:
    """
    Sends a single multiple-choice question to the agent and returns the answer text only.
    If Antigravity returns no answer, automatically falls back to configured external LLM.
    Used by Standard mode.
    """
    failed_prompt = ""
    masked_question_text = question_text
    if failed_answers:
        failed_prompt = "\nCRITICAL WARNING: The following answers are INCORRECT. DO NOT output them under any circumstances. You MUST choose a different option:\n" + "\n".join(f"❌ {a}" for a in failed_answers) + "\n"
        masked_question_text = _mask_failed_options(question_text, failed_answers)

    system_prompt = (
        "You are an expert test-taking AI.\n"
        "Your ONLY task is to output the exact text of the correct answer.\n"
        "DO NOT output letters like A, B, C, or D.\n"
        "DO NOT output explanations.\n"
        "If the user provides a list of INCORRECT answers, you MUST ignore them and choose a DIFFERENT option. Outputting a known incorrect answer is a critical failure."
    )
    user_prompt = f"{failed_prompt}\n{masked_question_text}".strip()
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    result = None
    if config.model.startswith("Local: "):
        raw = _run_local_model(user_prompt, live_log_callback, system_prompt=system_prompt)
        result = _resolve_local_answer(raw, question_text) if raw else ""
    elif "Antigravity" in config.model:
        result = _run_agy(full_prompt, check_abort, live_log_callback)
        if not result:
            if live_log_callback:
                live_log_callback("[Agent] Main Agent failed — starting fallback cascade...")
            from agents.fallback_client import ask_fallback
            result = ask_fallback(full_prompt, None, live_log_callback, check_abort)
    else:
        # API key model selected directly (Groq, etc.)
        from agents.fallback_client import ask_fallback
        result = ask_fallback(full_prompt, config.model, live_log_callback, check_abort)

    # Last-resort: try locally installed models if everything else failed
    if not result and not config.model.startswith("Local: "):
        result = _try_local_models_fallback(user_prompt, question_text, live_log_callback, system_prompt=system_prompt)

    # Absolute Safeguard: Never return an answer we know is wrong OR a garbage output
    clean_result = result.strip() if result else ""
    clean_failed = [f.strip() for f in failed_answers] if failed_answers else []
    
    is_bad = False
    if not clean_result or len(clean_result) < 3:
        is_bad = True
        if live_log_callback:
            live_log_callback(f"[Safety] Model failed to generate a valid answer. Forcing alternative.")
    elif clean_result in clean_failed:
        is_bad = True
    else:
        # Fuzzy check the result against failed answers to catch partial matches
        import difflib
        for cf in clean_failed:
            if difflib.SequenceMatcher(None, cf.lower(), clean_result.lower()).ratio() > 0.8:
                is_bad = True
                break

    if is_bad:
        if live_log_callback and clean_result and len(clean_result) >= 3:
            live_log_callback(f"[Safety] Model stubbornly chose known wrong answer. Forcing alternative.")
            options = _extract_options(question_text)
            valid_options = [o for o in options if o.strip() not in clean_failed]
            
            if valid_options:
                result = valid_options[0]
            else:
                # Regex failed to parse options (e.g. OCR noise destroyed 'a.', 'b.'). Chunk the text manually.
                import re
                import difflib
                chunks = re.split(r'\n|\s{2,}|(?<=[.?])\s+', question_text)
                for chunk in chunks:
                    c = chunk.strip()
                    if len(c) < 5 or c.lower().startswith("question"): continue
                    
                    c_is_failed = False
                    for cf in clean_failed:
                        if difflib.SequenceMatcher(None, cf.lower(), c.lower()).ratio() > 0.50 or cf.lower() in c.lower() or c.lower() in cf.lower():
                            c_is_failed = True
                            break
                    if not c_is_failed:
                        result = c
                        break
            
            if live_log_callback and result and result != clean_result:
                live_log_callback(f"[Safety] Forcefully selected: '{result}'")
            elif not result:
                result = ""

    return result


def ask_agent_google_forms_batch(
    screen_text: str,
    answered_questions: list[str],
    check_abort=None,
    live_log_callback=None
) -> list[tuple[str, str]]:
    """
    Sends the screen text ONCE and receives ALL visible unanswered Q/A pairs in a
    single LLM round-trip. One call per screen instead of one call per question.

    Returns a list of (question, answer) tuples in order.
    Returns an empty list when the agent signals DONE or on any error.
    """
    # Trim screen text to keep prompt size bounded and response fast
    trimmed = screen_text[:_SCREEN_TEXT_MAX_CHARS]

    answered_str = (
        "\n".join(f"- {q}" for q in dict.fromkeys(answered_questions))
        if answered_questions
        else "None"
    )

    system_prompt = (
        "You are an expert test-taking AI.\n"
        "For each unanswered question in the text, reply with the exact text of the correct option.\n"
        "Format your reply strictly as alternating lines of 'Q: <question_text>' and 'A: <exact_answer_text>'.\n"
        "Do not include any other text."
    )
    user_prompt = (
        "Answer the unanswered questions in the screen text below.\n"
        "Format example:\n"
        "Q: What is the capital of France?\n"
        "A: Paris\n"
        "Q: Which of these are fruits?\n"
        "A: Apple\n"
        "A: Banana\n\n"
        f"Already answered:\n{answered_str}\n\n"
        f"Screen text:\n{trimmed}"
    )
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    reply = None
    if config.model.startswith("Local: "):
        reply = _run_local_model(user_prompt, live_log_callback, max_tokens=300, system_prompt=system_prompt)
    elif "Antigravity" in config.model:
        reply = _run_agy(full_prompt, check_abort, live_log_callback)
        if not reply:
            if live_log_callback:
                live_log_callback("[Agent] Main Agent failed — starting fallback cascade...")
            from agents.fallback_client import ask_fallback
            reply = ask_fallback(full_prompt, None, live_log_callback, check_abort)
    else:
        from agents.fallback_client import ask_fallback
        reply = ask_fallback(full_prompt, config.model, live_log_callback, check_abort)

    # Last-resort: try locally installed models if everything else failed
    if not reply and not config.model.startswith("Local: "):
        raw_fb = _try_local_models_fallback(user_prompt, screen_text, live_log_callback, max_tokens=300, system_prompt=system_prompt)
        if raw_fb:
            reply = raw_fb

    if not reply:
        return None

    if reply.strip().upper() == "DONE":
        return []

    return _parse_batch_reply(reply)


def _parse_batch_reply(reply: str) -> list[tuple[str, str]]:
    """
    Parses alternating Q:/A: lines into (question, answer) tuples.
    Tolerates extra whitespace and case variations.
    Allows multiple A: lines for a single Q: to support checkboxes.
    """
    pairs: list[tuple[str, str]] = []
    current_q: str | None = None

    for raw_line in reply.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        q_match = re.match(r'^[Qq]\s*:\s*(.+)', line)
        a_match = re.match(r'^[Aa]\s*:\s*(.+)', line)

        if q_match:
            current_q = q_match.group(1).strip()
        elif a_match and current_q is not None:
            pairs.append((current_q, a_match.group(1).strip()))
            # We do NOT reset current_q = None here so that subsequent A: lines
            # bind to the same question for multiple-choice checkbox support.

    return pairs

import json

def format_qa_log(qa_log: list[dict], check_abort=None, live_log_callback=None) -> dict:
    """
    Sends raw QA logs to the agent to clean up OCR artifacts, format perfectly,
    and generate a title.
    Returns a dict: {"title": "Generated Name", "qa_pairs": [{"q": "Question", "a": "Answer"}]}
    """
    if not qa_log:
        return {}
        
    raw_text = "\n".join(f"Q: {entry['question']}\nA: {entry['answer']}" for entry in qa_log)
    
    prompt = (
        "You are an expert data cleaner. I have a list of raw questions and answers extracted via OCR.\n"
        "Clean up any OCR artifacts, typos, or completely unrelated random words that might have been accidentally captured.\n"
        "Generate a short, descriptive title for this test session based on its topic.\n\n"
        "You MUST reply with ONLY a valid JSON object matching this exact schema:\n"
        '{\n'
        '  "title": "Topic of the Test",\n'
        '  "qa_pairs": [\n'
        '    {"q": "Cleaned Question", "a": "Cleaned Answer"}\n'
        '  ]\n'
        '}\n\n'
        f"Raw Data:\n{raw_text}"
    )
    
    reply = _run_agy(prompt, check_abort, live_log_callback)
    
    if not reply:
        return {}
        
    # Extract JSON from reply in case the model adds markdown formatting
    try:
        json_match = re.search(r'\{.*\}', reply.replace('\n', ' '), re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        print(f"[Agent] Failed to parse JSON: {e}")
        
    return {}
