from flask import Flask, request, jsonify, render_template_string, render_template, send_file
from models import db, Event, Participant, Prize, History
import random
from datetime import datetime, timedelta
import os
import pandas as pd
from werkzeug.utils import secure_filename
import io
import pytz

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "luckydraw.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'luckydraw-secret-key-2025-production-change-this')
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database
db.init_app(app)

# Thailand timezone
THAILAND_TZ = pytz.timezone('Asia/Bangkok')

def get_thai_time():
    """Get current time in Thailand timezone"""
    return datetime.now(THAILAND_TZ)

def format_thai_datetime(dt):
    """Format datetime to Thailand timezone string"""
    if dt.tzinfo is None:
        # Simple heuristic: if hour is 0-6, likely it's converted from Thailand time
        # If hour is 7-23, likely it's already Thailand time (since UTC+7)
        if dt.hour >= 7:
            # Likely already Thailand time, just format it
            return dt.strftime('%d/%m/%Y %H:%M:%S')
        else:
            # Likely UTC time converted incorrectly, treat as UTC
            dt = pytz.utc.localize(dt)
            thai_dt = dt.astimezone(THAILAND_TZ)
            return thai_dt.strftime('%d/%m/%Y %H:%M:%S')
    else:
        # Already timezone aware, convert to Thailand timezone
        thai_dt = dt.astimezone(THAILAND_TZ)
        return thai_dt.strftime('%d/%m/%Y %H:%M:%S')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/event/<int:event_id>')
def event_dashboard(event_id):
    event = Event.query.get_or_404(event_id)
    # Add a method to format the created_at time in Thailand timezone
    event.thai_created_at = format_thai_datetime(event.created_at)
    return render_template('event_dashboard.html', event=event)

@app.route('/event/<int:event_id>/winners')
def winner_showcase(event_id):
    event = Event.query.get_or_404(event_id)
    # Add a method to format the created_at time in Thailand timezone
    event.thai_created_at = format_thai_datetime(event.created_at)
    return render_template('winner_showcase.html', event=event)

