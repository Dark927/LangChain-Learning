# Elite AI Architecture Expert App

This is a local FastAPI web application that serves as an elite, top-5% AI architecture expert. It runs locally and provides deep-dive answers regarding LangChain, Groq, Cursor, and Antigravity.

## Features
- **Neon Dark Mode UI**: Modern, clean, and styled with zero emojis.
- **Deep Technical Agent**: Powered by a custom LangChain agent using Groq.
- **HTML Report Generation**: Can automatically generate standalone `.html` files containing architectural breakdowns.
- **Mermaid Visualizations**: Generates system architecture diagrams (Mermaid.js) when requested.

## Setup Instructions

1. **Install Dependencies**:
   Open your terminal and run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Ensure you have a `.env` file in the root of your workspace (`F:\Computer-Science\Agentic AI\.env`) containing your `GROQ_API_KEY`.

3. **Run the Server**:
   From the main `Agentic AI` folder, run:
   ```bash
   python -m expert_app.main
   ```

4. **Access the App**:
   Open your browser and navigate to: `http://127.0.0.1:8000`
