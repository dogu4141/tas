from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, csrf
from models import User, Delivery, Load, LoadItem, Vehicle
from datetime import datetime

driver = Blueprint('driver', __name__)

@driver.route('/dashboard')
@login_required
def dashboard():
    """Driver dashboard showing work status, unread deliveries and assigned loads"""
    if current_user.role != 'driver':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Get unread deliveries for the driver
    unread_deliveries = Delivery.query.filter_by(
        driver_id=current_user.id,
        is_read=False
    ).order_by(Delivery.created_at.desc()).all()
    
    # Get assigned loads for the driver
    # A load is assigned to a driver if the driver is current_user and load is in pending or in_transit status
    assigned_loads = Load.query.join(LoadItem, Load.id == LoadItem.load_id)\
        .join(Vehicle, LoadItem.vehicle_id == Vehicle.id)\
        .join(Delivery, Vehicle.chassis_number == Delivery.chassis_number)\
        .filter(Delivery.driver_id == current_user.id)\
        .filter(Load.status.in_(['pending', 'in_transit']))\
        .distinct()\
        .all()
    
    return render_template(
        'driver/dashboard.html',
        unread_deliveries=unread_deliveries,
        assigned_loads=assigned_loads
    )

@driver.route('/update-work-status', methods=['POST'])
@login_required
def update_work_status():
    """Update driver's work status (active, inactive, break) and location"""
    if current_user.role != 'driver':
        flash('Bu işlemi yapma yetkiniz yok.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Get form data
    status = request.form.get('status')
    current_location = request.form.get('current_location')
    
    # Validate status
    if status not in ['active', 'inactive', 'break']:
        flash('Geçersiz çalışma durumu!', 'danger')
        return redirect(url_for('driver.dashboard'))
    
    # Update user
    current_user.work_status = status
    current_user.current_location = current_location
    current_user.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Success message based on status
    if status == 'active':
        flash('Çalışma durumunuz "Aktif" olarak güncellendi.', 'success')
    elif status == 'inactive':
        flash('Çalışma durumunuz "Pasif" olarak güncellendi.', 'success')
    else:
        flash('Çalışma durumunuz "Molada" olarak güncellendi.', 'success')
    
    return redirect(url_for('driver.dashboard'))

@driver.route('/delivery/<int:delivery_id>')
@login_required
def delivery_detail(delivery_id):
    """View delivery details and mark as read"""
    if current_user.role != 'driver':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Make sure the delivery belongs to this driver
    if delivery.driver_id != current_user.id:
        flash('Bu irsaliyeye erişim izniniz yok.', 'danger')
        return redirect(url_for('driver.dashboard'))
    
    # Mark delivery as read
    if not delivery.is_read:
        delivery.is_read = True
        db.session.commit()
    
    return render_template(
        'driver/delivery_detail.html',
        delivery=delivery
    )

@driver.route('/load/<int:load_id>')
@login_required
def load_detail(load_id):
    """View load details"""
    if current_user.role != 'driver':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    load = Load.query.get_or_404(load_id)
    
    # Check if driver has access to this load
    has_access = False
    for item in load.load_items:
        delivery = Delivery.query.filter_by(
            chassis_number=item.vehicle.chassis_number, 
            driver_id=current_user.id
        ).first()
        if delivery:
            has_access = True
            break
    
    if not has_access:
        flash('Bu yüke erişim izniniz yok.', 'danger')
        return redirect(url_for('driver.dashboard'))
    
    return render_template(
        'driver/load_detail.html',
        load=load
    )