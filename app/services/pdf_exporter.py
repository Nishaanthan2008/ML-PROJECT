import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFReportGenerator:
    """Generates commercial-grade PDF Trust Intelligence Reports using ReportLab."""

    @staticmethod
    def generate_profile_report(analysis_model):
        """
        Creates a PDF document in memory and returns bytes.
        
        analysis_model: ProfileAnalysis instance
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0f172a'),
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            fontName='Helvetica'
        )

        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#1e293b'),
            fontName='Helvetica-Bold',
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'BodyDark',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#334155'),
            fontName='Helvetica'
        )

        badge_style = ParagraphStyle(
            'BadgeStyle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#ffffff'),
            fontName='Helvetica-Bold',
            alignment=1
        )

        story = []

        # 1. Header Banner
        header_table_data = [
            [
                Paragraph("<b>PROFILE SHIELD AI</b><br/><font size=8 color='#64748b'>Next Generation Trust Intelligence Platform</font>", title_style),
                Paragraph(f"<b>REPORT ID:</b> {analysis_model.digital_dna}<br/><b>DATE:</b> {analysis_model.created_at.strftime('%Y-%m-%d')}", subtitle_style)
            ]
        ]
        header_table = Table(header_table_data, colWidths=[340, 200])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6366f1'), spaceAfter=15))

        # 2. Target Profile Summary
        profile_meta = [
            [
                Paragraph(f"<b>Target Handle:</b> @{analysis_model.username}", body_style),
                Paragraph(f"<b>Platform:</b> {analysis_model.platform}", body_style),
                Paragraph(f"<b>Account Age:</b> {analysis_model.account_age_days} days", body_style)
            ],
            [
                Paragraph(f"<b>Followers:</b> {analysis_model.followers_count:,}", body_style),
                Paragraph(f"<b>Following:</b> {analysis_model.following_count:,}", body_style),
                Paragraph(f"<b>Posts:</b> {analysis_model.posts_count:,}", body_style)
            ]
        ]
        meta_table = Table(profile_meta, colWidths=[180, 180, 180])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('PADDING', (0,0), (-1,-1), 8),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))

        # 3. Trust Score & Intelligence Badges
        risk_color_hex = '#22c55e' if analysis_model.risk_level == 'Low' else \
                         ('#eab308' if analysis_model.risk_level == 'Moderate' else \
                         ('#f97316' if analysis_model.risk_level == 'High' else '#ef4444'))

        score_box_data = [
            [
                Paragraph(f"<font size=28 color='{risk_color_hex}'><b>{int(analysis_model.trust_score)}</b></font><font size=12 color='#64748b'>/100</font><br/><b>AI TRUST SCORE</b>", ParagraphStyle('Score', parent=body_style, alignment=1)),
                Paragraph(f"<b>CONFIDENCE</b><br/><font size=16 color='#3b82f6'><b>{int(analysis_model.confidence)}%</b></font>", ParagraphStyle('Conf', parent=body_style, alignment=1)),
                Paragraph(f"<b>RISK LEVEL</b><br/><font size=14 color='{risk_color_hex}'><b>{analysis_model.risk_level.upper()}</b></font>", ParagraphStyle('Risk', parent=body_style, alignment=1)),
                Paragraph(f"<b>CLUSTER</b><br/><font size=12 color='#6366f1'><b>{analysis_model.behaviour_cluster}</b></font>", ParagraphStyle('Clust', parent=body_style, alignment=1))
            ]
        ]
        score_table = Table(score_box_data, colWidths=[135, 135, 135, 135])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 10),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 15))

        # 4. AI Security Analyst Narrative
        story.append(Paragraph("AI Analyst Assessment & Narrative", h2_style))
        narrative_p = Paragraph(f"<i>\"{analysis_model.ai_explanation_narrative}\"</i>", ParagraphStyle('Narrative', parent=body_style, backColor=colors.HexColor('#e0e7ff'), borderPadding=10, textColor=colors.HexColor('#1e1b4b')))
        story.append(narrative_p)
        story.append(Spacer(1, 15))

        # 5. Sub-scores Table Breakdown
        story.append(Paragraph("Sub-Score Intelligence Breakdown", h2_style))
        sub_scores = analysis_model.sub_scores
        sub_data = [
            [Paragraph("<b>Metric Dimension</b>", body_style), Paragraph("<b>Score</b>", body_style), Paragraph("<b>Status Assessment</b>", body_style)]
        ]
        for key, val in sub_scores.items():
            dim_name = key.replace('_', ' ').title()
            val_num = float(val)
            status_str = "Optimal" if val_num >= 75 else ("Acceptable" if val_num >= 50 else "High Anomaly Risk")
            sub_data.append([
                Paragraph(f"<b>{dim_name}</b>", body_style),
                Paragraph(f"<b>{val_num:.1f} / 100</b>", body_style),
                Paragraph(status_str, body_style)
            ])
            
        sub_table = Table(sub_data, colWidths=[200, 140, 200])
        sub_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ]))
        story.append(sub_table)
        story.append(Spacer(1, 15))

        # 6. Actionable AI Recommendation
        story.append(Paragraph("Platform Recommendation & Action Plan", h2_style))
        rec_box = Table([[
            Paragraph(f"<b>RECOMMENDED ACTION:</b> {analysis_model.recommendation}<br/><font color='#64748b'>Health Status: <b>{analysis_model.health_meter}</b>. DNA Code: <b>{analysis_model.digital_dna}</b></font>", body_style)
        ]], colWidths=[540])
        rec_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#6366f1')),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(rec_box)
        story.append(Spacer(1, 20))

        # Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
        story.append(Paragraph("Generated by Profile Shield AI • Next Generation Social Profile Trust Intelligence Platform • Confidential", subtitle_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
