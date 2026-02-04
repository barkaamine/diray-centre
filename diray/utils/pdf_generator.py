import os
from io import BytesIO
from django.conf import settings
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import uuid
from datetime import datetime

def generate_receipt_pdf(subscription):
    """Generate a PDF receipt for subscription"""
    try:
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for elements
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#34745C'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT,
            spaceAfter=10
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT
        )
        
        # Title
        elements.append(Paragraph("DIRAY CENTRE", title_style))
        elements.append(Paragraph("Reçu de Paiement", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Receipt info
        receipt_data = [
            ["ID Transaction:", str(subscription.transaction_id)],
            ["Date:", subscription.created_at.strftime("%d/%m/%Y %H:%M")],
            ["Statut:", "Paiement complété"],
        ]
        
        receipt_table = Table(receipt_data, colWidths=[3*inch, 4*inch])
        receipt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(receipt_table)
        elements.append(Spacer(1, 30))
        
        # Customer info
        elements.append(Paragraph("Informations Client", heading_style))
        customer_data = [
            ["Nom complet:", subscription.full_name],
            ["Email:", subscription.email],
            ["Téléphone:", subscription.phone],
            ["Ville:", subscription.city],
        ]
        
        customer_table = Table(customer_data, colWidths=[2*inch, 5*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F7F7F7')),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 30))
        
        # Training info
        elements.append(Paragraph("Détails de la Formation", heading_style))
        training = subscription.training
        training_data = [
            ["Formation:", training.title],
            ["Durée:", f"{training.duration_days} jours"],
            ["Prix original:", f"{subscription.original_price_mad} MAD"],
            ["Prix payé:", f"{subscription.paid_price_mad} {subscription.currency_used}"],
            ["Méthode de paiement:", subscription.get_payment_method_display()],
        ]
        
        training_table = Table(training_data, colWidths=[2*inch, 5*inch])
        training_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F7F7F7')),
        ]))
        elements.append(training_table)
        elements.append(Spacer(1, 40))
        
        # Total
        total_data = [
            ["TOTAL PAYÉ:", f"{subscription.paid_price_mad} {subscription.currency_used}"],
        ]
        
        total_table = Table(total_data, colWidths=[3*inch, 4*inch])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#34745C')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 50))
        
        # Footer
        footer_text = """
        <para align=center>
        <font size=9 color=grey>
        Merci pour votre confiance.<br/>
        Ce reçu est valable comme justificatif de paiement.<br/>
        Pour toute question, contactez-nous au +212 522-XXX-XXX ou email@diraycentre.ma
        </font>
        </para>
        """
        elements.append(Paragraph(footer_text, normal_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Save PDF to media directory
        media_root = settings.MEDIA_ROOT
        receipts_dir = os.path.join(media_root, 'receipts')
        os.makedirs(receipts_dir, exist_ok=True)
        
        filename = f"{subscription.transaction_id}.pdf"
        filepath = os.path.join(receipts_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_content)
        
        # Return URL
        return f"/media/receipts/{filename}"
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return None