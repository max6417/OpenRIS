import flask
import hl7_code
from flask import request, render_template, url_for, flash, jsonify
from flask_material import Material

from src.hl7_code.message_constructor import HL7MessageBuilder
from utils.checker import *
from utils.MongoDBClient import *
from utils import utils
from elements.Forms import *
from hl7_code.message_validators import *
from pydicom.uid import generate_uid
import pyorthanc
import requests
import logging


ORTHANC_SERVER = "http://localhost:8042/"


APP_LOGGER = logging.getLogger("app_logs")


def hl7_log(message: hl7.Message, direction: str):
    curr_date = datetime.datetime.now().strftime("%Y-%m%dT%H:%M:%S")
    APP_LOGGER.info(f"{curr_date} - {direction} - {str(message)}")



# TODO - A entire refactor of the LOG system AND the HL7 messages


app = flask.Flask(__name__, static_folder="js")
Material(app)
app.config['SECRET_KEY'] = "ADMIN"
app.config['TEMPLATES_AUTO_RELOAD'] = True


client = MongoDBClient.MongoDBClient()


pattern_val = PatternValidator("configs/hl7_messages_config.json", "configs/hl7_segment_config.json")


orthanc_client = pyorthanc.Orthanc(ORTHANC_SERVER)    # Connect to Orthanc service from RIS to enable communication
if not orthanc_client:
    print("Cannot find Orthanc server")
modalities = orthanc_client.get_modalities()



@app.route("/")
def index():
    return flask.redirect("/workflow/all")


@app.route("/patients", methods=["GET", "POST"])
def patients():
    search_form = PatientSearchForm()
    if request.method == "POST" and search_form.validate():
        if search_form.patient_surname.data and search_form.patient_name.data:
            patients = client.get_documents('patients', {'name': search_form.patient_name.data.upper(), 'surname': search_form.patient_surname.data.upper()})
        elif search_form.patient_name.data:
            patients = client.get_documents('patients', {'name': search_form.patient_name.data.upper()})
        elif search_form.patient_surname.data:
            patients = client.get_documents('patients', {'surname': search_form.patient_surname.data.upper()})
        else:
            patients = client.get_documents('patients', {})
        return flask.render_template("patients.html", patients=patients, page_name='patients', search_form=search_form)
    elif request.method == "POST":
        patients = client.get_documents("patients", {})
        search_form.patient_name.data = ""
        search_form.patient_surname.data = ""
        return flask.render_template("patients.html", patients=patients, page_name='patients', search_form=search_form)
    else:
        patients = client.get_documents("patients", {})
        search_form.patient_name.data = ""
        search_form.patient_surname.data = ""
        return flask.render_template("patients.html", patients=patients, page_name='patients', search_form=search_form)


@app.route("/patient_information/<id>")
def patient_information(id):
    patient = client.get_document('patients', {'_id': id})
    scheduled_orders = client.get_documents('orders', {'patient_id': id, 'is_active': True})
    past_orders = client.get_documents('orders', {'patient_id': id, 'is_active': False})
    return flask.render_template('patient_informations.html', patient=patient, scheduled_orders=scheduled_orders, past_orders=past_orders)


@app.route("/edit_profile/<id>", methods=["GET", "POST"])
def edit_profile(id):
    # TODO - Add a new HL7 message in order to show the updated fields
    patient = client.get_document('patients', {'_id': id})
    address = patient.get('address', {})
    PatientDemForm = PatientDemographics()
    if request.method == "POST" and PatientDemForm.validate():
        date = datetime.datetime.now().strftime("%Y%m%d")
        client.update_document(
            'patients',
            id,
            {
                'name': PatientDemForm.patient_name.data.upper(),
                'surname': PatientDemForm.patient_surname.data.upper(),
                'dob': PatientDemForm.patient_dob.data,
                'sex': PatientDemForm.patient_sex.data,
                'phone_number': PatientDemForm.patient_phone_number.data,
                'email': PatientDemForm.patient_email.data.lower(),
                'address': {
                    'address': PatientDemForm.patient_address.data.upper(),
                    'complement': PatientDemForm.patient_address_complement.data.upper(),
                    'zip_code': PatientDemForm.patient_zip_code.data.upper(),
                    'city': PatientDemForm.patient_city.data.upper(),
                    'country': PatientDemForm.patient_country.data.upper(),
                },
                'referring_physician': {
                    '_id': PatientDemForm.patient_referring_physician_id.data,
                    'name': PatientDemForm.patient_referring_physician_name.data.upper(),
                    'surname': PatientDemForm.patient_referring_physician_surname.data.upper()
                }
            }
        )
        # Creating HL7 ADT^A08 message
        adt_a08 = HL7MessageBuilder()
        adt_a08.add_segment(
            "MSH|^~\&|OPENRIS|DEBUG HOSPITAL|HIS|DEBUG HOSPITAL|"+date+"||ADT^A08^ADT_A08|"+str(uuid4())+"|D|2.8||\r"
        )
        adt_a08.add_segment(
            "EVN|A01|" + date + "||\r"
        )
        adt_a08.add_segment(
            "PID|1||"+id+"^5^M11^ADT1^MR^DEBUG HOSPITAL||"+PatientDemForm.patient_name.data.upper()+"^"+
            PatientDemForm.patient_surname.data.upper()+"||"+PatientDemForm.patient_dob.data.replace('-', '')+"|"+
            PatientDemForm.patient_sex.data.get('sex', '').upper()+"||"+patient.get('ethnicity', '').upper()+"|"+
            PatientDemForm.patient_address.data.upper()+"^^"+PatientDemForm.patient_city.data.upper()+"^"+
            address.get('province', '').upper()+"^"+PatientDemForm.patient_zip_code.data.upper()+"^"+
            PatientDemForm.patient_country.data.upper()+"|"+address.get('county-code', '').upper()+"|"+
            PatientDemForm.patient_phone_number.data+"|"+patient.get('business-phone', '')+"|"+
            patient.get('language', '').upper()+"|"+patient.get('marital-status', '').upper()+"|"+
            patient.get('religion', '').upper()+"||"+patient.get('ssn', '')+"||\r"
        )
        adt_a08.add_segment(
            "PV1||"+patient.get('patient-class', 'I')+"||"+patient.get('admission-type', 'R')+"||||"+
            PatientDemForm.patient_referring_physician_id+"^"+PatientDemForm.patient_referring_physician_name.data.upper()+"^"+
            PatientDemForm.patient_referring_physician_surname.data.upper()+"||MED||||ADM|A0|\r"
        )
        hl7_log(adt_a08.build(), "OUT")
        return flask.redirect("/patients")
    elif request.method == "POST":
        flash("Errors in the form", "error")
        return flask.render_template("patient-editor.html", form=PatientDemForm, id=patient.get('_id', -1))
    else:
        PatientDemForm.patient_surname.data = patient.get('surname', '')
        PatientDemForm.patient_name.data = patient.get('name', '')
        PatientDemForm.patient_dob.data = patient.get('dob', '')
        PatientDemForm.patient_sex.data = patient.get('sex', 'U')
        PatientDemForm.patient_phone_number.data = patient.get('phone_number', '')
        PatientDemForm.patient_email.data = patient.get('email', '')
        PatientDemForm.patient_address.data = patient.get('address', {}).get('address', '')
        PatientDemForm.patient_address_complement.data = patient.get('address', {}).get('complement', '')
        PatientDemForm.patient_zip_code.data = patient.get('address', {}).get('zip_code', '')
        PatientDemForm.patient_city.data = patient.get('address', {}).get('city', '')
        PatientDemForm.patient_country.data = patient.get('address', {}).get('country', '')
        PatientDemForm.patient_referring_physician_id.data = patient.get('referring_physician', {}).get('_id', '')
        PatientDemForm.patient_referring_physician_name.data = patient.get('referring_physician', {}).get('name', '')
        PatientDemForm.patient_referring_physician_surname.data = patient.get('referring_physician', {}).get('surname', '')
        return flask.render_template("patient-editor.html", form=PatientDemForm, id=patient.get('_id', -1))


