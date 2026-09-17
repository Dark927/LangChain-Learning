import mss
from PIL import Image
import pytesseract
from typing import Dict, List, Tuple, Optional
from core.config import config
import difflib
import re

class VisionHandler:
    def __init__(self):
        self.sct = mss.mss()
        # Set tesseract path from config
        pytesseract.pytesseract.tesseract_cmd = config.tesseract_path

    def capture_region(self, region: Tuple[int, int, int, int]) -> Image.Image:
        """Captures the defined screen region and returns a PIL Image."""
        left, top, width, height = region
        monitor = {"top": top, "left": left, "width": width, "height": height}
        
        sct_img = self.sct.grab(monitor)
        # Convert to PIL Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img

    def extract_text_and_boxes(self, img: Image.Image, is_button: bool = False, invert: bool = False) -> Tuple[str, List[Dict]]:
        """
        Runs OCR on the image. 
        Returns the full concatenated text and a list of word dictionaries with their coordinates.
        """
        from PIL import ImageEnhance, ImageOps
        
        scale_factor = 1
        custom_config = r'--psm 3'
        
        if is_button:
            # Upscale and enhance contrast for better button text recognition
            scale_factor = 3
            img = img.convert('L') # grayscale
            
            if invert:
                img = ImageOps.invert(img)
                
            img = img.resize((img.width * scale_factor, img.height * scale_factor), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(2.0)
            custom_config = r'--psm 11' # Sparse text mode is much better for finding buttons in large areas

        full_text_words = []
        word_boxes = []

        if config.ocr_mode == "Math Mode" and not is_button:
            try:
                from pix2text import Pix2Text
                # Initialize once globally to avoid reloading models
                if not hasattr(self, "_p2t_instance"):
                    p2t_langs = []
                    if 'eng' in config.ocr_language: p2t_langs.append('en')
                    if 'rus' in config.ocr_language: p2t_langs.append('ru')
                    # Pix2Text/CnOCR primarily targets en/ru/ch, fallback to 'en' if neither
                    if not p2t_langs: p2t_langs = ['en']
                    self._p2t_instance = Pix2Text(analyzer_config={'languages': tuple(p2t_langs)})
                
                # Pix2Text prefers RGB images
                img_rgb = img.convert('RGB') if img.mode != 'RGB' else img
                res = self._p2t_instance.recognize(img_rgb, return_text=False)
                
                for item in res:
                    text = item.get("text", "").strip()
                    if text:
                        full_text_words.append(text)
                        pos = item.get("position", [])
                        if len(pos) == 4:
                            left = int(min(p[0] for p in pos) / scale_factor)
                            top = int(min(p[1] for p in pos) / scale_factor)
                            right = int(max(p[0] for p in pos) / scale_factor)
                            bottom = int(max(p[1] for p in pos) / scale_factor)
                            word_boxes.append({
                                "text": text,
                                "left": left,
                                "top": top,
                                "width": right - left,
                                "height": bottom - top
                            })
                return " ".join(full_text_words), word_boxes
            except ImportError:
                print("Pix2Text not installed, falling back to Tesseract.")
            except Exception as e:
                print(f"Pix2Text error: {e}, falling back to Tesseract.")

        try:
            # Refresh path from config in case user changed it after init
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
            data = pytesseract.image_to_data(
                img,
                output_type=pytesseract.Output.DICT,
                config=custom_config,
                lang=config.ocr_language,
            )
        except FileNotFoundError:
            raise RuntimeError(f"Tesseract executable not found at {config.tesseract_path}. Please install Tesseract OCR and update the path in config.py if necessary.")

        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            # Filter out empty text and low confidence words
            if int(data['conf'][i]) > -1 and len(text) > 0:
                full_text_words.append(text)
                word_boxes.append({
                    "text": text,
                    "left": data['left'][i] // scale_factor,
                    "top": data['top'][i] // scale_factor,
                    "width": data['width'][i] // scale_factor,
                    "height": data['height'][i] // scale_factor
                })
                
        full_text = " ".join(full_text_words)
        return full_text, word_boxes

    def _normalize_text(self, text: str) -> str:
        # Strip exact known noise first
        text = re.sub(r'\b[O0]{2,}\b', '', text)
        text = re.sub(r'\|\)', '', text)
        text = re.sub(r'\+:', '', text)
        # Preserve all unicode word characters (including Cyrillic/Ukrainian); strip only punctuation and whitespace
        return re.sub(r'[^\w]', '', text.lower(), flags=re.UNICODE)

    def find_click_point(self, answer_text: str, word_boxes: List[Dict]) -> Optional[Tuple[int, int]]:
        """
        Robustly finds the answer text within the word boxes using difflib.
        Returns absolute screen (x, y) coordinates.
        """
        if not answer_text or not config.question_region or not word_boxes:
            return None
            
        answer_words = answer_text.split()
        if not answer_words:
            return None
            
        n = len(answer_words)
        target_norm = self._normalize_text(answer_text)
        
        best_score = 0
        best_box = None
        
        # Sliding window over the word_boxes
        for i in range(len(word_boxes)):
            for j in range(1, n + 3):  # allow slight length mismatch
                if i + j > len(word_boxes):
                    break
                
                window_boxes = word_boxes[i:i+j]
                window_text = " ".join(b["text"] for b in window_boxes)
                window_norm = self._normalize_text(window_text)
                
                # If both are empty after normalization, skip
                if not target_norm or not window_norm:
                    continue
                    
                score = difflib.SequenceMatcher(None, target_norm, window_norm).ratio()
                
                if score > best_score:
                    best_score = score
                    # Use the center of the first word in the best matching window
                    best_box = window_boxes[0]
                    
        # If we have a reasonable match (lowered to 0.55 to handle clean AI vs mangled screen text)
        if best_box and best_score > 0.55:
            center_x = best_box["left"] + (best_box["width"] // 2)
            center_y = best_box["top"] + (best_box["height"] // 2)
            abs_x = config.question_region[0] + center_x
            abs_y = config.question_region[1] + center_y
            print(f"[Vision] Found match with score {best_score:.2f}")
            return (abs_x, abs_y)
            
        print(f"[Vision] Best match score {best_score:.2f} was too low.")
        return None


