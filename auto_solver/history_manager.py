import json
import os
import uuid
import datetime

HISTORY_FILE = "logs_history.json"

def load_history() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history: list[dict]):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def add_log(title: str, qa_pairs: list[dict]):
    history = load_history()
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now().isoformat(),
        "title": title,
        "qa_pairs": qa_pairs
    }
    history.append(entry)
    save_history(history)

def delete_log(log_id: str):
    history = load_history()
    history = [log for log in history if log["id"] != log_id]
    save_history(history)

def rename_log(log_id: str, new_title: str):
    history = load_history()
    for log in history:
        if log["id"] == log_id:
            log["title"] = new_title
            break
    save_history(history)
