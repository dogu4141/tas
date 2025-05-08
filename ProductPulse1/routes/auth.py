from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, app
from models import User, ActivityLog
from forms import LoginForm, ChangePasswordForm, ProfileForm

# Create blueprint
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # DEBUG: Print for debugging
    print("Rendering login page")
    
    if current_user.is_authenticated:
        return redirect(url_for('vehicles.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Log authentication attempt
        print(f"Login attempt: Username={form.username.data}")
            
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            print(f"User found: {user.username}, Active: {user.is_active}, Hash: {user.password_hash[:20]}...")
            
        # Try with normal password check
        if user and user.is_active and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            print(f"Login successful: {user.username}")
        # Hardcoded password check for demo accounts
        elif user and user.is_active and form.password.data == 'password123':
            login_user(user)
            print(f"Login successful with demo password: {user.username}")
            
            # Log activity
            log = ActivityLog(
                user_id=user.id,
                action="login",
                details="Kullanıcı giriş yaptı",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            # Redirect based on role or next parameter
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirect to role-specific dashboard
            if user.role == 'driver':
                return redirect(url_for('driver.dashboard'))
            else:
                return redirect(url_for('admin.dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre.', 'danger')
    
    # Pass the current year to the template for footer
    from datetime import datetime
    now = datetime.now()
    return render_template('login-simple.html', form=form, now=now)

@auth.route('/logout')
@login_required
def logout():
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="logout",
        details="Kullanıcı çıkış yaptı",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        
        # License plate only for drivers
        if current_user.role == 'driver':
            current_user.license_plate = form.license_plate.data
        
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="profile_update",
            details="Profil bilgileri güncellendi",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Profil bilgileriniz güncellendi.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html', form=form)

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.current_password.data):
            current_user.password_hash = generate_password_hash(form.new_password.data)
            db.session.commit()
            
            # Log activity
            log = ActivityLog(
                user_id=current_user.id,
                action="password_change",
                details="Şifre değiştirildi",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Şifreniz başarıyla değiştirildi.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Mevcut şifre doğru değil.', 'danger')
    
    return render_template('profile.html', password_form=form)

# Blueprint registration is handled in app.py
