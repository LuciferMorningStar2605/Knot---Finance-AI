import uuid
import logging
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel

from config.settings import settings
from data.loader import load_invoices
from agent.escalation_engine import build_escalation_tasks, is_weekend
from agent.email_generator import generate_email
from agent.email_sender import send_or_log
from audit.logger import init_db, log_event

logger = logging.getLogger(__name__)

class AgentRunSummary(BaseModel):
    total_processed: int = 0
    emails_sent: int = 0
    dry_run_logged: int = 0
    generation_failed: int = 0
    legal_flags: int = 0
    run_timestamp: str = ""
    run_id: str = ""

def run_agent(filepath: str) -> AgentRunSummary:
    init_db()
    run_id = str(uuid.uuid4())
    summary = AgentRunSummary(run_timestamp=datetime.now().isoformat(), run_id=run_id)
    
    try:
        invoices = load_invoices(filepath)
    except Exception as e:
        logger.error(f"Failed to load invoices: {e}")
        return summary

    email_tasks, legal_tasks = build_escalation_tasks(invoices)
    
    # Process Legal Escalations
    for task in legal_tasks:
        log_event(task, send_status="LEGAL_ESCALATION", run_id=run_id)
        summary.legal_flags += 1
        summary.total_processed += 1

    # Check Weekend
    if settings.SKIP_WEEKENDS and is_weekend():
        logger.info("Weekend detected — skipping emails.")
        return summary

    # Process Emails
    for task in email_tasks:
        summary.total_processed += 1
        email = generate_email(task)
        
        if email is None:
            log_event(task, send_status="GENERATION_FAILED", run_id=run_id)
            summary.generation_failed += 1
            continue
            
        status = send_or_log(email, task.invoice)
        log_event(task, email=email, send_status=status, run_id=run_id)
        
        if status == "SENT":
            summary.emails_sent += 1
        elif status == "DRY_RUN_LOGGED":
            summary.dry_run_logged += 1
            
    return summary
