from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, TimeField, IntegerField, BooleanField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from models import User, Vehicle

class LoginForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    submit = SubmitField('Giriş')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mevcut Şifre', validators=[DataRequired()])
    new_password = PasswordField('Yeni Şifre', validators=[
        DataRequired(),
        Length(min=6, message='Şifre en az 6 karakter olmalıdır.')
    ])
    confirm_password = PasswordField('Yeni Şifre (Tekrar)', validators=[
        DataRequired(),
        EqualTo('new_password', message='Şifreler eşleşmiyor.')
    ])
    submit = SubmitField('Şifreyi Değiştir')

class UserForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[
        Length(min=6, message='Şifre en az 6 karakter olmalıdır.'),
        Optional()
    ])
    first_name = StringField('Ad', validators=[Optional(), Length(max=100)])
    last_name = StringField('Soyad', validators=[Optional(), Length(max=100)])
    phone = StringField('Telefon', validators=[Optional(), Length(max=20)])
    role = SelectField('Rol', choices=[
        ('admin', 'Yönetici'), 
        ('moderator', 'Moderatör'), 
        ('driver', 'Şoför')
    ])
    license_plate = StringField('Plaka', validators=[Optional(), Length(max=20)])
    is_active = BooleanField('Aktif')
    submit = SubmitField('Kaydet')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != getattr(self, 'user_id', None):
            raise ValidationError('Bu kullanıcı adı zaten kullanılıyor. Lütfen başka bir kullanıcı adı seçin.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != getattr(self, 'user_id', None):
            raise ValidationError('Bu e-posta adresi zaten kullanılıyor. Lütfen başka bir e-posta adresi seçin.')

class ProfileForm(FlaskForm):
    first_name = StringField('Ad', validators=[Optional(), Length(max=100)])
    last_name = StringField('Soyad', validators=[Optional(), Length(max=100)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    phone = StringField('Telefon', validators=[Optional(), Length(max=20)])
    license_plate = StringField('Plaka', validators=[Optional(), Length(max=20)])
    work_status = SelectField('Çalışma Durumu', choices=[
        ('active', 'Aktif'), 
        ('inactive', 'Pasif'), 
        ('break', 'Molada')
    ], validators=[Optional()])
    current_location = StringField('Güncel Konum', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Güncelle')

class VehicleForm(FlaskForm):
    chassis_number = StringField('Şasi No', validators=[DataRequired(), Length(max=20)])
    model = SelectField('Model', validators=[DataRequired()], choices=[])
    submit = SubmitField('Kaydet')

    def __init__(self, *args, **kwargs):
        super(VehicleForm, self).__init__(*args, **kwargs)
        # VehicleCatalog'dan modelleri al
        from models import VehicleCatalog
        models = VehicleCatalog.query.all()
        self.model.choices = [('', 'Model Seçiniz')] + [(m.model, m.model) for m in models]

    def validate_chassis_number(self, chassis_number):
        vehicle = Vehicle.query.filter_by(chassis_number=chassis_number.data).first()
        if vehicle and vehicle.id != getattr(self, 'vehicle_id', None):
            raise ValidationError('Bu şasi numarası zaten kullanılıyor. Lütfen başka bir şasi numarası girin.')

class VehicleEntryForm(FlaskForm):
    chassis_number = StringField('Şasi No', validators=[DataRequired(), Length(max=20)])
    driver_id = SelectField('Şoför', coerce=int)
    yard = StringField('Yükleme Sahası', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Giriş Kaydı Oluştur')

class VehicleExitForm(FlaskForm):
    chassis_number = StringField('Şasi No', validators=[DataRequired(), Length(max=20)])
    driver_id = SelectField('Şoför', coerce=int)
    destination = StringField('Hedef', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Çıkış Kaydı Oluştur')

class DamageTypeForm(FlaskForm):
    name = StringField('Hasar Tipi Adı', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Açıklama', validators=[Optional()])
    submit = SubmitField('Kaydet')

class DamageForm(FlaskForm):
    vehicle_id = SelectField('Araç', coerce=int)
    chassis_number = StringField('Şasi No', validators=[DataRequired(), Length(max=20)])
    model = StringField('Model')
    damage_type_id = SelectField('Hasar Tipi', coerce=int)
    description = TextAreaField('Açıklama', validators=[DataRequired()])
    location_x = HiddenField('Konum X')
    location_y = HiddenField('Konum Y')
    group = SelectField('Grup', choices=[
        ('35', '1 - ANTEN/ANTEN ÜNİTESİ'),
        ('36', '2 - AKÜ'),
        ('37', '3 - TAMPON/KAPAK/DIŞ, ÖN'),
        ('38', '4 - TAMPON/KAPAK/DIŞ, ARKA'),
        ('39', '5 - TAMPON KORUMASI/ŞERİDİ, ÖN'),
        ('40', '6 - TAMPON KORUMASI/ŞERİDİ, ARKA'),
        ('41', '7 - BAGAJ KAPISI – SAĞ'),
        ('42', '8 - BAGAJ KAPISI – SOL'),
        ('43', '9 - BAGAJ KAPISI (SÜRGÜLÜ) SAĞ/SOL'),
        ('44', '10 - KAPI, SOL ÖN'),
        ('45', '11 - KAPI, SOL ARKA'),
        ('46', '12 - KAPI, SAĞ ÖN'),
        ('47', '13 - KAPI, SAĞ ARKA'),
        ('48', '14 - ÇAMURLUK, SOL ÖN'),
        ('49', '15 - TEKERLEK ÜSTÜ PANEL VEYA BAGAJ YERİ, SOL'),
        ('50', '16 - ÇAMURLUK, SAĞ ÖN'),
        ('51', '17 - TEKERLEK ÜSTÜ PANEL VEYA BAGAJ YERİ, SAĞ'),
        ('52', '18 - ÖN ZEMİN PASPASLARI'),
        ('53', '19 - ARKA ZEMİN PASPASLARI'),
        ('54', '20 - ÖN CAM'),
        ('55', '21 - ARKA CAM'),
        ('56', '22 - ÖN IZGARA')
    ])
    damage_description = SelectField('Tanım', choices=[
        ('760', '1 - BÜKÜLME'),
        ('761', '2 - ÇALIŞAMAZ DURUMDA'),
        ('762', '3 - KESİK'),
        ('763', '4 - EZİK - BOYA VEYA KROM HASARLI'),
        ('764', '5 - ÇENTİKLİ - CAM VEYA PANEL KENARI İÇİN DEĞİL'),
        ('765', '6 - ÇATLAK - CAM İÇİN DEĞİL'),
        ('766', '7 - OYULMUŞ'),
        ('767', '8 - EKSİK'),
        ('768', '9 - AŞINMIŞ')
    ])
    level = SelectField('Hasar Seviyesi', choices=[
        ('1', '1 - 1" uzunluğa / çapa kadar olan hasarlar - 2,5 cm\'den az'),
        ('2', '2 - 1"den 3"e kadar uzunluktaki / çaplı hasarlar - 2,5 cm\'den 7,5 cm\'ye kadar'),
        ('3', '3 - 3"den 6"ya kadar uzunluktaki / çaplı hasarlar - 7,5 cm\'den 15 cm\'ye kadar'),
        ('4', '4 - 6"den 12"ye kadar uzunluktaki / çaptaki hasarlar – 15 cm\'den 30 cm\'ye kadar'),
        ('5', '5 - 12" uzunluğundan / çapından büyük hasarlar – 30 cm ve üzeri'),
        ('6', '6 - Eksik/Büyük Hasar')
    ])
    severity = SelectField('Hasar Şiddeti', choices=[
        ('minor', 'Hafif'),
        ('moderate', 'Orta'),
        ('severe', 'Ağır')
    ])
    status = SelectField('Durum', choices=[
        ('pending', 'Beklemede'),
        ('in_progress', 'İşlemde'),
        ('repaired', 'Onarıldı')
    ])
    submit = SubmitField('Kaydet')

class DeliveryForm(FlaskForm):
    delivery_number = StringField('İrsaliye No', validators=[DataRequired(), Length(max=20)])
    driver_id = SelectField('Şoför', coerce=int)
    issue_date = DateField('Tarih', validators=[DataRequired()])
    issue_time = TimeField('Saat', validators=[DataRequired()])
    loading_yard = StringField('Yükleme Sahası', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')

class DeliveryItemForm(FlaskForm):
    chassis_number = StringField('Şasi No', validators=[DataRequired(), Length(max=20)])
    brand = StringField('Marka', validators=[Optional(), Length(max=50)])
    model = StringField('Model', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Ekle')

class LoadForm(FlaskForm):
    load_number = StringField('Yük No', validators=[DataRequired(), Length(max=20)])
    destination = StringField('Hedef', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')

class LoadItemForm(FlaskForm):
    vehicle_id = SelectField('Araç', coerce=int)
    chassis_number = StringField('Şasi No', validators=[DataRequired(), Length(max=20)])
    position = SelectField('Pozisyon', coerce=int, choices=[(i, str(i)) for i in range(1, 9)])
    submit = SubmitField('Ekle')