# Generator of IDs
import uuid


def generate_id():
    return str(uuid.uuid4())


def check_examination_date_overlapping(current_examination_date, examination_dates):
    if len(examination_dates) == 0:
        return False
    for examination in examination_dates:
        if current_examination_date["start_time"] <= examination["examination_date"]["start_time"] and current_examination_date["end_time"] >= examination["examination_date"]["start_time"]:
            return True
        if current_examination_date["start_time"] <= examination["examination_date"]["end_time"] and current_examination_date["end_time"] >= examination["examination_date"]["end_time"]:
            return True
    return False    # There is no conflicts


def extract_patient_information(parsed_message):
    return {
        "_id": parsed_message.extract_field("PID", field_num=3, repeat_num=1, component_num=1, subcomponent_num=1),
        "name": parsed_message.extract_field("PID", field_num=5, repeat_num=1, component_num=1, subcomponent_num=1),
        "surname": parsed_message.extract_field("PID", field_num=5, repeat_num=1, component_num=2, subcomponent_num=1),
        "dob": parsed_message.extract_field("PID", field_num=7, repeat_num=1, component_num=1, subcomponent_num=1),
        "sex": parsed_message.extract_field("PID", field_num=8, repeat_num=1, component_num=1, subcomponent_num=1),
        "ethnicity": parsed_message.extract_field("PID", field_num=22, repeat_num=1, component_num=1, subcomponent_num=1),
        "address": {
            "street": parsed_message.extract_field("PID", field_num=11, repeat_num=1, component_num=1, subcomponent_num=1),
            "city": parsed_message.extract_field("PID", field_num=11, repeat_num=1, component_num=3, subcomponent_num=1),
            "state": parsed_message.extract_field("PID", field_num=11, repeat_num=1, component_num=4, subcomponent_num=1),
            "postal": parsed_message.extract_field("PID", field_num=11, repeat_num=1, component_num=5, subcomponent_num=1),
            "country": parsed_message.extract_field("PID", field_num=11, repeat_num=1, component_num=6, subcomponent_num=1),
        },
        "phone_number": parsed_message.extract_field("PID", field_num=13, repeat_num=1, component_num=1, subcomponent_num=1),
        "language": parsed_message.extract_field("PID", field_num=15, repeat_num=1, component_num=1, subcomponent_num=1),
        "marital_status": parsed_message.extract_field("PID", field_num=16, repeat_num=1, component_num=1, subcomponent_num=1),
        "ssn": parsed_message.extract_field("PID", field_num=19, repeat_num=1, component_num=1, subcomponent_num=1),
        "national_code": parsed_message.extract_field("PID", field_num=28, repeat_num=1, component_num=1, subcomponent_num=1),
        "referring_doctor": parsed_message.extract_field("PV1", field_num=8, repeat_num=1, component_num=1, subcomponent_num=1),
    }


def extract_status_information(parsed_message, status):
    return {
        "patient_id": parsed_message.extract_field("PID", field_num=3, repeat_num=1, component_num=1, subcomponent_num=1),
        "status": status,
        "location": {
            "point_of_care": parsed_message.extract_field("PID", field_num=3, repeat_num=1, component_num=1, subcomponent_num=1),
            "room": parsed_message.extract_field("PID", field_num=3, repeat_num=1, component_num=2, subcomponent_num=1),
            "bed": parsed_message.extract_field("PID", field_num=3, repeat_num=1, component_num=3, subcomponent_num=1),
            "facility": parsed_message.extract_field("PID", field_num=3, repeat_num=1, component_num=4, subcomponent_num=1),
            "building": parsed_message.extract_field("PID", field_num=3, repeat_num=1, component_num=7, subcomponent_num=1),
            "floor": parsed_message.extract_field("PID", field_num=3, repeat_num=1, component_num=8, subcomponent_num=1),
        }
    }