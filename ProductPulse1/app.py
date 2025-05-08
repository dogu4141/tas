import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from datetime import datetime


class Base(DeclarativeBase):
    pass


# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "tasdanlar-dev-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database connection
# Ensure instance folder exists
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'), exist_ok=True)

# Absolute path for SQLite database
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'product_pulse.db')
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WTF_CSRF_ENABLED"] = True

# Initialize SQLAlchemy with the app
db.init_app(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Route name stays the same, blueprint name is 'auth'
login_manager.login_message = 'Lütfen önce giriş yapın.'
login_manager.login_message_category = 'warning'

# Initialize CSRF protection
csrf = CSRFProtect(app)
csrf.init_app(app)
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['WTF_CSRF_CHECK_DEFAULT'] = False

# Add context processor to make 'now' available in all templates
# Custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    from markupsafe import Markup
    return Markup(s.replace('\n', '<br>'))

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Import models after db initialization to avoid circular imports
with app.app_context():
    # Import models.py directly
    from models import User, ChatGroup, ChatMessage, ChatAttachment

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.root import root
    from routes.chat_routes import chat
    from routes.driver import driver
    from routes.vehicles import vehicles
    from routes.damages import damages
    from routes.deliveries import deliveries
    from routes.loads import loads
    from routes.auth import auth

    app.register_blueprint(root)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(chat, url_prefix='/chat')
    app.register_blueprint(driver, url_prefix='/driver')
    app.register_blueprint(vehicles, url_prefix='/vehicles')
    app.register_blueprint(damages, url_prefix='/damages')
    app.register_blueprint(deliveries, url_prefix='/deliveries')
    app.register_blueprint(loads, url_prefix='/loads')

    # Create all tables if they don't exist
    try:
        db.create_all()
        # Create default users if no users exist
        if not User.query.first():
            from werkzeug.security import generate_password_hash

            # Create admin user
            admin = User(
                username='admin',
                email='admin@tasdanlar.com',
                password_hash=generate_password_hash('password123'),
                role='admin',
                first_name='Admin',
                last_name='User',
                is_active=True
            )
            db.session.add(admin)

            # Create moderator user
            moderator = User(
                username='moderator1',
                email='moderator@tasdanlar.com',
                password_hash=generate_password_hash('password123'),
                role='moderator',
                first_name='Moderator',
                last_name='User',
                is_active=True
            )
            db.session.add(moderator)

            # Create driver user
            driver = User(
                username='driver1',
                email='driver@tasdanlar.com',
                password_hash=generate_password_hash('password123'),
                role='driver',
                first_name='Driver',
                last_name='User',
                license_plate='34ABC123',
                is_active=True
            )
            db.session.add(driver)

            db.session.commit()
            logging.info("Created default users (admin, moderator, driver)")
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")