@app.route('/api/event/<int:event_id>/draw', methods=['POST'])
def draw_lucky(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        
        if event.event_type == 'classic':
            return handle_classic_draw(event)
        elif event.event_type == 'exchange':
            return handle_exchange_draw(event)
        else:
            return jsonify({'error': 'Invalid event type'}), 400
            
    except Exception as e:
        # Only rollback if not in test mode
        if not event.is_test_mode:
            db.session.rollback()
        return jsonify({'error': str(e)}), 500

def handle_classic_draw(event):
    from flask import request
    
    # Get participants who haven't won yet
    won_participant_ids = db.session.query(History.receiver_participant_id).filter_by(event_id=event.id).all()
    won_participant_ids = [pid[0] for pid in won_participant_ids]
    
    available_participants = Participant.query.filter(
        Participant.event_id == event.id,
        ~Participant.id.in_(won_participant_ids)
    ).all()
    
    if not available_participants:
        return jsonify({'error': 'No participants available for drawing'}), 400
    
    # Check if specific prizes are selected for drawing
    selected_prizes = None
    if request.is_json and request.json:
        selected_prizes = request.json.get('selected_prizes')
    
    if selected_prizes:
        # Get only selected prizes that are available
        prize_ids = [p['prize_id'] for p in selected_prizes]
        available_prizes = Prize.query.filter(
            Prize.event_id == event.id,
            Prize.id.in_(prize_ids),
            Prize.remaining_quantity > 0
        ).all()
        
        # Create a weighted list based on selected quantities
        weighted_prizes = []
        for prize in available_prizes:
            # Find the selected quantity for this prize
            selected_qty = 1  # Default
            for sp in selected_prizes:
                if sp['prize_id'] == prize.id:
                    # Use the selected quantity, but don't exceed remaining quantity
                    selected_qty = min(sp['quantity'], prize.remaining_quantity)
                    break
            
            # Add the prize multiple times based on selected quantity to increase probability
            # This creates a weighted selection where prizes with higher quantity have higher chance
            if selected_qty > 0:
                weighted_prizes.extend([prize] * selected_qty)
        
        if not weighted_prizes:
            return jsonify({'error': 'No selected prizes available for drawing'}), 400
    else:
        # Get all available prizes (original behavior)
        available_prizes = Prize.query.filter(
            Prize.event_id == event.id,
            Prize.remaining_quantity > 0
        ).all()
        
        if not available_prizes:
            return jsonify({'error': 'No prizes available'}), 400
        
        weighted_prizes = available_prizes
    
    # Calculate total quantity to draw
    total_quantity_to_draw = 1  # Default: draw 1 prize
    
    if selected_prizes:
        # Sum up all selected quantities
        total_quantity_to_draw = sum(min(sp['quantity'], 
                                       Prize.query.get(sp['prize_id']).remaining_quantity) 
                                   for sp in selected_prizes 
                                   if Prize.query.get(sp['prize_id']).remaining_quantity > 0)
    
    # Limit to available participants
    total_quantity_to_draw = min(total_quantity_to_draw, len(available_participants))
    
    if total_quantity_to_draw <= 0:
        return jsonify({'error': 'No prizes available to draw'}), 400
    
    # Draw multiple winners if needed
    winners = []
    drawn_prizes = []
    remaining_participants = available_participants.copy()
    remaining_weighted_prizes = weighted_prizes.copy()
    
    for i in range(total_quantity_to_draw):
        if not remaining_participants or not remaining_weighted_prizes:
            break
            
        # Random selection
        winner = random.choice(remaining_participants)
        prize = random.choice(remaining_weighted_prizes)
        
        winners.append(winner)
        drawn_prizes.append(prize)
        
        # Remove winner from remaining participants
        remaining_participants.remove(winner)
        
        # Remove one instance of the prize from weighted list
        remaining_weighted_prizes.remove(prize)
        
        # If not in test mode, update database immediately
        if not event.is_test_mode:
            # Update prize quantity
            prize.remaining_quantity -= 1
            
            # Create history record
            history_record = History(
                event_id=event.id,
                receiver_participant_id=winner.id,
                prize_id=prize.id,
                drawn_at=get_thai_time()
            )
            db.session.add(history_record)
    
    # Commit all changes at once (only in real mode)
    if not event.is_test_mode:
        db.session.commit()
    
    # Create response data
    if len(winners) == 1:
        # Single winner response (backward compatibility)
        response_data = {
            'success': True,
            'winner_name': winners[0].name,
            'prize_name': drawn_prizes[0].name,
            'draw_type': 'classic',
            'is_test_mode': event.is_test_mode
        }
    else:
        # Multiple winners response
        response_data = {
            'success': True,
            'multiple_winners': True,
            'results': [
                {
                    'winner_name': winner.name,
                    'prize_name': prize.name
                }
                for winner, prize in zip(winners, drawn_prizes)
            ],
            'draw_type': 'classic',
            'is_test_mode': event.is_test_mode,
            'total_drawn': len(winners)
        }
    
    return jsonify(response_data)

def handle_exchange_draw(event):
    # Get all history for this event to determine current giver
    history_records = History.query.filter_by(event_id=event.id).order_by(History.drawn_at).all()
    
    if not history_records:
        # First draw - first participant is the giver
        first_participant = Participant.query.filter_by(event_id=event.id).first()
        if not first_participant:
            return jsonify({'error': 'No participants in this event'}), 400
        current_giver = first_participant
    else:
        # Subsequent draws - previous receiver becomes the giver
        last_record = history_records[-1]
        current_giver = Participant.query.get(last_record.receiver_participant_id)
    
    # Get participants who haven't received yet (excluding current giver)
    received_participant_ids = [record.receiver_participant_id for record in history_records]
    
    # Always exclude the current giver from available receivers
    excluded_ids = received_participant_ids + [current_giver.id]
    
    available_receivers = Participant.query.filter(
        Participant.event_id == event.id,
        ~Participant.id.in_(excluded_ids)
    ).all()
    
    if not available_receivers:
        return jsonify({'error': 'No participants available to receive'}), 400
    
    # Random selection of receiver
    receiver = random.choice(available_receivers)
    
    # Create response data
    response_data = {
        'success': True,
        'giver_name': current_giver.name,
        'receiver_name': receiver.name,
        'draw_type': 'exchange',
        'is_test_mode': event.is_test_mode,
        'is_first_draw': len(history_records) == 0  # True if this is the first draw
    }
    
    # If in test mode, return the result without committing to database
    if event.is_test_mode:
        return jsonify(response_data)
    
    # Create history record (only in real mode)
    # For first draw, don't set giver_participant_id
    giver_id = None if len(history_records) == 0 else current_giver.id
    
    history_record = History(
        event_id=event.id,
        giver_participant_id=giver_id,
        receiver_participant_id=receiver.id,
        drawn_at=get_thai_time()
    )
    
    db.session.add(history_record)
    db.session.commit()
    
    return jsonify(response_data)

@app.route('/api/event/<int:event_id>/state', methods=['GET'])
def get_event_state(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Get participants who haven't won yet
    won_participant_ids = db.session.query(History.receiver_participant_id).filter_by(event_id=event.id).all()
    won_participant_ids = [pid[0] for pid in won_participant_ids]
    
    remaining_participants = Participant.query.filter(
        Participant.event_id == event.id,
        ~Participant.id.in_(won_participant_ids)
    ).all()
    
    # Get remaining prizes
    remaining_prizes = Prize.query.filter(
        Prize.event_id == event.id,
        Prize.remaining_quantity > 0
    ).all()
    
    # Get history
    history_records = History.query.filter_by(event_id=event.id).order_by(History.drawn_at.desc()).all()
    
    history_data = []
    for record in history_records:
        history_item = {
            'id': record.id,
            'receiver_name': record.receiver.name,
            'drawn_at': format_thai_datetime(record.drawn_at)
        }
        
        if event.event_type == 'classic' and record.prize:
            history_item['prize_name'] = record.prize.name
        elif event.event_type == 'exchange':
            # For exchange mode, add giver_name if exists (None for first draw)
            history_item['giver_name'] = record.giver.name if record.giver else None
            
        history_data.append(history_item)
    
    return jsonify({
        'event_type': event.event_type,
        'remaining_participants': [{'id': p.id, 'name': p.name} for p in remaining_participants],
        'remaining_prizes': [{'id': p.id, 'name': p.name, 'remaining_quantity': p.remaining_quantity} for p in remaining_prizes],
        'history': history_data,
        'is_test_mode': event.is_test_mode,
        'config': {
            'delay_ms': event.config_delay_ms,
            'draw_text': event.config_draw_text,
            'music_id': event.config_music_id,
            'random_animation': event.config_random_animation,
            'winner_animation': event.config_winner_animation,
            'background_url': event.config_background_url,
            'logo_url': event.config_logo_url
        }
    })

@app.route('/api/event/<int:event_id>/add_participant', methods=['POST'])
def add_participant(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    participant = Participant(
        name=data['name'].strip(),
        event_id=event.id
    )
    
    db.session.add(participant)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'participant': {'id': participant.id, 'name': participant.name}
    })

@app.route('/api/event/<int:event_id>/edit_participant/<int:participant_id>', methods=['POST'])
def edit_participant(event_id, participant_id):
    event = Event.query.get_or_404(event_id)
    
    participant = Participant.query.filter_by(id=participant_id, event_id=event.id).first()
    if not participant:
        return jsonify({'error': 'Participant not found'}), 404
    
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    try:
        new_name = data['name'].strip()
        
        if not new_name:
            return jsonify({'error': 'Participant name cannot be empty'}), 400
        
        # Check if another participant with the same name exists in this event
        existing = Participant.query.filter_by(event_id=event.id, name=new_name).filter(Participant.id != participant.id).first()
        if existing:
            return jsonify({'error': 'Another participant with this name already exists'}), 400
        
        # Update the participant
        participant.name = new_name
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Participant updated successfully',
            'participant': {
                'id': participant.id,
                'name': participant.name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/event/<int:event_id>/delete_participant/<int:participant_id>', methods=['POST'])
def delete_participant(event_id, participant_id):
    event = Event.query.get_or_404(event_id)
    
    participant = Participant.query.filter_by(id=participant_id, event_id=event.id).first()
    if not participant:
        return jsonify({'error': 'Participant not found'}), 404
    
    try:
        # Check if this participant has won any prizes (has history records as receiver)
        won_count = History.query.filter_by(event_id=event.id, receiver_participant_id=participant.id).count()
        
        # Check if this participant has given in exchange mode (has history records as giver)
        given_count = History.query.filter_by(event_id=event.id, giver_participant_id=participant.id).count()
        
        total_history = won_count + given_count
        
        if total_history > 0:
            return jsonify({
                'error': f'Cannot delete participant who has history in this event (won: {won_count}, given: {given_count}). Please reset the event first or use undo function.'
            }), 400
        
        # Get participant info for response
        participant_info = {
            'id': participant.id,
            'name': participant.name
        }
        
        # Delete the participant
        db.session.delete(participant)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Participant "{participant_info["name"]}" deleted successfully',
            'deleted_participant': participant_info
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/event/<int:event_id>/add_prize', methods=['POST'])
def add_prize(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.event_type != 'classic':
        return jsonify({'error': 'Prizes only available for classic events'}), 400
    
    data = request.get_json()
    
    if not data or 'name' not in data or 'quantity' not in data:
        return jsonify({'error': 'Name and quantity are required'}), 400
    
    try:
        quantity = int(data['quantity'])
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid quantity'}), 400
    
    prize = Prize(
        name=data['name'].strip(),
        total_quantity=quantity,
        remaining_quantity=quantity,
        event_id=event.id
    )
    
    db.session.add(prize)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'prize': {
            'id': prize.id, 
            'name': prize.name, 
            'total_quantity': prize.total_quantity,
            'remaining_quantity': prize.remaining_quantity
        }
    })

@app.route('/api/event/<int:event_id>/edit_prize/<int:prize_id>', methods=['POST'])
def edit_prize(event_id, prize_id):
    event = Event.query.get_or_404(event_id)
    
    if event.event_type != 'classic':
        return jsonify({'error': 'Prizes only available for classic events'}), 400
    
    prize = Prize.query.filter_by(id=prize_id, event_id=event.id).first()
    if not prize:
        return jsonify({'error': 'Prize not found'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    if 'name' not in data or 'remaining_quantity' not in data:
        return jsonify({'error': 'Name and remaining_quantity are required'}), 400
    
    try:
        new_name = data['name'].strip()
        new_remaining_quantity = int(data['remaining_quantity'])
        
        if not new_name:
            return jsonify({'error': 'Prize name cannot be empty'}), 400
        
        if new_remaining_quantity < 0:
            return jsonify({'error': 'Remaining quantity cannot be negative'}), 400
        
        # Calculate new total quantity based on drawn + remaining
        original_drawn = prize.total_quantity - prize.remaining_quantity
        new_total_quantity = original_drawn + new_remaining_quantity
        
        if new_total_quantity <= 0:
            return jsonify({'error': 'Total quantity must be positive'}), 400
        
        # Update the prize
        prize.name = new_name
        prize.total_quantity = new_total_quantity
        prize.remaining_quantity = new_remaining_quantity
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Prize updated successfully',
            'prize': {
                'id': prize.id,
                'name': prize.name,
                'total_quantity': prize.total_quantity,
                'remaining_quantity': prize.remaining_quantity
            }
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid quantity values'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/event/<int:event_id>/delete_prize/<int:prize_id>', methods=['POST'])
def delete_prize(event_id, prize_id):
    event = Event.query.get_or_404(event_id)
    
    if event.event_type != 'classic':
        return jsonify({'error': 'Prizes only available for classic events'}), 400
    
    prize = Prize.query.filter_by(id=prize_id, event_id=event.id).first()
    if not prize:
        return jsonify({'error': 'Prize not found'}), 404
    
    try:
        # Check if this prize has been drawn (has history records)
        drawn_count = History.query.filter_by(event_id=event.id, prize_id=prize.id).count()
        
        if drawn_count > 0:
            return jsonify({
                'error': f'Cannot delete prize that has been drawn to {drawn_count} winner(s). Please reset the event first or use undo function.'
            }), 400
        
        # Get prize info for response
        prize_info = {
            'id': prize.id,
            'name': prize.name,
            'total_quantity': prize.total_quantity,
            'remaining_quantity': prize.remaining_quantity
        }
        
        # Delete the prize
        db.session.delete(prize)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Prize "{prize_info["name"]}" deleted successfully',
            'deleted_prize': prize_info
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/event/<int:event_id>/reset', methods=['POST'])
def reset_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    try:
        # Delete all history records for this event
        History.query.filter_by(event_id=event.id).delete()
        
        # Reset all prize quantities to their original total
        prizes = Prize.query.filter_by(event_id=event.id).all()
        for prize in prizes:
            prize.remaining_quantity = prize.total_quantity
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event reset successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/event/<int:event_id>/settings', methods=['POST'])
def update_event_settings(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Update configuration fields
        if 'delay' in data:
            try:
                delay_seconds = float(data['delay'])
                if 1 <= delay_seconds <= 10:
                    event.config_delay_ms = int(delay_seconds * 1000)
                else:
                    return jsonify({'error': 'Delay must be between 1-10 seconds'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid delay value'}), 400
        
        if 'draw_text' in data and data['draw_text'].strip():
            event.config_draw_text = data['draw_text'].strip()
        
        if 'music' in data:
            valid_music = ['drumroll.mp3', 'snare_and_drum.mp3', 'tada.mp3', 'none']
            if data['music'] in valid_music:
                event.config_music_id = data['music']
            else:
                return jsonify({'error': 'Invalid music option'}), 400
        
        if 'random_animation' in data:
            valid_animations = ['scrolling_names', 'spinning_wheel', 'bouncing_icons', 'matrix_rain']
            if data['random_animation'] in valid_animations:
                event.config_random_animation = data['random_animation']
            else:
                return jsonify({'error': 'Invalid random animation option'}), 400
        
        if 'winner_animation' in data:
            valid_winner_animations = ['confetti', 'fireworks', 'balloons', 'sparkles']
            if data['winner_animation'] in valid_winner_animations:
                event.config_winner_animation = data['winner_animation']
            else:
                return jsonify({'error': 'Invalid winner animation option'}), 400
        
        if 'background_url' in data:
            # Allow empty string to remove background
            event.config_background_url = data['background_url'].strip() if data['background_url'] else None
        
        if 'logo_url' in data:
            # Allow empty string to remove logo
            event.config_logo_url = data['logo_url'].strip() if data['logo_url'] else None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'config': {
                'delay_ms': event.config_delay_ms,
                'draw_text': event.config_draw_text,
                'music_id': event.config_music_id,
                'random_animation': event.config_random_animation,
                'winner_animation': event.config_winner_animation,
                'background_url': event.config_background_url,
                'logo_url': event.config_logo_url
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/event/<int:event_id>/toggle_test_mode', methods=['POST'])
def toggle_test_mode(event_id):
    event = Event.query.get_or_404(event_id)
    
    try:
        # Toggle the test mode
        event.is_test_mode = not event.is_test_mode
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_test_mode': event.is_test_mode,
            'message': f'Test mode {"enabled" if event.is_test_mode else "disabled"}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/event/<int:event_id>/undo_draw', methods=['POST'])
def undo_last_draw(event_id):
    event = Event.query.get_or_404(event_id)
    
    try:
        # Find the most recent draw time
        latest_record = History.query.filter_by(event_id=event.id).order_by(History.drawn_at.desc()).first()
        
        if not latest_record:
            return jsonify({'error': 'No draw history found to undo'}), 400
        
        latest_draw_time = latest_record.drawn_at
        
        # Find all records from the same draw session (within 1 second of each other)
        # This handles multiple winners from the same draw
        records_to_undo = History.query.filter(
            History.event_id == event.id,
            History.drawn_at >= latest_draw_time - timedelta(seconds=1),
            History.drawn_at <= latest_draw_time + timedelta(seconds=1)
        ).order_by(History.drawn_at.desc()).all()
        
        if not records_to_undo:
            return jsonify({'error': 'No draw history found to undo'}), 400
        
        undone_records = []
        
        # Process each record
        for record in records_to_undo:
            # If it's a classic event with a prize, restore the prize quantity
            if event.event_type == 'classic' and record.prize_id:
                prize = Prize.query.get(record.prize_id)
                if prize:
                    prize.remaining_quantity += 1
            
            # Collect record info for response
            undone_records.append({
                'receiver_name': record.receiver.name,
                'giver_name': record.giver.name if record.giver else None,
                'prize_name': record.prize.name if record.prize else None,
                'drawn_at': format_thai_datetime(record.drawn_at)
            })
            
            # Delete the history record
            db.session.delete(record)
        
        db.session.commit()
        
        # Create appropriate response message
        if len(undone_records) == 1:
            message = 'Last draw has been undone successfully'
            response_data = {
                'success': True,
                'message': message,
                'undone_record': undone_records[0]
            }
        else:
            message = f'Last draw with {len(undone_records)} winners has been undone successfully'
            response_data = {
                'success': True,
                'message': message,
                'multiple_undone': True,
                'undone_records': undone_records,
                'total_undone': len(undone_records)
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/event/<int:event_id>/import_participants', methods=['POST'])
def import_participants(event_id):
    event = Event.query.get_or_404(event_id)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload CSV or Excel files only.'}), 400
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read file based on extension
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(filepath)
        else:  # xlsx or xls
            df = pd.read_excel(filepath)
        
        # Validate required columns
        if 'name' not in df.columns and 'Name' not in df.columns and 'ชื่อ' not in df.columns:
            os.remove(filepath)  # Clean up temp file
            return jsonify({'error': 'File must contain a column named "name", "Name", or "ชื่อ"'}), 400
        
        # Normalize column name
        name_column = None
        for col in ['name', 'Name', 'ชื่อ']:
            if col in df.columns:
                name_column = col
                break
        
        # Process participants
        added_count = 0
        skipped_count = 0
        errors = []
        
        for index, row in df.iterrows():
            participant_name = str(row[name_column]).strip()
            
            # Skip empty names
            if not participant_name or participant_name.lower() in ['nan', 'none', '']:
                skipped_count += 1
                continue
            
            # Check if participant already exists
            existing = Participant.query.filter_by(event_id=event.id, name=participant_name).first()
            if existing:
                skipped_count += 1
                continue
            
            try:
                participant = Participant(
                    name=participant_name,
                    event_id=event.id
                )
                db.session.add(participant)
                added_count += 1
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        # Commit all participants
        db.session.commit()
        
        # Clean up temp file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Import completed: {added_count} participants added, {skipped_count} skipped',
            'details': {
                'added': added_count,
                'skipped': skipped_count,
                'errors': errors
            }
        })
        
    except Exception as e:
        db.session.rollback()
        # Clean up temp file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'File processing error: {str(e)}'}), 500

@app.route('/api/event/<int:event_id>/import_prizes', methods=['POST'])
def import_prizes(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.event_type != 'classic':
        return jsonify({'error': 'Prizes can only be imported for classic events'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload CSV or Excel files only.'}), 400
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read file based on extension
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(filepath)
        else:  # xlsx or xls
            df = pd.read_excel(filepath)
        
        # Validate required columns
        name_col = None
        quantity_col = None
        
        # Check for name column
        for col in ['name', 'Name', 'ชื่อ', 'prize_name', 'Prize Name', 'ชื่อรางวัล']:
            if col in df.columns:
                name_col = col
                break
        
        # Check for quantity column
        for col in ['quantity', 'Quantity', 'จำนวน', 'total_quantity', 'Total Quantity']:
            if col in df.columns:
                quantity_col = col
                break
        
        if not name_col:
            os.remove(filepath)
            return jsonify({'error': 'File must contain a prize name column (name/Name/ชื่อ/prize_name/Prize Name/ชื่อรางวัล)'}), 400
        
        if not quantity_col:
            os.remove(filepath)
            return jsonify({'error': 'File must contain a quantity column (quantity/Quantity/จำนวน/total_quantity/Total Quantity)'}), 400
        
        # Process prizes
        added_count = 0
        skipped_count = 0
        errors = []
        
        for index, row in df.iterrows():
            prize_name = str(row[name_col]).strip()
            
            # Skip empty names
            if not prize_name or prize_name.lower() in ['nan', 'none', '']:
                skipped_count += 1
                continue
            
            try:
                quantity = int(float(row[quantity_col]))
                if quantity <= 0:
                    errors.append(f"Row {index + 2}: Quantity must be positive")
                    continue
            except (ValueError, TypeError):
                errors.append(f"Row {index + 2}: Invalid quantity value")
                continue
            
            # Check if prize already exists
            existing = Prize.query.filter_by(event_id=event.id, name=prize_name).first()
            if existing:
                skipped_count += 1
                continue
            
            try:
                prize = Prize(
                    name=prize_name,
                    total_quantity=quantity,
                    remaining_quantity=quantity,
                    event_id=event.id
                )
                db.session.add(prize)
                added_count += 1
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        # Commit all prizes
        db.session.commit()
        
        # Clean up temp file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Import completed: {added_count} prizes added, {skipped_count} skipped',
            'details': {
                'added': added_count,
                'skipped': skipped_count,
                'errors': errors
            }
        })
        
    except Exception as e:
        db.session.rollback()
        # Clean up temp file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'File processing error: {str(e)}'}), 500

@app.route('/api/event/<int:event_id>/export_history', methods=['GET'])
def export_history(event_id):
    event = Event.query.get_or_404(event_id)
    history_records = History.query.filter_by(event_id=event.id).order_by(History.drawn_at.asc()).all()

    history_data = []
    for record in history_records:
        history_item = {
            'Winner Name': record.receiver.name,
            'Prize': record.prize.name if record.prize else '',
            'Giver Name': record.giver.name if record.giver else '',
            'Drawn At': format_thai_datetime(record.drawn_at)
        }
        history_data.append(history_item)

    df = pd.DataFrame(history_data)
    
    # Create an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Draw History')
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'event_{event.id}_history.xlsx'
    )

@app.route('/api/create_event', methods=['POST'])
def create_event():
    data = request.get_json()
    
    if not data or 'name' not in data or 'event_type' not in data:
        return jsonify({'error': 'Name and event_type are required'}), 400
    
    try:
        name = data['name'].strip()
        event_type = data['event_type'].strip()
        
        if not name:
            return jsonify({'error': 'Event name cannot be empty'}), 400
        
        if event_type not in ['classic', 'exchange']:
            return jsonify({'error': 'Event type must be "classic" or "exchange"'}), 400
        
        # Create new event
        event = Event(
            name=name,
            event_type=event_type,
            created_at=get_thai_time()
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event created successfully',
            'event_id': event.id,
            'event': {
                'id': event.id,
                'name': event.name,
                'event_type': event.event_type,
                'created_at': format_thai_datetime(event.created_at)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        events = Event.query.order_by(Event.created_at.desc()).all()
        
        events_data = []
        for event in events:
            # Get participant and prize counts
            participant_count = Participant.query.filter_by(event_id=event.id).count()
            prize_count = Prize.query.filter_by(event_id=event.id).count() if event.event_type == 'classic' else 0
            history_count = History.query.filter_by(event_id=event.id).count()
            
            events_data.append({
                'id': event.id,
                'name': event.name,
                'event_type': event.event_type,
                'created_at': format_thai_datetime(event.created_at),
                'participant_count': participant_count,
                'prize_count': prize_count,
                'history_count': history_count,
                'is_test_mode': event.is_test_mode
            })
        
        return jsonify({
            'success': True,
            'events': events_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Production mode for PythonAnywhere
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=debug_mode, port=port, host='0.0.0.0')