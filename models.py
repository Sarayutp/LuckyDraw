from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

# Thailand timezone helper
def get_thai_time():
    """Get current time in Thailand timezone"""
    thailand_tz = pytz.timezone('Asia/Bangkok')
    return datetime.now(thailand_tz)

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 'classic' or 'exchange'
    created_at = db.Column(db.DateTime, default=get_thai_time)
    
    # Configuration fields with defaults
    config_delay_ms = db.Column(db.Integer, default=2000)
    config_music_id = db.Column(db.String(100), default='default_upbeat')
    config_random_animation = db.Column(db.String(100), default='scrolling_names')
    config_winner_animation = db.Column(db.String(100), default='confetti')
    config_draw_text = db.Column(db.String(100), default='จับรางวัล')
    config_background_url = db.Column(db.String(500), nullable=True)
    config_logo_url = db.Column(db.String(500), nullable=True)
    is_test_mode = db.Column(db.Boolean, default=False)
    
    # Relationships
    participants = db.relationship('Participant', backref='event', lazy=True, cascade='all, delete-orphan')
    prizes = db.relationship('Prize', backref='event', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('History', backref='event', lazy=True, cascade='all, delete-orphan')

class Participant(db.Model):
    __tablename__ = 'participants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)

class Prize(db.Model):
    __tablename__ = 'prizes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    total_quantity = db.Column(db.Integer, nullable=False)
    remaining_quantity = db.Column(db.Integer, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)

class History(db.Model):
    __tablename__ = 'history'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    giver_participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=True)
    receiver_participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False)
    prize_id = db.Column(db.Integer, db.ForeignKey('prizes.id'), nullable=True)
    drawn_at = db.Column(db.DateTime, default=get_thai_time)
    
    # Relationships for easier access
    giver = db.relationship('Participant', foreign_keys=[giver_participant_id], backref='given_draws')
    receiver = db.relationship('Participant', foreign_keys=[receiver_participant_id], backref='received_draws')
    prize = db.relationship('Prize', backref='draws')