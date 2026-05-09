from datetime import date
from typing import List, Tuple, Optional
from models.schemas import InvoiceRecord, EscalationTask, EscalationStage
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

def calculate_days_overdue(due_date: date) -> int:
    return (date.today() - due_date).days

def determine_stage(days_overdue: int) -> Optional[EscalationStage]:
    if days_overdue <= 0:
        return None
    elif 1 <= days_overdue <= 7:
        return EscalationStage.STAGE_1
    elif 8 <= days_overdue <= 14:
        return EscalationStage.STAGE_2
    elif 15 <= days_overdue <= 21:
        return EscalationStage.STAGE_3
    elif 22 <= days_overdue <= 30:
        return EscalationStage.STAGE_4
    else:
        return EscalationStage.LEGAL

def is_weekend() -> bool:
    return date.today().weekday() >= 5 # 5 is Saturday, 6 is Sunday

def build_escalation_tasks(invoices: List[InvoiceRecord]) -> Tuple[List[EscalationTask], List[EscalationTask]]:
    if settings.SKIP_WEEKENDS and is_weekend():
        logger.info("Weekend detected — skipping email generation as per settings.")
        return [], []

    email_tasks = []
    legal_tasks = []

    for inv in invoices:
        days = calculate_days_overdue(inv.due_date)
        stage = determine_stage(days)
        
        if stage is None:
            continue
            
        task = EscalationTask(invoice=inv, days_overdue=days, stage=stage)
        
        if stage == EscalationStage.LEGAL:
            legal_tasks.append(task)
        else:
            email_tasks.append(task)

    return email_tasks, legal_tasks
