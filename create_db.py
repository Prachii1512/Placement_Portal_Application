from app import create_app
from extensions import db
from models import User
from config import Config

app = create_app()

with app.app_context():
    db.create_all()
    print("Tables created.")

    existing_admin = User.query.filter_by(role="admin").first()
    if not existing_admin:
        admin = User(email=Config.ADMIN_EMAIL, role="admin", is_active=True)
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created -> email: {Config.ADMIN_EMAIL}  password: {Config.ADMIN_PASSWORD}")
    else:
        print("Admin already exists, skipping seed.")
