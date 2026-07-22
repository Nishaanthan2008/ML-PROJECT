from flask import Blueprint, make_response, render_template, redirect, url_for, flash
from flask_login import login_required

from app.models.profile_analysis import ProfileAnalysis
from app.services.pdf_exporter import PDFReportGenerator

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/pdf/<int:analysis_id>')
@login_required
def download_pdf(analysis_id):
    """Generates and downloads PDF Trust Intelligence Report."""
    analysis = ProfileAnalysis.query.get_or_404(analysis_id)
    pdf_bytes = PDFReportGenerator.generate_profile_report(analysis)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Profile_Shield_Report_{analysis.digital_dna}.pdf'
    return response

@reports_bp.route('/print/<int:analysis_id>')
@login_required
def print_report(analysis_id):
    """Renders print-optimized HTML report view."""
    analysis = ProfileAnalysis.query.get_or_404(analysis_id)
    return render_template('reports/pdf_template.html', analysis=analysis)
