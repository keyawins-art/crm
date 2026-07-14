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
from app.models.sales_order import SalesOrder, SalesOrderStatus, SalesOrderItem, SalesOrderPriority, SalesOrderPaymentStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment
from app.models.audit import AuditAction
from app.api.crm import log_audit
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
        priority=SalesOrderPriority.STANDARD,
        order_date=date.today(),
        total_amount=quotation.grand_total,
        quotation_id=quotation.id,
        account_id=quotation.account_id or (quotation.opportunity.account_id if quotation.opportunity else None),
        opportunity_id=quotation.opportunity_id,
        assignee_id=current_user.id
    )
    db.add(sales_order)
    db.flush()

    # Copy line items
    for q_item in quotation.items:
        so_item = SalesOrderItem(
            sales_order_id=sales_order.id,
            product_id=q_item.product_id,
            sku=q_item.product.code if q_item.product else None,
            product_name=q_item.product.name if q_item.product else "Unknown Product",
            category=q_item.product.category if q_item.product else None,
            quantity=q_item.quantity,
            unit_price=q_item.unit_price,
            discount_percent=q_item.discount_percent,
            total_price=q_item.total_price,
            description=q_item.description
        )
        db.add(so_item)
    
    # Auto-update status to accepted if it isn't
    quotation.status = QuotationStatus.ACCEPTED
    
    db.commit()
    db.refresh(sales_order)
    log_audit(db, current_user, AuditAction.CREATED, "SalesOrder", sales_order.id)
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
    log_audit(db, current_user, AuditAction.CREATED, "Invoice", invoice.id)
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
    log_audit(db, current_user, AuditAction.CREATED, "Payment", payment.id)
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

from pydantic import BaseModel
class SalesOrderItemUpdate(BaseModel):
    product_id: Optional[UUID] = None
    sku: Optional[str] = None
    product_name: str
    category: Optional[str] = None
    quantity: float
    unit_price: float
    discount_percent: float = 0.0

class SalesOrderUpdate(BaseModel):
    status: Optional[SalesOrderStatus] = None
    priority: Optional[SalesOrderPriority] = None
    order_date: Optional[date] = None
    ship_date: Optional[date] = None
    delivery_date: Optional[date] = None
    payment_status: Optional[SalesOrderPaymentStatus] = None
    payment_method: Optional[str] = None
    ship_to: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[SalesOrderItemUpdate]] = None

@router.get("/sales-orders/{id}", response_model=SalesOrderRead)
def get_sales_order(
    id: UUID,
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    so = db.query(SalesOrder).filter(SalesOrder.id == id, SalesOrder.is_deleted == False).first()
    if not so:
        raise HTTPException(status_code=404, detail="Sales Order not found")
    return so

@router.put("/sales-orders/{id}", response_model=SalesOrderRead)
def update_sales_order(
    id: UUID,
    update_data: SalesOrderUpdate,
    current_user: User = Depends(require_permission("opportunities:update")),
    db: Session = Depends(get_db)
):
    so = db.query(SalesOrder).filter(SalesOrder.id == id, SalesOrder.is_deleted == False).first()
    if not so:
        raise HTTPException(status_code=404, detail="Sales Order not found")
        
    if current_user.role not in ["admin", "support"] and so.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to modify this sales order")
        
    update_dict = update_data.model_dump(exclude_unset=True)
    items_data = update_dict.pop('items', None)

    for k, v in update_dict.items():
        setattr(so, k, v)
        
    if items_data is not None:
        # Delete existing items
        db.query(SalesOrderItem).filter(SalesOrderItem.sales_order_id == so.id).delete()
        
        total_amount = 0.0
        for item_data in items_data:
            qty = float(item_data['quantity'])
            rate = float(item_data['unit_price'])
            discount_pct = float(item_data.get('discount_percent', 0.0))
            
            line_taxable = (qty * rate) * (1 - (discount_pct / 100.0))
            # Sales Order items don't have tax_percent right now in schema, just total_price
            total_amount += line_taxable
            
            so_item = SalesOrderItem(
                sales_order_id=so.id,
                product_id=item_data.get('product_id'),
                sku=item_data.get('sku'),
                product_name=item_data.get('product_name'),
                category=item_data.get('category'),
                quantity=qty,
                unit_price=rate,
                discount_percent=discount_pct,
                total_price=line_taxable
            )
            db.add(so_item)
            
        so.total_amount = total_amount
        
    db.commit()
    db.refresh(so)
    return so



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
from fastapi.responses import StreamingResponse

@router.get("/sales-orders/{id}/pdf")
def get_sales_order_pdf(
    id: UUID,
    current_user: User = Depends(require_permission("opportunities:read")),
    db: Session = Depends(get_db),
):
    query = db.query(SalesOrder).filter(SalesOrder.id == id, SalesOrder.is_deleted == False)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Sales Order not found")
        
    from app.services.pdf_generator import generate_sales_order_pdf
    pdf_buffer = generate_sales_order_pdf(obj)
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=SalesOrder_{obj.order_number}.pdf"}
    )
