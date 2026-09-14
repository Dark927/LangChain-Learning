import time
import pyautogui
from pynput import keyboard
import threading
from typing import Tuple, Callable, Optional
from config import config
from vision import VisionHandler
from agy_client import ask_agent, ask_agent_google_forms_batch
import logging
import os

# Constant for Windows: 1 wheel notch = 120 units
_SCROLL_NOTCH_MULTIPLIER = 120

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
        self.qa_log = []
        
        # Callbacks for UI updates
        self.on_finish_callback: Optional[Callable] = None
        self.on_log_callback: Optional[Callable[[str], None]] = None
        self.on_status_callback: Optional[Callable[[str], None]] = None
        
        # Setup pynput listener for emergency stop and pause
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        
    def _log(self, msg: str):
        print(msg)
        if self.on_log_callback:
            self.on_log_callback(msg)
            
    def _set_status(self, status: str):
        if self.on_status_callback:
            self.on_status_callback(status)

    def on_press(self, key):
        if key == keyboard.Key.esc:
            self._log("\n[ESC pressed] Emergency stop requested.")
            self.stop_requested = True
            self.is_running = False
        elif key == keyboard.Key.f8:
            self.is_paused = not self.is_paused
            state = "PAUSED" if self.is_paused else "RESUMED"
            self._log(f"\n[F8 pressed] Automation {state}.")
            if self.is_paused:
                self._set_status("⏸️ Paused")
            else:
                self._set_status("▶️ Resumed")

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
        if config.work_mode == "Google Forms":
            self.run_google_forms_loop()
            return

        if not config.question_region:
            self._log("Error: Question region is not set.")
            return
            
        if not config.submit_button_pos or not config.submit_button_color:
            self._log("Error: Submit button position is not set.")
            return
            
        self.is_running = True
        self.stop_requested = False
        self.is_paused = False
        self._log("Automation started. Press F8 to Pause/Resume. Press ESC to Stop.")
        self._set_status("▶️ Started")
        
        while self.is_running and not self.stop_requested:
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            try:
                # 1. Capture screen
                self._set_status("📸 Capturing screen...")
                self._log("Capturing screen...")
                img = self.vision.capture_region(config.question_region)
                
                # 2. Extract text
                self._set_status("🔍 Running OCR...")
                self._log("Running OCR...")
                text, word_boxes = self.vision.extract_text_and_boxes(img)
                self._log(f"Extracted Text: {text}")
                
                if not text.strip():
                    self._log("No text found. Retrying in 1 second...")
                    if not self.safe_sleep(1): break
                    continue
                    
                qa_logger.info(f"QUESTION EXTRACTED:\n{text.strip()}")
                    
                # 3. Ask Agent
                self._set_status("🤖 Asking AI...")
                self._log("Asking Antigravity...")
                answer_text = ask_agent(text, lambda: self.stop_requested)
                
                if self.stop_requested:
                    break
                    
                self._log(f"Agent replied: {answer_text}")
                
                if not answer_text:
                    self._log("No answer from agent. Retrying...")
                    if not self.safe_sleep(1): break
                    continue
                    
                qa_logger.info(f"AGENT ANSWER:\n{answer_text.strip()}")
                    
                # 4. Find where to click
                self._set_status("🎯 Locating answer...")
                click_point = self.vision.find_click_point(answer_text, word_boxes)
                if not click_point:
                    self._log("Could not find the answer text on the screen to click. Skipping to next iteration.")
                    if not self.safe_sleep(1): break
                    continue
                    
                # 5. Click the answer
                if self.stop_requested: break
                self._set_status("🖱️ Clicking answer...")
                self._log(f"Clicking answer at {click_point}...")
                pyautogui.moveTo(*click_point, duration=0.2)
                pyautogui.click()
                
                if not self.safe_sleep(0.2): break
                
                # 5.5 Simulate Thinking Delay
                if config.thinking_delay > 0:
                    self._set_status("🧠 Thinking delay...")
                    self._log(f"Simulating human thinking... waiting {config.thinking_delay} seconds.")
                    if not self.safe_sleep(config.thinking_delay): break
                
                # 6. Wait for submit button to turn expected color
                self._set_status("⏳ Waiting for Submit...")
                self._log("Waiting for submit button to be ready...")
                target_color = config.submit_button_color
                pos = config.submit_button_pos
                found_color = False
                
                for _ in range(100):
                    if self.stop_requested: break
                    current_color = pyautogui.pixel(*pos)
                    if self.color_match(current_color, target_color):
                        found_color = True
                        break
                    time.sleep(0.1)
                    
                if self.stop_requested: break
                
                if not found_color:
                    self._log("Submit button did not turn the expected color after 10 seconds. Stopping.")
                    self.is_running = False
                    break
                    
                self._set_status("🖱️ Clicking Submit...")
                self._log(f"Clicking submit button at {pos}...")
                pyautogui.moveTo(*pos, duration=0.2)
                pyautogui.click()
                
                # 7. Wait for next question
                self._set_status(f"⏳ Loop delay ({config.loop_delay}s)...")
                self._log(f"Waiting {config.loop_delay} seconds...")
                if not self.safe_sleep(config.loop_delay): break
                
            except Exception as e:
                self._log(f"Error in runner loop: {e}")
                if not self.safe_sleep(1): break
                
        self._set_status("🛑 Stopped")
        self._log("Automation stopped.")

    def _scroll_down(self, clicks: int) -> None:
        """Scrolls the mouse wheel down by the given number of clicks inside the question region."""
        center_x = config.question_region[0] + (config.question_region[2] // 2)
        center_y = config.question_region[1] + (config.question_region[3] // 2)
        pyautogui.moveTo(center_x, center_y)
        # Windows requires scrolls in multiples of WHEEL_DELTA (120) to register as distinct notches
        scroll_amount = -(clicks * _SCROLL_NOTCH_MULTIPLIER)
        self._log(f"Scrolling wheel by {scroll_amount} units ({clicks} notches)...")
        pyautogui.scroll(scroll_amount)
        # Increased sleep to ensure smooth-scroll animations completely finish before OCR
        time.sleep(0.6)

    def run_google_forms_loop(self) -> None:
        if not config.question_region:
            self._log("Error: Question region is not set.")
            return

        self.is_running = True
        self.stop_requested = False
        self.is_paused = False
        self.qa_log = []
        answered_questions: list[str] = []
        last_screen_text = ""
        consecutive_empty_scrolls: int = 0
        max_empty_scrolls: int = 3

        self._log("Google Forms Automation started. Press F8 to Pause/Resume. Press ESC to Stop.")
        self._set_status("▶️ Started")

        while self.is_running and not self.stop_requested:
            if self.is_paused:
                time.sleep(0.1)
                continue

            try:
                # === STEP 1: Capture & OCR ===
                self._set_status("📸 Capturing screen...")
                img = self.vision.capture_region(config.question_region)
                
                self._set_status("🔍 Running OCR...")
                screen_text, word_boxes = self.vision.extract_text_and_boxes(img)

                if not screen_text.strip():
                    self._log("No text found. Retrying...")
                    if not self.safe_sleep(1): break
                    continue

                if screen_text == last_screen_text:
                    self._log("Screen content did not change after scroll (bottom reached). Finishing execution.")
                    self.is_running = False
                    break
                    
                last_screen_text = screen_text

                # === STEP 2: ONE agent call → ALL visible Q/A pairs ===
                self._set_status("🤖 Asking AI (batch)...")
                self._log("Asking Antigravity (batch)...")
                qa_pairs = ask_agent_google_forms_batch(
                    screen_text, answered_questions, lambda: self.stop_requested
                )

                if self.stop_requested:
                    break

                if not qa_pairs:
                    self._log("No new questions found on this screen. Form complete. Finishing execution.")
                    self.is_running = False
                    break

                consecutive_empty_scrolls = 0
                last_screen_text = ""
                self._log(f"Batch: {len(qa_pairs)} question(s) to answer.")

                # === STEP 3: Click every answer ===
                region_bottom = config.question_region[1] + config.question_region[3]
                safety_threshold = region_bottom - int(config.question_region[3] * 0.15)
                
                last_click_y = None

                for q, a in qa_pairs:
                    if self.stop_requested:
                        break
                    while self.is_paused and not self.stop_requested:
                        time.sleep(0.1)

                    self._log(f"Q: {q}\nA: {a}")
                    qa_logger.info(f"Q: {q}\nA: {a}")

                    for attempt in range(3):
                        self._set_status("🎯 Locating answer...")
                        click_point = self.vision.find_click_point(a, word_boxes)

                        if not click_point:
                            self._log(f"  Answer not found on screen (attempt {attempt + 1}). Marking answered and skipping.")
                            break

                        if click_point[1] > safety_threshold and attempt < 2:
                            self._log(f"  Answer near bottom edge (attempt {attempt + 1}) — gentle scroll...")
                            self._set_status("⬇️ Gentle scroll...")
                            self._scroll_down(3)  # Fixed small scroll to reveal the cutoff card
                            
                            fresh_img = self.vision.capture_region(config.question_region)
                            _, new_word_boxes = self.vision.extract_text_and_boxes(fresh_img)
                            
                            new_click = self.vision.find_click_point(a, new_word_boxes)
                            if new_click:
                                # BOTTOM-OF-PAGE DETECTION: If the answer didn't move UP, we hit the bottom of the form!
                                if abs(new_click[1] - click_point[1]) < 5:
                                    self._log("  Page did not move. Reached bottom of form! Clicking immediately.")
                                    word_boxes = new_word_boxes
                                    click_point = new_click
                                    # We are at the bottom, so break the safety checks and fall through to click
                                else:
                                    # The page successfully scrolled. Let the loop re-evaluate the new position.
                                    word_boxes = new_word_boxes
                                    continue
                            else:
                                self._log("  Answer lost after scroll! Using last known position.")
                                # Fall through to click the original point just in case

                        self._set_status("🖱️ Clicking answer...")
                        self._log(f"  Clicking at {click_point}...")
                        pyautogui.moveTo(*click_point, duration=0.1)
                        pyautogui.click()
                        self.qa_log.append({"question": q, "answer": a})
                        last_click_y = click_point[1]
                        break

                    answered_questions.append(q[:100])

                    settle = max(config.thinking_delay, 0.15)
                    if not self.safe_sleep(settle): break
                    
                # === STEP 4: Dynamic Auto-Scroll to next unread section ===
                if last_click_y is not None and not self.stop_requested:
                    # Distance from top of region to the last clicked answer
                    distance_from_top = last_click_y - config.question_region[1]
                    # We want to move this point to the top (with a 50px buffer so we can still see it)
                    pixels_to_scroll = max(0, distance_from_top - 50)
                    
                    if pixels_to_scroll > 50:
                        notches = max(1, round(pixels_to_scroll / 100.0))
                        self._set_status("⬇️ Smart auto-scroll...")
                        self._log(f"Batch done. Last answer at {distance_from_top}px. Smart scrolling {pixels_to_scroll}px ({notches} notches)...")
                        self._scroll_down(notches)
                        self.safe_sleep(0.5)
                    else:
                        self._log("Last answer is already near the top, no smart scroll needed.")

            except Exception as e:
                self._log(f"Error in Google Forms loop: {e}")
                if not self.safe_sleep(1): break

        self._set_status("🛑 Stopped")
        self._log("Google Forms Automation stopped.")
        if self.on_finish_callback:
            self.on_finish_callback()

