import os
import json
import time
import logging
import re
from typing import List, Optional, Tuple
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings
from models.schemas import EscalationTask, GeneratedEmail, PersonalizationCheck

logger = logging.getLogger(__name__)

# Primary and Fallback Models
PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "mixtral-8x7b-32768"

def get_llm(model_name: str):
    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=model_name,
        max_tokens=settings.GROQ_MAX_TOKENS,
        temperature=0.1 # Very low for structural consistency
    )

def repair_json(text: str) -> str:
    """Enterprise-grade JSON extraction and repair."""
    # 1. Extract block between first { and last }
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        text = match.group(1)
    
    # 2. Fix unescaped newlines in values
    # Find all "key": "value" patterns and escape newlines inside value
    def fix_newlines(m):
        key = m.group(1)
        val = m.group(2).replace('\n', '\\n').replace('\r', '\\r')
        return f'"{key}": "{val}"'
    
    text = re.sub(r'"([^"]+)":\s*"([^"]*)"', fix_newlines, text, flags=re.DOTALL)
    
    # 3. Final cleanup of common artifacts
    text = text.replace('```json', '').replace('```', '').strip()
    return text

def generate_email(task: EscalationTask) -> Optional[GeneratedEmail]:
    system_prompt, stage_prompt = load_prompt(task.stage.value)
    inv = task.invoice
    
    # Enhanced Context Data
    invoice_data = f"""
CLIENT_FULL_NAME: {inv.client_name}
INVOICE_ID: {inv.invoice_no}
TOTAL_DUE: {inv.currency} {inv.amount_due:,.2f}
DUE_DATE: {inv.due_date.strftime('%d %B %Y')}
OVERDUE_DAYS: {task.days_overdue}
PAYMENT_SECURE_LINK: {inv.payment_link}
COMPANY: {inv.company_name}
OFFICER: {inv.finance_manager}
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + "\n\n" + stage_prompt),
        ("human", "GENERATE CORPORATE FOLLOW-UP FOR:\n{invoice_data}")
    ])

    # Try Primary then Fallback
    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        llm = get_llm(model)
        chain = prompt | llm
        
        for attempt in range(2):
            try:
                response = chain.invoke({"invoice_data": invoice_data})
                raw_text = response.content
                repaired_text = repair_json(raw_text)
                
                data = json.loads(repaired_text, strict=False)
                email_obj = GeneratedEmail(**data)
                
                # Check for "None" or blank fields which indicate LLM failed to map data
                if "none" in email_obj.subject.lower() or not email_obj.body:
                    raise ValueError("LLM returned blank or placeholder content")
                
                return email_obj
            except Exception as e:
                logger.warning(f"Model {model} attempt {attempt+1} failed: {e}")
                continue
                
    return None

def load_prompt(stage: int) -> Tuple[str, str]:
    # Fixed Pathing
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    system_path = os.path.join(base_path, "prompts", "system_prompt.txt")
    stage_path = os.path.join(base_path, "prompts", f"stage{stage}_prompt.txt")
    
    with open(system_path, "r") as f:
        system_prompt = f.read()
    with open(stage_path, "r") as f:
        stage_prompt = f.read()
        
    return system_prompt, stage_prompt

def generate_batch(tasks: List[EscalationTask]) -> List[GeneratedEmail]:
    generated = []
    for task in tasks:
        email = generate_email(task)
        if email:
            generated.append(email)
        time.sleep(0.4)
    return generated
