"""
Veda Conjoint Experiment Application
Entry point for running the Flask server
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Use PORT from environment (Railway sets this) or default to 5001
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print("\n" + "="*60)
    print("🎯 Veda Conjoint Experiment")
    print("="*60)
    print(f"\n📍 Main Survey:    http://localhost:{port}")
    print(f"📊 Admin Dashboard: http://localhost:{port}/admin")
    print(f"🔧 Debug Mode:     {debug}")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
