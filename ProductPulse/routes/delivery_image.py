from flask import Blueprint, render_template, redirect, url_for, flash, current_app, jsonify, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

from app import db
from models import Delivery, DeliveryAttachment
from forms.delivery import DeliveryImageForm

delivery_image_bp = Blueprint('delivery_image', __name__, url_prefix='/delivery/image')

@delivery_image_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    """İrsaliye resmi yükle"""
    form = DeliveryImageForm()
    
    if form.validate_on_submit():
        # İrsaliye numarası ile var mı kontrol et
        delivery = Delivery.query.filter_by(delivery_number=form.delivery_number.data).first()
        
        # İrsaliye yoksa ve şoför ise yeni irsaliye oluştur
        if not delivery and current_user.role == 'driver':
            delivery = Delivery(
                delivery_number=form.delivery_number.data,
                driver_id=current_user.id,
                issue_date=datetime.utcnow().date(),
                issue_time=datetime.utcnow().time(),
                notes=form.notes.data,
                status='active'
            )
            db.session.add(delivery)
            db.session.commit()
            flash('Yeni irsaliye oluşturuldu.', 'success')
        elif not delivery:
            flash('Bu numarada bir irsaliye bulunamadı.', 'danger')
            return render_template('delivery/upload_image.html', form=form)
        
        # Dosya kaydetme
        if form.image.data:
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'delivery')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Güvenli dosya adı oluştur
            filename = secure_filename(form.image.data.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Dosyayı kaydet
            form.image.data.save(file_path)
            
            # Veritabanına ekle
            file_size = os.path.getsize(file_path)
            file_type = form.image.data.content_type
            
            attachment = DeliveryAttachment(
                delivery_id=delivery.id,
                file_name=filename,
                file_path=os.path.join('uploads', 'delivery', unique_filename),
                file_type=file_type,
                file_size=file_size
            )
            
            db.session.add(attachment)
            db.session.commit()
            
            flash('İrsaliye resmi başarıyla yüklendi.', 'success')
            return redirect(url_for('delivery.view', delivery_id=delivery.id))
    
    return render_template('delivery/upload_image.html', form=form)


@delivery_image_bp.route('/list/<int:delivery_id>')
@login_required
def list_images(delivery_id):
    """İrsaliye resimlerini listele"""
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Admin olmayan kullanıcılar sadece kendilerine ait irsaliyeleri görebilir
    if delivery.driver_id != current_user.id and current_user.role not in ['admin', 'moderator']:
        flash('Bu irsaliyeye erişim izniniz yok.', 'danger')
        return redirect(url_for('delivery.list'))
    
    return render_template('delivery/images.html', delivery=delivery)


@delivery_image_bp.route('/delete/<int:attachment_id>', methods=['POST'])
@login_required
def delete_image(attachment_id):
    """İrsaliye resmini sil"""
    attachment = DeliveryAttachment.query.get_or_404(attachment_id)
    delivery = Delivery.query.get(attachment.delivery_id)
    
    # Yetki kontrolü
    if current_user.role not in ['admin', 'moderator'] and delivery.driver_id != current_user.id:
        flash('Bu dosyayı silme yetkiniz yok.', 'danger')
        return redirect(url_for('delivery_image.list_images', delivery_id=attachment.delivery_id))
    
    try:
        # Dosyayı diskten sil
        file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static'), attachment.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Veritabanından sil
        db.session.delete(attachment)
        db.session.commit()
        
        flash('İrsaliye resmi başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dosya silinemedi: {str(e)}', 'danger')
    
    return redirect(url_for('delivery_image.list_images', delivery_id=attachment.delivery_id))