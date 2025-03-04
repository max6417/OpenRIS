import wtforms.csrf.session
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DateField, SubmitField, FormField, validators
from wtforms.validators import InputRequired, DataRequired, ValidationError
from wtforms.fields import TimeField
import json
# Attention render_kw permet de définir classes et id d'un element
import datetime


class BaseForm(FlaskForm):
    class Meta:
        csrf = False

class Schedule(BaseForm):
    date = DateField(label="Schedule Date", validators=[InputRequired(), DataRequired()])
    timing = TimeField(label="Timing", validators=[InputRequired(), DataRequired()], format="%H:%M")

    def validate_date(self, field):
        entered_date = datetime.datetime.strptime(str(field.data), "%Y-%m-%d").date()
        current_date = datetime.datetime.today().date()
        if entered_date < current_date:
            raise ValidationError("An imaging examination cannot be schedule earlier than the current date")

    def validate_timing(self, field):
        entered_time = datetime.datetime.strptime(f"{str(self.date.data)} {str(field.data)}", '%Y-%m-%d %H:%M:%S')
        current_time = datetime.datetime.now()
        if entered_time < current_time:
            raise ValidationError("An imaging examination cannot be schedule earlier than the current time")


class Order(BaseForm):
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
    add_note = TextAreaField(label="Note", validators=[validators.optional("Enter additional information about the requested examination"), validators.length(max=250)])

    # Sub Form
    examination_date = FormField(Schedule)
    submit = SubmitField("Submit")

    def validate_patient_name(self, field):
        pass

    def validate_imaging_modality(self, field):
        pass

    def validate_ordering_physician(self, field):
        pass

    def validate_exam_type(self, field):
        pass

    def validate_add_note(self, field):
        pass
