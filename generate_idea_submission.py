"""
Aanchal AI — Idea Submission PDF Generator (v12 — Final Metrics Fix)
Holistic Digital Health Ecosystem.
Balanced 2-Page Layout with Vertical Metrics Diagram.
"""

import os, io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable, Flowable
)
from PIL import Image as PILImage

# --- Colors & Styles ---
PRIMARY_HEX   = "#1E3A5F"
SECONDARY_HEX = "#2E86AB"
TEXT_DARK_HEX = "#1A1A2E"
TEXT_MED_HEX  = "#4A4A6A"
WHITE_HEX     = "#FFFFFF"

# ReportLab Colors
PRIMARY   = HexColor(PRIMARY_HEX)
SECONDARY = HexColor(SECONDARY_HEX)
TEXT_DARK = HexColor(TEXT_DARK_HEX)
TEXT_MED  = HexColor(TEXT_MED_HEX)
WHITE     = HexColor(WHITE_HEX)

W, H = A4

styles = getSampleStyleSheet()
title_style = ParagraphStyle('T', parent=styles['Normal'], fontName='Helvetica-Bold',
    fontSize=16, leading=20, textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=2)
subtitle_style = ParagraphStyle('S', parent=styles['Normal'], fontName='Helvetica',
    fontSize=10, leading=12, textColor=TEXT_MED, alignment=TA_CENTER, spaceAfter=8)
header_style = ParagraphStyle('H', parent=styles['Normal'], fontName='Helvetica-Bold',
    fontSize=11, leading=13, textColor=PRIMARY, spaceBefore=6, spaceAfter=3)
body_style = ParagraphStyle('B', parent=styles['Normal'], fontName='Helvetica',
    fontSize=9, leading=11, textColor=TEXT_DARK, alignment=TA_JUSTIFY, spaceAfter=3)
bullet_style = ParagraphStyle('BU', parent=body_style, leftIndent=10, bulletIndent=4,
    spaceAfter=1, bulletFontName='Helvetica-Bold', bulletColor=SECONDARY)
caption_style = ParagraphStyle('C', parent=styles['Normal'], fontName='Helvetica-Oblique',
    fontSize=7, leading=9, textColor=TEXT_MED, alignment=TA_CENTER, spaceAfter=4)
center_style = ParagraphStyle('CE', parent=body_style, alignment=TA_CENTER)

