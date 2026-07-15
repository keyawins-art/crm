import sys

with open("d:/CRM/backend/app/services/pdf_generator.py", "r", encoding="utf-8") as f:
    content = f.read()

new_func = """
def generate_sales_order_pdf(order):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=10*mm, 
        leftMargin=10*mm, 
        topMargin=15*mm, 
        bottomMargin=10*mm
    )

    elements = []
    styles = getSampleStyleSheet()
    
    style_normal = styles["Normal"]
    style_normal.fontSize = 8
    style_normal.leading = 10
    
    style_bold = ParagraphStyle(
        name='Bold',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold'
    )
    
    style_title = ParagraphStyle(
        name='DocTitle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        fontName='Helvetica-Bold',
        alignment=1 # Center
    )

    # Load Company Settings from DB
    from app.db.database import SessionLocal
    from app.models.company_settings import CompanySettings

    db = SessionLocal()
    settings = db.query(CompanySettings).first()
    db.close()

    if settings:
        c_name = settings.company_name
        c_addr = settings.address or ""
        c_gst = settings.gst_number or ""
        c_phone = settings.phone or ""
        b_name = settings.bank_name or ""
        b_branch = settings.bank_branch or ""
        b_acc = settings.bank_account_no or ""
        b_ifsc = settings.bank_ifsc or ""
        logo_text = settings.company_name.upper()
    else:
        c_name = "Keya Fusion Technology Pvt Ltd"
        c_addr = "7, Prime Industry Estate, Savli - Vadodara Rd, behind Guru Krupa Farm, Manjusar,\\nGujarat\\n391775"
        c_gst = "24AAECK0154G1ZZ"
        c_phone = "9824420127"
        b_name = "STATE BANK OF INDIA"
        b_branch = "SAMA SAVLI"
        b_acc = "31753679471"
        b_ifsc = "SBIN0013553"
        logo_text = "KEYA FUSION"

    formatted_addr = c_addr.replace('\\n', '<br/>')
    company_info = f\"\"\"<font name="Helvetica-Bold" size="14">{c_name}</font><br/>
{formatted_addr}<br/>
GST : {c_gst}<br/>
Phone : {c_phone}\"\"\"

    logo_placeholder = f\"\"\"<font color="#005A9C" name="Helvetica-Bold" size="14">{logo_text}</font><br/>
<font color="#555555" size="7">TECHNOLOGY PVT LTD</font>\"\"\"

    logo_file = settings.logo_url if settings and settings.logo_url else None
    if logo_file and os.path.exists(logo_file):
        try:
            from PIL import Image as PILImage
            with PILImage.open(logo_file) as img:
                orig_w, orig_h = img.size
            max_w = 52 * mm
            max_h = 19 * mm
            scale = min(max_w / orig_w, max_h / orig_h)
            logo_element = Image(logo_file, width=orig_w * scale, height=orig_h * scale, hAlign='RIGHT')
        except Exception as e:
            logo_element = Image(logo_file, width=52*mm, height=18*mm, hAlign='RIGHT')
    else:
        logo_element = Paragraph(logo_placeholder, ParagraphStyle(name='R', alignment=2))

    header_table_data = [
        [Paragraph(company_info, style_normal), logo_element]
    ]
    header_table = Table(header_table_data, colWidths=[120*mm, 70*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Sales Order", style_title))
    elements.append(Spacer(1, 10))

    o_date = order.order_date.strftime("%d %B %Y") if getattr(order, "order_date", None) else "N/A"
    s_date = order.ship_date.strftime("%d %B %Y") if getattr(order, "ship_date", None) else "TBD"
    
    meta_data = f\"\"\"<font name="Helvetica-Bold">Order No. :</font> {order.order_number}<br/>
<font name="Helvetica-Bold">Date :</font> {o_date}<br/>
<font name="Helvetica-Bold">Ship Date :</font> {s_date}<br/>
<font name="Helvetica-Bold">Priority :</font> {order.priority.title() if order.priority else 'Standard'}\"\"\"

    meta_table = Table([["", Paragraph(meta_data, ParagraphStyle(name='R', alignment=2, fontSize=8, leading=11))]], colWidths=[130*mm, 60*mm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 5))

    acc = order.account
    client_name = acc.name.upper() if acc else "UNKNOWN CLIENT"
    
    addr_parts = []
    if acc:
        if acc.billing_street: addr_parts.append(acc.billing_street)
        if acc.billing_city: addr_parts.append(acc.billing_city)
        if acc.billing_state: addr_parts.append(acc.billing_state)
        if acc.billing_pincode: addr_parts.append(acc.billing_pincode)
    
    default_client_addr = ", ".join(addr_parts) if addr_parts else "N/A"
    client_gst = acc.gst_number if acc and getattr(acc, 'gst_number', None) else "N/A"
    client_phone = acc.phone if acc and getattr(acc, 'phone', None) else "N/A"

    shipping_address_str = order.ship_to if getattr(order, 'ship_to', None) else default_client_addr

    billing_text = f\"\"\"<font name="Helvetica-Bold">{client_name}</font><br/>
Address :- {default_client_addr}<br/>
GSTIN : {client_gst}<br/>
Phone :- {client_phone}\"\"\"

    shipping_text = f\"\"\"<font name="Helvetica-Bold">{client_name}</font><br/>
Address :- {shipping_address_str}<br/>
GSTIN : {client_gst}<br/>
Phone :- {client_phone}\"\"\"

    address_data = [
        [Paragraph("Billing Address", ParagraphStyle('C', alignment=1, fontSize=8, fontName='Helvetica-Bold')), 
         Paragraph("Shipping Address", ParagraphStyle('C', alignment=1, fontSize=8, fontName='Helvetica-Bold'))],
        [Paragraph(billing_text, style_normal), Paragraph(shipping_text, style_normal)]
    ]
    
    address_table = Table(address_data, colWidths=[95*mm, 95*mm])
    address_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(address_table)
    
    items_header = [
        "No.", "Item & Descripon", "HSN / SAC", "Qty", "Unit", 
        "Rate (Rs)", "Taxable (Rs)", "IGST(%)", "IGST Rs", "Amount (Rs)"
    ]
    
    items_data = [items_header]
    
    total_taxable = 0
    total_igst = 0
    total_amount = 0

    if hasattr(order, 'items') and order.items:
        for idx, item in enumerate(order.items, 1):
            desc = f"<font name='Helvetica-Bold'>{item.product_name}</font>"
            if getattr(item, 'sku', None):
                desc += f"<br/>SKU: {item.sku}"
                
            qty = float(item.quantity)
            rate = float(item.unit_price)
            taxable = qty * rate
            igst_pct = float(item.tax_percent) if getattr(item, 'tax_percent', None) else 0.0
            igst_amt = taxable * (igst_pct / 100.0)
            amt = taxable + igst_amt
            
            total_taxable += taxable
            total_igst += igst_amt
            total_amount += amt
            
            hsn = getattr(item.product, 'hsn_code', '84224000') if hasattr(item, 'product') and item.product else '84224000'
            unit = "Nos"
            
            row = [
                str(idx),
                Paragraph(desc, style_normal),
                hsn,
                str(int(qty) if qty.is_integer() else qty),
                unit,
                f"{rate:,.2f}",
                f"{taxable:,.2f}",
                str(int(igst_pct)),
                f"{igst_amt:,.2f}",
                f"{amt:,.2f}"
            ]
            items_data.append(row)
    else:
        desc_p = Paragraph("<font name='Helvetica-Bold'>Product</font>", style_normal)
        items_data.append(["1", desc_p, "84224000", "1", "Nos", "0.00", "0.00", "18", "0.00", "0.00"])

    items_table = Table(items_data, colWidths=[8*mm, 48*mm, 18*mm, 10*mm, 10*mm, 22*mm, 22*mm, 12*mm, 17*mm, 23*mm])
    
    items_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#A8C3E6')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),
    ])
    
    for i in range(1, len(items_data)):
        bg_color = colors.HexColor('#EBF3FA') if i % 2 == 0 else colors.HexColor('#D5E6F6')
        items_style.add('BACKGROUND', (0,i), (-1,i), bg_color)
        
    items_table.setStyle(items_style)
    elements.append(items_table)
    
    bank_text = f\"\"\"<font name="Helvetica-Bold">Bank Details :</font><br/>
Bank Name : {b_name}<br/>
Branch : {b_branch}<br/>
Account No. : {b_acc}<br/>
IFSC : {b_ifsc}\"\"\"

    words = get_amount_in_words(total_amount)
    amount_words_text = f\"\"\"<font name="Helvetica-Bold">Total Amount in Words :</font><br/>
<font name="Helvetica-Bold">{words}</font>\"\"\"

    totals_table_data = [
        ["Total Amount before Tax (Rs)", f"{total_taxable:,.2f}"],
        ["Add IGST (Rs)", f"{total_igst:,.2f}"],
        ["Grand Total (Rs)", f"{total_amount:,.2f}"]
    ]
    
    t_style = TableStyle([
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ])
    totals_t = Table(totals_table_data, colWidths=[40*mm, 20*mm])
    totals_t.setStyle(t_style)

    bottom_master_data = [
        [Paragraph(bank_text, style_normal), Paragraph(amount_words_text, style_normal), totals_t]
    ]
    bottom_master_table = Table(bottom_master_data, colWidths=[65*mm, 65*mm, 60*mm])
    bottom_master_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(bottom_master_table)
    
    if getattr(order, 'notes', None):
        tc_body = order.notes.replace('\\n', '<br/>')
        tc_text = f\"\"\"<font name="Helvetica-Bold">Notes:</font><br/>{tc_body}\"\"\"
    else:
        tc_text = \"\"\"<font name="Helvetica-Bold">Notes:</font><br/>None\"\"\"

    disclaimer = \"\"\"<font name="Helvetica-Bold">Disclaimer :-</font> The delivery timelines provided are tentative estimates.\"\"\"

    tc_table_data = [
        [Paragraph(tc_text, style_normal)],
        [Paragraph(disclaimer, style_normal)]
    ]
    tc_table = Table(tc_table_data, colWidths=[190*mm])
    tc_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(tc_table)
    
    sig_text1 = "This is a computer-generated sales order. E. & O. E."
    sig_text2 = f"For,{c_name}<br/><br/><br/><br/><b>Authorised Signatory</b>"
    
    sig_table_data = [
        [Paragraph(sig_text1, ParagraphStyle('C', alignment=1, fontSize=7)), 
         Paragraph(sig_text2, ParagraphStyle('C', alignment=1, fontSize=8))]
    ]
    sig_table = Table(sig_table_data, colWidths=[95*mm, 95*mm], rowHeights=[25*mm])
    sig_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (0,0), 'BOTTOM'),
        ('VALIGN', (1,0), (1,0), 'TOP'),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
"""
with open("d:/CRM/backend/app/services/pdf_generator.py", "w", encoding="utf-8") as f:
    f.write(content + new_func)
