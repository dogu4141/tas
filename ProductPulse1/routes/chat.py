from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound
from sqlalchemy import or_, and_, desc
from datetime import datetime
import os
import json

from app import db
from models import User, ChatGroup, ChatMessage, ChatAttachment, ActivityLog
from chat_forms import ChatGroupForm, MessageForm, MessageSearchForm

chat = Blueprint('chat', __name__)

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
    groups = current_user.chat_groups
    
    # Count unread messages in each group
    for group in groups:
        unread_count = ChatMessage.query.filter(
            ChatMessage.group_id == group.id,
            ChatMessage.sender_id != current_user.id,
            ChatMessage.is_read == False
        ).count()
        group.unread_count = unread_count
    
    # List of available users for new conversations
    users = User.query.filter(User.id != current_user.id).all()
    
    return render_template('chat/index.html', 
                          conversations=conversations.values(),
                          groups=groups,
                          users=users)

@chat.route('/create-group', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new chat group"""
    form = ChatGroupForm()
    # Populate the members field with all active users
    form.members.choices = [(u.id, u.full_name) for u in User.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        group = ChatGroup(
            name=form.name.data,
            description=form.description.data,
            created_by=current_user.id,
            is_private=form.is_private.data,
            region=form.region.data
        )
        # Add creator as a member
        group.members.append(current_user)
        
        # Add selected members
        for member_id in form.members.data:
            member = User.query.get(member_id)
            if member and member != current_user:
                group.members.append(member)
        
        db.session.add(group)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="create_chat_group",
            entity_type="chat_group",
            details=f"Oluşturulan grup: {group.name}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Grup başarıyla oluşturuldu.', 'success')
        return redirect(url_for('chat.view_group', group_id=group.id))
    
    return render_template('chat/create_group.html', form=form)

@chat.route('/group/<int:group_id>')
@login_required
def view_group(group_id):
    """View group chat conversation"""
    group = ChatGroup.query.get_or_404(group_id)
    
    # Check if user is a member of this group
    if current_user not in group.members:
        flash('Bu gruba erişim izniniz yok.', 'danger')
        return redirect(url_for('chat.index'))
    
    # Get messages for this group with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    messages = ChatMessage.query.filter_by(group_id=group_id)\
        .order_by(ChatMessage.sent_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    # Mark unread messages as read
    unread_messages = ChatMessage.query.filter(
        ChatMessage.group_id == group_id,
        ChatMessage.sender_id != current_user.id,
        ChatMessage.is_read == False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    # Create message form
    form = MessageForm()
    
    return render_template('chat/group.html', 
                          group=group,
                          messages=messages,
                          form=form)

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
    
    # Create message form
    form = MessageForm()
    
    return render_template('chat/direct.html', 
                          other_user=other_user,
                          messages=messages,
                          form=form)

@chat.route('/send-message', methods=['POST'])
@login_required
def send_message():
    """Send a message to a group or user"""
    form = MessageForm()
    
    if form.validate_on_submit():
        group_id = request.form.get('group_id')
        receiver_id = request.form.get('receiver_id')
        
        # Create new message
        message = ChatMessage(
            sender_id=current_user.id,
            content=form.content.data,
            sent_at=datetime.utcnow()
        )
        
        # Handle location if provided
        if form.location_lat.data and form.location_lng.data:
            message.location_lat = float(form.location_lat.data)
            message.location_lng = float(form.location_lng.data)
        
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
        if form.attachment.data:
            file = form.attachment.data
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
    
    # If validation fails and it's an AJAX request, return errors
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'error',
            'errors': form.errors
        }), 400
    
    flash('Mesaj gönderilemedi. Lütfen gerekli alanları doldurun.', 'danger')
    return redirect(url_for('chat.index'))

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
        last_update = datetime.utcnow().replace(microsecond=0)
    
    # Get new direct messages
    new_direct_messages = ChatMessage.query.filter(
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.sent_at > last_update,
        ChatMessage.group_id.is_(None)
    ).all()
    
    # Get new group messages
    user_group_ids = [g.id for g in current_user.chat_groups]
    new_group_messages = ChatMessage.query.filter(
        ChatMessage.group_id.in_(user_group_ids),
        ChatMessage.sender_id != current_user.id,
        ChatMessage.sent_at > last_update
    ).all()
    
    # Format messages for JSON response
    direct_messages_data = []
    for msg in new_direct_messages:
        direct_messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.full_name,
            'content': msg.content,
            'has_attachment': msg.has_attachment,
            'has_location': bool(msg.location_lat and msg.location_lng),
            'sent_at': msg.sent_at.isoformat()
        })
    
    group_messages_data = []
    for msg in new_group_messages:
        group_messages_data.append({
            'id': msg.id,
            'group_id': msg.group_id,
            'group_name': msg.group.name,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.full_name,
            'content': msg.content,
            'has_attachment': msg.has_attachment, 
            'has_location': bool(msg.location_lat and msg.location_lng),
            'sent_at': msg.sent_at.isoformat()
        })
    
    response = {
        'timestamp': datetime.utcnow().replace(microsecond=0).isoformat(),
        'direct_messages': direct_messages_data,
        'group_messages': group_messages_data
    }
    
    return jsonify(response)

@chat.route('/manage-groups')
@login_required
def manage_groups():
    """Manage user's groups - view/edit/leave groups"""
    # Get all groups the user is a member of
    user_groups = current_user.chat_groups
    
    # Get groups created by the user
    created_groups = ChatGroup.query.filter_by(created_by=current_user.id).all()
    
    return render_template('chat/manage_groups.html',
                          user_groups=user_groups,
                          created_groups=created_groups)

@chat.route('/edit-group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    """Edit an existing group - only creator or admin"""
    group = ChatGroup.query.get_or_404(group_id)
    
    # Check if user is the creator of this group or an admin
    if group.created_by != current_user.id and current_user.role != 'admin':
        flash('Bu grubu düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('chat.manage_groups'))
    
    form = ChatGroupForm(obj=group)
    form.members.choices = [(u.id, u.full_name) for u in User.query.filter_by(is_active=True).all()]
    
    # Set current members
    if request.method == 'GET':
        form.members.data = [member.id for member in group.members if member.id != current_user.id]
    
    if form.validate_on_submit():
        group.name = form.name.data
        group.description = form.description.data
        group.is_private = form.is_private.data
        group.region = form.region.data
        
        # Update members - keep creator and add selected members
        current_members = set(member.id for member in group.members)
        new_members = set(form.members.data)
        
        # Always keep the creator
        new_members.add(current_user.id)
        
        # Add new members
        for member_id in new_members - current_members:
            member = User.query.get(member_id)
            if member:
                group.members.append(member)
        
        # Remove members
        for member_id in current_members - new_members:
            # Don't remove the creator
            if member_id != current_user.id:
                member = User.query.get(member_id)
                if member:
                    group.members.remove(member)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="edit_chat_group",
            entity_type="chat_group",
            entity_id=group.id,
            details=f"Grup güncellendi: {group.name}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Grup başarıyla güncellendi.', 'success')
        return redirect(url_for('chat.view_group', group_id=group.id))
    
    return render_template('chat/edit_group.html', form=form, group=group)

@chat.route('/leave-group/<int:group_id>', methods=['POST'])
@login_required
def leave_group(group_id):
    """Leave a group"""
    group = ChatGroup.query.get_or_404(group_id)
    
    # Cannot leave if you're the creator
    if group.created_by == current_user.id:
        flash('Grup kurucusu olduğunuz için gruptan ayrılamazsınız. Grubu silmek isterseniz grup ayarlarını kullanın.', 'warning')
        return redirect(url_for('chat.manage_groups'))
    
    if current_user in group.members:
        group.members.remove(current_user)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="leave_chat_group",
            entity_type="chat_group",
            entity_id=group.id,
            details=f"Gruptan ayrılma: {group.name}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash(f'"{group.name}" grubundan ayrıldınız.', 'success')
    else:
        flash('Bu grubun üyesi değilsiniz.', 'warning')
    
    return redirect(url_for('chat.manage_groups'))

@chat.route('/delete-group/<int:group_id>', methods=['POST'])
@login_required
def delete_group(group_id):
    """Delete a group - only creator or admin"""
    group = ChatGroup.query.get_or_404(group_id)
    
    # Check if user is the creator of this group or an admin
    if group.created_by != current_user.id and current_user.role != 'admin':
        flash('Bu grubu silme yetkiniz yok.', 'danger')
        return redirect(url_for('chat.manage_groups'))
    
    group_name = group.name
    
    # Delete all messages in this group first
    ChatMessage.query.filter_by(group_id=group.id).delete()
    
    # Now delete the group itself
    db.session.delete(group)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="delete_chat_group",
        entity_type="chat_group",
        details=f"Grup silindi: {group_name}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    flash(f'"{group_name}" grubu başarıyla silindi.', 'success')
    return redirect(url_for('chat.manage_groups'))

@chat.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Search for messages"""
    form = MessageSearchForm()
    results = []
    
    if form.validate_on_submit() or request.args.get('search_term'):
        # Get search parameters from form or query string
        search_term = form.search_term.data or request.args.get('search_term', '')
        search_type = form.search_type.data or request.args.get('search_type', 'content')
        date_from = form.date_from.data or request.args.get('date_from', '')
        date_to = form.date_to.data or request.args.get('date_to', '')
        
        # Base query - only include messages user has access to
        query = ChatMessage.query
        
        # For content search
        if search_type == 'content' and search_term:
            query = query.filter(ChatMessage.content.ilike(f'%{search_term}%'))
        
        # For sender search
        elif search_type == 'sender' and search_term:
            sender_users = User.query.filter(
                or_(
                    User.username.ilike(f'%{search_term}%'),
                    User.first_name.ilike(f'%{search_term}%'),
                    User.last_name.ilike(f'%{search_term}%')
                )
            ).all()
            sender_ids = [u.id for u in sender_users]
            if sender_ids:
                query = query.filter(ChatMessage.sender_id.in_(sender_ids))
            else:
                # No matching senders, return empty result
                return render_template('chat/search.html', form=form, results=[], search_term=search_term)
        
        # For group search
        elif search_type == 'group' and search_term:
            groups = ChatGroup.query.filter(
                ChatGroup.name.ilike(f'%{search_term}%'),
                ChatGroup.members.any(id=current_user.id)
            ).all()
            group_ids = [g.id for g in groups]
            if group_ids:
                query = query.filter(ChatMessage.group_id.in_(group_ids))
            else:
                # No matching groups, return empty result
                return render_template('chat/search.html', form=form, results=[], search_term=search_term)
        
        # Date filtering
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(ChatMessage.sent_at >= from_date)
            except ValueError:
                flash('Başlangıç tarihi geçerli değil. YYYY-MM-DD formatında olmalıdır.', 'warning')
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                # Add a day to include the end date
                to_date = to_date.replace(hour=23, minute=59, second=59)
                query = query.filter(ChatMessage.sent_at <= to_date)
            except ValueError:
                flash('Bitiş tarihi geçerli değil. YYYY-MM-DD formatında olmalıdır.', 'warning')
        
        # Filter to only include messages the user can see
        # Direct messages to or from the user
        direct_messages = query.filter(
            or_(
                ChatMessage.sender_id == current_user.id,
                ChatMessage.receiver_id == current_user.id
            ),
            ChatMessage.group_id.is_(None)
        )
        
        # Group messages in groups the user is a member of
        user_group_ids = [g.id for g in current_user.chat_groups]
        group_messages = query.filter(
            ChatMessage.group_id.in_(user_group_ids)
        )
        
        # Combine the queries
        results = direct_messages.union(group_messages).order_by(ChatMessage.sent_at.desc()).all()
        
    return render_template('chat/search.html', form=form, results=results)

# Blueprint registration will be done in app.py