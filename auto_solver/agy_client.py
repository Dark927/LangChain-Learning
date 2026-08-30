import subprocess
import time
from config import config

def ask_agent(question_text: str, check_abort=None) -> str:
    """
    Sends the question text to the Antigravity CLI and returns the correct answer text.
    """
    prompt = (
        "Here is a new multiple-choice question. "
        "Reply with ONLY the exact text of the correct option. "
        "NO explanation. NO extra words. Just the answer text.\n\n"
        f"{question_text}"
    )
    
    # Run the agy CLI non-interactively but using the same session
    proc = subprocess.Popen(
        ["agy", "--print", prompt, "--model", config.model, "--continue"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    
    while proc.poll() is None:
        if check_abort and check_abort():
            proc.kill()
            return ""
        time.sleep(0.1)
        
    stdout, stderr = proc.communicate()
    
    if proc.returncode != 0:
        print(f"Error from agy CLI: {stderr}")
        return ""
        
    return stdout.strip()
