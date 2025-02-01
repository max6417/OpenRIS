import flask
import hl7
from utils.checker import *
from utils.MongoDBClient import *

app = flask.Flask(__name__)

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
    return flask.Response(str(message.create_ack("AA")), mimetype='text/hl7')
