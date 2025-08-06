import flask
from pydicom.uid import generate_uid

import src.hl7_code.handlers as handlers
from pymongo.errors import WriteError

from flask import request, flash, jsonify, make_response, Response
from flask_material import Material

from src.hl7_code.message_constructor import construct_adt_a08, construct_omi_023, construct_orm_o01, \
    construct_oru_r01
from src.utils.utils import generate_uuid
from utils import utils
from elements.Forms import *
from hl7_code.message_validators import *
from src.NER.NER import *
import pyorthanc
import requests
import src.log as log

import config
from utils.scheduler import *

# TODO : Write the GIT page + function static + documentation + test the code
# TODO : Publish the code in public + choose a license Open Source

ner_model = NERModel()
hl7_logger = log.HL7LogHandler()
app_logger = log.AppLogHandler()


app = flask.Flask(__name__, static_folder="js")
Material(app)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True


client = MongoDBClient()
scheduler = Scheduler(config.D_RANGE, datetime.datetime.strptime(config.SHIFT_START, "%H:%M").time(), datetime.datetime.strptime(config.SHIFT_END, "%H:%M").time())

pattern_val = PatternValidator(config.MESSAGE_HL7_DIR, config.SEGMENT_HL7_DIR)


orthanc_client = pyorthanc.Orthanc(config.ORTHANC_SERVER)    # Connect to Orthanc service from RIS to enable communication
if not orthanc_client:
    app_logger.add_error_log("Orthanc server not available")
modalities = orthanc_client.get_modalities()


def send_hl7(message: hl7.Message) -> bool:
    """
    Contains the logic to send HL7 messages to others applications except Orthanc which has a specific route

    Currently, there isn't any logic here and this function should change later, all the messages are logged in order
    to simulate the sending except for the OMI message to Orthanc which is really sent
    """
    hl7_logger.add_log("OUT", str(message))
    if message.extract_field("MSH", field_num=9, component_num=1) == "OMI" and message.extract_field("MSH", field_num=5) == config.ORTHANC_AET:
        resp = requests.post(
            f"{config.ORTHANC_SERVER}/mwl/create_worklist",
            data=str(message),
            headers={"Content-Type": "application/hl7"}
        )
        resp_data = resp.content.decode("utf-8")
        hl7_logger.add_log("IN", str(hl7.parse(resp_data)))
        if hl7.parse(resp_data).extract_field("MSA", field_num=1) == "AA":
            return True
        else:
            return False
    return True