@app.route("/receive-hl7", methods=['POST'])
def receive_hl7_message():
    message = hl7.parse(flask.request.get_data().decode('utf-8'))

    match extract_information(message, "MSH", field_num=9, component_num=3):
        case "ADT_A01":
            ret_message = ADTA01Validator().validate_and_ack(message, pattern_val, "DEBUG HOSPITAL", "OPENRIS")
            hl7_log(message, "IN")
            if extract_information(ret_message, "MSA", field_num=1) == "AA":
                # TODO - Add patient to patients DB if do not already exist
                new_patient_id = extract_information(message, "PID", field_num=3)
                is_existing_patient = client.get_document('patients', {'_id': new_patient_id})
                if is_existing_patient is None:    # Create new patient
                    new_patient = {
                        '_id': new_patient_id,
                        'name': extract_information(message, "PID", field_num=5, component_num=1) if extract_information(message, "PID", field_num=5, component_num=1) else "",
                        'surname': extract_information(message, "PID", field_num=5, component_num=2) if extract_information(message, "PID", field_num=5, component_num=2) else "",
                        'dob': f"{extract_information(message, "PID", field_num=7)[:3]}-{extract_information(message, "PID", field_num=7)[3:5]}-{extract_information(message, "PID", field_num=7)[5:7]}" if extract_information(message, "PID", field_num=7) else "",
                        'sex': extract_information(message, "PID", field_num=8) if extract_information(message, "PID", field_num=8) else "U",
                        'phone_number': extract_information(message, "PID", field_num=13) if extract_information(message, "PID", field_num=13) else "",
                        'email': extract_information(message, "PID", field_num=14) if extract_information(message, "PID", field_num=14) else "",
                        'address': {
                            'address': extract_information(message, "PID", field_num=11, component_num=1) if extract_information(message, "PID", field_num=11, component_num=1) else "",
                            'complement': extract_information(message, "PID", field_num=11, component_num=2) if extract_information(message, "PID", field_num=11, component_num=2) else "",
                            'city': extract_information(message, "PID", field_num=11, component_num=3) if extract_information(message, "PID", field_num=11, component_num=3) else "",
                            'zip_code': extract_information(message, "PID", field_num=11, component_num=5) if extract_information(message, "PID", field_num=11, component_num=5) else "",
                            'country': extract_information(message, "PID", field_num=11, component_num=6) if extract_information(message, "PID", field_num=11, component_num=6) else "",
                        },
                        'referring_physician': {
                            '_id': extract_information(message, "PV1", field_num=8, component_num=1) if extract_information(message, "PV1", field_num=8, component_num=1) else "",
                            'name': extract_information(message, "PV1", field_num=8, component_num=2) if extract_information(message, "PV1", field_num=8, component_num=2) else "",
                            'surname': extract_information(message, "PV1", field_num=8, component_num=3) if extract_information(message, "PV1", field_num=8, component_num=3) else ""
                        }
                    }
                    client.add_document('patients', new_patient)
                    APP_LOGGER.info(f"New patient {new_patient['_id']} added to DB")
                else:
                    APP_LOGGER.info(f"Patient {new_patient_id} already exist in DB")
                return flask.Response(status=200)
            hl7_log(ret_message, "OUT")
            return flask.Response(status=400)
        case _:
            hl7_log(message, "IN")
            APP_LOGGER.info(f"Uncaught HL7 message: {message}")
            return flask.Response(status=400)


