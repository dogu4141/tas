from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

from app import db
from models import User, Shift, LeaveRequest, EmployeeReport, ReportAttachment
from forms.employee import (
    EmployeeForm, ShiftForm, LeaveRequestForm, 
    EmployeeReportForm, LeaveRequestApprovalForm
)

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

# Admin tarafından çalışan yönetimi

@employee_bp.route('/list')
@login_required
def list_employees():
    """Çalışanları listele"""
    if current_user.role not in ['admin', 'moderator']:
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('root.index'))
    
    employees = User.query.filter(User.role != 'admin').all()
    return render_template('employee/list.html', employees=employees)


@employee_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    """Yeni çalışan ekle"""
    if current_user.role != 'admin':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('root.index'))
    
    form = EmployeeForm()
    if form.validate_on_submit():
        # Kullanıcı adı ve email kontrolü
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Bu kullanıcı adı veya e-posta zaten kullanılıyor.', 'danger')
            return render_template('employee/add.html', form=form)
        
        # Yeni çalışan oluştur
        new_employee = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=form.role.data,
            employee_id=form.employee_id.data,
            department=form.department.data,
            position=form.position.data,
            hire_date=form.hire_date.data,
            license_plate=form.license_plate.data,
            is_active=form.is_active.data
        )
        
        db.session.add(new_employee)
        db.session.commit()
        
        flash(f'{new_employee.full_name} adlı çalışan başarıyla eklendi.', 'success')
        return redirect(url_for('employee.list_employees'))
    
    return render_template('employee/add.html', form=form)


@employee_bp.route('/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    """Çalışan bilgilerini düzenle"""
    if current_user.role != 'admin':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('root.index'))
    
    employee = User.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)
    
    # Admin rolü düzenlenemez
    if employee.role == 'admin':
        form.role.choices = [('admin', 'Yönetici')]
    
    if form.validate_on_submit():
        # Kullanıcı adı ve email kontrolü (kendisi hariç)
        existing_user = User.query.filter(
            ((User.username == form.username.data) | 
            (User.email == form.email.data)) &
            (User.id != employee_id)
        ).first()
        
        if existing_user:
            flash('Bu kullanıcı adı veya e-posta zaten kullanılıyor.', 'danger')
            return render_template('employee/edit.html', form=form, employee=employee)
        
        # Çalışan bilgilerini güncelle
        employee.username = form.username.data
        employee.email = form.email.data
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.phone = form.phone.data
        employee.role = form.role.data
        employee.employee_id = form.employee_id.data
        employee.department = form.department.data
        employee.position = form.position.data
        employee.hire_date = form.hire_date.data
        employee.license_plate = form.license_plate.data
        employee.is_active = form.is_active.data
        
        # Şifre sadece girilmişse değiştirilir
        if form.password.data:
            employee.password_hash = generate_password_hash(form.password.data)
        
        db.session.commit()
        
        flash(f'{employee.full_name} adlı çalışanın bilgileri güncellendi.', 'success')
        return redirect(url_for('employee.list_employees'))
    
    # Şifre alanı gösterilmez
    form.password.data = ''
    return render_template('employee/edit.html', form=form, employee=employee)


@employee_bp.route('/delete/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    """Çalışanı sil"""
    if current_user.role != 'admin':
        flash('Bu işlemi gerçekleştirme yetkiniz yok.', 'danger')
        return redirect(url_for('employee.list_employees'))
    
    employee = User.query.get_or_404(employee_id)
    
    # Admin silinmez
    if employee.role == 'admin':
        flash('Admin kullanıcılar silinemez.', 'danger')
        return redirect(url_for('employee.list_employees'))
    
    # Kendini silme
    if employee.id == current_user.id:
        flash('Kendinizi silemezsiniz.', 'danger')
        return redirect(url_for('employee.list_employees'))
    
    try:
        # İlişkili kayıtları kontrol et
        db.session.delete(employee)
        db.session.commit()
        flash(f'{employee.full_name} adlı çalışan başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Çalışan silinemedi: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_employees'))


# Vardiya yönetimi

@employee_bp.route('/shifts')
@login_required
def list_shifts():
    """Vardiyaları listele"""
    if current_user.role != 'admin':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('root.index'))
    
    shifts = Shift.query.all()
    return render_template('employee/shifts.html', shifts=shifts)


