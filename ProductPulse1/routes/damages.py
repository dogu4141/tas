from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db, app
from models import Vehicle, Damage, DamageType, User, ActivityLog, VehicleCatalog # Added VehicleCatalog import
from forms import DamageForm, DamageTypeForm
from datetime import datetime
from sqlalchemy import func
from routes.admin import moderator_required

# Create blueprint
damages = Blueprint('damages', __name__)

@damages.route('/')
@login_required
def index():
    # Get query parameters for filtering
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    severity = request.args.get('severity', '')

    # Base query
    query = Damage.query.join(Vehicle)

    # Apply filters
    if search:
        query = query.filter(
            (Vehicle.chassis_number.ilike(f'%{search}%')) |
            (Vehicle.brand.ilike(f'%{search}%')) |
            (Vehicle.model.ilike(f'%{search}%'))
        )

    if status:
        query = query.filter(Damage.status == status)

    if severity:
        query = query.filter(Damage.severity == severity)

    # Pagination
    page = request.args.get('page', 1, type=int)
    damages_list = query.order_by(Damage.recorded_at.desc()).paginate(page=page, per_page=10)

    return render_template('damages/index.html', damages=damages_list, search=search, status=status, severity=severity)

@damages.route('/types')
@login_required
@moderator_required
def damage_types():
    types = DamageType.query.all()
    return render_template('damages/types.html', types=types)

@damages.route('/types/add', methods=['GET', 'POST'])
@login_required
@moderator_required
def add_damage_type():
    form = DamageTypeForm()

    if form.validate_on_submit():
        damage_type = DamageType(
            name=form.name.data,
            description=form.description.data
        )

        db.session.add(damage_type)

        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="damage_type_create",
            entity_type="damage_type",
            entity_id=damage_type.id,
            details=f"Hasar tipi oluşturuldu: {damage_type.name}",
            ip_address=request.remote_addr
        )
        db.session.add(log)

        db.session.commit()
        flash('Hasar tipi başarıyla eklendi.', 'success')
        return redirect(url_for('damages.damage_types'))

    return render_template('damages/add_damage_type.html', form=form)

@damages.route('/types/edit/<int:type_id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def edit_damage_type(type_id):
    damage_type = DamageType.query.get_or_404(type_id)

    # Pre-fill the form
    form = DamageTypeForm(obj=damage_type)

    if form.validate_on_submit():
        damage_type.name = form.name.data
        damage_type.description = form.description.data

        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="damage_type_update",
            entity_type="damage_type",
            entity_id=damage_type.id,
            details=f"Hasar tipi güncellendi: {damage_type.name}",
            ip_address=request.remote_addr
        )
        db.session.add(log)

        db.session.commit()
        flash('Hasar tipi başarıyla güncellendi.', 'success')
        return redirect(url_for('damages.damage_types'))

    return render_template('damages/edit_damage_type.html', form=form, damage_type=damage_type)

