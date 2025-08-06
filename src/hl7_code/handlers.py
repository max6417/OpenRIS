"""
The file contains all the code to handle HL7 message received from the HIS. Can be extended to extract more information.
Currently, it only contains basic handlers selecting essential information to let the RIS working by itself including
    - Take new order
    - Take patient information + modification
It is encouraged to extend this file to handle more message and information in order to fit the radiology workflow of any
institution
"""
import datetime
from uuid import uuid4
import hl7
from src.hl7_code.message_validators import extract_information
from src.utils.MongoDBClient import MongoDBClient



def handle_adta01(message: hl7.Message, client: MongoDBClient) -> bool | None:
    """
    Handle an ADT^A01 message, basically carrying the same information as ADT^A04
    """
    return handle_adta04(message, client)

def handle_adta04(message: hl7.Message, client: MongoDBClient) -> bool | None:
    """
    Handle an ADT^A04 (register a new patient in the system) message to extract all the patient information (Name, Surname, ID, etc.). Can be extended to
    extract more information.
    """
    if message.extract_field("MSH", field_num=5) != "OPENRIS":
        return None
    patient_id = message.extract_field("PID", field_num=3)
    if client.get_document('patients', {'_id': patient_id}) is not None:
        return True

    new_patient = {
        '_id': patient_id,
        'name': extract_information(message, "PID", field_num=5, component_num=1) if extract_information(message, "PID",
                                                                                                         field_num=5,
                                                                                                         component_num=1) else "",
        'surname': extract_information(message, "PID", field_num=5, component_num=2) if extract_information(message,
                                                                                                            "PID",
                                                                                                            field_num=5,
                                                                                                            component_num=2) else "",
        'dob': f"{extract_information(message, "PID", field_num=7)[:4]}-{extract_information(message, "PID", field_num=7)[4:6]}-{extract_information(message, "PID", field_num=7)[6:8]}" if extract_information(
            message, "PID", field_num=7) else "",
        'sex': extract_information(message, "PID", field_num=8) if extract_information(message, "PID",
                                                                                       field_num=8) else "U",
        'phone_number': extract_information(message, "PID", field_num=13) if extract_information(message, "PID",
                                                                                                 field_num=13) else "",
        'email': extract_information(message, "PID", field_num=14) if extract_information(message, "PID",
                                                                                          field_num=14) else "",
        'address': {
            'address': extract_information(message, "PID", field_num=11, component_num=1) if extract_information(
                message, "PID", field_num=11, component_num=1) else "",
            'complement': extract_information(message, "PID", field_num=11, component_num=2) if extract_information(
                message, "PID", field_num=11, component_num=2) else "",
            'city': extract_information(message, "PID", field_num=11, component_num=3) if extract_information(message,
                                                                                                              "PID",
                                                                                                              field_num=11,
                                                                                                              component_num=3) else "",
            'zip_code': extract_information(message, "PID", field_num=11, component_num=5) if extract_information(
                message, "PID", field_num=11, component_num=5) else "",
            'country': extract_information(message, "PID", field_num=11, component_num=6) if extract_information(
                message, "PID", field_num=11, component_num=6) else "",
        },
        'referring_physician': {
            '_id': extract_information(message, "PV1", field_num=8, component_num=1) if extract_information(message,
                                                                                                            "PV1",
                                                                                                            field_num=8,
                                                                                                            component_num=1) else "",
            'name': extract_information(message, "PV1", field_num=8, component_num=2) if extract_information(message,
                                                                                                             "PV1",
                                                                                                             field_num=8,
                                                                                                             component_num=2) else "",
            'surname': extract_information(message, "PV1", field_num=8, component_num=3) if extract_information(message,
                                                                                                                "PV1",
                                                                                                                field_num=8,
                                                                                                                component_num=3) else ""
        }
    }
    client.add_document('patients', new_patient)
    return True


