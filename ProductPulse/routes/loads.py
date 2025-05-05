from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db, app
from models import Load, LoadItem, Vehicle, User, ActivityLog
from forms import LoadForm, LoadItemForm
from datetime import datetime
from sqlalchemy import func
from routes.admin import moderator_required

# Create blueprint
loads = Blueprint('loads', __name__)

@loads.route('/')
@login_required
def index():
    # Get query parameters for filtering
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    # Base query
    query = Load.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Load.load_number.ilike(f'%{search}%')) |
            (Load.destination.ilike(f'%{search}%'))
        )
    
    if status:
        query = query.filter(Load.status == status)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    loads_list = query.order_by(Load.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('loads/index.html', loads=loads_list, search=search, status=status)

@loads.route('/create', methods=['GET', 'POST'])
@login_required
@moderator_required
def create_load():
    form = LoadForm()
    item_form = LoadItemForm()
    
    # Populate vehicle dropdown
    vehicles = Vehicle.query.filter_by(status='active').all()
    item_form.vehicle_id.choices = [(v.id, f"{v.chassis_number} - {v.brand} {v.model}") for v in vehicles]
    
    # If the main form is submitted
    if form.validate_on_submit() and 'submit' in request.form:
        # Check if load number already exists
        existing_load = Load.query.filter_by(load_number=form.load_number.data).first()
        if existing_load:
            flash('Bu yük numarası zaten kullanılıyor.', 'danger')
            return render_template('loads/create.html', form=form, item_form=item_form, items=[])
        
        # Create new load
        load = Load(
            load_number=form.load_number.data,
            created_by=current_user.id,
            destination=form.destination.data,
            notes=form.notes.data
        )
        
        db.session.add(load)
        db.session.flush()  # Get the load ID
        
        # Check if there are any items in the session
        items = request.args.get('items', '')
        if items:
            items_list = items.split(',')
            for item_data in items_list:
                parts = item_data.split('|')
                if len(parts) >= 2:
                    vehicle_id, position = int(parts[0]), int(parts[1])
                    load_item = LoadItem(
                        load_id=load.id,
                        vehicle_id=vehicle_id,
                        position=position
                    )
                    db.session.add(load_item)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="load_create",
            entity_type="load",
            entity_id=load.id,
            details=f"Yük oluşturuldu: {load.load_number}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Yük başarıyla oluşturuldu.', 'success')
        return redirect(url_for('loads.view_load', load_id=load.id))
    
    # Get items from query string for displaying saved items
    items_param = request.args.get('items', '')
    items = []
    if items_param:
        items_list = items_param.split(',')
        for item in items_list:
            parts = item.split('|')
            if len(parts) >= 2:
                vehicle_id, position = int(parts[0]), int(parts[1])
                vehicle = Vehicle.query.get(vehicle_id)
                if vehicle:
                    items.append({
                        'vehicle_id': vehicle_id,
                        'position': position,
                        'chassis_number': vehicle.chassis_number,
                        'brand': vehicle.brand,
                        'model': vehicle.model
                    })
    
    return render_template('loads/create.html', form=form, item_form=item_form, items=items)

@loads.route('/add-item', methods=['POST'])
@login_required
@moderator_required
def add_load_item():
    item_form = LoadItemForm()
    
    # Populate vehicle dropdown
    vehicles = Vehicle.query.filter_by(status='active').all()
    item_form.vehicle_id.choices = [(v.id, f"{v.chassis_number} - {v.brand} {v.model}") for v in vehicles]
    
    # Get current items
    items_param = request.args.get('items', '')
    items_list = items_param.split(',') if items_param else []
    
    if item_form.validate_on_submit():
        vehicle_id = item_form.vehicle_id.data
        position = item_form.position.data
        
        # Check if position is already taken
        for item in items_list:
            parts = item.split('|')
            if len(parts) >= 2 and int(parts[1]) == position:
                flash(f'Pozisyon {position} zaten dolu.', 'danger')
                return redirect(url_for('loads.create_load', items=items_param))
        
        # Check if vehicle is already in the load
        for item in items_list:
            parts = item.split('|')
            if len(parts) >= 2 and int(parts[0]) == vehicle_id:
                flash('Bu araç zaten yüke eklenmiş.', 'danger')
                return redirect(url_for('loads.create_load', items=items_param))
        
        # Check if we've reached the maximum of 8 vehicles
        if len(items_list) >= 8:
            flash('Bir yüke en fazla 8 araç eklenebilir.', 'danger')
            return redirect(url_for('loads.create_load', items=items_param))
        
        # Add the new item to the list
        new_item = f"{vehicle_id}|{position}"
        if new_item and new_item not in items_list:
            items_list.append(new_item)
        
        # Rebuild items parameter
        new_items_param = ','.join(items_list)
        
        flash('Araç yüke eklendi.', 'success')
        return redirect(url_for('loads.create_load', items=new_items_param))
    
    # If validation fails, show errors
    for field, errors in item_form.errors.items():
        for error in errors:
            flash(f"{getattr(item_form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('loads.create_load', items=items_param))

@loads.route('/remove-item', methods=['POST'])
@login_required
@moderator_required
def remove_load_item():
    vehicle_id = request.form.get('vehicle_id')
    
    # Get current items
    items_param = request.args.get('items', '')
    items_list = items_param.split(',') if items_param else []
    
    # Remove the item from the list
    updated_items = []
    for item in items_list:
        parts = item.split('|')
        if len(parts) >= 2 and parts[0] != vehicle_id:
            updated_items.append(item)
    
    # Rebuild items parameter
    new_items_param = ','.join(updated_items)
    
    flash('Araç yükten çıkarıldı.', 'success')
    return redirect(url_for('loads.create_load', items=new_items_param))

@loads.route('/view/<int:load_id>')
@login_required
def view_load(load_id):
    load = Load.query.get_or_404(load_id)
    
    return render_template('loads/view.html', load=load)

@loads.route('/edit/<int:load_id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def edit_load(load_id):
    load = Load.query.get_or_404(load_id)
    
    # Pre-fill the form
    form = LoadForm(obj=load)
    item_form = LoadItemForm()
    
    # Populate vehicle dropdown
    vehicles = Vehicle.query.filter_by(status='active').all()
    item_form.vehicle_id.choices = [(v.id, f"{v.chassis_number} - {v.brand} {v.model}") for v in vehicles]
    
    if form.validate_on_submit() and 'submit' in request.form:
        load.load_number = form.load_number.data
        load.destination = form.destination.data
        load.notes = form.notes.data
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="load_update",
            entity_type="load",
            entity_id=load.id,
            details=f"Yük güncellendi: {load.load_number}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Yük başarıyla güncellendi.', 'success')
        return redirect(url_for('loads.view_load', load_id=load.id))
    
    return render_template('loads/edit.html', form=form, item_form=item_form, load=load)

@loads.route('/add-item/<int:load_id>', methods=['POST'])
@login_required
@moderator_required
def add_item_to_load(load_id):
    load = Load.query.get_or_404(load_id)
    item_form = LoadItemForm()
    
    # Populate vehicle dropdown
    vehicles = Vehicle.query.filter_by(status='active').all()
    item_form.vehicle_id.choices = [(v.id, f"{v.chassis_number} - {v.brand} {v.model}") for v in vehicles]
    
    if item_form.validate_on_submit():
        vehicle_id = item_form.vehicle_id.data
        position = item_form.position.data
        
        # Check if position is already taken
        existing_position = LoadItem.query.filter_by(load_id=load.id, position=position).first()
        if existing_position:
            flash(f'Pozisyon {position} zaten dolu.', 'danger')
            return redirect(url_for('loads.edit_load', load_id=load.id))
        
        # Check if vehicle is already in the load
        existing_vehicle = LoadItem.query.filter_by(load_id=load.id, vehicle_id=vehicle_id).first()
        if existing_vehicle:
            flash('Bu araç zaten yüke eklenmiş.', 'danger')
            return redirect(url_for('loads.edit_load', load_id=load.id))
        
        # Check if we've reached the maximum of 8 vehicles
        items_count = LoadItem.query.filter_by(load_id=load.id).count()
        if items_count >= 8:
            flash('Bir yüke en fazla 8 araç eklenebilir.', 'danger')
            return redirect(url_for('loads.edit_load', load_id=load.id))
        
        # Add the new item
        load_item = LoadItem(
            load_id=load.id,
            vehicle_id=vehicle_id,
            position=position
        )
        db.session.add(load_item)
        
        # Log activity
        vehicle = Vehicle.query.get(vehicle_id)
        log = ActivityLog(
            user_id=current_user.id,
            action="load_item_add",
            entity_type="load",
            entity_id=load.id,
            details=f"Yüke araç eklendi: {vehicle.chassis_number if vehicle else 'Bilinmeyen araç'}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Araç yüke eklendi.', 'success')
    
    return redirect(url_for('loads.edit_load', load_id=load.id))

@loads.route('/remove-item/<int:load_id>/<int:item_id>', methods=['POST'])
@login_required
@moderator_required
def remove_item_from_load(load_id, item_id):
    load = Load.query.get_or_404(load_id)
    item = LoadItem.query.get_or_404(item_id)
    
    # Ensure the item belongs to the load
    if item.load_id != load.id:
        abort(400)
    
    vehicle = Vehicle.query.get(item.vehicle_id)
    db.session.delete(item)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="load_item_remove",
        entity_type="load",
        entity_id=load.id,
        details=f"Yükten araç çıkarıldı: {vehicle.chassis_number if vehicle else 'Bilinmeyen araç'}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    flash('Araç yükten çıkarıldı.', 'success')
    
    return redirect(url_for('loads.edit_load', load_id=load.id))

@loads.route('/update-status/<int:load_id>', methods=['POST'])
@login_required
@moderator_required
def update_load_status(load_id):
    load = Load.query.get_or_404(load_id)
    
    new_status = request.form.get('status')
    if new_status in ['pending', 'in_transit', 'delivered']:
        old_status = load.status
        load.status = new_status
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="load_status_update",
            entity_type="load",
            entity_id=load.id,
            details=f"Yük durumu güncellendi: {old_status} -> {new_status}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Yük durumu güncellendi.', 'success')
    else:
        flash('Geçersiz durum değeri.', 'danger')
    
    return redirect(url_for('loads.view_load', load_id=load.id))

@loads.route('/delete/<int:load_id>', methods=['POST'])
@login_required
@moderator_required
def delete_load(load_id):
    load = Load.query.get_or_404(load_id)
    
    # Log activity before deletion
    log = ActivityLog(
        user_id=current_user.id,
        action="load_delete",
        entity_type="load",
        details=f"Yük silindi: {load.load_number}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.delete(load)
    db.session.commit()
    
    flash('Yük başarıyla silindi.', 'success')
    return redirect(url_for('loads.index'))

# Register blueprint
app.register_blueprint(loads, url_prefix='/loads')
