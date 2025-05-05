from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db, app
from models import Delivery, DeliveryItem, User, Vehicle, ActivityLog
from forms import DeliveryForm, DeliveryItemForm
from datetime import datetime, date, time
from sqlalchemy import func
from routes.admin import moderator_required

# Create blueprint
deliveries = Blueprint('deliveries', __name__)

@deliveries.route('/')
@login_required
def index():
    # Get query parameters for filtering
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Base query
    query = Delivery.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Delivery.delivery_number.ilike(f'%{search}%')) |
            (Delivery.loading_yard.ilike(f'%{search}%'))
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Delivery.issue_date >= date_from_obj)
        except ValueError:
            flash('Geçersiz başlangıç tarihi formatı.', 'danger')
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Delivery.issue_date <= date_to_obj)
        except ValueError:
            flash('Geçersiz bitiş tarihi formatı.', 'danger')
    
    # Filter by driver if user is a driver
    if current_user.role == 'driver':
        query = query.filter(Delivery.driver_id == current_user.id)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    deliveries_list = query.order_by(Delivery.issue_date.desc(), Delivery.issue_time.desc()).paginate(page=page, per_page=10)
    
    return render_template('deliveries/index.html', deliveries=deliveries_list, search=search, date_from=date_from, date_to=date_to)

@deliveries.route('/create', methods=['GET', 'POST'])
@login_required
def create_delivery():
    form = DeliveryForm()
    item_form = DeliveryItemForm()
    
    # Set default date and time
    if not form.issue_date.data:
        form.issue_date.data = date.today()
    if not form.issue_time.data:
        form.issue_time.data = datetime.now().time()
    
    # Populate driver dropdown
    drivers = User.query.filter_by(role='driver', is_active=True).all()
    form.driver_id.choices = [(d.id, f"{d.full_name} ({d.license_plate})") for d in drivers]
    
    # Automatically set driver to current user if they're a driver
    if current_user.role == 'driver' and request.method == 'GET':
        form.driver_id.data = current_user.id
    
    # If the main form is submitted
    if form.validate_on_submit() and 'submit' in request.form:
        # Check if delivery number already exists
        existing_delivery = Delivery.query.filter_by(delivery_number=form.delivery_number.data).first()
        if existing_delivery:
            flash('Bu irsaliye numarası zaten kullanılıyor.', 'danger')
            return render_template('deliveries/create.html', form=form, item_form=item_form, items=[])
        
        # Create new delivery
        delivery = Delivery(
            delivery_number=form.delivery_number.data,
            driver_id=form.driver_id.data,
            issue_date=form.issue_date.data,
            issue_time=form.issue_time.data,
            loading_yard=form.loading_yard.data,
            notes=form.notes.data
        )
        
        db.session.add(delivery)
        db.session.flush()  # Get the delivery ID
        
        # Check if there are any items in the session
        items = request.args.get('items', '')
        if items:
            items_list = items.split(',')
            for item_data in items_list:
                parts = item_data.split('|')
                if len(parts) >= 3:
                    chassis_number, brand, model = parts[0], parts[1], parts[2]
                    delivery_item = DeliveryItem(
                        delivery_id=delivery.id,
                        chassis_number=chassis_number,
                        brand=brand,
                        model=model
                    )
                    db.session.add(delivery_item)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="delivery_create",
            entity_type="delivery",
            entity_id=delivery.id,
            details=f"İrsaliye oluşturuldu: {delivery.delivery_number}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('İrsaliye başarıyla oluşturuldu.', 'success')
        return redirect(url_for('deliveries.view_delivery', delivery_id=delivery.id))
    
    # Get items from query string for displaying saved items
    items_param = request.args.get('items', '')
    items = []
    if items_param:
        items_list = items_param.split(',')
        for item in items_list:
            parts = item.split('|')
            if len(parts) >= 3:
                items.append({'chassis_number': parts[0], 'brand': parts[1], 'model': parts[2]})
    
    return render_template('deliveries/create.html', form=form, item_form=item_form, items=items)

