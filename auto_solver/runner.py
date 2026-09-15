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
        self.on_log_callback: Optional[Callable[[str, str], None]] = None
        self.on_status_callback: Optional[Callable[[str], None]] = None
        
        # Setup pynput listener for emergency stop and pause
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        
        # Step timing variables
        self.last_status_name: Optional[str] = None
        self.last_status_time: float = 0.0
        
    def _log(self, msg: str, color: str = None):
        print(msg)
        if self.on_log_callback:
            self.on_log_callback(msg, color)
            
    def _set_status(self, status: str):
        if self.last_status_name:
            if config.show_step_timings and self.last_status_name not in ["Idle", "Stopped", "Finished", "Started", "Paused", "Resumed"]:
                elapsed = time.time() - self.last_status_time
                if elapsed >= 0.1:
                    self._log(f"  └─ [{self.last_status_name}] took {elapsed:.1f}s", "gray")
                    
        self.last_status_name = status
        self.last_status_time = time.time()
        
        if self.on_status_callback:
            self.on_status_callback(status)

    def on_press(self, key):
        if key == keyboard.Key.esc:
            self._log("\n[ESC pressed] Emergency stop requested.", "red")
            self.stop_requested = True
            self.is_running = False
        elif key == keyboard.Key.f8:
            self.is_paused = not self.is_paused
            state = "PAUSED" if self.is_paused else "RESUMED"
            self._log(f"\n[F8 pressed] Automation {state}.", "yellow")
            if self.is_paused:
                self._set_status("Paused")
            else:
                self._set_status("Resumed")

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
            self._log("Error: Question region is not set.", "red")
            return
            
        for act in config.click_sequence:
            if not act.get("pos"):
                self._log(f"Error: Position for '{act.get('name')}' is not set.", "red")
                return
            
        self.is_running = True
        self.stop_requested = False
        self.is_paused = False
        self._log("Automation started. Press F8 to Pause/Resume. Press ESC to Stop.")
        self._set_status("Started")
        
        while self.is_running and not self.stop_requested:
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            try:
                # 1. Capture screen
                self._set_status("Capturing screen")
                self._log("Capturing screen...", "blue")
                img = self.vision.capture_region(config.question_region)
                
                # 2. Extract text
                self._set_status("Running OCR")
                self._log("Running OCR...", "blue")
                text, word_boxes = self.vision.extract_text_and_boxes(img)
                self._log(f"Extracted Text: {text}")
                
                if not text.strip():
                    self._log("No text found. Retrying in 1 second...", "yellow")
                    if not self.safe_sleep(1): break
                    continue
                    
                qa_logger.info(f"QUESTION EXTRACTED:\n{text.strip()}")
                    
                # 3. Ask Agent
                self._set_status("Asking AI")
                self._log("Asking Antigravity...", "green")
                answer_text = ask_agent(text, lambda: self.stop_requested)
                
                if self.stop_requested:
                    break
                    
                self._log(f"Agent replied: {answer_text}", "green")
                
                if not answer_text:
                    self._log("No answer from agent. Retrying...", "yellow")
                    if not self.safe_sleep(1): break
                    continue
                    
                qa_logger.info(f"AGENT ANSWER:\n{answer_text.strip()}")
                    
                # 4. Find where to click
                self._set_status("Locating answer")
                click_point = self.vision.find_click_point(answer_text, word_boxes)
                if not click_point:
                    self._log("Could not find the answer text on the screen to click. Skipping to next iteration.", "red")
                    if not self.safe_sleep(1): break
                    continue
                    
                # 5. Click the answer
                if self.stop_requested: break
                self._set_status("Clicking answer")
                self._log(f"Clicking answer at {click_point}...", "yellow")
                pyautogui.moveTo(*click_point, duration=0.2)
                pyautogui.click()
                
                if not self.safe_sleep(0.2): break
                
                # 5.5 Simulate Thinking Delay
                if config.thinking_delay > 0:
                    self._set_status("Thinking delay")
                    self._log(f"Simulating human thinking... waiting {config.thinking_delay} seconds.")
                    if not self.safe_sleep(config.thinking_delay): break
                
                # 6. Execute Click Sequence
                for idx, action in enumerate(config.click_sequence):
                    if self.stop_requested: break
                    
                    pos = action['pos']
                    name = action.get('name', f'Action {idx+1}')
                    
                    if action.get('check_color', True) and action.get('color'):
                        self._set_status(f"Waiting for {name}")
                        self._log(f"Waiting for '{name}' button to match color...")
                        target_color = action['color']
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
                            self._log(f"'{name}' button did not turn the expected color after 10 seconds. Stopping.", "red")
                            self.is_running = False
                            break
                    else:
                        self._log(f"Bypassing color match for '{name}'.")

                    if not self.is_running: break

                    self._set_status(f"Clicking {name}")
                    self._log(f"Clicking '{name}' at {pos}...", "yellow")
                    pyautogui.moveTo(*pos, duration=0.2)
                    pyautogui.click()
                    
                    # Small delay between actions in sequence
                    if idx < len(config.click_sequence) - 1:
                        if not self.safe_sleep(0.5): break
                
                # 7. Wait for next question
                self._set_status(f"Loop delay ({config.loop_delay}s)")
                self._log(f"Waiting {config.loop_delay} seconds...")
                if not self.safe_sleep(config.loop_delay): break
                
            except Exception as e:
                self._log(f"Error in runner loop: {e}", "red")
                if not self.safe_sleep(1): break
                
        self._set_status("Stopped")
        self._log("Automation stopped.")

    def _scroll_down(self, clicks: int) -> None:
        """Scrolls the mouse wheel down by the given number of clicks inside the question region."""
        center_x = config.question_region[0] + (config.question_region[2] // 2)
        center_y = config.question_region[1] + (config.question_region[3] // 2)
        pyautogui.moveTo(center_x, center_y)
        # Windows requires scrolls in multiples of WHEEL_DELTA (120) to register as distinct notches
        scroll_amount = -(clicks * _SCROLL_NOTCH_MULTIPLIER)
        self._log(f"Scrolling wheel by {scroll_amount} units ({clicks} notches)...", "blue")
        pyautogui.scroll(scroll_amount)
        # Increased sleep to ensure smooth-scroll animations completely finish before OCR
        time.sleep(0.6)

    def run_google_forms_loop(self) -> None:
        if not config.question_region:
            self._log("Error: Question region is not set.", "red")
            return

        self.is_running = True
        self.stop_requested = False
        self.is_paused = False
        self.qa_log = []
        answered_questions: list[str] = []
        last_screen_text = ""

        self._log("Google Forms Automation started. Press F8 to Pause/Resume. Press ESC to Stop.")
        self._set_status("Started")

        while self.is_running and not self.stop_requested:
            if self.is_paused:
                time.sleep(0.1)
                continue

            try:
                # === STEP 1: Capture & OCR ===
                self._set_status("Capturing screen")
                self._log("Capturing screen...", "blue")
                img = self.vision.capture_region(config.question_region)
                
                self._set_status("Running OCR")
                self._log("Running OCR...", "blue")
                screen_text, word_boxes = self.vision.extract_text_and_boxes(img)

                if not screen_text.strip():
                    self._log("No text found. Retrying...", "yellow")
                    if not self.safe_sleep(1): break
                    continue

                if screen_text == last_screen_text:
                    self._log("Screen content did not change after scroll (bottom reached). Finishing execution.")
                    self.is_running = False
                    break
                    
                last_screen_text = screen_text

                # === STEP 2: ONE agent call → ALL visible Q/A pairs ===
                self._set_status("Asking AI (batch)")
                self._log("Asking Antigravity (batch)...", "green")
                
                def agent_live_log(msg):
                    self._log(f"  [AI] {msg}", "gray")
                    
                qa_pairs = ask_agent_google_forms_batch(
                    screen_text, answered_questions, lambda: self.stop_requested, agent_live_log
                )

                if self.stop_requested:
                    break

                if not qa_pairs:
                    self._log("No new questions found on this screen. Form complete. Finishing execution.")
                    self.is_running = False
                    break

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

                    clicked = False
                    for attempt in range(3):
                        self._set_status("Locating answer")
                        click_point = self.vision.find_click_point(a, word_boxes)

                        if not click_point:
                            self._log(f"  Answer not found on screen (attempt {attempt + 1}). Marking answered and skipping.", "red")
                            break

                        if click_point[1] > safety_threshold and attempt < 2:
                            self._log(f"  Answer near bottom edge (attempt {attempt + 1}) — gentle scroll...", "blue")
                            self._set_status("Gentle scroll")
                            self._scroll_down(3)  # Fixed small scroll to reveal the cutoff card
                            
                            fresh_img = self.vision.capture_region(config.question_region)
                            _, new_word_boxes = self.vision.extract_text_and_boxes(fresh_img)
                            
                            new_click = self.vision.find_click_point(a, new_word_boxes)
                            if new_click:
                                # BOTTOM-OF-PAGE DETECTION: If the answer didn't move UP, we hit the bottom of the form!
                                if abs(new_click[1] - click_point[1]) < 5:
                                    self._log("  Page did not move. Reached bottom of form! Clicking immediately.", "yellow")
                                    word_boxes = new_word_boxes
                                    click_point = new_click
                                    # We are at the bottom, so break the safety checks and fall through to click
                                else:
                                    # The page successfully scrolled. Let the loop re-evaluate the new position.
                                    word_boxes = new_word_boxes
                                    continue
                            else:
                                self._log("  Answer lost after scroll! Using last known position.", "red")
                                # Fall through to click the original point just in case

                        self._set_status("Clicking answer")
                        self._log(f"  Clicking at {click_point}...", "yellow")
                        pyautogui.moveTo(*click_point, duration=0.1)
                        pyautogui.click()
                        self.qa_log.append({"question": q, "answer": a})
                        clicked = True
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
                        self._set_status("Smart auto-scroll")
                        self._log(f"Batch done. Last answer at {distance_from_top}px. Smart scrolling {pixels_to_scroll}px ({notches} notches)...", "blue")
                        self._scroll_down(notches)
                        self.safe_sleep(0.5)
                    else:
                        self._log("Last answer is already near the top, no smart scroll needed.")

            except Exception as e:
                self._log(f"Error in Google Forms loop: {e}", "red")
                if not self.safe_sleep(1): break

        self._set_status("Stopped")
        self._log("Google Forms Automation stopped.")
        
        if config.save_qa_logs and self.qa_log:
            self._set_status("Formatting Final Log")
            self._log("Sending final QA log to AI for cleanup and title generation...", "blue")
            try:
                from agy_client import format_qa_log
                import history_manager
                
                def fmt_log_cb(msg):
                    self._log(f"  [AI] {msg}", "gray")
                    
                formatted_data = format_qa_log(self.qa_log, lambda: self.stop_requested, fmt_log_cb)
                if formatted_data and "title" in formatted_data and "qa_pairs" in formatted_data:
                    title = formatted_data["title"]
                    clean_pairs = formatted_data["qa_pairs"]
                    self._log(f"AI generated title: '{title}'", "green")
                    history_manager.add_log(title, clean_pairs)
                    self._log("Clean QA log saved to history successfully.", "green")
                    
                    # Update local qa_log with the cleaned one to show nicely in the dashboard!
                    self.qa_log = [{"question": p.get("q", ""), "answer": p.get("a", "")} for p in clean_pairs]
                else:
                    self._log("AI returned empty or invalid formatting. Falling back to raw log.", "yellow")
                    history_manager.add_log("Unformatted Session", self.qa_log)
            except Exception as e:
                self._log(f"Failed to format/save log: {e}", "red")
        
        self._set_status("Idle")
        if self.on_finish_callback:
            self.on_finish_callback()
