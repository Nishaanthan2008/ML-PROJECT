from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    """User model for authentication, roles, and session management."""
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64),  unique=True, nullable=False, index=True)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20),  default='user')   # 'admin' or 'user'
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────────────
    # User → many ProfileAnalyses
    analyses = db.relationship(
        'ProfileAnalysis',
        backref=db.backref('author', lazy='select'),
        lazy='dynamic',
        cascade='all, delete-orphan',
        foreign_keys='ProfileAnalysis.user_id',
    )

    # ── Auth helpers ──────────────────────────────────────────────────
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        return self.role.lower() == 'admin'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
