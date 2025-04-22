import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.config['MONGODB_URI'] = os.getenv('MONGODB_URI', 'mongodb+srv://admin:vanmanh@sudo-code-nhom1.dmiub.mongodb.net/?retryWrites=true&w=majority&appName=Sudo-code-nhom1')
    
    # Register blueprints
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app