@deliveries.route('/add-item', methods=['POST'])
@login_required
def add_delivery_item():
    item_form = DeliveryItemForm()
    
    # Get current items
    items_param = request.args.get('items', '')
    items_list = items_param.split(',') if items_param else []
    
    if item_form.validate_on_submit():
        chassis_number = item_form.chassis_number.data
        brand = item_form.brand.data or 'Bilinmiyor'
        model = item_form.model.data or 'Bilinmiyor'
        
        # Check if vehicle exists in the database
        vehicle = Vehicle.query.filter_by(chassis_number=chassis_number).first()
        if vehicle:
            brand = vehicle.brand
            model = vehicle.model
        
        # Add the new item to the list
        new_item = f"{chassis_number}|{brand}|{model}"
        if new_item not in items_list and new_item:
            items_list.append(new_item)
        
        # Rebuild items parameter
        new_items_param = ','.join(items_list)
        
        flash('Araç irsaliyeye eklendi.', 'success')
        return redirect(url_for('deliveries.create_delivery', items=new_items_param))
    
    # If validation fails, show errors
    for field, errors in item_form.errors.items():
        for error in errors:
            flash(f"{getattr(item_form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('deliveries.create_delivery', items=items_param))

@deliveries.route('/remove-item', methods=['POST'])
@login_required
def remove_delivery_item():
    chassis_number = request.form.get('chassis_number')
    
    # Get current items
    items_param = request.args.get('items', '')
    items_list = items_param.split(',') if items_param else []
    
    # Remove the item from the list
    updated_items = []
    for item in items_list:
        parts = item.split('|')
        if parts[0] != chassis_number:
            updated_items.append(item)
    
    # Rebuild items parameter
    new_items_param = ','.join(updated_items)
    
    flash('Araç irsaliyeden çıkarıldı.', 'success')
    return redirect(url_for('deliveries.create_delivery', items=new_items_param))

@deliveries.route('/view/<int:delivery_id>')
@login_required
def view_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Check if user has access to this delivery
    if current_user.role == 'driver' and delivery.driver_id != current_user.id:
        abort(403)
    
    return render_template('deliveries/view.html', delivery=delivery)

@deliveries.route('/edit/<int:delivery_id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def edit_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Pre-fill the form
    form = DeliveryForm(obj=delivery)
    item_form = DeliveryItemForm()
    
    # Populate driver dropdown
    drivers = User.query.filter_by(role='driver', is_active=True).all()
    form.driver_id.choices = [(d.id, f"{d.full_name} ({d.license_plate})") for d in drivers]
    
    if form.validate_on_submit() and 'submit' in request.form:
        delivery.delivery_number = form.delivery_number.data
        delivery.driver_id = form.driver_id.data
        delivery.issue_date = form.issue_date.data
        delivery.issue_time = form.issue_time.data
        delivery.loading_yard = form.loading_yard.data
        delivery.notes = form.notes.data
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="delivery_update",
            entity_type="delivery",
            entity_id=delivery.id,
            details=f"İrsaliye güncellendi: {delivery.delivery_number}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('İrsaliye başarıyla güncellendi.', 'success')
        return redirect(url_for('deliveries.view_delivery', delivery_id=delivery.id))
    
    return render_template('deliveries/edit.html', form=form, item_form=item_form, delivery=delivery)

@deliveries.route('/add-item/<int:delivery_id>', methods=['POST'])
@login_required
@moderator_required
def add_item_to_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    item_form = DeliveryItemForm()
    
    if item_form.validate_on_submit():
        chassis_number = item_form.chassis_number.data
        brand = item_form.brand.data or 'Bilinmiyor'
        model = item_form.model.data or 'Bilinmiyor'
        
        # Check if vehicle exists in the database
        vehicle = Vehicle.query.filter_by(chassis_number=chassis_number).first()
        if vehicle:
            brand = vehicle.brand
            model = vehicle.model
        
        # Check if item already exists
        existing_item = DeliveryItem.query.filter_by(delivery_id=delivery.id, chassis_number=chassis_number).first()
        if existing_item:
            flash('Bu şasi numarası zaten irsaliyeye eklenmiş.', 'danger')
            return redirect(url_for('deliveries.edit_delivery', delivery_id=delivery.id))
        
        # Add the new item
        delivery_item = DeliveryItem(
            delivery_id=delivery.id,
            chassis_number=chassis_number,
            brand=brand,
            model=model
        )
        db.session.add(delivery_item)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="delivery_item_add",
            entity_type="delivery",
            entity_id=delivery.id,
            details=f"İrsaliyeye araç eklendi: {chassis_number}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        flash('Araç irsaliyeye eklendi.', 'success')
    
    return redirect(url_for('deliveries.edit_delivery', delivery_id=delivery.id))

@deliveries.route('/remove-item/<int:delivery_id>/<int:item_id>', methods=['POST'])
@login_required
@moderator_required
def remove_item_from_delivery(delivery_id, item_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    item = DeliveryItem.query.get_or_404(item_id)
    
    # Ensure the item belongs to the delivery
    if item.delivery_id != delivery.id:
        abort(400)
    
    chassis_number = item.chassis_number
    db.session.delete(item)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="delivery_item_remove",
        entity_type="delivery",
        entity_id=delivery.id,
        details=f"İrsaliyeden araç çıkarıldı: {chassis_number}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    flash('Araç irsaliyeden çıkarıldı.', 'success')
    
    return redirect(url_for('deliveries.edit_delivery', delivery_id=delivery.id))

@deliveries.route('/delete/<int:delivery_id>', methods=['POST'])
@login_required
@moderator_required
def delete_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Log activity before deletion
    log = ActivityLog(
        user_id=current_user.id,
        action="delivery_delete",
        entity_type="delivery",
        details=f"İrsaliye silindi: {delivery.delivery_number}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.delete(delivery)
    db.session.commit()
    
    flash('İrsaliye başarıyla silindi.', 'success')
    return redirect(url_for('deliveries.index'))

@deliveries.route('/print/<int:delivery_id>')
@login_required
def print_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Check if user has access to this delivery
    if current_user.role == 'driver' and delivery.driver_id != current_user.id:
        abort(403)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="delivery_print",
        entity_type="delivery",
        entity_id=delivery.id,
        details=f"İrsaliye yazdırıldı: {delivery.delivery_number}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return render_template('deliveries/print.html', delivery=delivery, now=datetime.now())

# Register blueprint
app.register_blueprint(deliveries, url_prefix='/deliveries')
