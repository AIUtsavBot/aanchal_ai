"""
PDF Report Generation Service for Postnatal Care
Creates comprehensive PDF reports with assessment history
"""

import io
import logging
from datetime import datetime
from typing import Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from services.auth_service import supabase_admin

logger = logging.getLogger(__name__)

class PostnatalReportGenerator:
    """Generate PDF reports for postnatal care"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#059669'),  # Green
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#047857'),
            spaceAfter=12,
            spaceBefore=20
        ))
        
        # Alert text
        self.styles.add(ParagraphStyle(
            name='AlertText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            spaceAfter=6
        ))
    
    async def generate_mother_report(self, mother_id: str) -> bytes:
        """
        Generate comprehensive postnatal report for a mother
        
        Args:
            mother_id: Mother's ID
            
        Returns:
            PDF as bytes
        """
        try:
            # Fetch mother data
            mother_result = await supabase_admin.table("mothers").select("*").eq("id", mother_id).single().execute()
            mother = mother_result.data
            
            if not mother:
                raise ValueError(f"Mother {mother_id} not found")
            
            # Fetch assessments
            assessments_result = await supabase_admin.table("postnatal_assessments") \
                .select("*") \
                .eq("mother_id", mother_id) \
                .eq("assessment_type", "mother_postnatal") \
                .order("assessment_date", desc=True) \
                .execute()
            assessments = assessments_result.data or []
            
            # Fetch children
            children_result = await supabase_admin.table("children") \
                .select("*") \
                .eq("mother_id", mother_id) \
                .execute()
            children = children_result.data or []
            
            # Create PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)
            
            # Container for PDF elements
            elements = []
            
            # Title
            elements.append(Paragraph(
                "🏥 Postnatal Care Report",
                self.styles['CustomTitle']
            ))
            elements.append(Spacer(1, 12))
            
            # Mother Information
            elements.append(Paragraph("Mother Information", self.styles['SectionHeading']))
            
            mother_info = [
                ['Name:', mother.get('name', 'N/A')],
                ['Age:', f"{mother.get('age', 'N/A')} years"],
                ['Phone:', mother.get('phone', 'N/A')],
                ['Location:', mother.get('location', 'N/A')],
                ['Status:', mother.get('status', 'N/A').upper()],
                ['Delivery Date:', mother.get('delivery_date', 'N/A')],
            ]
            
            mother_table = Table(mother_info, colWidths=[2*inch, 4*inch])
            mother_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0f2fe')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0c4a6e')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(mother_table)
            elements.append(Spacer(1, 20))
            
            # Assessment History
            if assessments:
                elements.append(Paragraph(
                    f"Assessment History ({len(assessments)} assessments)",
                    self.styles['SectionHeading']
                ))
                
                for idx, assessment in enumerate(assessments[:10]):  # Latest 10
                    elements.append(Paragraph(
                        f"<b>Assessment {idx + 1}</b> - {assessment.get('assessment_date', 'N/A')}",
                        self.styles['Heading3']
                    ))
                    
                    assessment_data = [
                        ['Days Postpartum:', str(assessment.get('days_postpartum', 'N/A'))],
                        ['Temperature:', f"{assessment.get('temperature', 'N/A')}°C"],
                        ['Blood Pressure:', f"{assessment.get('blood_pressure_systolic', '-')}/{assessment.get('blood_pressure_diastolic', '-')} mmHg"],
                        ['Pulse Rate:', f"{assessment.get('pulse_rate', 'N/A')} bpm"],
                        ['Mood Status:', assessment.get('mood_status', 'N/A').replace('_', ' ').title()],
                        ['Breastfeeding:', 'Established' if assessment.get('breastfeeding_established') else 'Not Established'],
                    ]
                    
                    assessment_table = Table(assessment_data, colWidths=[2*inch, 4*inch])
                    assessment_table.setStyle(TableStyle([
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f9fafb')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ]))
                    elements.append(assessment_table)
                    
                    # Danger signs (if any)
                    danger_signs = []
                    if assessment.get('fever'): danger_signs.append('Fever')
                    if assessment.get('excessive_bleeding'): danger_signs.append('Excessive Bleeding')
                    if assessment.get('foul_discharge'): danger_signs.append('Foul Discharge')
                    if assessment.get('mastitis'): danger_signs.append('Mastitis')
                    
                    if danger_signs:
                        elements.append(Paragraph(
                            f"⚠️ <b>Danger Signs:</b> {', '.join(danger_signs)}",
                            self.styles['AlertText']
                        ))
                    
                    # Notes
                    if assessment.get('notes'):
                        elements.append(Paragraph(
                            f"<b>Notes:</b> {assessment.get('notes', '')}",
                            self.styles['Normal']
                        ))
                    
                    elements.append(Spacer(1, 12))
            
            # Children Information
            if children:
                elements.append(PageBreak())
                elements.append(Paragraph("Children Information", self.styles['SectionHeading']))
                
                for child in children:
                    child_info = [
                        ['Name:', child.get('name', 'N/A')],
                        ['Gender:', child.get('gender', 'N/A').title()],
                        ['Birth Date:', child.get('birth_date', 'N/A')],
                        ['Birth Weight:', f"{child.get('birth_weight_kg', 'N/A')} kg"],
                        ['Birth Length:', f"{child.get('birth_length_cm', 'N/A')} cm"],
                    ]
                    
                    child_table = Table(child_info, colWidths=[2*inch, 4*inch])
                    child_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fef3c7')),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ]))
                    elements.append(child_table)
                    elements.append(Spacer(1, 12))
            
            # Footer
            elements.append(Spacer(1, 30))
            elements.append(Paragraph(
                f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                self.styles['Normal']
            ))
            elements.append(Paragraph(
                "Aanchal AI - Maternal Health Guardian System",
                self.styles['Normal']
            ))
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"✅ Generated PDF report for mother {mother_id} ({len(pdf_bytes)} bytes)")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"❌ Error generating PDF report: {e}")
            raise


# Singleton instance
report_generator = PostnatalReportGenerator()