@app.route("/")
def index():
    app_logger.add_info_log("Application launched")
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
    patient = client.get_document('patients', {'_id': id})
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
        patient = client.get_document("patients", {"_id": id})
        # Creating HL7 ADT^A08 message
        send_hl7(construct_adt_a08(patient, date, generate_uuid()))
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
            valid = ADTA01Validator().validate_and_ack(message, pattern_val, config.INSTITUTION_NAME, "OPENRIS")
            hl7_logger.add_log("IN", str(valid))
            if extract_information(valid, "MSA", field_num=1) == "AA":
                success = handlers.handle_adta01(message, client)
                if success:
                    hl7_logger.add_log("OUT", str(valid))
                    return make_response(jsonify({"ack": valid}), 200)
                else:
                    return flask.Response(status=200)    # Not destined for RIS
            else:
                hl7_logger.add_log("OUT", str(valid))
                return make_response(jsonify({"ack": valid}), 400)
        case"ADT_A04":
            valid = ADTA04Validator().validate_and_ack(message, pattern_val, config.INSTITUTION_NAME, "OPENRIS")
            hl7_logger.add_log("IN", str(message))
            if extract_information(valid, "MSA", field_num=1) == "AA":
                success = handlers.handle_adta04(message, client)
                if success:
                    hl7_logger.add_log("OUT", str(valid))
                    return make_response(jsonify({"ack": str(valid)}), 200)
                else:
                    return flask.Response(status=200)    # Not destined for the RIS
            else:
                hl7_logger.add_log("OUT", str(valid))
                return make_response(jsonify({"ack": str(valid)}), 400)
        case "ADT_A08":
            valid = ADTA08Validator().validate_and_ack(message, pattern_val, config.INSTITUTION_NAME, "OPENRIS")
            hl7_logger.add_log("IN", str(message))
            if extract_information(valid, "MSA", field_num=1) == "AA":
                success = handlers.handle_adta08(message, client)
                if success:
                    hl7_logger.add_log("OUT", str(valid))
                    return make_response(jsonify({"ack": str(valid)}), 200)
                else:
                    return flask.Response(status=200)
            else:
                hl7_logger.add_log("OUT", str(valid))
                return make_response(jsonify({"ack": str(valid)}), 400)
        case "ORM_O01":
            valid = ORMO01Validator().validate_and_ack(message, pattern_val, config.INSTITUTION_NAME, "OPENRIS")
            hl7_logger.add_log("IN", str(message))
            if extract_information(valid, "MSA", field_num=1) == "AA":
                success = handlers.handle_orm_o01(message, client)
                if success:
                    hl7_logger.add_log("OUT", str(valid))
                    return make_response(jsonify({"ack": str(valid)}), 200)
                else:
                    valid = message.create_ack("AR", message_id=str(generate_uuid()), facility=config.INSTITUTION_NAME, application="OPENRIS")
                    hl7_logger.add_log("OUT", str(valid))
                    return make_response(jsonify({"ack": str(valid)}), 400)
        case _:
            hl7_logger.add_log("IN", str(message))
            valid = message.create_ack("AR", generate_uuid(), config.INSTITUTION_NAME, "OPENRIS")
            hl7_logger.add_log("OUT", str(valid))
            app_logger.add_error_log(f"Uncaught HL7 message: {message}")
            return make_response(jsonify({"ack": str(valid)}), 400)


@app.route('/schedule/<patient_id>/<proc_id>', methods=['GET'])
def schedule(patient_id, proc_id):
    procedure = client.get_document('procedures', {'_id': proc_id})
    possible_scheduling = scheduler.get_possible_schedules(int(procedure["duration"]), patient_id, [station for station in modalities if station.startswith(procedure["modality"])], client)
    slots = list()
    for possible_slot in possible_scheduling:
        slot_id = possible_slot[1].date.strftime("%Y-%m-%d")+"|"+possible_slot[1].start_t.strftime("%H:%M")+"|"+possible_slot[1].end_t.strftime("%H:%M")+"|"+possible_slot[0]
        slot_display = possible_slot[1].date.strftime("%Y-%m-%d")+" "+possible_slot[1].start_t.strftime("%H:%M")+" - "+possible_slot[1].end_t.strftime("%H:%M")
        slots.append(
            {
                "id": slot_id,
                "elem": slot_display
            }
        )
    return slots


@app.route("/schedule_order/<id>", methods=['POST'])
def schedule_new_order(id):
    order = client.get_document('orders', {'_id': id})
    patient = client.get_document('patients', {'_id': order['patient_id']})
    procedure = client.get_document('procedures', {'name': order['procedure']})
    date = request.form["slots"].split('|')
    order["examination_date"] = {
        "date": date[0],
        "start_time": date[1],
        "end_time": date[2],
    }
    order["status"] = "SCHEDULED"
    order["station_aet"] = date[3]
    if send_hl7(construct_orm_o01(order, procedure, patient, generate_uuid(), datetime.datetime.now().strftime("%Y%m%d"), "SC", "SC")):
        client.update_document(
            'orders',
            id,
            {
                "status": "SCHEDULED",
                "station_aet": date[3],
                "examination_date": {
                    "date": date[0],
                    "start_time": date[1],
                    "end_time": date[2],
                }
            }
        )
        app_logger.add_info_log(f"HIS successfully gets the scheduling of order {id}")
        flash(f"Order {id} has been successfully scheduled!", "toast")
    else:
        app_logger.add_error_log(f"HIS failed to get the scheduling of order {id}")
        flash(f"Order {id} failed to be scheduled!", "toast")
    return flask.redirect("/")