def handle_adta08(message: hl7.Message, client: MongoDBClient) -> bool | None:
    """
    Handle an ADT^A08 (change patient information) message
    """
    try:
        if message.extract_field("MSH", field_num=5) != "OPENRIS":
            return None
        patient_id = message.extract_field("PID", field_num=3)
        patient_to_update = client.get_document('patients', {'_id': patient_id})
        dob = extract_information(message, "PID", field_num=7)
        client.update_document(
            'patients',
            patient_id,
            {
                'name': extract_information(message, "PID", field_num=5, component_num=1) if extract_information(
                    message, "PID", field_num=5, component_num=1) else patient_to_update['name'],
                'surname': extract_information(message, "PID", field_num=5, component_num=2) if extract_information(
                    message, "PID", field_num=5, component_num=2) else patient_to_update['surname'],
                'dob': f"{dob[0:4]}-{dob[4:6]}-{dob[6:8]}" if dob else patient_to_update['dob'],
                'sex': extract_information(message, "PID", field_num=8) if extract_information(message, "PID",
                                                                                               field_num=8) else patient_to_update['sex'],
                'phone_number': extract_information(message, "PID", field_num=13) if extract_information(message,
                                                                                                         "PID", field_num=13) else patient_to_update['phone_number'],
                'address': {
                    'address': extract_information(message, "PID", field_num=11, component_num=1).upper() if extract_information(
                        message, "PID", field_num=11, component_num=1) else patient_to_update['address']['address'],
                    'zip_code': extract_information(message, "PID", field_num=11, component_num=5) if extract_information(message, "PID", field_num=11, component_num=5) else patient_to_update['address']['zip_code'],
                    'city': extract_information(message, "PID", field_num=11, component_num=3).upper() if extract_information(message, "PID", field_num=11, component_num=3) else patient_to_update['address']['city'],
                    'country': extract_information(message, "PID", field_num=11, component_num=6).upper() if extract_information(message, "PID", field_num=11, component_num=6) else patient_to_update['address']['country'],
                },
                'referring_physician': {
                    '_id': extract_information(message, "PV1", field_num=8, component_num=1) if extract_information(message, "PV1", field_num=8, component_num=1) else patient_to_update['referring_physician']['_id'],
                    'name': extract_information(message, "PV1", field_num=8, component_num=2).upper() if extract_information(message, "PV1", field_num=8, component_num=2) else patient_to_update['referring_physician']['name'],
                    'surname': extract_information(message, "PV1", field_num=8, component_num=3).upper() if extract_information(message, "PV1", field_num=8, component_num=3) else patient_to_update['referring_physician']['surname']
                }
            }
        )
        return True
    except Exception as e:
        return False


def handle_omio23(message: hl7.Message, client: MongoDBClient):
    pass

def handle_orm_o01(message: hl7.Message, client: MongoDBClient) -> bool | None:
    """
    Handle an ORM^O01 (order management) message. Information checked :
        - procedure ID in OBX segment to verify the existence of the requesting procedure
        - patient ID in PID to verify the existence of the requesting patient
        - Control the Order Number and Placer ID because it indicates an order already placed or change the placer ID
    With its communication the HIS can only : add a new order, communicate a placer number if the order come from RIS,
    cancel an order.
    """
    match extract_information(message, "ORC", field_num=1):
        case "NW":
            patient = client.get_document('patients', {'_id': extract_information(message, "PID", field_num=3)})
            procedure = client.get_document('procedures', {'_id': extract_information(message, "OBR", field_num=4, component_num=1)})
            if patient is None or procedure is None:
                return False

            # Order Creation
            new_order = {
                '_id': str(uuid4()),
                'placer_id': extract_information(message, "ORC", field_num=2),
                'patient_id': patient['_id'],
                'placer_physician': {
                    '_id': extract_information(message, "ORC", field_num=10, component_num=1),
                    'name': extract_information(message, "ORC", field_num=10, component_num=2).upper(),
                    'surname': extract_information(message, "ORC", field_num=10, component_num=3).upper(),
                },
                'examination_date': {
                    'date': datetime.datetime.now().strftime('%Y-%m-%d'),
                    'start_time': '00:00',
                    'end_time': '00:00',
                },
                'modality': procedure['modality'],
                'procedure': procedure['name'],
                'note': extract_information(message, "OBR", field_num=13),
                'status': "UNSCHEDULED",
                'is_active': True,
            }
            client.add_document('orders', new_order)
            return True

        case "CA":
            res = client.delete_document('orders', extract_information(message, "ORC", field_num=3))
            if res is None:
                return False
            else:
                return True
        case "SN":
            order = client.get_document('orders', {'_id': extract_information(message, "ORC", field_num=3)})
            if order is None:
                return False
            else:
                _ = client.update_document(
                    'orders',
                    order['_id'],
                    {'placer-id': extract_information(message, "ORC", field_num=2)}
                )
                return True
        case _:
            return False