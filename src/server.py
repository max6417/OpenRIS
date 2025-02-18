import flask
import hl7
from flask_material import Material
from utils.checker import *
from utils.MongoDBClient import *
from utils import utils
from elements.forms import *

app = flask.Flask(__name__)
Material(app)
app.config['SECRET_KEY'] = "ADMIN"

client = MongoDBClient()
if "patients" not in client.list_databases():
    print("no database")


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


@app.route("/create_new_order", methods=["GET"])
def create_new_order():
    form = Order()
    return flask.render_template("index.html", title="Create Order", canvas= form)


