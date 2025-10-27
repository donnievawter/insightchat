from flask import Blueprint

chat_bp = Blueprint('chat', __name__)

from .routes import *  # Import routes to register them with the blueprint