@app.route("/get_available_slots/<order_id>", methods=['GET'])
def get_available_slots(order_id):
    order = client.get_document('orders', {'_id': order_id})
    procedure = client.get_document('procedures', {'name': order["procedure"]})
    slots = scheduler.get_possible_schedules(procedure["duration"], order["patient_id"], [station for station in modalities if station.startswith(procedure["modality"])], client)
    res = list()
    for slot in slots:
        slot_id = slot[1].date.strftime("%Y-%m-%d") + "|" + slot[1].start_t.strftime("%H:%M") + "|" + \
                  slot[1].end_t.strftime("%H:%M") + "|" + slot[0]
        slot_display = slot[1].date.strftime("%Y-%m-%d") + " " + slot[1].start_t.strftime(
            "%H:%M") + " - " + slot[1].end_t.strftime("%H:%M")
        res.append(
            {
                "id": slot_id,
                "elem": slot_display
            }
        )
    return res


@app.route("/register_new_order/<patient_id>", methods=['GET', 'POST'])
def register_new_order(patient_id):
    order_form = Order()
    patient = client.get_document('patients', {'_id': patient_id})
    order_form.procedure.choices = [(procedure['_id'], procedure['name']) for procedure in client.get_documents('procedures', {'modality': order_form.imaging_modality.choices[0][1]})]
    date = datetime.datetime.now().strftime("%Y%m%d")
    if request.method == 'POST' and order_form.validate():
        procedure = client.get_document('procedures', {'_id': order_form.procedure.data})
        modality = order_form.imaging_modality.data
        parsed_date = order_form.slots.data.split("|")
        examination_date = {
            "date": str(parsed_date[0]),
            "start_time": str(parsed_date[1]),
            "end_time": str(parsed_date[2])
        }

        new_order = {
            "_id": utils.generate_uuid(),
            "patient_id": patient["_id"],
            "placer_physician": {
                "_id": str(order_form.ordering_physician_identifier.data),
                "name": str(order_form.ordering_physician_name.data).upper(),
                "surname": str(order_form.ordering_physician_surname.data).upper(),
                "department": str(order_form.placer_department.data).upper(),
            },
            "modality": modality,
            "station_aet": parsed_date[3],
            "procedure": procedure['name'],
            "note": order_form.add_note.data,
            "examination_date": examination_date,
            "status": "SCHEDULED",
            "is_active": True,
        }
        if send_hl7(construct_orm_o01(new_order, procedure, patient, generate_uuid(), datetime.datetime.now().strftime("%Y%m%d"), "NW", "")):
            client.add_document('orders', new_order)
            flash("New order registered!", "toast")
            app_logger.add_info_log(f"New order {new_order['_id']} registered!")
            return flask.redirect("/")
        else:
            flash("Failed to register the newest order!", "error")
            app_logger.add_error_log(f"Failed to register order {new_order['_id']}")
            return flask.redirect("/register_new_order/"+str(patient_id))
    elif request.method == 'GET':
        return flask.render_template("create_order.html", form=order_form, id=patient_id, p_name=patient["name"], p_surname=patient["surname"], flash_msg=flask.get_flashed_messages(with_categories=True))
    else:
        order_form.procedure.choices = [(procedure['_id'], procedure['name']) for procedure in
                                  client.get_documents('procedures', {
                                      'modality': order_form.imaging_modality.data.split('_')[0]})]
        flash("Error in Form", "error")
        return flask.redirect("/register_new_order/"+str(patient_id))

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


@app.route("/search-reports", methods=["GET", "POST"])
def report():
    searching_form = SearchSpecificReport()
    if request.method == "POST" and searching_form.validate():
        if searching_form.observation.data:
            reports = client.get_documents('reports', {
                "labels." + str(searching_form.section_find.data): {
                    "$elemMatch": {
                        "observation": searching_form.observation.data.lower(),
                        "tags": searching_form.select_presence.data
                    }
                }
            })

            return flask.render_template("reports.html", reports=reports, search_form=searching_form)
    reports = client.get_documents('reports', {})
    searching_form.observation.data = ""
    return flask.render_template("reports.html", reports=reports, search_form=searching_form)