@damages.route('/record', methods=['GET', 'POST'])
@login_required
def record_damage():
    chassis_number = request.args.get('chassis_number', '')
    model = request.args.get('model', '')
    form = DamageForm()
    
    if chassis_number:
        form.chassis_number.data = chassis_number
        vehicle = Vehicle.query.filter_by(chassis_number=chassis_number).first()
        if vehicle:
            form.vehicle_id.data = vehicle.id
            form.model.data = model if model else vehicle.model
            form.model.render_kw = {'readonly': True}

    # Populate damage type dropdown
    damage_types = DamageType.query.all()
    form.damage_type_id.choices = [(dt.id, dt.name) for dt in damage_types]

    # Populate vehicle dropdown if user is moderator or admin
    if current_user.role in ['admin', 'moderator']:
        vehicles = Vehicle.query.all()
        form.vehicle_id.choices = [(v.id, f"{v.chassis_number} - {v.brand} {v.model}") for v in vehicles]

    # Get drivers (users with driver role)
    drivers = User.query.filter_by(role='driver', is_active=True).all()

    if form.validate_on_submit():
        # If chassis number is provided, find the vehicle
        if form.chassis_number.data:
            vehicle = Vehicle.query.filter_by(chassis_number=form.chassis_number.data).first()

            if not vehicle:
                flash('Araç bulunamadı. Lütfen geçerli bir şasi numarası girin.', 'danger')
                return render_template('damages/record_new2.html', form=form, drivers=drivers)

            vehicle_id = vehicle.id
        else:
            vehicle_id = form.vehicle_id.data

        # Create new damage record
        damage = Damage(
            vehicle_id=vehicle_id,
            damage_type_id=form.damage_type_id.data,
            description=form.description.data,
            location_x=form.location_x.data,
            location_y=form.location_y.data,
            group=form.group.data,
            damage_description=form.damage_description.data,
            level=form.level.data,
            severity=form.severity.data,
            status=form.status.data,
            recorded_by=current_user.id
        )

        db.session.add(damage)

        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="damage_record",
            entity_type="damage",
            entity_id=damage.id,
            details=f"Hasar kaydı oluşturuldu. Araç: {form.chassis_number.data}",
            ip_address=request.remote_addr
        )
        db.session.add(log)

        db.session.commit()
        flash('Hasar kaydı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('damages.index'))

    # Get latest damages for the data table (limited to 10)
    damages_list = Damage.query.order_by(Damage.recorded_at.desc()).limit(10).all()

    # Format today's date for the form
    from datetime import date
    today_date = date.today().isoformat()

    # Get all vehicle models
    models = VehicleCatalog.query.order_by(VehicleCatalog.model).all()

    return render_template(
        'damages/record_new3.html', 
        form=form, 
        drivers=drivers, 
        damages=damages_list,
        today_date=today_date,
        models=models,  # Pass models to template
        vehicle_models=models  # Keep this for backwards compatibility
    )

@damages.route('/view/<int:damage_id>')
@login_required
def view_damage(damage_id):
    damage = Damage.query.get_or_404(damage_id)

    return render_template('damages/view.html', damage=damage)

@damages.route('/update-status/<int:damage_id>', methods=['POST'])
@login_required
@moderator_required
def update_status(damage_id):
    damage = Damage.query.get_or_404(damage_id)

    new_status = request.form.get('status')
    if new_status in ['pending', 'in_progress', 'repaired']:
        old_status = damage.status
        damage.status = new_status

        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="damage_status_update",
            entity_type="damage",
            entity_id=damage.id,
            details=f"Hasar durumu güncellendi: {old_status} -> {new_status}",
            ip_address=request.remote_addr
        )
        db.session.add(log)

        db.session.commit()
        flash('Hasar durumu güncellendi.', 'success')
    else:
        flash('Geçersiz durum değeri.', 'danger')

    return redirect(url_for('damages.view_damage', damage_id=damage_id))

@damages.route('/delete/<int:damage_id>', methods=['POST'])
@login_required
@moderator_required
def delete_damage(damage_id):
    damage = Damage.query.get_or_404(damage_id)

    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="damage_delete",
        entity_type="damage",
        entity_id=damage.id,
        details=f"Hasar kaydı silindi. Araç: {damage.vehicle.chassis_number}",
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(damage)
    db.session.commit()

    flash('Hasar kaydı başarıyla silindi.', 'success')
    return redirect(url_for('damages.index'))

@damages.route('/edit/<int:damage_id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def edit_damage(damage_id):
    damage = Damage.query.get_or_404(damage_id)

    # Pre-fill the form
    form = DamageForm(obj=damage)

    # Populate damage type dropdown
    damage_types = DamageType.query.all()
    form.damage_type_id.choices = [(dt.id, dt.name) for dt in damage_types]

    # Populate vehicle dropdown
    vehicles = Vehicle.query.all()
    form.vehicle_id.choices = [(v.id, f"{v.chassis_number} - {v.brand} {v.model}") for v in vehicles]

    if form.validate_on_submit():
        damage.damage_type_id = form.damage_type_id.data
        damage.description = form.description.data
        damage.location_x = form.location_x.data
        damage.location_y = form.location_y.data
        damage.group = form.group.data
        damage.damage_description = form.damage_description.data
        damage.level = form.level.data
        damage.severity = form.severity.data
        damage.status = form.status.data

        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="damage_update",
            entity_type="damage",
            entity_id=damage.id,
            details="Hasar kaydı güncellendi",
            ip_address=request.remote_addr
        )
        db.session.add(log)

        db.session.commit()
        flash('Hasar kaydı başarıyla güncellendi.', 'success')
        return redirect(url_for('damages.view_damage', damage_id=damage.id))

    # Set default values for the form
    form.chassis_number.data = damage.vehicle.chassis_number

    # Get drivers (users with driver role)
    drivers = User.query.filter_by(role='driver', is_active=True).all()

    # Get latest damages for the data table (limited to 10)
    damages_list = Damage.query.order_by(Damage.recorded_at.desc()).limit(10).all()

    # Format today's date for the form
    from datetime import date
    today_date = date.today().isoformat()

    return render_template(
        'damages/record_new3.html', 
        form=form, 
        edit_mode=True, 
        damage=damage,
        drivers=drivers, 
        damages=damages_list,
        today_date=today_date,
        vehicle_models=VehicleCatalog.query.order_by(VehicleCatalog.model).all()
    )