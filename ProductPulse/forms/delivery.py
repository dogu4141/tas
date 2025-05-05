from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, DateField, TimeField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

class DeliveryForm(FlaskForm):
    """İrsaliye ekleme formu"""
    delivery_number = StringField('İrsaliye Numarası', validators=[DataRequired(), Length(max=20)])
    issue_date = DateField('Düzenleme Tarihi', format='%Y-%m-%d', validators=[DataRequired()])
    issue_time = TimeField('Düzenleme Saati', format='%H:%M', validators=[DataRequired()])
    loading_yard = StringField('Yükleme Sahası', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notlar', validators=[Optional()])


class DeliveryItemForm(FlaskForm):
    """İrsaliye kalem formu"""
    chassis_number = StringField('Şasi Numarası', validators=[DataRequired(), Length(max=20)])
    brand = StringField('Marka', validators=[Optional(), Length(max=50)])
    model = StringField('Model', validators=[Optional(), Length(max=50)])


class DeliveryImageForm(FlaskForm):
    """İrsaliye fotoğraf ekleme formu"""
    delivery_number = StringField('İrsaliye Numarası', validators=[DataRequired(), Length(max=20)])
    image = FileField('İrsaliye Fotoğrafı', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Sadece resim dosyaları yüklenebilir.')
    ])
    notes = TextAreaField('Notlar', validators=[Optional()])