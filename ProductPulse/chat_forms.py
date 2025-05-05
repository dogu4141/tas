from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, SelectMultipleField, SelectField, FileField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed

class ChatGroupForm(FlaskForm):
    """Form for creating/editing chat groups"""
    name = StringField('Grup Adı', validators=[
        DataRequired(message='Grup adı gereklidir'),
        Length(min=3, max=100, message='Grup adı 3-100 karakter olmalıdır')
    ])
    description = TextAreaField('Açıklama', validators=[Optional()])
    region = StringField('Bölge', validators=[Optional(), Length(max=100)])
    is_private = BooleanField('Özel Grup')
    members = SelectMultipleField('Üyeler', coerce=int)
    submit = SubmitField('Kaydet')

class MessageForm(FlaskForm):
    """Form for sending messages"""
    content = TextAreaField('Mesaj', validators=[
        DataRequired(message='Mesaj boş olamaz'),
        Length(max=2000, message='Mesaj en fazla 2000 karakter olabilir')
    ])
    attachment = FileField('Dosya Ekle', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'pdf', 'doc', 'docx', 'xls', 'xlsx'],
                    'Sadece belirtilen dosya türleri yüklenebilir.')
    ])
    location_lat = HiddenField()
    location_lng = HiddenField()
    submit = SubmitField('Gönder')

class MessageSearchForm(FlaskForm):
    """Form for searching messages"""
    search_term = StringField('Ara', validators=[Optional()])
    date_from = StringField('Başlangıç Tarihi', validators=[Optional()])
    date_to = StringField('Bitiş Tarihi', validators=[Optional()])
    search_type = SelectField('Arama Tipi', choices=[
        ('content', 'Mesaj İçeriği'),
        ('sender', 'Gönderen'),
        ('group', 'Grup')
    ])
    submit = SubmitField('Ara')