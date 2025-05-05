from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, IntegerField, FloatField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class VehicleCatalogForm(FlaskForm):
    """Araç kataloğu ekleme formu"""
    brand = StringField('Marka', validators=[DataRequired(), Length(max=100)])
    model = StringField('Model', validators=[DataRequired(), Length(max=100)])
    year = IntegerField('Model Yılı', validators=[
        DataRequired(),
        NumberRange(min=2020, max=2030, message='Geçerli bir model yılı giriniz (2020-2030)')
    ])
    tonnage = FloatField('Tonaj', validators=[Optional()])
    image = FileField('Araç Fotoğrafı', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Sadece resim dosyaları yüklenebilir.')
    ])
    description = TextAreaField('Açıklama', validators=[Optional()])


class VehicleCatalogSearchForm(FlaskForm):
    """Araç kataloğu arama formu"""
    brand = StringField('Marka', validators=[Optional()])
    model = StringField('Model', validators=[Optional()])
    year = IntegerField('Model Yılı', validators=[Optional()])
    min_tonnage = FloatField('Minimum Tonaj', validators=[Optional()])
    max_tonnage = FloatField('Maksimum Tonaj', validators=[Optional()])
    only_with_image = BooleanField('Sadece Resimli', default=False)