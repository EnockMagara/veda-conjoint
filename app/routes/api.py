"""
API Routes - RESTful API endpoints for the conjoint experiment
"""
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId

from app.services.session_service import SessionService
from app.services.conjoint_service import ConjointService
from app.services.response_service import ResponseService
from app.services.attribute_service import AttributeService
from app.services.export_service import ExportService

api_bp = Blueprint('api', __name__)


# Global error handler for API blueprint
@api_bp.errorhandler(Exception)
def handle_api_error(error):
    """Handle all API errors and return JSON response."""
    current_app.logger.error(f"API Error: {str(error)}")
    return jsonify({'error': str(error)}), 500


@api_bp.errorhandler(400)
def handle_bad_request(error):
    """Handle 400 Bad Request errors."""
    return jsonify({'error': 'Bad request', 'details': str(error)}), 400


# ============== Session Endpoints ==============

@api_bp.route('/session/start', methods=['POST'])
def start_session():
    """
    Start a new chat session.
    
    Request body (optional):
        - email: User email
        - name: User name
        - zip_code: User zip code
    
    Returns:
        Session info and first question
    """
    try:
        data = request.get_json(silent=True) or {}
        
        result = SessionService.start_session(
            email=data.get('email'),
            name=data.get('name'),
            zip_code=data.get('zip_code')
        )
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error starting session: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/session/<session_id>/state', methods=['GET'])
def get_session_state(session_id):
    """Get current session state including progress."""
    try:
        state = SessionService.get_session_state(session_id)
        if not state:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify(state)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/session/<session_id>/question', methods=['GET'])
def get_current_question(session_id):
    """Get the current question for a session."""
    try:
        question = SessionService.get_current_question(session_id)
        if not question:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify(question)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/session/<session_id>/respond', methods=['POST'])
def submit_response(session_id):
    """
    Submit a response to the current question.
    
    Request body:
        - question_id: ID of the question being answered
        - response: User's response
        - question_type: Type of question (text, choice, number)
    
    Returns:
        Next question or completion status
    """
    data = request.get_json()
    
    if not data or 'question_id' not in data or 'response' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    question_id = data['question_id']
    raw_input = data['response']
    question_type = data.get('question_type', 'text')
    
    # Validate response
    validation = ResponseService.validate_response(question_id, raw_input)
    if not validation['valid']:
        return jsonify({'error': validation['error']}), 400
    
    # Normalize response
    normalized = ResponseService.normalize_text_response(raw_input, question_id)
    
    # Save response
    response = ResponseService.save_response(
        session_id=session_id,
        question_id=question_id,
        question_type=question_type,
        raw_input=raw_input,
        normalized_value=normalized
    )
    
    # Handle special questions
    if question_id == 'email':
        # Link user to session
        name_response = ResponseService.get_response(session_id, 'name')
        name = name_response.normalized_value if name_response else None
        
        SessionService.link_user_to_session(session_id, normalized, name)
    
    elif question_id == 'zip_code':
        # Update user zip code
        session = SessionService.get_session(session_id)
        if session and session.user_id:
            from app.models.user import User
            User.find_by_id(session.user_id).collection.update_one(
                {'_id': session.user_id},
                {'$set': {'zip_code': normalized}}
            )
    
    # Advance to next step
    next_step = SessionService.advance_to_next_step(session_id)
    
    return jsonify({
        'response_saved': True,
        'response_id': str(response.id),
        'next': next_step
    })


@api_bp.route('/session/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    """Mark session as completed."""
    try:
        SessionService.complete_session(session_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============== Conjoint Endpoints ==============

@api_bp.route('/conjoint/<session_id>/round/<int:round_number>', methods=['GET'])
def get_conjoint_round(session_id, round_number):
    """
    Get job cards for a specific conjoint round.
    
    Returns:
        Card A and Card B data with attributes
    """
    try:
        cards = ConjointService.get_round_cards(session_id, round_number)
        if not cards:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify(cards)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/conjoint/<session_id>/choice', methods=['POST'])
def submit_conjoint_choice(session_id):
    """
    Submit a choice for a conjoint round.
    
    Request body:
        - round_number: Current round
        - choice: 'A' or 'B'
        - response_time_ms: Time taken to make choice
    
    Returns:
        Confirmation and next round info
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Missing request body'}), 400
    
    required = ['round_number', 'choice', 'response_time_ms']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        result = ConjointService.record_choice(
            session_id=session_id,
            round_number=data['round_number'],
            choice=data['choice'],
            response_time_ms=data['response_time_ms']
        )
        
        if result.get('error'):
            return jsonify(result), 400
        
        # If conjoint is complete, advance to next step
        if result.get('conjoint_complete'):
            next_step = SessionService.advance_to_next_step(session_id)
            result['next'] = next_step
        
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/conjoint/<session_id>/results', methods=['GET'])
def get_conjoint_results(session_id):
    """Get all conjoint results for a session."""
    try:
        results = ConjointService.get_session_results(session_id)
        if not results:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============== Attribute Endpoints ==============

@api_bp.route('/attributes', methods=['GET'])
def get_attributes():
    """Get all job attribute definitions."""
    try:
        attributes = AttributeService.get_attributes_json()
        return jsonify(attributes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/attributes/statistics', methods=['GET'])
def get_attribute_statistics():
    """Get attribute statistics for experiment design."""
    try:
        stats = AttributeService.get_attribute_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== Export Endpoints ==============

@api_bp.route('/export/session/<session_id>', methods=['GET'])
def export_session(session_id):
    """
    Export data for a single session.
    
    Query params:
        - format: Export format (csv, json, r, python)
    """
    format_type = request.args.get('format', 'csv')
    
    try:
        data = ExportService.export_session_data(session_id, format_type)
        if not data:
            return jsonify({'error': 'Session not found'}), 404
        
        return ExportService.export_to_response(
            data, format_type, f'session_{session_id}'
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/export/all', methods=['GET'])
def export_all():
    """
    Export all experiment data.
    
    Query params:
        - format: Export format (csv, json, r, python)
    """
    format_type = request.args.get('format', 'csv')
    
    try:
        data = ExportService.export_all_data(format_type)
        return ExportService.export_to_response(
            data, format_type, 'conjoint_experiment_data'
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/export/formats', methods=['GET'])
def get_export_formats():
    """Get available export formats."""
    return jsonify(ExportService.get_available_formats())


@api_bp.route('/export/statistics', methods=['GET'])
def get_statistics():
    """Get summary statistics for the experiment."""
    try:
        stats = ExportService.get_summary_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== Health Check ==============

@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Jack & Jill Conjoint Experiment API'
    })
