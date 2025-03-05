import flask
import hl7
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_material import Material
from utils.checker import *
from utils.MongoDBClient import *
from utils import utils
from elements.forms import *

app = flask.Flask(__name__)
Material(app)
app.config['SECRET_KEY'] = "ADMIN"

client = MongoDBClient.MongoDBClient()


@app.route("/")
def test_hello_world():
    return flask.render_template("index.html", title="Page Fixe", message="Yo!")


@app.route("/receive", methods=['GET'])
def receive_hl7_message():
    message = flask.request.get_data()
    message = hl7.parse(message)
    # Routing the message type of the hl7 request in order to check it
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
            return flask.Response(str(message.create_ack("AA")), mimetype="text/hl7")
    else:
        return flask.Response(str(message.create_ack("AE")), mimetype='text/hl7')


@app.route("/create_new_order", methods=["GET", "POST"])
def create_new_order():
    form = Order()
    duration = 20
    if form.validate_on_submit():
        patient = client.get_document("patients", {'name': form.patient_name.data, 'surname': form.patient_surname.data, 'dob': str(form.patient_dob.data)})
        modality = form.choices[int(form.imaging_modality.data) - 1][1]
        examination_date = {
            "date": str(form.examination_date.date.data),
            "start_time": (datetime.datetime.strptime(str(form.examination_date.timing.data), "%H:%M:%S")).strftime("%H:%M:%S"),
            "end_time": (datetime.datetime.strptime(str(form.examination_date.timing.data), "%H:%M:%S") + datetime.timedelta(minutes=duration)).strftime("%H:%M:%S")
        }
        ## TIMING CONFLICT DETECTION ##
        patient_conflict = list(client.get_documents("orders", {
            "patient_id": str(patient["_id"]),
            "examination_date.date": examination_date["date"],
            "is_active": True
        }))
        print(patient_conflict)
        if utils.check_examination_date_overlapping(examination_date, patient_conflict):
            flash("Patient have already an examination at this time", "error")
            return render_template("create_order.html", form=form)

        modality_conflict = list(client.get_documents("orders", {
            "modality": modality,
            "examination_date.date": examination_date["date"],
            "is_active": True
        }))
        if utils.check_examination_date_overlapping(examination_date, modality_conflict):
            flash("This modality already booked for this timing", "error")
            return render_template("create_order.html", form=form)

        ## NO CONFLICTS FOR TIMING EXAMINATION ##
        # New Order Insertion in DB
        new_order = {
            "_id": utils.generate_id(),
            "patient_id": str(patient["_id"]),
            "modality": modality,
            "exam_type": form.exam_type.data,
            "note": form.add_note.data,
            "ordering_physician": form.ordering_physician.data,
            "examination_date": examination_date,
            "is_active": True,
        }
        sended = client.add_document("orders", new_order)
        if not sended:
            return flask.render_template("create_order.html", form=form)
        flash("New Order Placed !", "toast")
        # Treat the order and maybe redirecting to workflow page -> TODO
    return flask.render_template("create_order.html", form=form)
