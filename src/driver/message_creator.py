import hl7
import sys
import json
import requests
import datetime
from uuid import uuid4


class HL7MessageBuilder:

    def __init__(self):
        self.__message = ""

    def add_segment(self, segment: str):
        self.__message = self.__message + segment

    def build(self) -> hl7.Message:
        return hl7.parse(self.__message)

    def get_message(self):
        return self.__message


def read_json_file(filepath):
    try:
        data = json.load(open(filepath))
        return data
    except Exception as e:
        print(f"The file {filepath} does not exist or it is not a JSON file")

def create_adta01(patient_information):
    date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    patient_id = patient_information['name'][:4].upper() + patient_information['dob'].replace('-', '') + patient_information['sex']
    address = patient_information.get("address", {})
    referring_phys = patient_information.get("referring-physician", {})
    message = HL7MessageBuilder()
    seg = "MSH|^~\&|ADT1|DEBUG HOSPITAL|OPENRIS|DEBUG HOSPITAL|"+date+"||ADT^A01^ADT_A01|"+str(uuid4())+"|D|2.8||\r"
    message.add_segment(
        seg
    )
    seg = "EVN|A01|"+date+"||\r"
    message.add_segment(
        seg
    )
    seg = "PID|1||"+patient_id+"^5^M11^ADT1^MR^DEBUG HOSPITAL||"+patient_information["name"].upper()+"^"+patient_information["surname"].upper()+"||"+patient_information["dob"].replace('-', '')+"|"+patient_information.get('sex', '').upper()+"||"+patient_information.get('ethnicity', '')+"|"+address.get('address', '').upper()+"^^"+address.get('city', '').upper()+"^"+address.get('province', '').upper()+"^"+address.get('zip-code', '').upper()+"^"+address.get('country', '').upper()+"|"+address.get('county-code', '').upper()+"|"+patient_information.get('home-phone', '')+"|"+patient_information.get('business-phone', '')+"|"+patient_information.get('language', '').upper()+"|"+patient_information.get('marital-status', '').upper()+"|"+patient_information.get('religion', '').upper()+"||"+patient_information.get('ssn', '')+"||\r"
    message.add_segment(
        seg
    )
    seg =  "PV1||"+patient_information.get('patient-class', 'I')+"||"+patient_information.get('admission-type', 'R')+"||||"+referring_phys.get('id', '').upper()+"^"+referring_phys.get('name', '').upper()+"^"+referring_phys.get('surname', '').upper()+"||MED||||ADM|A0|\r"
    message.add_segment(
       seg
    )
    return message


def main():
    filepath = sys.argv[1]
    patient_information = read_json_file(filepath)
    message = create_adta01(patient_information)
    for segment in str(message.build()).split("\r"):
        print(segment)
    _ = requests.post("http://localhost:5000/receive-hl7", data=message.get_message(), headers={"Content-Type": "application/hl7"})


if __name__ == "__main__":
    main()