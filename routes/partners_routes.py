"""
Routes des partenaires et réductions
"""

from flask import Blueprint, render_template

partners_bp = Blueprint('partners', __name__)

@partners_bp.route('/')
def partners():
    """Page des partenaires et réductions"""
    return render_template('partners.html')