import os
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any

@dataclass
class AppConfig:
    # Screen region for capturing questions: (left, top, width, height)
    question_region: Optional[Tuple[int, int, int, int]] = None
    
    # Sequence of click actions for Standard mode
    # e.g. [{"name": "Submit", "pos": (x,y), "color": (r,g,b), "check_color": True}]
    click_sequence: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"name": "Action 1", "pos": None, "color": None, "check_color": True}
    ])
    
    # Delay in seconds to simulate human thinking before submitting
    thinking_delay: float = 0.0
    
    # Delay in seconds between completing a question and starting the next one
    loop_delay: float = 1.0
    
    # Path to tesseract executable if it's not in the system PATH
    # Defaulting to common Windows installation path
    tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # Tesseract OCR language(s) — use '+' to combine, e.g. "ukr+rus+eng"
    ocr_language: str = "ukr+rus+eng"
    
    # Model to use in Antigravity CLI
    model: str = "Gemini 3.7 Flash (High)"
    
    # Work mode: "Standard" or "Google Forms"
    work_mode: str = "Standard"
    
    # Number of mouse wheel scroll clicks per scroll event in Google Forms mode
    # Each click scrolls ~100-120px; increase for larger screens
    scroll_amount: int = 5
    
    # Toggle logging of exact time taken per step
    show_step_timings: bool = True
    
    # Enable AI formatting and saving of final QA logs
    save_qa_logs: bool = True

config = AppConfig()
