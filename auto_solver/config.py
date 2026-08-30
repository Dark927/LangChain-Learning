import os
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class AppConfig:
    # Screen region for capturing questions: (left, top, width, height)
    question_region: Optional[Tuple[int, int, int, int]] = None
    
    # Coordinates of the submit button: (x, y)
    submit_button_pos: Optional[Tuple[int, int]] = None
    
    # The required RGB color of the submit button pixel
    submit_button_color: Optional[Tuple[int, int, int]] = None
    
    # Delay in seconds to simulate human thinking before submitting
    thinking_delay: float = 0.0
    
    # Delay in seconds between completing a question and starting the next one
    loop_delay: float = 1.0
    
    # Path to tesseract executable if it's not in the system PATH
    # Defaulting to common Windows installation path
    tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # Model to use in Antigravity CLI
    model: str = "Gemini 3.7 Flash (High)"
    
config = AppConfig()
