import math
import random
from typing import List, Optional
from datetime import datetime, date, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.models.opportunity import Quotation, QuotationStatus
from app.models.sales_order import SalesOrder, SalesOrderStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment
from app.core.rbac import require_permission

from app.schemas.sales_order import SalesOrderRead
from app.schemas.invoice import InvoiceRead
from app.schemas.payment import PaymentRead
from app.schemas.crm import PaginatedResponse

router = APIRouter(prefix="/crm", tags=["Sales Process"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_unique_number(prefix: str) -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    rand_val = random.randint(1000, 9999)
    return f"{prefix}-{date_str}-{rand_val}"


@router.post("/quotations/{id}/convert-to-order", response_model=SalesOrderRead, status_code=status.HTTP_201_CREATED)
def convert_quotation_to_order(
    id: UUID,
    current_user: User = Depends(require_permission("opportunities:update")),
    db: Session = Depends(get_db)
):
    """Convert an approved/accepted Quotation to a Sales Order."""
    quotation = db.query(Quotation).filter(Quotation.id == id, Quotation.is_deleted == False).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
        
    if quotation.status not in [QuotationStatus.APPROVED, QuotationStatus.ACCEPTED]:
        raise HTTPException(status_code=400, detail="Only approved or accepted quotations can be converted to a Sales Order")

    # Check if Sales Order already exists for this quotation
    existing_so = db.query(SalesOrder).filter(SalesOrder.quotation_id == id, SalesOrder.is_deleted == False).first()
    if existing_so:
        return existing_so

    sales_order = SalesOrder(
        order_number=generate_unique_number("SO"),
        status=SalesOrderStatus.CONFIRMED,
        total_amount=quotation.grand_total,
        quotation_id=quotation.id,
        account_id=quotation.opportunity.account_id if quotation.opportunity else None,
        opportunity_id=quotation.opportunity_id
    )
    db.add(sales_order)
    
    # Auto-update status to approved/accepted if it isn't
    quotation.status = QuotationStatus.APPROVED
    
    db.commit()
    db.refresh(sales_order)
    return sales_order


@router.post("/sales-orders/{id}/convert-to-invoice", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def convert_order_to_invoice(
    id: UUID,
    current_user: User = Depends(require_permission("opportunities:update")),
    db: Session = Depends(get_db)
):
    """Convert a confirmed Sales Order to an Invoice."""
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == id, SalesOrder.is_deleted == False).first()
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales Order not found")

    existing_inv = db.query(Invoice).filter(Invoice.sales_order_id == id, Invoice.is_deleted == False).first()
    if existing_inv:
        return existing_inv

    invoice = Invoice(
        invoice_number=generate_unique_number("INV"),
        status=InvoiceStatus.SENT,
        total_amount=sales_order.total_amount,
        amount_paid=0.00,
        due_date=date.today(),
        sales_order_id=sales_order.id,
        account_id=sales_order.account_id
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/invoices/{id}/pay", response_model=InvoiceRead, status_code=status.HTTP_200_OK)
def pay_invoice(
    id: UUID,
    amount: float = Query(..., gt=0),
    payment_method: Optional[str] = Query("Credit Card"),
    current_user: User = Depends(require_permission("opportunities:update")),
    db: Session = Depends(get_db)
):
    """Record a payment transaction against an Invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == id, Invoice.is_deleted == False).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Invoice is already fully paid")

    payment = Payment(
        payment_number=generate_unique_number("PAY"),
        amount=amount,
        payment_date=datetime.now(timezone.utc),
        payment_method=payment_method,
        invoice_id=invoice.id
    )
    db.add(payment)
    
    invoice.amount_paid = float(invoice.amount_paid) + amount
    if invoice.amount_paid >= float(invoice.total_amount):
        invoice.status = InvoiceStatus.PAID
    else:
        invoice.status = InvoiceStatus.PARTIALLY_PAID
        
    db.commit()
    db.refresh(invoice)
    return invoice


# Listing endpoints for dashboards/reports
@router.get("/sales-orders", response_model=PaginatedResponse[SalesOrderRead])
def list_sales_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    query = db.query(SalesOrder).filter(SalesOrder.is_deleted == False)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/invoices", response_model=PaginatedResponse[InvoiceRead])
def list_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    query = db.query(Invoice).filter(Invoice.is_deleted == False)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }
