"""
View Routes - Serves HTML templates
"""
from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')


@views_bp.route('/admin')
def admin():
    """Admin dashboard for viewing experiment results."""
    return render_template('admin.html')
