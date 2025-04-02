from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DateField, FormField, validators
from wtforms.validators import ValidationError, DataRequired, Optional
from wtforms.fields import TimeField, DateField, TelField, EmailField
import datetime
from html import escape
import re
from utils import MongoDBClient

client = MongoDBClient.MongoDBClient()


class BaseForm(FlaskForm):
    class Meta:
        csrf = False


class ScheduleForm(BaseForm):
    date = DateField("Sechedule Date", format="%Y-%m-%d", render_kw={"type": "text", "placeholder": "yyyy-mm-dd"}, validators=[DataRequired()])
    timing = TimeField("Timing", format="%H:%M", validators=[DataRequired()])

    def validate_date(self, field):
        entered_date = datetime.datetime.strptime(str(self.date.data), "%Y-%m-%d").date()
        current_date = datetime.datetime.today().date()
        if entered_date < current_date:
            raise ValidationError("An imaging examination cannot be schedule earlier than the current date")
        return True

    def validate_timing(self, field):
        entered_time = datetime.datetime.strptime(f"{str(self.date.data)} {str(self.timing.data)}", "%Y-%m-%d %H:%M:%S")
        current_time = datetime.datetime.now()
        if entered_time < current_time:
            raise ValidationError("An imaging examination cannot be schedule earlier than the current time")
        return True


class Order(BaseForm):
    ordering_physician = StringField("Ordering Physician", validators=[DataRequired()])

    # Imaging Request Information
    imaging_modality = SelectField(
        "Modality",
        choices=[(modality['_id'], modality['name']) for modality in client.list_documents("modalities")],
        render_kw={"style": "display:block"}
    )
    procedure = SelectField(
        "Procedure",
        choices=[],
        render_kw={"style": "display:block"}
    )
    add_note = TextAreaField("Note", validators=[validators.length(max=250), Optional()])
    examination_date = FormField(ScheduleForm)

    def validate_ordering_physician(self, field):
        if not bool(re.fullmatch(r'^[a-zA-Z\s\-\']+$', field.data)):
            raise ValidationError("Name of physician not conform")

    def validate_imaging_modality(self, field):
        pass

    def validate_procedure(self, field):
        pass

    def validate_add_note(self, field):
        pass


class PatientSearchForm(BaseForm):
    patient_name = StringField("Patient Name", validators=[Optional()])
    patient_surname = StringField("Patient Surname", validators=[Optional()])

    def validate_patient_name(self, field):
        pattern = r'^[a-zA-Z\s\-\']+$'
        if not bool(re.fullmatch(pattern, field.data)):
            raise ValidationError('Patient Name incorrect format')

    def validate_patient_surname(self, field):
        pattern = r'^[a-zA-Z\s\-\']+$'
        if not bool(re.fullmatch(pattern, field.data)):
            raise ValidationError('Patient Surname incorrect format')


class PatientDemographics(BaseForm):
    """
    Form used to edit the patient demographic data :
        - Name
        - Surname
        - DOB
        - Sex
        - Phone Number
        - Email
        - Address + Code Postal + Complement + Country + City
        - Referring Physician
    """
    patient_name = StringField("Patient Name", validators=[DataRequired()])
    patient_surname = StringField("Patient Surname", validators=[DataRequired()])
    patient_dob = StringField("Date of Birth", validators=[DataRequired()], render_kw={"type": "text", "placeholder": "yyyy-mm-dd"})
    patient_sex = SelectField(
        "Sex",
        choices=[("F", "F"), ("M", "M"), ("O", "O"), ("U", "U")],
        render_kw={"style": "display:block"}
    )
    patient_phone_number = TelField("Phone Number", validators=[Optional()])
    patient_email = EmailField("Email Address", validators=[Optional()])
    patient_address = StringField("Address", validators=[Optional()])
    patient_address_complement = StringField("Complement", validators=[Optional()])
    patient_zip_code = StringField("Zip Code", validators=[Optional()])
    patient_city = StringField("City", validators=[Optional()])
    patient_country = StringField("Country", validators=[Optional()])
    patient_referring_physician = StringField("Referring Physician", validators=[Optional()])

    def validate_patient_name(self, field):
        if not bool(re.fullmatch(r'^[a-zA-Z\s\-\']+$', field.data)):
            raise ValidationError("Patient name doesn't fit the pattern")

    def validate_patient_surname(self, field):
        if not bool(re.fullmatch(r'^[a-zA-Z\s\-\']+$', field.data)):
            raise ValidationError("Patient surname doesn't fit the pattern")

    def validate_patient_dob(self, field):
        if not bool(re.fullmatch(r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$', field.data)):
            raise ValidationError("date is not in the right format")

    def validate_phone_number(self, field):
        if not bool(re.fullmatch(r'^\d{9}$', field.data)):
            raise ValidationError("This is not a valid ")

    def validate_email(self, field):
        if not bool(re.fullmatch(r'^[a-z]@[a-z]\.[a-z]', field.data.lower())):
            raise ValidationError("email is not in the right format")

    def validate_zip_code(self, field):
        pass
