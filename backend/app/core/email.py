import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Basic mock email configuration, in a real app these come from .env
SMTP_HOST = os.getenv("SMTP_HOST", "mock")
SMTP_PORT = os.getenv("SMTP_PORT", "587")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

def send_email(to_email: str, subject: str, body: str, cc: Optional[List[str]] = None):
    """
    Simulates sending an email by printing it to the terminal logger.
    If SMTP_HOST is not 'mock', it would send a real email using smtplib.
    """
    cc_str = f", cc={cc}" if cc else ""
    
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
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            print(f"Failed to send email: {e}")
