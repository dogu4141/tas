from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound
from sqlalchemy import or_, and_, desc
from datetime import datetime, timedelta
import os
import json

from app import db
from models import User, ChatGroup, ChatMessage, ChatAttachment, ActivityLog
from chat_forms import ChatGroupForm, MessageForm, MessageSearchForm

chat = Blueprint('chat', __name__)

# Add necessary routes for chat functionality

@chat.route('/')
@login_required
def index():
    """Chat dashboard with recent conversations and groups"""
    # Get user's direct message conversations
    direct_messages_sent = ChatMessage.query.filter(
        ChatMessage.sender_id == current_user.id,
        ChatMessage.group_id.is_(None)
    ).order_by(ChatMessage.sent_at.desc()).all()
    
    direct_messages_received = ChatMessage.query.filter(
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.group_id.is_(None)
    ).order_by(ChatMessage.sent_at.desc()).all()
    
    # Combine and find unique conversations
    conversations = {}
    for msg in direct_messages_sent:
        if msg.receiver_id not in conversations:
            conversations[msg.receiver_id] = {
                'user': User.query.get(msg.receiver_id),
                'last_message': msg,
                'unread_count': 0
            }
    
    for msg in direct_messages_received:
        if msg.sender_id not in conversations:
            conversations[msg.sender_id] = {
                'user': User.query.get(msg.sender_id),
                'last_message': msg,
                'unread_count': 0
            }
        if not msg.is_read:
            conversations[msg.sender_id]['unread_count'] += 1
    
    # Get user's groups
    user_groups = current_user.chat_groups
    
    # Count unread messages in each group
    groups = []
    for group in user_groups:
        group_obj = {
            'id': group.id,
            'name': group.name,
            'region': group.region,
            'members': group.members,
            'unread_count': 0
        }
        
        # Count unread messages
        unread_count = ChatMessage.query.filter(
            ChatMessage.group_id == group.id,
            ChatMessage.sender_id != current_user.id,
            ChatMessage.is_read == False
        ).count()
        
        group_obj['unread_count'] = unread_count
        groups.append(group_obj)
    
    # List of available users for new conversations
    users = User.query.filter(User.id != current_user.id, User.is_active == True).all()
    
    return render_template('chat/index.html', 
                          conversations=conversations.values(),
                          groups=groups,
                          users=users)

@chat.route('/unread-count')
@login_required
def unread_count():
    """Get count of unread messages for the current user"""
    # Count direct unread messages
    direct_unread = ChatMessage.query.filter(
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False,
        ChatMessage.group_id.is_(None)
    ).count()
    
    # Count group unread messages
    # First get all groups the user is a member of
    user_groups = current_user.chat_groups
    if user_groups:
        group_ids = [g.id for g in user_groups]
        group_unread = ChatMessage.query.filter(
            ChatMessage.group_id.in_(group_ids),
            ChatMessage.sender_id != current_user.id,
            ChatMessage.is_read == False
        ).count()
    else:
        group_unread = 0
    
    # Total unread
    total_unread = direct_unread + group_unread
    
    return jsonify({'count': total_unread})

