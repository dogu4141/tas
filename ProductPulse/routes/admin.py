from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db, app
from models import User, ActivityLog, Vehicle, Damage, Delivery, Load
from forms import UserForm
from sqlalchemy import func

# Create blueprint
admin = Blueprint('admin', __name__)

# Admin required decorator
def admin_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Moderator or above required decorator
def moderator_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'moderator']:
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@admin.route('/dashboard')
@login_required
def dashboard():
    # Statistics for the dashboard
    stats = {
        'users_count': User.query.count(),
        'vehicles_count': Vehicle.query.count(),
        'damages_count': Damage.query.count(),
        'open_damages_count': Damage.query.filter(Damage.status != 'repaired').count(),
        'deliveries_count': Delivery.query.count(),
        'active_loads_count': Load.query.filter(Load.status != 'delivered').count()
    }
    
    # Recent activity logs
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', stats=stats, recent_logs=recent_logs)

@admin.route('/users')
@login_required
@admin_required
def users():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    users = query.order_by(User.username).paginate(page=page, per_page=10)
    
    return render_template('admin/users.html', users=users, search=search)

@admin.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = UserForm()
    
    if form.validate_on_submit():
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=form.role.data,
            license_plate=form.license_plate.data,
            is_active=form.is_active.data
        )
        
        db.session.add(user)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="user_create",
            details=f"Kullanıcı oluşturuldu: {user.username}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Kullanıcı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/add_user.html', form=form)

@admin.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Pre-fill the form
    form = UserForm(obj=user)
    form.user_id = user.id  # For validation
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.role = form.role.data
        user.license_plate = form.license_plate.data
        user.is_active = form.is_active.data
        
        # Only update password if provided
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="user_update",
            entity_type="user",
            entity_id=user.id,
            details=f"Kullanıcı güncellendi: {user.username}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Kullanıcı başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin.route('/users/deactivate/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating self
    if user.id == current_user.id:
        flash('Kendi hesabınızı devre dışı bırakamazsınız.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = False
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="user_deactivate",
        entity_type="user",
        entity_id=user.id,
        details=f"Kullanıcı devre dışı bırakıldı: {user.username}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    flash('Kullanıcı devre dışı bırakıldı.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/users/activate/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="user_activate",
        entity_type="user",
        entity_id=user.id,
        details=f"Kullanıcı etkinleştirildi: {user.username}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    flash('Kullanıcı etkinleştirildi.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/activity-logs')
@login_required
@moderator_required
def activity_logs():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    action_filter = request.args.get('action', 'tümü')
    
    query = ActivityLog.query
    
    if search:
        query = query.filter(
            (ActivityLog.details.ilike(f'%{search}%')) |
            (ActivityLog.action.ilike(f'%{search}%')) |
            (ActivityLog.ip_address.ilike(f'%{search}%'))
        )
    
    if action_filter and action_filter != 'tümü':
        query = query.filter(ActivityLog.action == action_filter)
        
    # Get distinct action types for dropdown
    action_types = db.session.query(ActivityLog.action).distinct().all()
    action_types = [action[0] for action in action_types]
    
    logs = query.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/activity_logs.html', logs=logs, search=search, 
                          action_filter=action_filter, action_types=action_types)

# Register blueprint
app.register_blueprint(admin, url_prefix='/admin')