@app.route("/create_new_order/<id>", methods=["GET", "POST"])
def create_new_order(id):
    form = Order()
    form.procedure.choices = [(procedure['_id'], procedure['name']) for procedure in client.get_documents('procedures', {'modality': form.imaging_modality.choices[0][1].split('_')[0]})]
    if request.method == "POST" and form.examination_date.form.validate() and form.validate_ordering_physician(form.ordering_physician):
        procedure = client.get_document("procedures", {"_id": form.procedure.data})
        modality = form.imaging_modality.data
        examination_date = {
            "date": str(form.examination_date.date.data),
            "start_time": (datetime.datetime.strptime(str(form.examination_date.timing.data), "%H:%M:%S")).strftime("%H:%M:%S"),
            "end_time": (datetime.datetime.strptime(str(form.examination_date.timing.data), "%H:%M:%S") + datetime.timedelta(minutes=int(procedure['duration']))).strftime("%H:%M:%S")
        }
        ## TIMING CONFLICT DETECTION ##
        patient_conflict = list(client.get_documents("orders", {
            "patient_id": str(id),
            "examination_date.date": examination_date["date"],
            "is_active": True
        }))
        if utils.check_examination_date_overlapping(examination_date, patient_conflict):
            APP_LOGGER.info(f"Patient {id} already have an examination at this time")
            flash("Patient have already an examination at this time", "error")
            return render_template("create_order.html", form=form, id=id)

        modality_conflict = list(client.get_documents("orders", {
            "station_aet": modality,
            "examination_date.date": examination_date["date"],
            "is_active": True
        }))
        if utils.check_examination_date_overlapping(examination_date, modality_conflict):
            flash("This modality already booked for this timing", "error")
            APP_LOGGER.info(f"Modality {modality} already booked for {examination_date['date']} at {examination_date['start_time']} - {examination_date['end_time']}")
            return render_template("create_order.html", form=form, id=id)

        ## NO CONFLICTS FOR TIMING EXAMINATION ##
        # New Order Insertion in DB
        new_order = {
            "_id": utils.generate_uuid(),
            "patient_id": str(id),
            "modality": modality.split('_')[0],
            "station_aet": modality,
            "procedure": procedure['name'],
            "note": form.add_note.data,
            "ordering_physician": form.ordering_physician.data,
            "examination_date": examination_date,
            "status": "SCHEDULED",
            "is_active": True,
        }
        sended = client.add_document("orders", new_order)
        if not sended:
            return flask.render_template("create_order.html", form=form, id=id)
        flash("New Order Placed !", "toast")
        APP_LOGGER.info(f"New order {new_order['_id']} placed for patient {id}")
        return flask.redirect(url_for('index'))
    elif request.method == "POST":
        form.procedure.choices = [(procedure['_id'], procedure['name']) for procedure in
                                  client.get_documents('procedures', {
                                      'modality': form.imaging_modality.data.split('_')[0]})]
        flash("Error in form", "error")
    return flask.render_template("create_order.html", form=form, id=id)


@app.route("/workflow/<filter>")
def workflow(filter):
    messages = flask.get_flashed_messages(with_categories=True)
    current_date = datetime.datetime.today().date()
    if filter == "today":
        page_name = "today"
        orders = client.get_documents('orders', {'examination_date.date': str(current_date), 'is_active': True})
    elif filter == "all":
        page_name = "all"
        orders = client.get_documents('orders', {'is_active': True})
    else:
        page_name = "reporting"
        orders = client.get_documents('orders', {'is_active': True, 'status': 'FINISHED'})
    for order in orders:
        patient = client.get_document('patients', {'_id': order['patient_id']})
        order['patient_name'] = patient['name']
        order['patient_surname'] = patient['surname']
    return flask.render_template("workflow.html", orders=orders, curr_date=str(current_date), page_name=f"workflow-{page_name}", flash_msg=messages)


@app.route("/report")
def report():
    # TODO - Implement this page + server logic
    return flask.redirect("/")


@app.route("/get_procedures/<modality>")
def get_procedures(modality):
    modality_name = modality.split('_')[0]
    procedures = client.get_documents("procedures", {"modality": modality_name})
    return jsonify([{"_id": option['_id'], 'name': option['name']} for option in procedures])


@app.route("/remove_order/<order_id>")
def remove_order(order_id):
    # TODO - Add a log message to inform about the order deletion (OMI^O23 HL7 to build)
    deleted_order = client.delete_document("orders", order_id)    # Return a DeleteResult (status + elem deleted)
    if deleted_order.acknowledged and deleted_order.raw_result['n']:
        flash(f"Order {order_id} removed", "toast")
    else:
        flash(f"Error when deleting {order_id} order", "error")
    return flask.redirect("/workflow/all")


