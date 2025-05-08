from flask import Blueprint, redirect, url_for, current_app, render_template
from flask_login import current_user
from app import app
import logging
import os

# Create blueprint
root = Blueprint('root', __name__)

@root.route('/')
def index():
    logging.info("Root route accessed")
    # Direct redirection based on authentication status
    if current_user.is_authenticated:
        logging.info(f"Authenticated user: {current_user.username}, redirecting to vehicles.index")
        return redirect(url_for('vehicles.index'))
    else:
        logging.info("User not authenticated, redirecting to auth.login")
        return redirect(url_for('auth.login'))

# Blueprint registration is handled in app.py