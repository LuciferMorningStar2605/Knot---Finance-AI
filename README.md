# 💰 Finance Credit Follow-Up Email Agent
> AI-powered invoice follow-up automation | LangChain + Groq + Streamlit

## Project Overview
An autonomous AI agent that reads overdue invoice data, determines escalation stage (1–4 or Legal Flag), generates personalized professional emails using Llama 3.1 70B (via Groq API), and logs every action in a complete audit trail.

## Tech Stack
- **LLM**: Groq API (Llama 3.1 70B)
- **Framework**: LangChain (LCEL)
- **UI**: Streamlit
- **Data**: Pandas + SQLite

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Ensure GROQ_API_KEY is set in .env

# Run Dashboard
streamlit run app.py
```

## CLI Usage
```bash
python main.py --file data/sample_invoices.csv
```

## Features
- **Tone Escalation**: Automatically adjusts tone from "Friendly" to "Urgent" based on days overdue.
- **Audit Trail**: Every email and action is logged to a local SQLite database.
- **Personalization Check**: Uses LLM tool calling/validation to ensure no placeholder text is sent.
- **Dry Run Mode**: Default safety mode to preview emails without sending.

## Security
- PII masking in logs.
- Input sanitization for prompt injection.
- Credentials managed via `.env`.
