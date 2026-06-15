import smtplib
import json
import os
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config.settings import settings
from models.schemas import GeneratedEmail, InvoiceRecord

logger = logging.getLogger(__name__)

def mask_email(email: str) -> str:
    try:
        user, domain = email.split("@")
        return f"{user[:2]}***@{domain}"
    except:
        return email

def send_email_smtp(generated: GeneratedEmail, invoice: InvoiceRecord) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
        msg['To'] = invoice.client_email
        msg['Subject'] = generated.subject
        msg.attach(MIMEText(generated.body, 'plain'))

        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"SMTP error for {invoice.invoice_no}: {e}")
        return False

def dry_run_log(generated: GeneratedEmail, invoice: InvoiceRecord) -> bool:
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(settings.LOGS_DIR, f"dry_run_{date_str}.json")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "invoice_no": invoice.invoice_no,
        "client": invoice.client_name,
        "email": mask_email(invoice.client_email),
        "subject": generated.subject,
        "body": generated.body
    }
    
    # Append to JSON
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
        except:
            pass
    
    logs.append(log_entry)
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)
        
    print(f"\n--- DRY RUN PREVIEW [{invoice.invoice_no}] ---")
    print(f"To: {mask_email(invoice.client_email)}")
    print(f"Subject: {generated.subject}")
    print(f"Body snippet: {generated.body[:100]}...")
    print("------------------------------------------\n")
    return True

def send_or_log(generated: GeneratedEmail, invoice: InvoiceRecord) -> str:
    if settings.DRY_RUN_MODE:
        dry_run_log(generated, invoice)
        return "DRY_RUN_LOGGED"
    else:
        success = send_email_smtp(generated, invoice)
        if success:
            return "SENT"
        else:
            # Simple retry
            success = send_email_smtp(generated, invoice)
            return "SENT" if success else "FAILED"
