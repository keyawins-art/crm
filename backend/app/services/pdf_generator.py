import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from num2words import num2words

def get_amount_in_words(num):
    try:
        words = num2words(num, lang='en_IN').title()
        return f"{words} Rupees Only"
    except:
        return f"{num} Rupees Only"

def generate_quotation_pdf(quotation):
    buffer = io.BytesIO()
    
    # Page margins: left=10mm, right=10mm, top=10mm, bottom=10mm
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
    
    # Custom Styles
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

    style_company_name = ParagraphStyle(
        name='CompanyName',
        parent=styles['Normal'],
        fontSize=14,
        leading=16,
        fontName='Helvetica-Bold'
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
        c_addr = "7, Prime Industry Estate, Savli - Vadodara Rd, behind Guru Krupa Farm, Manjusar,\nGujarat\n391775"
        c_gst = "24AAECK0154G1ZZ"
        c_phone = "9824420127"
        b_name = "STATE BANK OF INDIA"
        b_branch = "SAMA SAVLI"
        b_acc = "31753679471"
        b_ifsc = "SBIN0013553"
        logo_text = "KEYA FUSION"

    # Top Section: Company Info and Logo Placeholder
    formatted_addr = c_addr.replace('\n', '<br/>')
    company_info = f"""<font name="Helvetica-Bold" size="14">{c_name}</font><br/>
{formatted_addr}<br/>
GST : {c_gst}<br/>
Phone : {c_phone}"""

    logo_placeholder = f"""<font color="#005A9C" name="Helvetica-Bold" size="14">{logo_text}</font><br/>
<font color="#555555" size="7">TECHNOLOGY PVT LTD</font>"""

    # Choose logo element
    logo_file = settings.logo_url if settings and settings.logo_url else None
    if logo_file and os.path.exists(logo_file):
        try:
            from PIL import Image as PILImage
            with PILImage.open(logo_file) as img:
                orig_w, orig_h = img.size
            # Max bounding box for the logo (larger size)
            max_w = 52 * mm
            max_h = 19 * mm
            # Scale proportionally to fit inside max_w x max_h (contain)
            scale = min(max_w / orig_w, max_h / orig_h)
            target_width = orig_w * scale
            target_height = orig_h * scale
            logo_element = Image(logo_file, width=target_width, height=target_height, hAlign='RIGHT')
        except Exception as e:
            logo_element = Image(logo_file, width=52*mm, height=18*mm, hAlign='RIGHT')
    else:
        logo_element = Paragraph(logo_placeholder, ParagraphStyle(name='R', alignment=2))

    # We use a table for the header to align left (info) and right (logo)
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

    # Title
    elements.append(Paragraph("Quotation", style_title))
    elements.append(Spacer(1, 10))

    # Quotation Meta Data
    q_date = quotation.created_at.strftime("%d %B %Y") if getattr(quotation, "created_at", None) else "N/A"
    v_date = quotation.valid_until.strftime("%d %B %Y") if getattr(quotation, "valid_until", None) else "N/A"
    
    meta_data = f"""<font name="Helvetica-Bold">Quotation No. :</font> {quotation.quote_number}<br/>
<font name="Helvetica-Bold">Date :</font> {q_date}<br/>
<font name="Helvetica-Bold">Valid Till :</font> {v_date}"""

    meta_table = Table([["", Paragraph(meta_data, ParagraphStyle(name='R', alignment=2, fontSize=8, leading=11))]], colWidths=[130*mm, 60*mm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 5))

    # Addresses Section
    acc = quotation.account
    client_name = acc.name.upper() if acc else "UNKNOWN CLIENT"
    
    # We will build default address string
    addr_parts = []
    if acc:
        if acc.billing_street: addr_parts.append(acc.billing_street)
        if acc.billing_city: addr_parts.append(acc.billing_city)
        if acc.billing_state: addr_parts.append(acc.billing_state)
        if acc.billing_pincode: addr_parts.append(acc.billing_pincode)
    
    default_client_addr = ", ".join(addr_parts) if addr_parts else "N/A"
    client_gst = acc.gst_number if acc and getattr(acc, 'gst_number', None) else "N/A"
    client_phone = acc.phone if acc and getattr(acc, 'phone', None) else "N/A"

    billing_address_str = quotation.billing_address if getattr(quotation, 'billing_address', None) else default_client_addr
    shipping_address_str = quotation.shipping_address if getattr(quotation, 'shipping_address', None) else default_client_addr

    billing_text = f"""<font name="Helvetica-Bold">{client_name}</font><br/>
Address :- {billing_address_str}<br/>
GSTIN : {client_gst}<br/>
Phone :- {client_phone}"""

    shipping_text = f"""<font name="Helvetica-Bold">{client_name}</font><br/>
Address :- {shipping_address_str}<br/>
GSTIN : {client_gst}<br/>
Phone :- {client_phone}"""

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
    
    # Items Table
    items_header = [
        "No.", "Item & Descripon", "HSN / SAC", "Qty", "Unit", 
        "Rate (Rs)", "Taxable (Rs)", "IGST(%)", "IGST Rs", "Amount (Rs)"
    ]
    
    # Build items row
    items_data = [items_header]
    
    total_taxable = 0
    total_igst = 0
    total_amount = 0

    if hasattr(quotation, 'items') and quotation.items:
        for idx, item in enumerate(quotation.items, 1):
            prod = item.product
            desc = f"<font name='Helvetica-Bold'>{prod.name}</font>"
            if getattr(item, 'description', None):
                desc += f"<br/>{item.description}"
                
            qty = float(item.quantity)
            rate = float(item.unit_price)
            taxable = qty * rate
            igst_pct = float(item.tax_percent)
            igst_amt = taxable * (igst_pct / 100.0)
            amt = taxable + igst_amt
            
            total_taxable += taxable
            total_igst += igst_amt
            total_amount += amt
            
            hsn = getattr(prod, 'hsn_code', '84224000') # default or from product
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
        # Dummy row if no items for rendering preview
        desc_p = Paragraph("<font name='Helvetica-Bold'>Vertical Chamber Vacuum Packing Machine</font><br/>Capacity: 1kg - 25kg", style_normal)
        items_data.append(["1", desc_p, "84224000", "2", "Nos", "1,50,000.00", "3,00,000.00", "18", "54,000.00", "3,54,000.00"])
        total_taxable = 300000
        total_igst = 54000
        total_amount = 354000

    items_table = Table(items_data, colWidths=[8*mm, 48*mm, 18*mm, 10*mm, 10*mm, 22*mm, 22*mm, 12*mm, 17*mm, 23*mm])
    
    # Style for items table
    items_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#A8C3E6')), # Header background
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        # Right align numeric columns
        ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),
    ])
    
    # Alternate row colors
    for i in range(1, len(items_data)):
        bg_color = colors.HexColor('#EBF3FA') if i % 2 == 0 else colors.HexColor('#D5E6F6')
        items_style.add('BACKGROUND', (0,i), (-1,i), bg_color)
        
    items_table.setStyle(items_style)
    elements.append(items_table)
    
    # Bottom calculations and Bank Details
    bank_text = f"""<font name="Helvetica-Bold">Bank Details :</font><br/>
Bank Name : {b_name}<br/>
Branch : {b_branch}<br/>
Account No. : {b_acc}<br/>
IFSC : {b_ifsc}"""

    words = get_amount_in_words(total_amount)
    amount_words_text = f"""<font name="Helvetica-Bold">Total Quotation Amount in Words :</font><br/>
<font name="Helvetica-Bold">{words}</font>"""

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

    # Master table for bottom section
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
    
    # Terms & Conditions
    if getattr(quotation, 'terms_and_conditions', None):
        tc_body = quotation.terms_and_conditions.replace('\n', '<br/>')
        tc_text = f"""<font name="Helvetica-Bold">Terms and Conditions:</font><br/>{tc_body}"""
    else:
        tc_text = """<font name="Helvetica-Bold">Terms and Conditions:</font><br/>
* 1 Year Warranty<br/>
* 50% advance payment for order conformation & 50% before Dispatch<br/>
* Delivery Charges at actual<br/>
* Onsite Installation, Demo and Training (India) - Ensuring you fully understand the machine's capabilities<br/>
* Please note that the machine will be supplied with 2 Nos. of 20 kg moulds and 2 Nos. of 25 kg moulds included in our offer"""

    disclaimer = """<font name="Helvetica-Bold">Disclaimer :-</font> The delivery timelines provided are tentative estimates and are subject to variation due to factors including, but not limited to, manufacturing 
schedules, availability of raw materials, transportation constraints, or any other unforeseen circumstances beyond the reasonable control of the Company. 
The Company shall not, under any circumstances, be held liable or responsible for any direct, indirect, incidental, or consequential loss, damage, cost, or 
penalty arising out of, or in connection with, any delay or failure in delivery."""

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
    
    # Signature Section
    sig_text1 = "This is a computer-generated quotaon.E. & O. E."
    sig_text2 = "For,Keya Fusion Technology Pvt Ltd<br/><br/><br/><br/><b>Authorised Signatory</b>"
    
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

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
