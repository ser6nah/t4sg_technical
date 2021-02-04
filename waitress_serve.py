"""Serves the Flask app using waitress"""

from waitress import serve
from application import app

serve(app, host='0.0.0.0', port=8080)