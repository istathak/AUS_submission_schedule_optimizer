"""
Flask application for the schedule assignment API.
"""
from flask import Flask, render_template
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from endpoints import assign_cell

app = Flask(__name__, template_folder='templates')

# Register routes
app.add_url_rule('/assign', 'assign_cell', assign_cell, methods=['GET', 'POST'])

@app.route('/', methods=['GET'])
def index():
    """Serve the test interface."""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    from flask import jsonify
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    PORT = 5001
    print("=" * 60)
    print("Schedule Assignment API Server")
    print("=" * 60)
    print(f"\nStarting server on http://0.0.0.0:{PORT}")
    print(f"\nWeb Interface:")
    print(f"  http://localhost:{PORT}")
    print("\nAPI Endpoints:")
    print("  GET      /                    - Web test interface")
    print("  GET/POST /assign              - Assign a cell")
    print("  GET      /health              - Health check")
    print(f"\nExample request:")
    print(f"  curl 'http://localhost:{PORT}/assign?schedule_detail_id=8849241&day_num=1'")
    print("=" * 60)
    app.run(debug=False, host='0.0.0.0', port=PORT)