# Messaging routes
@chat.route('/direct/<int:user_id>')
@login_required
def direct_message(user_id):
    """View direct message conversation with another user"""
    other_user = User.query.get_or_404(user_id)
    
    # Get messages between the users with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Get messages to or from the other user
    messages = ChatMessage.query.filter(
        or_(
            and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == user_id),
            and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == current_user.id)
        ),
        ChatMessage.group_id.is_(None)
    ).order_by(ChatMessage.sent_at.desc()).paginate(page=page, per_page=per_page)
    
    # Mark unread messages as read
    unread_messages = ChatMessage.query.filter(
        ChatMessage.sender_id == user_id,
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False,
        ChatMessage.group_id.is_(None)
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    return render_template('chat/direct.html', 
                          other_user=other_user,
                          messages=messages,
                          form=form)

@chat.route('/send-message', methods=['POST'])
@login_required
def send_message():
    """Send a message to a group or user"""
    # Create a form for CSRF validation
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    if not form.validate_on_submit():
        flash('Geçersiz istek. Lütfen tekrar deneyin.', 'danger')
        return redirect(url_for('chat.index'))
        
    if not request.form.get('content'):
        flash('Mesaj içeriği boş olamaz.', 'danger')
        return redirect(url_for('chat.index'))
    
    group_id = request.form.get('group_id')
    receiver_id = request.form.get('receiver_id')
    
    # Create new message
    message = ChatMessage(
        sender_id=current_user.id,
        content=request.form.get('content'),
        sent_at=datetime.utcnow()
    )
    
    # Handle location if provided
    if request.form.get('location_lat') and request.form.get('location_lng'):
        message.location_lat = float(request.form.get('location_lat'))
        message.location_lng = float(request.form.get('location_lng'))
    
    # Set group or receiver
    if group_id:
        group = ChatGroup.query.get_or_404(int(group_id))
        if current_user not in group.members:
            flash('Bu gruba mesaj gönderme yetkiniz yok.', 'danger')
            return redirect(url_for('chat.index'))
            
        message.group_id = group.id
        redirect_url = url_for('chat.view_group', group_id=group.id)
    elif receiver_id:
        receiver = User.query.get_or_404(int(receiver_id))
        message.receiver_id = receiver.id
        redirect_url = url_for('chat.direct_message', user_id=receiver.id)
    else:
        flash('Mesaj göndermek için bir alıcı veya grup belirtmelisiniz.', 'danger')
        return redirect(url_for('chat.index'))
    
    # Handle attachment if provided
    if 'attachment' in request.files and request.files['attachment'].filename:
        file = request.files['attachment']
        filename = secure_filename(file.filename)
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.static_folder, 'uploads/chat')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Create attachment record
        file_type = filename.split('.')[-1].lower()
        file_size = os.path.getsize(file_path)
        
        # Set has_attachment flag
        message.has_attachment = True
        
        # Add message to get ID before creating attachment
        db.session.add(message)
        db.session.flush()
        
        attachment = ChatAttachment(
            message_id=message.id,
            file_name=filename,
            file_path=f'/static/uploads/chat/{filename}',
            file_type=file_type,
            file_size=file_size
        )
        db.session.add(attachment)
    else:
        db.session.add(message)
    
    # Log activity
    log_action = f"send_message_{'group' if group_id else 'direct'}"
    log_entity_type = "chat_message"
    log_details = f"Mesaj gönderildi: {message.content[:50]}..." if len(message.content) > 50 else message.content
    
    log = ActivityLog(
        user_id=current_user.id,
        action=log_action,
        entity_type=log_entity_type,
        entity_id=message.id,
        details=log_details,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    
    # If it's an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'message_id': message.id,
            'sent_at': message.sent_at.strftime('%H:%M'),
            'content': message.content
        })
    
    flash('Mesaj gönderildi.', 'success')
    return redirect(redirect_url)

