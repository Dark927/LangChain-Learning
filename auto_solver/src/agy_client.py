import subprocess
import time
import re
from config import config

# Maximum seconds to wait for an agy subprocess before killing it and retrying
_AGENT_TIMEOUT_SEC: int = 45
# Maximum characters of screen text sent to the agent to keep prompts lean
_SCREEN_TEXT_MAX_CHARS: int = 3000


def _run_agy(prompt: str, check_abort=None, live_log_callback=None) -> str:
    """
    Spawns a single agy subprocess, polls until it exits, and returns stdout.
    Kills the process if stop is requested or the call exceeds _AGENT_TIMEOUT_SEC.
    Returns empty string on any failure.
    """
    import sys
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    proc = subprocess.Popen(
        ["agy", "--print", prompt, "--model", config.model],
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


def ask_agent(question_text: str, check_abort=None, live_log_callback=None) -> str:
    """
    Sends a single multiple-choice question to the agent and returns the answer text only.
    If Antigravity returns no answer, automatically falls back to configured external LLM.
    Used by Standard mode.
    """
    prompt = (
        "Here is a new multiple-choice question. "
        "Reply with ONLY the exact text of the correct option. "
        "NO explanation. NO extra words. Just the answer text.\n\n"
        f"{question_text}"
    )
    result = _run_agy(prompt, check_abort, live_log_callback)

    if not result and config.fallback_model:
        if live_log_callback:
            live_log_callback("[Agent] No answer from Antigravity — trying fallback model...")
        from fallback_client import ask_fallback
        result = ask_fallback(prompt, config.fallback_model, live_log_callback)

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

    prompt = (
        "You are a form answering engine reading OCR text from a Google Form.\n"
        "Find ALL multiple-choice questions visible that are NOT in the answered list.\n\n"
        "OUTPUT FORMAT — one block per question, nothing else:\n"
        "Q: <question text verbatim>\n"
        "A: <correct answer verbatim>\n\n"
        "STRICT RULES:\n"
        "- Output ONLY Q:/A: line pairs. No numbers, no markdown, no explanation.\n"
        "- If a question has multiple correct answers (e.g., checkboxes) and you are sure, output multiple A: lines for that Q.\n"
        "- If no unanswered questions are visible, output only: DONE\n\n"
        "Example (2 questions, one with multiple answers):\n"
        "Q: What is the capital of France?\n"
        "A: Paris\n"
        "Q: Which of these are fruits?\n"
        "A: Apple\n"
        "A: Banana\n\n"
        f"Already answered:\n{answered_str}\n\n"
        f"Screen text:\n{trimmed}"
    )

    reply = _run_agy(prompt, check_abort, live_log_callback)

    if not reply and config.fallback_model:
        if live_log_callback:
            live_log_callback("[Agent] No answer from Antigravity — trying fallback model...")
        from fallback_client import ask_fallback
        reply = ask_fallback(prompt, config.fallback_model, live_log_callback)

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