@app.route("/create-report/<id>", methods=["GET", "POST"])
def create_report(id):
    order = client.get_document('orders', {'_id': id})
    patient = client.get_document('patients', {'_id': order['patient_id']})
    procedure = client.get_document('procedures', {'name': order['procedure']})
    info = {
        'patient': patient,
        'order' : order
    }
    form = NewReport()

    if request.method == 'POST' and form.validate():
        processed_impressions = ner_model.process_data(form.impressions.data)
        processed_findings = ner_model.process_data(form.findings.data)
        label = dict()
        label['findings'] = list()
        label['impressions'] = list()
        for item in processed_impressions[0]:
            label['impressions'].append(item)
        for item in processed_findings[0]:
            label['findings'].append(item)
        client.add_document('reports', {
            '_id': utils.generate_uuid(),
            'order_id': order['_id'],
            'patient_id': patient['_id'],
            'labels': label,
            'impressions-text': processed_impressions[1]['radgraph_text'],
            'findings-text': processed_findings[1]['radgraph_text'],
            'impressions-annotations': processed_impressions[1]['radgraph_annotations'],
            'findings-annotations': processed_findings[1]['radgraph_annotations'],
            'recommendations': form.recommendations.data,
            'date': datetime.datetime.today().date().strftime("%Y-%m-%d"),
            'time': datetime.datetime.now().strftime("%H:%M"),
            'radiologist': {
                'name': form.name.data.upper(),
                'surname': form.surname.data.upper(),
            }
        })
        client.update_document('orders', order['_id'], {'is_active': False})
        report = client.get_document('reports', {'order_id': order['_id']})
        _ = send_hl7(construct_oru_r01(report, procedure, order, patient, generate_uuid(), datetime.datetime.today().date().strftime("%Y%m%d")))
        flash(f"Report Created for {order['_id']}", 'toast')
        return flask.redirect("/")
    elif request.method == 'GET':
        return flask.render_template("report.html", info=info, form=form, flash_msg=flask.get_flashed_messages(with_categories=True))
    else:
        flash("Error in report Form", "error")
        return flask.redirect("/")


@app.route("/view-report/<patient_id>/<order_id>")
def view_report(patient_id, order_id):
    report = client.get_document('reports', {"patient_id": patient_id, "order_id": order_id})
    patient = client.get_document('patients', {"_id": patient_id})
    order = client.get_document('orders', {"_id": order_id})
    return flask.render_template("report_viewer.html", info={"patient": patient, "order": order, "report": report}, flash_msg=flask.get_flashed_messages(with_categories=True))


@app.route("/get_procedures/<modality>")
def get_procedures(modality):
    modality_name = modality.split('_')[0]
    procedures = client.get_documents("procedures", {"modality": modality_name})
    return jsonify([{"_id": option['_id'], 'name': option['name']} for option in procedures])


@app.route("/remove_order/<order_id>")
def remove_order(order_id):
    old_order = client.get_document('orders', {'_id': order_id})
    procedure = client.get_document('procedures', {'name': old_order['procedure']})
    patient = client.get_document('patients', {'_id': old_order['patient_id']})
    deleted_order = client.delete_document("orders", order_id)    # Return a DeleteResult (status + elem deleted)
    if deleted_order.acknowledged and deleted_order.raw_result['n']:
        stat = send_hl7(construct_orm_o01(old_order, procedure, patient, generate_uuid(), datetime.datetime.today().date().strftime("%Y%m%d"), "OC", "CA"))
        if stat:
            app_logger.add_info_log(f"Message successfully sent to HIS")
        else:
            app_logger.add_error_log(f"Message failed to sent to HIS")
        flash(f"Order {order_id} removed", "toast")
    else:
        app.logger.error(f"Error when deleting {order_id} order")
        flash(f"Error when deleting {order_id} order", "error")
    return flask.redirect("/workflow/all")


