import flask
import hl7_code
from flask import request, render_template, url_for, flash, jsonify
from flask_material import Material
from utils.checker import *
from utils.MongoDBClient import *
from utils import utils
from elements.Forms import *
from pydicom.uid import UID
import pyorthanc
import requests


ORTHANC_SERVER = "http://localhost:8042/"


app = flask.Flask(__name__, static_folder="js")
Material(app)
app.config['SECRET_KEY'] = "ADMIN"
app.config['TEMPLATES_AUTO_RELOAD'] = True


client = MongoDBClient.MongoDBClient()

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
        # TODO - Maybe add a flash message ??
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
                'referring_physician': PatientDemForm.patient_referring_physician.data.upper()
            }
        )
        return flask.redirect("/patients")
    elif request.method == "POST":
        # TODO - Logic if form not correct
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
        PatientDemForm.patient_referring_physician.data = patient.get('referring_physician', '')
        return flask.render_template("patient-editor.html", form=PatientDemForm, id=patient.get('_id', -1))

# TODO - Modify the HL7 getter section
@app.route("/receive-hl7", methods=['GET'])
def receive_hl7_message():
    message = flask.request.get_data()
    message = hl7_code.parse(message)
    # Routing the message type of the hl7_code request in order to check it
    correct = Checker().check_message_type(message)
    if correct:
        # patient already store in DB
        if client.get_document("patients", {"_id": message.extract_field("PID", field_num=3, repeat_num=1, component_num=1, subcomponent_num=1)}) != None:
            client.update_document("patients_stat", message.extract_field("PID", field_num=3, repeat_num=1, component_num=1, subcomponent_num=1), utils.extract_status_information(message, "ADM"))
        else:
            patient_information = utils.extract_patient_information(message)
        # Save in DB
            client.add_document("patients", patient_information)
            client.add_document("patient_status", utils.extract_status_information(message, "ADM"))
            return flask.Response(str(message.create_ack("AA")), mimetype="text/hl7_code")
    else:
        return flask.Response(str(message.create_ack("AE")), mimetype='text/hl7_code')


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
            flash("Patient have already an examination at this time", "error")
            return render_template("create_order.html", form=form, id=id)

        modality_conflict = list(client.get_documents("orders", {
            "station_aet": modality,
            "examination_date.date": examination_date["date"],
            "is_active": True
        }))
        if utils.check_examination_date_overlapping(examination_date, modality_conflict):
            flash("This modality already booked for this timing", "error")
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
    if filter == "today":
        current_date = datetime.datetime.today().date()
        orders = client.get_documents('orders', {'examination_date.date': str(current_date), 'is_active': True})
        for order in orders:
            patient = client.get_document('patients', {'_id': order['patient_id']})
            order['patient_name'] = patient['name']
            order['patient_surname'] = patient['surname']
        return flask.render_template("workflow.html", orders=orders, page_name='workflow-today', can_worklist=True, flash_msg=messages)
    elif filter == "all":
        orders = client.get_documents('orders', {'is_active': True})
        for order in orders:
            patient = client.get_document('patients', {'_id': order['patient_id']})
            order['patient_name'] = patient['name']
            order['patient_surname'] = patient['surname']
        return flask.render_template("workflow.html", orders=orders, page_name='workflow-all', can_worklist=False, flash_msg=messages)
    else:
        pass
    return flask.redirect("/")


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
    # TODO - Maybe use find_one_and_delete to get the deleted document from DB
    deleted_order = client.delete_document("orders", order_id)    # Return a DeleteResult (status + elem deleted)
    if deleted_order.acknowledged and deleted_order.raw_result['n']:
        flash(f"Order {order_id} removed", "toast")
    else:
        flash(f"Error when deleting {order_id} order", "error")
    return flask.redirect("/workflow/all")


@app.route("/create_worklist/<order_id>")
def create_worklist(order_id):
    # TODO : create the element to be sent in orthanc python script!
    # Accession Number is simply entire date + time + 2 first ms numbers
    accession_number = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + datetime.datetime.now().strftime("%f")[:2]
    order = client.get_document("orders", {'_id': order_id})
    patient = client.get_document("patients", {'_id': order["patient_id"]})
    procedure = client.get_document("procedures", {'name': order['procedure']})
    data = {
        "_id": order['_id'],
        "patient_name": patient["name"],
        "patient_surname": patient["surname"],
        "patient_id": order["patient_id"],
        "patient_dob": patient["dob"],
        "patient_sex": patient["sex"],
        "procedure_name": "^".join(order["procedure"].split(" ")),
        "procedure_id": procedure['_id'],
        "modality": order["modality"],
        "modality_station_ae": order["station_aet"],
        "examination_date": order["examination_date"],
        "performing_physician_name": "DEBUG",
        "performing_physician_surname": "PHYSICIAN",
        "accession_number": accession_number
    }
    resp = requests.post(f"{ORTHANC_SERVER}mwl/create_worklist", json=data, headers={"Content-Type": "application/json"})
    client.update_document(
        "orders",
        order_id,
        {
            "status": "GENERATED",
            "study_instance_uid": UID(resp.content.decode()),
            "accession_number": accession_number,
        }
    )
    return flask.redirect("/workflow/today")

@app.route('/get_order_info/<order_id>')
def get_order_info(order_id):
    order = client.get_document('orders', {'_id': order_id})
    patient = client.get_document('patients', {'_id': order['patient_id']})
    order['patient_name'] = patient['name']
    order['patient_surname'] = patient['surname']
    order['patient_dob'] = patient['dob']
    return jsonify(order)


@app.route('/new_study_created/<accession_number>', methods=['POST'])
def new_study_created(accession_number):
    order_to_update = client.get_document("orders", {'accession_number': accession_number})
    client.update_document('orders', order_to_update['_id'], {"status": "IN PROGRESS"})
    return flask.Response()


@app.route('/stable_study', methods=['POST'])
def stable_study():
    # TODO - Implement the server logic behind this
    req = flask.request.get_json()
    if not req:
        return flask.Response(status=400)
    else:
        order_to_update = client.get_document("orders", {"accession_number": req['AccessionNumber']})
        client.update_document("orders", order_to_update['_id'], {
            "status": "FINISHED",
            "orthanc_study_id": req["ID"],
            "orthanc_series_id": req["Series"]
        })
        return flask.Response(status=200)


if __name__ == "__main__":
    app.run(debug=True)
