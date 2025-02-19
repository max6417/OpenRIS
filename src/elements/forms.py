from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DateField, SubmitField, FormField, validators
from wtforms.validators import InputRequired, DataRequired
from wtforms.fields import TimeField
import json
# Attention render_kw permet de définir classes et id d'un element

class Schedule(FlaskForm):
    date = DateField(label="Schedule Date", validators=[InputRequired()])
    timing = TimeField(label="Timing", validators=[InputRequired()], format="%H:%M")


class Order(FlaskForm):
    with open("src/assets/modalities.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    choices = [(int(modality["id"]), modality["name"]) for modality in data['modalities']]
    # patient information

    patient_name = StringField(label="Patient Name", validators=[DataRequired("Enter the patient's name")])
    imaging_modality = SelectField(
        "Modality",
        choices=choices,
        default=1,
        render_kw={"style": "display:block"}
    )
    ordering_physician = StringField(label="Ordering Phycisian", validators=[DataRequired("Enter Orderer physician")])

    exam_type = StringField(label="Examen Name", validators=[DataRequired("Examination")])
    add_note = TextAreaField(label="Note", validators=[validators.optional("Enter additional information about the requested examination"), validators.length(max=250)], render_kw={"class":"materialize-textarea"})

    # Sub Form
    examination_date = FormField(Schedule)
    submit = SubmitField("Submit")