@app.route("/create_worklist/<order_id>")
def create_worklist(order_id):
    # Accession Number is simply entire date + time + 2 first ms numbers
    accession_number = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + datetime.datetime.now().strftime("%f")[:2]
    order = client.get_document("orders", {'_id': order_id})
    patient = client.get_document("patients", {'_id': order["patient_id"]})
    procedure = client.get_document("procedures", {'name': order['procedure']})
    study_uid = generate_uid()
    omi_msg = construct_omi_023(patient, procedure, order, str(generate_uuid()), accession_number, datetime.datetime.now().strftime("%Y%m%d"), study_uid)
    if send_hl7(omi_msg):
        client.update_document(
            'orders',
            order_id,
            {
                "status": "GENERATED",
                "study_instance_uid": study_uid,
                "accession_number": accession_number,
            }
        )
        app_logger.add_info_log(f"Worklist with accession number {accession_number} created")
        flash(f"Worklist {accession_number} created", "toast")
    else:
        app_logger.add_error_log(f"Error when creating sending order {order_id} to create worklist")
        flash(f"Error when creating worklist {accession_number}", "error")
    return flask.redirect("/workflow/today")


@app.route("/new_study", methods=["POST"])
def new_study():
    data = request.get_json()
    order_to_update = client.get_document("orders", {"accession_number": data["accession-number"]})
    client.update_document("orders", order_to_update['_id'], {"status": "IN PROGRESS", "executive-start-time": data["creation-time"]})
    return flask.Response(status=200)


@app.route("/stable_study", methods=["POST"])
def stable_study():
    data = request.get_json()
    if not data:
        return flask.Response(status=400)
    else:
        order_to_update = client.get_document("orders", {"accession_number": data["accession-number"]})
        procedure = client.get_document("procedures", {"name": order_to_update["procedure"]})
        patient = client.get_document("patients", {"_id": order_to_update["patient_id"]})
        client.update_document("orders", order_to_update['_id'], {
            "status": "FINISHED",
            "orthanc_study_id": data["ID"],
            "orthanc_series_id": data["Series"],
            "executive-end-time": data["creation-time"],
        })
        _ = send_hl7(construct_orm_o01(order_to_update, procedure, patient, generate_uuid(), datetime.datetime.today().date().strftime("%Y%m%d"), "SC", "CM"))
        return flask.Response(status=200)

@app.route('/get_order_info/<order_id>')
def get_order_info(order_id):
    order = client.get_document('orders', {'_id': order_id})
    patient = client.get_document('patients', {'_id': order['patient_id']})
    order['patient_name'] = patient['name']
    order['patient_surname'] = patient['surname']
    order['patient_dob'] = patient['dob']
    return jsonify(order)


@app.route('/new_procedure', methods=['GET', 'POST'])
def new_procedure():
    procedure_form = NewProcedureForm()
    if request.method == 'POST' and procedure_form.validate():
        new_proc = {
            '_id': procedure_form.procedure_id.data,
            'name': procedure_form.procedure_name.data.upper(),
            'modality': procedure_form.procedure_modality.data,
            'duration': int(procedure_form.procedure_duration.data)
        }
        # Check if the procedure is already in the system
        try:
            client.add_document("procedures", new_proc)
            flash("New procedure added", "toast")
            return flask.redirect("/")
        except WriteError:
            flash(f"Procedure {new_proc['name']} cannot be added", "error")
            app.logger.error(f"Procedure {new_proc['name']} already exists in DB")
            return flask.redirect("/new_procedure")
    elif request.method == 'GET':
        return flask.render_template('new_procedure.html', page_name='new_proc', form=procedure_form, flash_msg=flask.get_flashed_messages(with_categories=True))
    else:
        flash("Error in form", "error")
        return flask.redirect("/new_procedure")


@app.route("/view_series/<serie_id>")
def view_series(serie_id):
    return {
        "url": config.ORTHANC_SERVER+"web-viewer/app/viewer.html?series="+serie_id
    }


if __name__ == "__main__":
    app.run(debug=True)