@employee_bp.route('/shift/add', methods=['GET', 'POST'])
@login_required
def add_shift():
    """Yeni vardiya ekle"""
    if current_user.role != 'admin':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('root.index'))
    
    form = ShiftForm()
    
    # Çalışan listesini form için hazırla
    employees = User.query.filter(User.role.in_(['driver', 'employee'])).all()
    form.employee_id.choices = [(e.id, f"{e.full_name} ({e.role})") for e in employees]
    
    if form.validate_on_submit():
        # Yeni vardiya oluştur
        new_shift = Shift(
            employee_id=form.employee_id.data,
            day_of_week=form.day_of_week.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            is_active=form.is_active.data,
            created_by=current_user.id
        )
        
        db.session.add(new_shift)
        db.session.commit()
        
        flash('Vardiya başarıyla eklendi.', 'success')
        return redirect(url_for('employee.list_shifts'))
    
    return render_template('employee/add_shift.html', form=form)


@employee_bp.route('/shift/edit/<int:shift_id>', methods=['GET', 'POST'])
@login_required
def edit_shift(shift_id):
    """Vardiya düzenle"""
    if current_user.role != 'admin':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('root.index'))
    
    shift = Shift.query.get_or_404(shift_id)
    form = ShiftForm(obj=shift)
    
    # Çalışan listesini form için hazırla
    employees = User.query.filter(User.role.in_(['driver', 'employee'])).all()
    form.employee_id.choices = [(e.id, f"{e.full_name} ({e.role})") for e in employees]
    
    if form.validate_on_submit():
        # Vardiya bilgilerini güncelle
        shift.employee_id = form.employee_id.data
        shift.day_of_week = form.day_of_week.data
        shift.start_time = form.start_time.data
        shift.end_time = form.end_time.data
        shift.is_active = form.is_active.data
        
        db.session.commit()
        
        flash('Vardiya bilgileri güncellendi.', 'success')
        return redirect(url_for('employee.list_shifts'))
    
    return render_template('employee/edit_shift.html', form=form, shift=shift)


@employee_bp.route('/shift/delete/<int:shift_id>', methods=['POST'])
@login_required
def delete_shift(shift_id):
    """Vardiya sil"""
    if current_user.role != 'admin':
        flash('Bu işlemi gerçekleştirme yetkiniz yok.', 'danger')
        return redirect(url_for('employee.list_shifts'))
    
    shift = Shift.query.get_or_404(shift_id)
    
    try:
        db.session.delete(shift)
        db.session.commit()
        flash('Vardiya başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Vardiya silinemedi: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_shifts'))


# İzin talepleri

@employee_bp.route('/leaves')
@login_required
def list_leaves():
    """İzin taleplerini listele"""
    if current_user.role == 'admin':
        # Adminler tüm izin taleplerini görür
        leaves = LeaveRequest.query.all()
    else:
        # Diğer kullanıcılar sadece kendi izin taleplerini görür
        leaves = LeaveRequest.query.filter_by(employee_id=current_user.id).all()
    
    return render_template('employee/leaves.html', leaves=leaves)


@employee_bp.route('/leave/add', methods=['GET', 'POST'])
@login_required
def add_leave():
    """Yeni izin talebi oluştur"""
    form = LeaveRequestForm()
    
    # Admin ise tüm çalışanlar için izin talebi oluşturabilir
    if current_user.role == 'admin':
        employees = User.query.all()
        form.employee_id.choices = [(e.id, e.full_name) for e in employees]
    else:
        # Admin değilse sadece kendisi için izin talebi oluşturabilir
        form.employee_id.data = current_user.id
        form.employee_id.render_kw = {'readonly': True}
    
    if form.validate_on_submit():
        # Yeni izin talebi oluştur
        new_leave = LeaveRequest(
            employee_id=form.employee_id.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            leave_type=form.leave_type.data,
            reason=form.reason.data,
            status='approved' if current_user.role == 'admin' else 'pending'
        )
        
        # Admin eklediyse otomatik onaylanır ve admin bilgileri eklenir
        if current_user.role == 'admin':
            new_leave.approved_by = current_user.id
            new_leave.approved_at = datetime.utcnow()
        
        db.session.add(new_leave)
        db.session.commit()
        
        flash('İzin talebi başarıyla oluşturuldu.', 'success')
        return redirect(url_for('employee.list_leaves'))
    
    return render_template('employee/add_leave.html', form=form)


@employee_bp.route('/leave/approve/<int:leave_id>', methods=['GET', 'POST'])
@login_required
def approve_leave(leave_id):
    """İzin talebini onayla/reddet"""
    if current_user.role != 'admin':
        flash('Bu işlemi gerçekleştirme yetkiniz yok.', 'danger')
        return redirect(url_for('employee.list_leaves'))
    
    leave = LeaveRequest.query.get_or_404(leave_id)
    form = LeaveRequestApprovalForm(obj=leave)
    
    if form.validate_on_submit():
        leave.status = form.status.data
        
        # Onay/red bilgilerini kaydet
        if form.status.data != 'pending':
            leave.approved_by = current_user.id
            leave.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        status_text = {
            'approved': 'onaylandı',
            'rejected': 'reddedildi',
            'pending': 'beklemede olarak güncellendi'
        }
        
        flash(f'İzin talebi {status_text[form.status.data]}.', 'success')
        return redirect(url_for('employee.list_leaves'))
    
    return render_template('employee/approve_leave.html', form=form, leave=leave)


