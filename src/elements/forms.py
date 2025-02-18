from flask_material import Material
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import HiddenField, StringField, SelectField, TextAreaField, DateField, DateTimeField, SubmitField, FormField, validators
from wtforms.validators import InputRequired, DataRequired
import json

class Schedule(FlaskForm):
    date = DateField(label="Schedule Date", validators=[InputRequired()])
    timing = DateTimeField(label="Timing", validators=[InputRequired()], format="%H:%M")

class Order(FlaskForm):
    with open("src/assets/modalities.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    choices = [(int(modality["id"]), modality["name"]) for modality in data['modalities']]
    # patient information

    patient_name = StringField(label="Patient Name", validators=[DataRequired("Enter the patient's name")])
    imaging_modality = SelectField(
        "Modality",
        choices=choices,
        default=1
    )
    ordering_phycisian = StringField(label="Ordering Phycisian", validators=[DataRequired("Enter Orderer physician")])

    exam_type = StringField(label="Examen Name", validators=[DataRequired("Examination")])
    add_note = TextAreaField(label="Note", validators=[validators.optional("Enter additional information about the requested examination"), validators.length(max=250)])

    # Sub Form
    date_timing = FormField(Schedule)
    submit = SubmitField("Submit")
