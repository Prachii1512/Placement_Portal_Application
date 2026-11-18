from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' | 'student' | 'company'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship("StudentProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship("CompanyProfile", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "role": self.role, "is_active": self.is_active}


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=False)
    branch = db.Column(db.String(100))
    cgpa = db.Column(db.Float, default=0.0)
    grad_year = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    resume_path = db.Column(db.String(255))
    is_blacklisted = db.Column(db.Boolean, default=False)

    applications = db.relationship("Application", backref="student", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "name": self.name, "branch": self.branch,
            "cgpa": self.cgpa, "grad_year": self.grad_year, "phone": self.phone,
            "resume_path": self.resume_path, "is_blacklisted": self.is_blacklisted,
            "email": self.user.email if self.user else None,
            "is_active": self.user.is_active if self.user else True,
        }


class CompanyProfile(db.Model):
    __tablename__ = "company_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(255))
    approval_status = db.Column(db.String(20), default="pending")  # pending/approved/rejected
    is_blacklisted = db.Column(db.Boolean, default=False)

    drives = db.relationship("Drive", backref="company", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "company_name": self.company_name,
            "hr_contact": self.hr_contact, "website": self.website,
            "approval_status": self.approval_status, "is_blacklisted": self.is_blacklisted,
            "email": self.user.email if self.user else None,
            "is_active": self.user.is_active if self.user else True,
        }


class Drive(db.Model):
    __tablename__ = "drives"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profiles.id"), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text)
    eligible_branch = db.Column(db.String(150))  # comma separated, "Any" = all
    min_cgpa = db.Column(db.Float, default=0.0)
    eligible_year = db.Column(db.Integer)
    application_deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending/approved/rejected/closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship("Application", backref="drive", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "company_id": self.company_id,
            "company_name": self.company.company_name if self.company else None,
            "job_title": self.job_title, "job_description": self.job_description,
            "eligible_branch": self.eligible_branch, "min_cgpa": self.min_cgpa,
            "eligible_year": self.eligible_year,
            "application_deadline": self.application_deadline.isoformat() if self.application_deadline else None,
            "status": self.status, "applicant_count": len(self.applications),
        }


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("drives.id"), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="applied")
    # applied / shortlisted / interview_scheduled / selected / rejected

    interview_date = db.Column(db.DateTime, nullable=True)
    interview_mode = db.Column(db.String(30), nullable=True)      # 'Online' or 'In-person'
    interview_location = db.Column(db.String(255), nullable=True)  # meeting link or venue
    interview_notes = db.Column(db.Text, nullable=True)
    result_notes = db.Column(db.Text, nullable=True)  # final remarks when selected/rejected

    __table_args__ = (db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),)

    def to_dict(self):
        return {
            "id": self.id, "student_id": self.student_id, "drive_id": self.drive_id,
            "student_name": self.student.name if self.student else None,
            "student_email": self.student.user.email if self.student and self.student.user else None,
            "job_title": self.drive.job_title if self.drive else None,
            "company_name": self.drive.company.company_name if self.drive and self.drive.company else None,
            "application_date": self.application_date.isoformat() if self.application_date else None,
            "status": self.status,
            "interview_date": self.interview_date.isoformat() if self.interview_date else None,
            "interview_mode": self.interview_mode,
            "interview_location": self.interview_location,
            "interview_notes": self.interview_notes,
            "result_notes": self.result_notes,
        }
