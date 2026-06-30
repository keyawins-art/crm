import traceback
from app.db.database import SessionLocal
from app.models.opportunity import Quotation
from app.models.sales_order import SalesOrder, SalesOrderStatus
from app.api.sales_process import generate_unique_number

db = SessionLocal()
try:
    quotation = db.query(Quotation).first()
    if not quotation:
        print("No Quotation found!")
        exit(1)
        
    print(f"Testing SO conversion for quote: {quotation.id}")
    sales_order = SalesOrder(
        order_number=generate_unique_number("SO"),
        status=SalesOrderStatus.CONFIRMED,
        total_amount=quotation.total_amount,
        quotation_id=quotation.id,
        account_id=quotation.opportunity.account_id if quotation.opportunity else None,
        opportunity_id=quotation.opportunity_id
    )
    db.add(sales_order)
    db.commit()
    print("SUCCESS")
except Exception as e:
    print("FAILED")
    traceback.print_exc()
finally:
    db.close()
