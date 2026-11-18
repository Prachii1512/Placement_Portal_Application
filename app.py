import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, jwt, cache


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    CORS(app)

    from api.auth import auth_bp
    from api.admin import admin_bp
    from api.company import company_bp
    from api.student import student_bp
    from api.drives import drives_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(company_bp, url_prefix="/api/company")
    app.register_blueprint(student_bp, url_prefix="/api/student")
    app.register_blueprint(drives_bp, url_prefix="/api/drives")

    @jwt.unauthorized_loader
    def unauthorized(reason):
        return jsonify({"error": "Missing or invalid token", "detail": reason}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid token", "detail": reason}), 422

    @jwt.expired_token_loader
    def expired_token(header, payload):
        return jsonify({"error": "Token expired"}), 401


    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/admin/dashboard")
    def admin_dashboard():
        return render_template("admin_dashboard.html")

    @app.route("/company/dashboard")
    def company_dashboard():
        return render_template("company_dashboard.html")

    @app.route("/student/dashboard")
    def student_dashboard():
        return render_template("student_dashboard.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