@chat.route('/group/<int:group_id>')
@login_required
def view_group(group_id):
    """View a chat group and its messages"""
    group = ChatGroup.query.get_or_404(group_id)
    
    # Check if user is a member of this group
    if current_user not in group.members:
        flash('Bu gruba erişim yetkiniz yok.', 'danger')
        return redirect(url_for('chat.index'))
    
    # Get messages with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    messages = ChatMessage.query.filter(
        ChatMessage.group_id == group.id
    ).order_by(ChatMessage.sent_at.desc()).paginate(page=page, per_page=per_page)
    
    # Mark unread messages as read
    unread_messages = ChatMessage.query.filter(
        ChatMessage.group_id == group.id,
        ChatMessage.sender_id != current_user.id,
        ChatMessage.is_read == False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    # Message form for CSRF validation
    form = MessageForm()
    
    return render_template('chat/group.html',
                          group=group,
                          messages=messages,
                          form=form)

@chat.route('/manage-groups')
@login_required
def manage_groups():
    """Manage chat groups"""
    # Only allow admin and moderator to see all groups
    if current_user.role in ['admin', 'moderator']:
        groups = ChatGroup.query.all()
    else:
        groups = current_user.chat_groups
    
    return render_template('chat/manage_groups.html',
                          groups=groups)

@chat.route('/create-group', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new chat group"""
    # Only allow admin and moderator to create groups
    if current_user.role not in ['admin', 'moderator']:
        flash('Grup oluşturma yetkiniz yok.', 'danger')
        return redirect(url_for('chat.index'))
    
    form = ChatGroupForm()
    
    # Get all users for the members field
    users = User.query.filter(User.is_active == True).all()
    form.members.choices = [(user.id, f"{user.full_name} ({user.username})") for user in users]
    
    if form.validate_on_submit():
        # Create new group
        group = ChatGroup(
            name=form.name.data,
            description=form.description.data,
            region=form.region.data,
            is_private=form.is_private.data,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        # Add members
        if form.members.data:
            for user_id in form.members.data:
                user = User.query.get(user_id)
                if user:
                    group.members.append(user)
        
        # Add current user as member if not already added
        if current_user not in group.members:
            group.members.append(current_user)
        
        db.session.add(group)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="create_chat_group",
            entity_type="chat_group",
            details=f"Sohbet grubu oluşturuldu: {group.name}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        
        flash(f'"{group.name}" grubu başarıyla oluşturuldu.', 'success')
        return redirect(url_for('chat.manage_groups'))
    
    return render_template('chat/create_group.html', form=form)

@chat.route('/edit-group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    """Edit an existing chat group"""
    group = ChatGroup.query.get_or_404(group_id)
    
    # Check permission
    if current_user.role not in ['admin', 'moderator'] and group.created_by != current_user.id:
        flash('Bu grubu düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('chat.index'))
    
    form = ChatGroupForm(obj=group)
    
    # Get all users for the members field
    users = User.query.filter(User.is_active == True).all()
    form.members.choices = [(user.id, f"{user.full_name} ({user.username})") for user in users]
    
    # Set current members
    if request.method == 'GET':
        form.members.data = [member.id for member in group.members]
    
    if form.validate_on_submit():
        # Update group details
        group.name = form.name.data
        group.description = form.description.data
        group.region = form.region.data
        group.is_private = form.is_private.data
        
        # Update members
        group.members = []
        if form.members.data:
            for user_id in form.members.data:
                user = User.query.get(user_id)
                if user:
                    group.members.append(user)
        
        # Add current user as member if not already added
        if current_user not in group.members:
            group.members.append(current_user)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="update_chat_group",
            entity_type="chat_group",
            entity_id=group.id,
            details=f"Sohbet grubu güncellendi: {group.name}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        
        flash(f'"{group.name}" grubu başarıyla güncellendi.', 'success')
        return redirect(url_for('chat.manage_groups'))
    
    return render_template('chat/edit_group.html', form=form, group=group)

@chat.route('/delete-group/<int:group_id>', methods=['POST'])
@login_required
def delete_group(group_id):
    """Delete a chat group"""
    group = ChatGroup.query.get_or_404(group_id)
    
    # Check permission
    if current_user.role not in ['admin', 'moderator'] and group.created_by != current_user.id:
        flash('Bu grubu silme yetkiniz yok.', 'danger')
        return redirect(url_for('chat.index'))
    
    group_name = group.name
    
    # Delete all messages in the group
    ChatMessage.query.filter_by(group_id=group.id).delete()
    
    # Delete the group
    db.session.delete(group)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="delete_chat_group",
        entity_type="chat_group",
        details=f"Sohbet grubu silindi: {group_name}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    
    flash(f'"{group_name}" grubu başarıyla silindi.', 'success')
    return redirect(url_for('chat.manage_groups'))

@chat.route('/get-updates')
@login_required
def get_updates():
    """Poll for new messages and notifications (for AJAX)"""
    # Get timestamp of last update from request
    last_update = request.args.get('last_update')
    if last_update:
        last_update = datetime.fromisoformat(last_update)
    else:
        # Default to current time minus 10 seconds if no timestamp provided
        last_update = datetime.utcnow() - timedelta(seconds=10)
    
    # Get new direct messages
    new_direct_messages = ChatMessage.query.filter(
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.sent_at > last_update,
        ChatMessage.group_id.is_(None)
    ).all()
    
    # Get new group messages
    user_groups = current_user.chat_groups
    if user_groups:
        user_group_ids = [g.id for g in user_groups]
        new_group_messages = ChatMessage.query.filter(
            ChatMessage.group_id.in_(user_group_ids),
            ChatMessage.sender_id != current_user.id,
            ChatMessage.sent_at > last_update
        ).all()
    else:
        new_group_messages = []
    
    # Format messages for JSON response
    direct_messages_data = []
    for msg in new_direct_messages:
        direct_messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.full_name,
            'content': msg.content,
            'sent_at': msg.sent_at.isoformat()
        })
    
    group_messages_data = []
    for msg in new_group_messages:
        group_messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.full_name,
            'group_id': msg.group_id,
            'group_name': msg.group.name if msg.group else '',
            'content': msg.content,
            'sent_at': msg.sent_at.isoformat()
        })
    
    return jsonify({
        'new_messages': len(direct_messages_data) > 0 or len(group_messages_data) > 0,
        'direct_messages': direct_messages_data,
        'group_messages': group_messages_data,
        'timestamp': datetime.utcnow().isoformat()
    })

@chat.route('/search')
@login_required
def search():
    """Search for messages"""
    search_term = request.args.get('search_term', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search_type = request.args.get('search_type', 'content')
    
    # Convert date strings to datetime objects if provided
    date_from_obj = None
    date_to_obj = None
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Set time to end of day
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass
    
    # Build the query
    query = ChatMessage.query
    
    # Filter by search type
    if search_type == 'content' and search_term:
        query = query.filter(ChatMessage.content.ilike(f'%{search_term}%'))
    elif search_type == 'sender' and search_term:
        # Join with User table to search by sender name or username
        query = query.join(User, ChatMessage.sender_id == User.id).filter(
            or_(
                User.username.ilike(f'%{search_term}%'),
                User.first_name.ilike(f'%{search_term}%'),
                User.last_name.ilike(f'%{search_term}%')
            )
        )
    elif search_type == 'group' and search_term:
        # Join with Group table to search by group name
        query = query.join(ChatGroup, ChatMessage.group_id == ChatGroup.id).filter(
            ChatGroup.name.ilike(f'%{search_term}%')
        )
    
    # Filter by date range
    if date_from_obj:
        query = query.filter(ChatMessage.sent_at >= date_from_obj)
    
    if date_to_obj:
        query = query.filter(ChatMessage.sent_at <= date_to_obj)
    
    # Filter to only show messages user has access to
    user_groups = current_user.chat_groups
    if user_groups:
        user_group_ids = [g.id for g in user_groups]
        
        # User can see: 
        # 1. Messages the user sent
        # 2. Direct messages sent to the user
        # 3. Messages in groups the user is a member of
        query = query.filter(
            or_(
                ChatMessage.sender_id == current_user.id,
                and_(ChatMessage.receiver_id == current_user.id, ChatMessage.group_id.is_(None)),
                ChatMessage.group_id.in_(user_group_ids)
            )
        )
    else:
        # If user is not in any groups, just show direct messages
        query = query.filter(
            or_(
                ChatMessage.sender_id == current_user.id,
                and_(ChatMessage.receiver_id == current_user.id, ChatMessage.group_id.is_(None))
            )
        )
    
    # Sort by sent time, most recent first
    query = query.order_by(ChatMessage.sent_at.desc())
    
    # Paginate results
    page = request.args.get('page', 1, type=int)
    per_page = 20
    results = query.paginate(page=page, per_page=per_page)
    
    # Create a search form with the current search parameters
    form = MessageSearchForm()
    form.search_term.data = search_term
    form.date_from.data = date_from
    form.date_to.data = date_to
    form.search_type.data = search_type
    
    return render_template('chat/search_results.html',
                          results=results,
                          search_term=search_term,
                          date_from=date_from,
                          date_to=date_to,
                          search_type=search_type,
                          form=form)