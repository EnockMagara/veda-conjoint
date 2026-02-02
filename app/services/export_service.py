"""
Export Service - Handles data export for analysis
Uses Adapter pattern for format conversion
"""
from typing import List, Dict, Any, Optional
from bson import ObjectId
from flask import Response

from app.services.conjoint_service import ConjointService
from app.patterns.adapter import ExportAdapterFactory


class ExportService:
    """
    Service for exporting experiment data to various formats.
    Uses Adapter pattern for format-specific exports.
    """
    
    @classmethod
    def export_session_data(cls, session_id: str, format_type: str = 'csv') -> str:
        """
        Export data for a single session.
        
        Args:
            session_id: Session ObjectId string
            format_type: Export format (csv, json, r, python)
        
        Returns:
            Formatted export string
        """
        results = ConjointService.get_session_results(session_id)
        if not results:
            return None
        
        adapter = ExportAdapterFactory.create(format_type)
        return adapter.export(results['choices'])
    
    @classmethod
    def export_all_data(cls, format_type: str = 'csv',
                        session_ids: List[str] = None) -> str:
        """
        Export data for multiple or all sessions.
        
        Args:
            format_type: Export format
            session_ids: Optional list of specific sessions
        
        Returns:
            Formatted export string
        """
        data = ConjointService.get_analysis_data(session_ids)
        
        adapter = ExportAdapterFactory.create(format_type)
        return adapter.export(data)
    
    @classmethod
    def export_to_response(cls, data: str, format_type: str,
                           filename: str = 'conjoint_data') -> Response:
        """
        Create a Flask Response for file download.
        
        Args:
            data: Exported data string
            format_type: Export format
            filename: Base filename without extension
        
        Returns:
            Flask Response object
        """
        adapter = ExportAdapterFactory.create(format_type)
        
        response = Response(
            data,
            mimetype=adapter.get_content_type(),
            headers={
                'Content-Disposition': f'attachment; filename={filename}.{adapter.get_file_extension()}'
            }
        )
        return response
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get list of available export formats."""
        return ExportAdapterFactory.get_available_formats()
    
    @classmethod
    def get_summary_statistics(cls, session_ids: List[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics for analysis.
        """
        from app import mongo
        from app.models.chat_session import SessionStatus
        
        # Build query
        session_query = {}
        if session_ids:
            session_query['_id'] = {'$in': [ObjectId(sid) for sid in session_ids]}
        
        # Count sessions by status
        total_sessions = mongo.db.chat_sessions.count_documents(session_query)
        completed_sessions = mongo.db.chat_sessions.count_documents({
            **session_query,
            'status': SessionStatus.COMPLETED.value
        })
        
        # Count total choices
        choice_query = {}
        if session_ids:
            choice_query['session_id'] = {'$in': [ObjectId(sid) for sid in session_ids]}
        total_choices = mongo.db.conjoint_choices.count_documents(choice_query)
        
        # Get choice distribution
        pipeline = [
            {'$match': choice_query} if choice_query else {'$match': {}},
            {'$group': {
                '_id': '$choice',
                'count': {'$sum': 1}
            }}
        ]
        choice_dist = list(mongo.db.conjoint_choices.aggregate(pipeline))
        
        # Average response time
        pipeline = [
            {'$match': choice_query} if choice_query else {'$match': {}},
            {'$group': {
                '_id': None,
                'avg_response_time': {'$avg': '$response_time_ms'},
                'min_response_time': {'$min': '$response_time_ms'},
                'max_response_time': {'$max': '$response_time_ms'}
            }}
        ]
        response_time_stats = list(mongo.db.conjoint_choices.aggregate(pipeline))
        
        return {
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'completion_rate': completed_sessions / total_sessions if total_sessions > 0 else 0,
            'total_choices': total_choices,
            'choice_distribution': {item['_id']: item['count'] for item in choice_dist},
            'response_time_stats': response_time_stats[0] if response_time_stats else {}
        }
