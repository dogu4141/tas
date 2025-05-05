from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db, app
from models import Vehicle, VehicleEntry, VehicleExit, User, ActivityLog
from forms import VehicleForm, VehicleEntryForm, VehicleExitForm
from datetime import datetime
from sqlalchemy import func
from routes.admin import moderator_required

# Create blueprint
vehicles = Blueprint('vehicles', __name__)

@vehicles.route('/')
@login_required
def index():
    # Get query parameters for filtering
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    # Base query
    query = Vehicle.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Vehicle.chassis_number.ilike(f'%{search}%')) |
            (Vehicle.brand.ilike(f'%{search}%')) |
            (Vehicle.model.ilike(f'%{search}%')) |
            (Vehicle.license_plate.ilike(f'%{search}%'))
        )
    
    if status:
        query = query.filter(Vehicle.status == status)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    vehicles_list = query.order_by(Vehicle.updated_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('vehicles/index.html', vehicles=vehicles_list, search=search, status=status)

@vehicles.route('/add', methods=['GET', 'POST'])
@login_required
@moderator_required
def add_vehicle():
    form = VehicleForm()
    
    if form.validate_on_submit():
        vehicle = Vehicle(
            chassis_number=form.chassis_number.data,
            brand=form.brand.data,
            model=form.model.data,
            license_plate=form.license_plate.data,
            year=form.year.data,
            status=form.status.data
        )
        
        db.session.add(vehicle)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="vehicle_create",
            entity_type="vehicle",
            entity_id=vehicle.id,
            details=f"Araç oluşturuldu: {vehicle.chassis_number}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Araç başarıyla eklendi.', 'success')
        return redirect(url_for('vehicles.index'))
    
    return render_template('vehicles/index.html', form=form)

@vehicles.route('/edit/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Pre-fill the form
    form = VehicleForm(obj=vehicle)
    form.vehicle_id = vehicle.id  # For validation
    
    if form.validate_on_submit():
        vehicle.chassis_number = form.chassis_number.data
        vehicle.brand = form.brand.data
        vehicle.model = form.model.data
        vehicle.license_plate = form.license_plate.data
        vehicle.year = form.year.data
        vehicle.status = form.status.data
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="vehicle_update",
            entity_type="vehicle",
            entity_id=vehicle.id,
            details=f"Araç güncellendi: {vehicle.chassis_number}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Araç başarıyla güncellendi.', 'success')
        return redirect(url_for('vehicles.index'))
    
    return render_template('vehicles/index.html', form=form, edit_mode=True, vehicle=vehicle)

@vehicles.route('/entry', methods=['GET', 'POST'])
@login_required
def vehicle_entry():
    form = VehicleEntryForm()
    
    # Populate driver dropdown
    drivers = User.query.filter_by(role='driver', is_active=True).all()
    form.driver_id.choices = [(d.id, f"{d.full_name} ({d.license_plate})") for d in drivers]
    
    if form.validate_on_submit():
        # Check if the vehicle exists
        vehicle = Vehicle.query.filter_by(chassis_number=form.chassis_number.data).first()
        
        if not vehicle:
            flash('Araç bulunamadı. Lütfen geçerli bir şasi numarası girin.', 'danger')
            return render_template('vehicles/entry.html', form=form)
        
        # Create new entry record
        entry = VehicleEntry(
            vehicle_id=vehicle.id,
            driver_id=form.driver_id.data,
            yard=form.yard.data,
            notes=form.notes.data
        )
        
        db.session.add(entry)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="vehicle_entry",
            entity_type="vehicle",
            entity_id=vehicle.id,
            details=f"Araç girişi kaydedildi: {vehicle.chassis_number}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Araç girişi başarıyla kaydedildi.', 'success')
        return redirect(url_for('vehicles.index'))
    
    return render_template('vehicles/entry.html', form=form)

@vehicles.route('/exit', methods=['GET', 'POST'])
@login_required
def vehicle_exit():
    form = VehicleExitForm()
    
    # Populate driver dropdown
    drivers = User.query.filter_by(role='driver', is_active=True).all()
    form.driver_id.choices = [(d.id, f"{d.full_name} ({d.license_plate})") for d in drivers]
    
    if form.validate_on_submit():
        # Check if the vehicle exists
        vehicle = Vehicle.query.filter_by(chassis_number=form.chassis_number.data).first()
        
        if not vehicle:
            flash('Araç bulunamadı. Lütfen geçerli bir şasi numarası girin.', 'danger')
            return render_template('vehicles/exit.html', form=form)
        
        # Create new exit record
        exit_record = VehicleExit(
            vehicle_id=vehicle.id,
            driver_id=form.driver_id.data,
            destination=form.destination.data,
            notes=form.notes.data
        )
        
        db.session.add(exit_record)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="vehicle_exit",
            entity_type="vehicle",
            entity_id=vehicle.id,
            details=f"Araç çıkışı kaydedildi: {vehicle.chassis_number}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Araç çıkışı başarıyla kaydedildi.', 'success')
        return redirect(url_for('vehicles.index'))
    
    return render_template('vehicles/exit.html', form=form)

@vehicles.route('/api/vehicle-info', methods=['GET'])
@login_required
def vehicle_info():
    chassis_number = request.args.get('chassis_number', '')
    
    if not chassis_number:
        return jsonify({'status': 'error', 'message': 'Şasi numarası gerekli'})
    
    vehicle = Vehicle.query.filter_by(chassis_number=chassis_number).first()
    
    if not vehicle:
        return jsonify({'status': 'error', 'message': 'Araç bulunamadı'})
    
    return jsonify({
        'status': 'success',
        'vehicle': {
            'id': vehicle.id,
            'chassis_number': vehicle.chassis_number,
            'brand': vehicle.brand,
            'model': vehicle.model,
            'license_plate': vehicle.license_plate,
            'year': vehicle.year,
            'status': vehicle.status
        }
    })

@vehicles.route('/view/<int:vehicle_id>')
@login_required
def view_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Get entry and exit history
    entries = VehicleEntry.query.filter_by(vehicle_id=vehicle_id).order_by(VehicleEntry.entry_time.desc()).all()
    exits = VehicleExit.query.filter_by(vehicle_id=vehicle_id).order_by(VehicleExit.exit_time.desc()).all()
    
    return render_template('vehicles/view.html', vehicle=vehicle, entries=entries, exits=exits)

# Register blueprint
app.register_blueprint(vehicles, url_prefix='/vehicles')