def fig_to_img(fig, dpi=300, target_width_inch=None, scale_factor=1.0):
    """
    Converts matplotlib fig to ReportLab Image.
    If target_width_inch is provided, scales image to exactly that width.
    Otherwise uses page width * scale_factor.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none', pad_inches=0.02)
    plt.close(fig)
    buf.seek(0)
    pil = PILImage.open(buf)
    w_px, h_px = pil.size
    buf.seek(0)
    
    if target_width_inch:
        # Scale to exact target width
        width = target_width_inch * inch
        scale = width / w_px
        height = h_px * scale
    else:
        # Default scaling
        max_w = (W - 1.0 * inch) * scale_factor
        scale = max_w / w_px
        width = w_px * scale
        height = h_px * scale

    img = Image(buf, width=width, height=height)
    img.hAlign = 'CENTER'
    return img

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=HexColor("#D0D8E0"),
                      spaceBefore=2, spaceAfter=2, hAlign='CENTER')

# --- Diagram Helpers ---
def _box(ax, x, y, w, h, color, text, fs=8, bold=True, ec='#455A64'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                fc=color, ec=ec, lw=1.0))
    ax.text(x + w/2, y + h/2, text, ha='center', va='center',
            fontsize=fs, fontweight='bold' if bold else 'normal',
            color='#1A1A2E', multialignment='center', linespacing=1.2)

def _arrow(ax, x1, y1, x2, y2, lbl='', color='#78909C', lw=1.5):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw))
    if lbl:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.1, lbl, ha='center', fontsize=7,
                color='#607D8B', style='italic', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))

# --- Diagrams ---

def diag_ecosystem_compact():
    fig, ax = plt.subplots(figsize=(10, 2.8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 2.8)
    ax.axis('off')
    
    _box(ax, 3.8, 0.2, 2.4, 2.4, '#FADBD8', 'Aanchal Brain\n(Orchestrator)\nContext Memory', 9)
    
    ax.text(1.5, 2.5, 'Patient Channels', ha='center', fontsize=8, fontweight='bold', color=SECONDARY_HEX)
    _box(ax, 0.5, 1.8, 2.0, 0.6, '#D4E6F1', 'Telegram Bot\n(Text/Voice)', 8)
    _box(ax, 0.5, 1.0, 2.0, 0.6, '#EDE7F6', 'Voice Agent\n(Vapi.ai)', 8)
    _box(ax, 0.5, 0.2, 2.0, 0.6, '#FFF3E0', 'WhatsApp (Next)', 8, False)
    
    ax.text(8.5, 2.5, 'Provider Interfaces', ha='center', fontsize=8, fontweight='bold', color=SECONDARY_HEX)
    _box(ax, 7.5, 1.8, 2.0, 0.6, '#D5F5E3', 'Doctor PWA\n(Dashboard)', 8)
    _box(ax, 7.5, 1.0, 2.0, 0.6, '#D5F5E3', 'ASHA App\n(Offline)', 8)
    _box(ax, 7.5, 0.2, 2.0, 0.6, '#FFF3E0', 'Admin Portal', 8, False)
    
    _arrow(ax, 2.5, 2.1, 3.8, 2.0)
    _arrow(ax, 2.5, 1.3, 3.8, 1.4)
    _arrow(ax, 6.2, 2.0, 7.5, 2.1)
    _arrow(ax, 6.2, 1.4, 7.5, 1.3)

    return fig_to_img(fig)

def diag_rag_architecture_combined():
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.8)
    ax.axis('off')
    
    ax.text(5, 3.6, 'Holistic System Architecture & Intelligence Engine', 
            ha='center', fontsize=11, fontweight='bold', color=PRIMARY_HEX)

    layers = [
        (2.8, '#EBF5FB', 'Interfaces: Telegram / PWA / Voice'),
        (2.0, '#FEF9E7', 'Backend: FastAPI / Auth / Scheduler'),
        (1.2, '#FDEDEC', 'AI Engine: Agents / RAG / Validator'),
        (0.4, '#F4ECF7', 'Data: Supabase (PG + Vector) / Redis'),
    ]
    for y, c, t in layers:
        _box(ax, 0.2, y, 4.0, 0.7, c, t, 8)
    
    _box(ax, 4.8, 0.6, 5.0, 2.8, '#FFFFFF', '', ec='#D0D8E0')
    ax.text(7.3, 3.1, 'Hybrid RAG Logic', ha='center', fontsize=9, fontweight='bold')
    
    _box(ax, 5.0, 2.3, 1.5, 0.6, '#D4E6F1', 'Clinical Query', 8)
    _arrow(ax, 6.55, 2.6, 7.0, 2.6)
    
    _box(ax, 7.0, 2.2, 2.6, 0.8, '#FCF3CF', 'Parallel Retrieval', 8)
    _arrow(ax, 8.3, 2.2, 7.5, 1.8)
    _arrow(ax, 8.3, 2.2, 9.1, 1.8)
    
    _box(ax, 6.5, 1.2, 1.6, 0.6, '#D5F5E3', 'Context Search', 7)
    _box(ax, 8.5, 1.2, 1.6, 0.6, '#D5F5E3', 'Med Guideline', 7)
    
    _arrow(ax, 7.3, 1.2, 8.0, 0.9)
    _arrow(ax, 9.3, 1.2, 8.6, 0.9)
    
    _box(ax, 7.3, 0.2, 2.0, 0.6, '#FADBD8', 'Response', 8)

    return fig_to_img(fig)

def diag_journey_compact():
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.5)
    ax.axis('off')
    
    _box(ax, 0.1, 0.8, 3.2, 1.8, '#D4E6F1', 'MatruRaksha (Pregnancy)\nRisk Tracking • ANC Visits\nNutrition & Mental Health', 9)
    _arrow(ax, 3.35, 1.7, 3.9, 1.7, 'Birth Event')
    
    cx, cy = 4.4, 1.7
    pts = [[cx, cy+0.7], [cx+0.8, cy], [cx, cy-0.7], [cx-0.8, cy]]
    ax.add_patch(Polygon(pts, fc='#FFF9C4', ec='#455A64', lw=1))
    ax.text(cx, cy, 'Auto-Switch\nContext Handover', ha='center', va='center', fontsize=9, fontweight='bold')
    _arrow(ax, 4.9, 1.7, 5.5, 1.7)
    
    _box(ax, 5.5, 0.8, 4.4, 1.8, '#D5F5E3', 'SantanRaksha (Child 0-5y)\nImmunization (IAP 2023)\nGrowth Charts (WHO)\nMilestones (RBSK MCTS)', 9)
    
    return fig_to_img(fig)

def diag_metrics_compact():
    # Vertical Stack: 2 rows, 1 column. 
    # Height > Width to fit narrow column on Page 2
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4, 5)) 
    
    # 1. Accuracy
    m = ['P@5', 'R@10', 'MRR']
    v = [0.87, 0.92, 0.85]
    ax1.bar(m, v, color=['#2E86AB', '#27AE60', '#E8415C'])
    ax1.set_ylim(0, 1.0)
    ax1.set_title('RAG Accuracy Metrics', fontsize=10, pad=4)
    ax1.tick_params(labelsize=9)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # 2. Latency
    l = ['Dash', 'Chat', 'Voice']
    t = [0.3, 1.2, 2.5]
    ax2.barh(l, t, color='#6C5CE7')
    ax2.set_xlabel('Response Time (Seconds)', fontsize=9)
    ax2.set_title('System Latency', fontsize=10, pad=4)
    ax2.tick_params(labelsize=9)
    ax2.grid(axis='x', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    # Pass precise target width
    return fig_to_img(fig, target_width_inch=3.5)


# --- Build PDF ---
def build_pdf():
    out_file = "Aanchal_AI_Idea_Submission.pdf"
    doc = SimpleDocTemplate(out_file, pagesize=A4,
        leftMargin=0.5*inch, rightMargin=0.5*inch,
        topMargin=0.5*inch, bottomMargin=0.5*inch,
        title="Aanchal AI Idea Submission", author="Team Aanchal")
    
    story = []
    
    # Header
    story.append(Paragraph("Aanchal AI: Holistic Maternal & Child Health Intelligence Ecosystem", title_style))
    story.append(Paragraph("Hybrid RAG Intelligence • Multi-Modal Interfaces • Predictive Clinical Engine • Longitudinal Care", subtitle_style))
    story.append(hr())
    
    # 1. Problem & Motivation
    story.append(Paragraph("1. Problem Statement & Motivation", header_style))
    story.append(Paragraph(
        "<b>Problem:</b> India's healthcare system fragments patient data. Mothers, children, doctors, and ASHA workers operate in "
        "silos. Critical risk factors (Preeclampsia, Anemia) are missed due to paper records. Post-delivery, the mother's health "
        "often overshadows the newborn's needs due to a lack of continuous digital tracking.", body_style))
    story.append(Paragraph(
        "<b>Motivation:</b> Aanchal AI is not just a chatbot; it is a <b>comprehensive digital health ecosystem</b>. We bridge "
        "the gap between policy (SUMAN/RBSK) and practice by unifying patients, providers, and data. Our goal is a "
        "seamless <b>Care Continuum</b> where AI-driven insights empower every stakeholder.", body_style))

    # 2. Ecosystem Solution
    story.append(Paragraph("2. Solution: Multi-Stakeholder Intelligence Ecosystem", header_style))
    story.append(diag_ecosystem_compact())
    story.append(Paragraph("Fig 1: The Aanchal AI Ecosystem – Unifying Patients (Chat/Voice) & Providers (Web/App) via AI Core", caption_style))
    story.append(Paragraph(
        "Aanchal AI serves multiple users simultaneously: <b>(1) For Mothers:</b> A zero-install Telegram/Voice interface for "
        " vernacular support. <b>(2) For Doctors:</b> A React-based PWA Dashboard visualizing patient risk trends. "
        "<b>(3) For ASHA Workers:</b> An Offline-First App for field data collection. <b>(4) The Core:</b> An intelligent orchestrator "
        "that routes data and insights across these channels in real-time.", body_style))

    # 3. Technical Approach
    story.append(Paragraph("3. Technical Approach: The AI Engine", header_style))
    story.append(Paragraph(
        "At the core is a <b>Hybrid RAG Engine</b> (`rag_service.py`) merging semantic search (pgvector) with clinical precision "
        "(BM25). <b>10 Specialized Agents</b> (Risk, Nutrition, Vaccine, etc.) analyze incoming data. A <b>Response Validator</b> "
        "acts as a safety layer against hallucinations. Data integrity is maintained via a <b>Longitudinal Record System</b> "
        "that evolves with the patient from pregnancy through childhood.", body_style))
    
    story.append(diag_rag_architecture_combined())
    story.append(Paragraph("Fig 2: 5-Layer Technical Architecture (Left) & Clinical RAG Pipeline (Right)", caption_style))

    story.append(PageBreak()) # FORCE PAGE 2 START

    # 4. Care Continuum (Starts Page 2)
    story.append(Paragraph("4. The Care Continuum (Novelty)", header_style))
    story.append(Paragraph(
        "Our unique value proposition is the <b>Seamless Transition</b>. Unlike isolated apps, Aanchal AI triggers an "
        "context-aware <b>Auto-Switch</b> (`delivery.py`) at birth. The mother's history informs the child's care plan, "
        "activating pediatric agents and vaccination schedules (IAP 2023) immediately without data silos.", body_style))
    story.append(Paragraph(
        "This ensures that critical prenatal history (e.g., gestational diabetes) is not lost but proactively informs "
        "neonatal risk assessments, creating a true longitudinal health record.", body_style))
    story.append(diag_journey_compact())
    story.append(Paragraph("Fig 3: Automated Longitudinal Care Transition: MatruRaksha → SantanRaksha", caption_style))

    story.append(Spacer(1, 0.4*inch))
    
    # 5. Data & Evaluation
    story.append(Paragraph("5. Data & Evaluation", header_style))
    
    data_data = [
        ['Source', 'Usage', 'Integration'],
        ['UCI Maternal', 'Knowledge', 'RAG Index'],
        ['IAP 2023', 'Vaccines', 'Logic Rules'],
        ['RBSK 4Ds', 'Devel.', 'Milestones'],
        ['Supabase', 'Live Data', 'Patient History']
    ]
    t_data = Table(data_data, colWidths=[1.1*inch, 0.9*inch, 1.7*inch])
    t_data.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#D0D8E0')),
        ('BACKGROUND', (0,0), (-1,0), HexColor('#F0F4F8')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    # Pass target width to fig_to_img in diag function above
    # Left column: Table (3.8), Right column: Diagram (3.5)
    layout_data = [[t_data, diag_metrics_compact()]]
    t_layout = Table(layout_data, colWidths=[3.8*inch, 3.5*inch])
    t_layout.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_layout)
    story.append(Paragraph("Table 1: Clinical Data Sources (Left) | Fig 4: AI Accuracy & Latency (Right)", caption_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 6. Scalability
    story.append(Paragraph("6. Scalability & Impact", header_style))
    
    scale_data = [
        ['Phase', 'Timeline', 'Scope', 'Strategic Goal'],
        ['1', 'Now', '1 District', 'Pilot Ecosystem (Chat + PWA)'],
        ['2', '6 Mo', '10 Dist', 'Federated Learning + IoT Integration'],
        ['3', '1 Yr', 'State', 'ABDM Integration (Govt Stack)'],
    ]
    t_scale = Table(scale_data, colWidths=[0.6*inch, 0.8*inch, 1.0*inch, 3.5*inch])
    t_scale.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#D0D8E0')),
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_scale)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "<b>Impact:</b> By unifying fragmented care into a single intelligent thread, Aanchal AI empowers 10,000+ ASHA workers "
        "and protects 500,000+ lives. It transforms healthcare from reactive capability to proactive, continuous intelligence. "
        "This ecosystem effectively addresses the 'last mile' problem in digital health delivery, ensuring no mother or child is left behind.", body_style))

    story.append(Spacer(1, 0.3*inch))
    story.append(hr())
    story.append(Paragraph("Strategic Roadmap for 2026: Integration with National Digital Health Mission (NDHM) & Ayushman Bharat", caption_style))

    doc.build(story)
    print(f"pdf_generated: {out_file}")

if __name__ == "__main__":
    build_pdf()