# Çalışan raporları

@employee_bp.route('/reports')
@login_required
def list_reports():
    """Raporları listele"""
    if current_user.role == 'admin':
        # Adminler tüm raporları görür
        reports = EmployeeReport.query.all()
    else:
        # Diğer kullanıcılar sadece kendi raporlarını görür
        reports = EmployeeReport.query.filter_by(employee_id=current_user.id).all()
    
    return render_template('employee/reports.html', reports=reports)


@employee_bp.route('/report/add', methods=['GET', 'POST'])
@login_required
def add_report():
    """Yeni rapor ekle"""
    form = EmployeeReportForm()
    
    if form.validate_on_submit():
        # Yeni rapor oluştur
        new_report = EmployeeReport(
            employee_id=current_user.id,
            report_date=datetime.utcnow().date(),
            report_type=form.report_type.data,
            title=form.title.data,
            content=form.content.data,
            status='submitted'
        )
        
        # Önce raporu kaydet (ID almak için)
        db.session.add(new_report)
        db.session.commit()
        
        # Dosya eklerini kaydet
        if form.attachments.data:
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'reports')
            os.makedirs(upload_dir, exist_ok=True)
            
            for attachment in form.attachments.data:
                if attachment.filename:
                    # Güvenli dosya adı oluştur
                    filename = secure_filename(attachment.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(upload_dir, unique_filename)
                    
                    # Dosyayı kaydet
                    attachment.save(file_path)
                    
                    # Veritabanına ekle
                    file_size = os.path.getsize(file_path)
                    file_type = attachment.content_type
                    
                    new_attachment = ReportAttachment(
                        report_id=new_report.id,
                        file_name=filename,
                        file_path=os.path.join('uploads', 'reports', unique_filename),
                        file_type=file_type,
                        file_size=file_size
                    )
                    
                    db.session.add(new_attachment)
            
            # Ekleri kaydet
            db.session.commit()
        
        flash('Rapor başarıyla oluşturuldu.', 'success')
        return redirect(url_for('employee.list_reports'))
    
    return render_template('employee/add_report.html', form=form)


@employee_bp.route('/report/view/<int:report_id>')
@login_required
def view_report(report_id):
    """Rapor detaylarını görüntüle"""
    report = EmployeeReport.query.get_or_404(report_id)
    
    # Yetki kontrolü
    if report.employee_id != current_user.id and current_user.role != 'admin':
        flash('Bu rapora erişim izniniz yok.', 'danger')
        return redirect(url_for('employee.list_reports'))
    
    return render_template('employee/view_report.html', report=report)


@employee_bp.route('/report/review/<int:report_id>', methods=['POST'])
@login_required
def review_report(report_id):
    """Raporu incele (admin)"""
    if current_user.role != 'admin':
        flash('Bu işlemi gerçekleştirme yetkiniz yok.', 'danger')
        return redirect(url_for('employee.list_reports'))
    
    report = EmployeeReport.query.get_or_404(report_id)
    status = request.form.get('status')
    
    if status in ['reviewed', 'approved']:
        report.status = status
        report.reviewed_by = current_user.id
        report.reviewed_at = datetime.utcnow()
        
        db.session.commit()
        
        status_text = 'incelendi' if status == 'reviewed' else 'onaylandı'
        flash(f'Rapor başarıyla {status_text}.', 'success')
    
    return redirect(url_for('employee.view_report', report_id=report_id))


# API Endpoint'leri

@employee_bp.route('/api/check-shift-status')
@login_required
def check_shift_status():
    """Vardiya durumunu kontrol et (AJAX)"""
    employee_id = request.args.get('employee_id', type=int)
    
    if not employee_id:
        return jsonify({'error': 'Çalışan ID\'si gerekli'}), 400
    
    employee = User.query.get_or_404(employee_id)
    
    # İzin durumunu kontrol et
    is_on_leave = employee.is_on_leave
    
    # Vardiya durumunu kontrol et
    current_shift = employee.check_current_shift()
    
    return jsonify({
        'employee_name': employee.full_name,
        'is_on_leave': is_on_leave,
        'on_shift': current_shift is not None,
        'shift_details': {
            'day': current_shift.day_of_week if current_shift else None,
            'start': current_shift.start_time.strftime('%H:%M') if current_shift else None,
            'end': current_shift.end_time.strftime('%H:%M') if current_shift else None
        } if current_shift else None
    })