# Auto Solver Pro

Auto Solver Pro is a desktop automation tool designed to extract multiple-choice questions from a user interface, resolve them using large language models via the Google Antigravity CLI, and autonomously execute interface interactions.

## Architecture & Design

The application operates as a bridge between computer vision and language models. It leverages a modern CustomTkinter graphical interface for configuration and standard Python modules for background execution.

- **Computer Vision**: Utilizes `mss` for high-speed screen captures and `pytesseract` for Optical Character Recognition (OCR). The pipeline applies Lanczos upscaling and contrast enhancement to reliably extract text and UI element bounding boxes.
- **Agent Integration**: Interfaces with the Google Antigravity CLI (`agy`) using asynchronous subprocess execution. It employs the `--continue` flag to maintain a persistent chat session, eliminating container initialization overhead between requests.
- **Execution Logic**: Employs sliding-window text matching (`difflib`) for precise coordinate mapping and pixel color sampling to confirm UI state before triggering simulated inputs via `pyautogui`.

## Prerequisites

- Python 3.10 or higher.
- Tesseract OCR engine installed locally.
- Google Antigravity CLI (`agy`) installed and authenticated on the host machine.

## Installation & Configuration

1. Install the required Python dependencies:
```bash
cd auto_solver
pip install -r requirements.txt
```

2. Execute the primary application script:
```bash
python main.py
```

3. Click **Show Preferences** within the interface to verify the **Tesseract Path** points to your local `tesseract.exe` binary.

## Usage

1. **Target Acquisition**: 
   - Click **Select Question Region** to define the coordinate bounding box for the target question text.
   - Click **Select Submit Pos & Color** to define the specific coordinate and target RGB pixel color of the submission UI element.
2. **Execution**: 
   - Select the required language model and configure the simulated execution delay.
   - Click **Start Automation** to initialize the background subprocess loop.
3. **System Interrupts**: 
   - Press **F8** to toggle execution pause states.
   - Press **ESC** to trigger an emergency process termination.

## Disclaimer / Legal

This software is provided for educational purposes to demonstrate the integration of computer vision, UI automation, and command-line LLM orchestration. It is not intended or authorized for subverting security mechanisms, exploiting software vulnerabilities, or engaging in academic dishonesty within proctored environments.
