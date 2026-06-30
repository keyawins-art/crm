import os
import logging
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from app.db.database import SessionLocal
from app.models.email import EmailLog, EmailStatus

logger = logging.getLogger(__name__)

# Basic mock email configuration, in a real app these come from .env
SMTP_HOST = os.getenv("SMTP_HOST", "mock")
SMTP_PORT = os.getenv("SMTP_PORT", "587")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

def send_email(
    to_email: str, 
    subject: str, 
    body: str, 
    cc: Optional[List[str]] = None,
    sender_id: Optional[UUID] = None,
    lead_id: Optional[UUID] = None,
    contact_id: Optional[UUID] = None,
    opportunity_id: Optional[UUID] = None,
):
    """
    Simulates sending an email by printing it to the terminal logger,
    and logs the result into the database.
    """
    cc_str = f", cc={cc}" if cc else ""
    
    # Pre-create the log entry in DB
    db = SessionLocal()
    log = EmailLog(
        recipient=to_email,
        subject=subject,
        body=body,
        sender_id=sender_id,
        lead_id=lead_id,
        contact_id=contact_id,
        opportunity_id=opportunity_id,
        status=EmailStatus.PENDING
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    if SMTP_HOST == "mock":
        # Mock Email sending (Logs to terminal)
        print("\n" + "="*50)
        print("📧 NEW EMAIL (MOCK)")
        print(f"To:      {to_email}{cc_str}")
        print(f"Subject: {subject}")
        print("-" * 50)
        print(body)
        print("="*50 + "\n")
        logger.info(f"Mock email sent to {to_email}")
        
        # Update DB
        log.status = EmailStatus.SENT
        log.sent_time = datetime.now(timezone.utc)
        db.commit()
    else:
        # Placeholder for real SMTP sending
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(SMTP_HOST, int(SMTP_PORT))
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            logger.info(f"Real email sent to {to_email}")
            
            # Update DB
            log.status = EmailStatus.SENT
            log.sent_time = datetime.now(timezone.utc)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            print(f"Failed to send email: {e}")
            
            # Update DB on failure
            log.status = EmailStatus.FAILED
            db.commit()
    
    db.close()
