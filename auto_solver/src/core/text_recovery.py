import re

def strip_ui_artifacts(text: str) -> str:
    """Removes known UI garbage like radio button misreads and random symbols."""
    # Remove O0O0 or 0O0O circles (radio button artifacts)
    text = re.sub(r'\b[O0]{2,}\b', '', text)
    # Remove rogue symbols like |), +:, Tryagain
    text = re.sub(r'\|\)', '', text)
    text = re.sub(r'\+:', '', text)
    text = re.sub(r'(?i)\btry\s*again\b', '', text)
    # Clean up excessive whitespace
    return re.sub(r'\s{2,}', ' ', text).strip()

def recover_ocr_text_ai(text: str, log_cb, stop_check) -> str:
    """Uses the configured LLM to contextually fix typos like 'c4r' -> 'car' without destroying code."""
    prompt = (
        "You are an OCR text recovery assistant. Your ONLY job is to fix typos (e.g., c4r -> car), "
        "fix spacing (thisis -> this is), and remove UI noise. "
        "DO NOT answer the question. DO NOT change the meaning. "
        "Preserve all code snippets and technical terms exactly. "
        "Output ONLY the cleaned text, nothing else."
    )
    
    from core.config import config
    
    log_cb("[Recovery] Running AI OCR Correction on mangled text...")
    
    full_prompt = f"{prompt}\n\nRAW OCR TEXT:\n{text}"
    
    result = None
    if config.model.startswith("Local: "):
        from agents.agy_client import _run_local_model
        raw = _run_local_model(full_prompt, log_cb, max_tokens=1500, system_prompt=prompt)
        result = raw.strip() if raw else ""
    elif "Antigravity" in config.model:
        from agents.agy_client import _run_agy
        result = _run_agy(full_prompt, stop_check, log_cb)
    else:
        from agents.fallback_client import ask_fallback
        result = ask_fallback(full_prompt, config.model, log_cb, stop_check)
        
    if not result:
        log_cb("[Recovery] AI correction failed or returned empty. Using raw text.")
        return text
        
    # Sometimes models prepend "Here is the cleaned text:"
    clean_result = re.sub(r'(?i)^(here is the|cleaned|fixed).*?:\s*', '', result).strip()
    return clean_result
