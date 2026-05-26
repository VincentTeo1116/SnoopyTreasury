import csv
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

def export_to_csv(data: list, filename: str = None) -> dict:
    if not data:
        return {"success": False, "error": "No data to export", "row_count": 0}
    
    # Create exports directory
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate filename
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transactions_{timestamp}.csv"
    
    filepath = os.path.join(export_dir, filename)
    
    try:
        # Get all unique keys
        fieldnames = set()
        for row in data:
            fieldnames.update(row.keys())
        fieldnames = sorted(list(fieldnames))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Write uppercase headers
            uppercase_headers = [h.upper() for h in fieldnames]
            writer = csv.DictWriter(csvfile, fieldnames=uppercase_headers)
            writer.writeheader()
            
            # Write data with original keys (CSV will have uppercase headers but data remains)
            for row in data:
                # Create row with uppercase keys for writing
                uppercase_row = {k.upper(): row.get(k, '') for k in fieldnames}
                writer.writerow(uppercase_row)
        
        return {
            "success": True,
            "filepath": filepath,
            "filename": filename,
            "row_count": len(data),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "row_count": 0
        }


def export_to_pdf(data: list, title: str = "Transaction Report", filename: str = None) -> dict:    
    if not data:
        return {"success": False, "error": "No data to export", "row_count": 0}
    
    # Create exports directory
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate filename
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.pdf"
    
    filepath = os.path.join(export_dir, filename)
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1E3A5F'),
            spaceAfter=30
        )
        elements.append(Paragraph(title, title_style))
        
        # Date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey
        )
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
        elements.append(Spacer(1, 20))
        
        # Summary
        total_transactions = len(data)
        total_difference = sum([row.get('difference', 0) for row in data])
        
        elements.append(Paragraph(f"Total Transactions: {total_transactions}", styles['Normal']))
        elements.append(Paragraph(f"Total Discrepancy: RM {total_difference:,.2f}", styles['Normal']))
        elements.append(Spacer(1, 20))

        original_headers = list(data[0].keys())
        display_headers = original_headers[:8]
        # Convert to uppercase for display
        uppercase_headers = [h.upper() for h in display_headers]
        
        # Build table data
        table_data = [uppercase_headers]
        
        for row in data[:50]:
            # Use original keys to get values, but display in uppercase column order
            table_row = [str(row.get(h, '')) for h in display_headers]
            table_data.append(table_row)
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A5F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        return {
            "success": True,
            "filepath": filepath,
            "filename": filename,
            "row_count": len(data),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "row_count": 0
        }


def generate_report(transactions: list, report_type: str = "both") -> dict:
    results = {}
    
    if report_type in ["csv", "both"]:
        csv_result = export_to_csv(transactions)
        results["csv"] = csv_result
    
    if report_type in ["pdf", "both"]:
        pdf_result = export_to_pdf(transactions)
        results["pdf"] = pdf_result
    
    return {
        "success": True,
        "reports": results,
        "timestamp": datetime.now().isoformat()
    }