@app.route("/create_worklist/<order_id>")
def create_worklist(order_id):
    # Accession Number is simply entire date + time + 2 first ms numbers
    accession_number = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + datetime.datetime.now().strftime("%f")[:2]
    order = client.get_document("orders", {'_id': order_id})
    patient = client.get_document("patients", {'_id': order["patient_id"]})
    address = patient.get('address', {})
    procedure = client.get_document("procedures", {'name': order['procedure']})
    study_uid = generate_uid()
    omi_message = HL7MessageBuilder()
    omi_message.add_segment(
        "MSH|^~\&|OPENRIS|DEBUG HOSPITAL|ORTHANC|DEBUG HOSPITAL|"+datetime.datetime.now().strftime("%Y%m%d")+"||OMI^O23^OMI_O23|"+str(uuid4())+"|D|2.8|\r"
    )
    omi_message.add_segment(
        "PID|1||"+patient['_id']+"^5^M11^ADT1^MR^DEBUG HOSPITAL||"+patient["name"]+"^"+patient["surname"]+"||"+patient.get('dob', '').replace('-', '')+"|"+patient.get('sex', '')+"||"+patient.get('ethnicity', '')+"|"+address.get('address', '').upper()+"^^"+address.get('city', '').upper()+"^"+address.get('province', '').upper()+"^"+address.get('zip-code', '').upper()+"^"+address.get('country', '').upper()+"|"+address.get('county-code', '').upper()+"|"+patient.get('phone_number', '')+"||"+patient.get('language', '').upper()+"|"+patient.get('marital-status', '').upper()+"|"+patient.get('religion', '').upper()+"||"+patient.get('ssn', '')+"||\r"
    )
    omi_message.add_segment(
        "ORC|NW||||SC|\r"
    )
    omi_message.add_segment(
        "OBR||||"+procedure['_id']+"^"+procedure['name']+"||"+order['examination_date']['date'].replace('-', '')+"^"+order['examination_date']['start_time'].replace(':', '')+"|\r"
    )
    omi_message.add_segment(
        "IPC|"+accession_number+"|"+procedure['_id']+"|"+str(study_uid)+"|"+procedure['_id']+"|"+order['modality']+"||||"+order['station_aet']+"|\r"
    )
    hl7_log(omi_message.build(), "OUT")
    resp = requests.post(f"{ORTHANC_SERVER}mwl/create_worklist", data=omi_message.get_message(), headers={"Content-Type": "application/hl7"})
    resp_data = resp.content.decode('utf-8')
    hl7_log(hl7.parse(resp_data), "IN")
    if hl7.parse(resp_data).extract_field("MSA", field_num=1) == "AA":
        client.update_document(
            "orders",
            order_id,
            {
                "status": "GENERATED",
                "study_instance_uid": str(study_uid),
                "accession_number": accession_number,
            }
        )
        flash(f"Worklist {accession_number} created", "toast")
    else:
        flash(f"Error when creating {accession_number} worklist", "error")
    return flask.redirect("/workflow/today")


@app.route('/get_order_info/<order_id>')
def get_order_info(order_id):
    order = client.get_document('orders', {'_id': order_id})
    patient = client.get_document('patients', {'_id': order['patient_id']})
    order['patient_name'] = patient['name']
    order['patient_surname'] = patient['surname']
    order['patient_dob'] = patient['dob']
    return jsonify(order)


@app.route('/new_study_created', methods=['POST'])
def new_study_created():
    data = flask.request.get_json()
    order_to_update = client.get_document("orders", {'accession_number': data['accession-number']})
    client.update_document('orders', order_to_update['_id'], {"status": "IN PROGRESS", "executive-start-time": data["creation-time"]})
    return flask.Response()


@app.route('/stable_study', methods=['POST'])
def stable_study():
    req = flask.request.get_json()
    if not req:
        return flask.Response(status=400)
    else:
        order_to_update = client.get_document("orders", {"accession_number": req['AccessionNumber']})
        client.update_document("orders", order_to_update['_id'], {
            "status": "FINISHED",
            "orthanc_study_id": req["ID"],
            "orthanc_series_id": req["Series"],
            "executive-end-time": req["creation-time"]
        })
        return flask.Response(status=200)


if __name__ == "__main__":
    app.run(debug=True)
