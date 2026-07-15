from app.db.database import SessionLocal
from app.models.account import Account, AccountType, AccountIndustry
from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
import random

companies = [
    {"name": "OpenAI", "industry": AccountIndustry.TECHNOLOGY, "domain": "openai.com"},
    {"name": "Google", "industry": AccountIndustry.TECHNOLOGY, "domain": "google.com"},
    {"name": "Microsoft", "industry": AccountIndustry.TECHNOLOGY, "domain": "microsoft.com"},
    {"name": "Amazon", "industry": AccountIndustry.RETAIL, "domain": "amazon.com"},
    {"name": "Tesla", "industry": AccountIndustry.MANUFACTURING, "domain": "tesla.com"},
    {"name": "Apple", "industry": AccountIndustry.TECHNOLOGY, "domain": "apple.com"},
    {"name": "IBM", "industry": AccountIndustry.TECHNOLOGY, "domain": "ibm.com"},
    {"name": "Oracle", "industry": AccountIndustry.TECHNOLOGY, "domain": "oracle.com"},
    {"name": "Zoho", "industry": AccountIndustry.TECHNOLOGY, "domain": "zoho.com"},
    {"name": "Infosys", "industry": AccountIndustry.OTHER, "domain": "infosys.com"},
    {"name": "TCS", "industry": AccountIndustry.OTHER, "domain": "tcs.com"},
    {"name": "Wipro", "industry": AccountIndustry.OTHER, "domain": "wipro.com"},
    {"name": "Salesforce", "industry": AccountIndustry.TECHNOLOGY, "domain": "salesforce.com"},
    {"name": "Meta", "industry": AccountIndustry.TECHNOLOGY, "domain": "meta.com"},
    {"name": "Netflix", "industry": AccountIndustry.OTHER, "domain": "netflix.com"},
    {"name": "Adobe", "industry": AccountIndustry.TECHNOLOGY, "domain": "adobe.com"},
    {"name": "Intel", "industry": AccountIndustry.MANUFACTURING, "domain": "intel.com"},
    {"name": "Cisco", "industry": AccountIndustry.TECHNOLOGY, "domain": "cisco.com"},
    {"name": "Nvidia", "industry": AccountIndustry.MANUFACTURING, "domain": "nvidia.com"},
    {"name": "Samsung", "industry": AccountIndustry.MANUFACTURING, "domain": "samsung.com"}
]

def seed():
    db = SessionLocal()
    try:
        # Check if an admin user exists, else create one using environment variables
        admin_user = db.query(User).first()
        if not admin_user:
            import os
            admin_email = os.getenv("INITIAL_ADMIN_EMAIL")
            admin_password = os.getenv("INITIAL_ADMIN_PASSWORD")
            
            if admin_email and admin_password:
                admin_role = db.query(Role).filter(Role.name == "System Administrator").first()
                admin_user = User(
                    email=admin_email,
                    first_name="System",
                    last_name="Admin",
                    password_hash=get_password_hash(admin_password),
                    role_id=admin_role.id if admin_role else None
                )
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)
                print(f"Created default admin user: {admin_email}")
            else:
                print("Skipping admin creation: INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD not set in environment.")

        count = 0
        for comp in companies:
            exists = db.query(Account).filter(Account.name == comp["name"]).first()
            if not exists:
                acc = Account(
                    name=comp["name"],
                    type=random.choice([AccountType.CUSTOMER, AccountType.PROSPECT, AccountType.PARTNER]),
                    industry=comp["industry"],
                    website=f"https://{comp['domain']}",
                    phone=f"98{random.randint(10000000, 99999999)}",
                    email=f"contact@{comp['domain']}",
                    description=f"Enterprise account for {comp['name']}",
                    annual_revenue=random.randint(1000000, 50000000),
                    employee_count=random.randint(50, 10000),
                    owner_id=admin_user.id if admin_user else None
                )
                db.add(acc)
                count += 1
                
        db.commit()
        print(f"Successfully seeded {count} new Accounts into the database.")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding accounts: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
