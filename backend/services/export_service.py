
import logging
import io
import csv
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

logger = logging.getLogger(__name__)

class ExportService:
    @staticmethod
    def generate_vaccination_pdf(child_data: dict, vaccinations: list) -> io.BytesIO:
        """Generate PDF report for vaccination history"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Header
        elements.append(Paragraph(f"Vaccination Report: {child_data.get('name', 'Child')}", styles['Title']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Table Data
        data = [['Vaccine', 'Status', 'Due Date', 'Given Date']]
        for v in vaccinations:
            data.append([
                v.get('vaccine_name', ''),
                v.get('status', '').upper(),
                v.get('due_date', '') or '-',
                v.get('administered_date', '') or '-'
            ])
            
        # Table Style
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_csv_export(data: list, fieldnames: list) -> io.StringIO:
        """Generate CSV string from list of dicts"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # Filter row to only include fieldnames
            filtered_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(filtered_row)
        output.seek(0)
        return output
