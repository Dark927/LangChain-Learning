import time
import pyautogui
from pynput import keyboard
import threading
from typing import Tuple
from config import config
from vision import VisionHandler
from agy_client import ask_agent
import logging
import os

# Set up Q&A trace logger
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa_trace.log")
qa_logger = logging.getLogger("QATrace")
qa_logger.setLevel(logging.INFO)
if not qa_logger.handlers:
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setFormatter(logging.Formatter('[%(asctime)s]\n%(message)s\n' + '-'*50))
    qa_logger.addHandler(fh)

class Runner:
    def __init__(self):
        self.vision = VisionHandler()
        self.is_running = False
        self.stop_requested = False
        self.is_paused = False
        
        # Setup pynput listener for emergency stop and pause
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        
    def on_press(self, key):
        if key == keyboard.Key.esc:
            print("\n[ESC pressed] Emergency stop requested.")
            self.stop_requested = True
            self.is_running = False
        elif key == keyboard.Key.f8:
            self.is_paused = not self.is_paused
            state = "PAUSED" if self.is_paused else "RESUMED"
            print(f"\n[F8 pressed] Automation {state}.")

    def safe_sleep(self, duration: float) -> bool:
        """Sleeps for duration but returns False immediately if stop is requested."""
        steps = int(duration / 0.1)
        for _ in range(max(1, steps)):
            if self.stop_requested:
                return False
            time.sleep(0.1)
        return True

    def color_match(self, c1: Tuple[int,int,int], c2: Tuple[int,int,int], tolerance=20) -> bool:
        return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))

    def run_loop(self):
        if not config.question_region:
            print("Error: Question region is not set.")
            return
            
        if not config.submit_button_pos or not config.submit_button_color:
            print("Error: Submit button position is not set.")
            return
            
        self.is_running = True
        self.stop_requested = False
        self.is_paused = False
        print("Automation started. Press F8 to Pause/Resume. Press ESC to Stop.")
        
        while self.is_running and not self.stop_requested:
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            try:
                # 1. Capture screen
                print("Capturing screen...")
                img = self.vision.capture_region(config.question_region)
                
                # 2. Extract text
                print("Running OCR...")
                text, word_boxes = self.vision.extract_text_and_boxes(img)
                print(f"Extracted Text: {text}")
                
                if not text.strip():
                    print("No text found. Retrying in 1 second...")
                    if not self.safe_sleep(1): break
                    continue
                    
                qa_logger.info(f"QUESTION EXTRACTED:\n{text.strip()}")
                    
                # 3. Ask Agent
                print("Asking Antigravity...")
                # Pass lambda to allow subprocess kill if stop requested
                answer_text = ask_agent(text, lambda: self.stop_requested)
                
                if self.stop_requested:
                    break
                    
                print(f"Agent replied: {answer_text}")
                
                if not answer_text:
                    print("No answer from agent. Retrying...")
                    if not self.safe_sleep(1): break
                    continue
                    
                qa_logger.info(f"AGENT ANSWER:\n{answer_text.strip()}")
                    
                # 4. Find where to click
                click_point = self.vision.find_click_point(answer_text, word_boxes)
                if not click_point:
                    print("Could not find the answer text on the screen to click. Skipping to next iteration.")
                    if not self.safe_sleep(1): break
                    continue
                    
                # 5. Click the answer
                if self.stop_requested: break
                print(f"Clicking answer at {click_point}...")
                pyautogui.moveTo(*click_point, duration=0.2)
                pyautogui.click()
                
                # Wait briefly after clicking answer
                if not self.safe_sleep(0.2): break
                
                # 5.5 Simulate Thinking Delay
                if config.thinking_delay > 0:
                    print(f"Simulating human thinking... waiting {config.thinking_delay} seconds.")
                    if not self.safe_sleep(config.thinking_delay): break
                
                # 6. Wait for submit button to turn expected color
                print("Waiting for submit button to be ready...")
                target_color = config.submit_button_color
                pos = config.submit_button_pos
                found_color = False
                
                # Wait up to 10 seconds for the button to turn the correct color
                for _ in range(100):
                    if self.stop_requested: break
                    current_color = pyautogui.pixel(*pos)
                    if self.color_match(current_color, target_color):
                        found_color = True
                        break
                    time.sleep(0.1)
                    
                if self.stop_requested: break
                
                if not found_color:
                    print("Submit button did not turn the expected color after 10 seconds. Stopping.")
                    self.is_running = False
                    break
                    
                print(f"Clicking submit button at {pos}...")
                pyautogui.moveTo(*pos, duration=0.2)
                pyautogui.click()
                
                # 7. Wait for next question
                print(f"Waiting {config.loop_delay} seconds...")
                if not self.safe_sleep(config.loop_delay): break
                
            except Exception as e:
                print(f"Error in runner loop: {e}")
                if not self.safe_sleep(1): break
                
        print("Automation stopped.")
