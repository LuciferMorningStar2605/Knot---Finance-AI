from pydantic import BaseModel, EmailStr, field_validator
from datetime import date
from typing import Optional, List
from enum import IntEnum

class EscalationStage(IntEnum):
    STAGE_1 = 1   # 1–7 days overdue
    STAGE_2 = 2   # 8–14 days overdue
    STAGE_3 = 3   # 15–21 days overdue
    STAGE_4 = 4   # 22–30 days overdue
    LEGAL   = 5   # 30+ days — no email, manual review

class InvoiceRecord(BaseModel):
    invoice_no: str
    client_name: str
    client_email: str            # validated as email format in validator.py
    amount_due: float
    due_date: date
    follow_up_count: int
    currency: str = "INR"
    payment_link: str
    finance_manager: str
    company_name: str
    notes: Optional[str] = None

class EscalationTask(BaseModel):
    invoice: InvoiceRecord
    days_overdue: int
    stage: EscalationStage

class PersonalizationCheck(BaseModel):
    client_name_present: bool
    invoice_no_present: bool
    amount_present: bool
    due_date_present: bool
    days_overdue_present: bool
    payment_link_present: bool

    @property
    def all_passed(self) -> bool:
        return all([
            self.client_name_present, self.invoice_no_present,
            self.amount_present, self.due_date_present,
            self.days_overdue_present, self.payment_link_present
        ])

class GeneratedEmail(BaseModel):
    invoice_no: str
    subject: str
    body: str
    tone_used: str
    stage: int
    personalization_check: PersonalizationCheck

class AuditRecord(BaseModel):
    id: Optional[int] = None
    invoice_no: str
    client_name: str
    client_email: str
    amount_due: float
    currency: str
    days_overdue: int
    stage: int
    tone_used: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    send_status: str       # "SENT", "DRY_RUN_LOGGED", "FAILED", "LEGAL_ESCALATION"
    timestamp: str
    error_message: Optional[str] = None
    run_id: Optional[str] = None
