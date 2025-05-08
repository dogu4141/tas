from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, IntegerField
from wtforms import TextAreaField, BooleanField, TimeField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from datetime import datetime

class EmployeeForm(FlaskForm):
    """Çalışan ekleme ve düzenleme formu"""
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('E-posta', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Şifre', validators=[Length(min=6, max=64)])  # Düzenleme modunda opsiyonel
    first_name = StringField('Ad', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Soyad', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Telefon', validators=[Optional(), Length(max=20)])
    role = SelectField('Rol', choices=[
        ('admin', 'Yönetici'),
        ('moderator', 'Moderatör'),
        ('driver', 'Şoför'),
        ('employee', 'Çalışan')
    ], validators=[DataRequired()])
    employee_id = StringField('Çalışan Numarası', validators=[Optional(), Length(max=20)])
    department = StringField('Departman', validators=[Optional(), Length(max=50)])
    position = StringField('Pozisyon', validators=[Optional(), Length(max=50)])
    hire_date = DateField('İşe Başlama Tarihi', format='%Y-%m-%d', validators=[Optional()])
    license_plate = StringField('Plaka', validators=[Optional(), Length(max=20)])
    is_active = BooleanField('Aktif')


class ShiftForm(FlaskForm):
    """Vardiya ekleme formu"""
    employee_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])
    day_of_week = SelectField('Gün', choices=[
        (0, 'Pazartesi'),
        (1, 'Salı'),
        (2, 'Çarşamba'),
        (3, 'Perşembe'),
        (4, 'Cuma'),
        (5, 'Cumartesi'),
        (6, 'Pazar')
    ], coerce=int, validators=[DataRequired()])
    start_time = TimeField('Başlangıç Saati', format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('Bitiş Saati', format='%H:%M', validators=[DataRequired()])
    is_active = BooleanField('Aktif', default=True)

    def validate_end_time(self, field):
        """Bitiş saati başlangıç saatinden sonra olmalı"""
        if self.start_time.data and field.data <= self.start_time.data:
            raise ValidationError('Bitiş saati başlangıç saatinden sonra olmalıdır.')


class LeaveRequestForm(FlaskForm):
    """İzin talep formu"""
    employee_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])
    start_date = DateField('Başlangıç Tarihi', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('Bitiş Tarihi', format='%Y-%m-%d', validators=[DataRequired()])
    leave_type = SelectField('İzin Türü', choices=[
        ('paid', 'Ücretli İzin'),
        ('unpaid', 'Ücretsiz İzin'),
        ('sick', 'Hastalık İzni'),
        ('annual', 'Yıllık İzin'),
        ('maternity', 'Doğum İzni'),
        ('paternity', 'Babalık İzni'),
        ('wedding', 'Evlilik İzni'),
        ('bereavement', 'Vefat İzni'),
        ('other', 'Diğer')
    ], validators=[DataRequired()])
    reason = TextAreaField('İzin Sebebi', validators=[Optional(), Length(max=500)])

    def validate_end_date(self, field):
        """Bitiş tarihi başlangıç tarihinden sonra olmalı"""
        if self.start_date.data and field.data < self.start_date.data:
            raise ValidationError('Bitiş tarihi başlangıç tarihinden sonra olmalıdır.')
        
        # Geçmiş tarihli izin talebi kontrolü
        today = datetime.utcnow().date()
        if field.data < today:
            raise ValidationError('Geçmiş tarihli izin talep edilemez.')


class EmployeeReportForm(FlaskForm):
    """Çalışan rapor formu"""
    report_type = SelectField('Rapor Türü', choices=[
        ('daily', 'Günlük Rapor'),
        ('weekly', 'Haftalık Rapor'),
        ('incident', 'Olay Raporu'),
        ('feedback', 'Geri Bildirim'),
        ('other', 'Diğer')
    ], validators=[DataRequired()])
    title = StringField('Başlık', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Rapor İçeriği', validators=[DataRequired()])
    attachments = MultipleFileField('Ekler')


class LeaveRequestApprovalForm(FlaskForm):
    """İzin talebi onaylama formu (yöneticiler için)"""
    status = SelectField('Durum', choices=[
        ('pending', 'Beklemede'),
        ('approved', 'Onaylandı'),
        ('rejected', 'Reddedildi')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notlar', validators=[Optional()])