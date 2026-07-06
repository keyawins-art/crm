import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.lead import Lead
from app.models.account import Account

db = SessionLocal()

# Find all accounts that have empty contact_name or email
accounts = db.query(Account).all()
for acc in accounts:
    # Try to find a converted lead for this account
    lead = db.query(Lead).filter(Lead.converted_account_id == acc.id).first()
    if lead:
        if not acc.contact_name and lead.first_name:
            acc.contact_name = f"{lead.first_name} {lead.last_name or ''}".strip()
        if not acc.phone and lead.phone:
            acc.phone = lead.phone
        if not acc.email and lead.email:
            acc.email = lead.email
        if not acc.source and lead.source:
            acc.source = lead.source
        if not acc.product_of_interest and lead.requirements:
            acc.product_of_interest = lead.requirements
        if not acc.billing_city and lead.address:
            acc.billing_city = lead.address

db.commit()
print("Accounts fixed!")
