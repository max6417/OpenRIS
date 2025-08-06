"""
This file contains the code to construct all HL7 message used by OpenRIS to communicate with Orthanc and the HIS.
It is encouraged to extend this file to fit the workflow of each institution
"""
import hl7
import src.config as config


class HL7MessageBuilder:

    def __init__(self):
        self.__message = ""

    def add_segment(self, segment: str):
        self.__message = self.__message + segment

    def build(self) -> hl7.Message:
        return hl7.parse(self.__message)

    def get_message(self):
        return self.__message


def construct_orm_o01(order: dict, procedure: dict, patient: dict, msg_id: str, date: str, status: str, status2: str) -> hl7.Message:
    """
    Function to create a HL7 message ORM^O01 with all the basic information
        :param @order: A document stored in the "orders" collection of MongoDB
        :param @procedure: A document stored in the "procedures" collection of MongoDB
        :param @patient: A document stored in the "patients" collection of MongoDB
        :param @msg_id: A string representing the message ID following the uuid4 convention
        :param @date: A string representing the date of the message
        :param @status: A string representing the status (ORC.1 of HL7 documentation)
        :param @status2: A string representing the status (ORC.5 of HL7 documentation)
    return a Message as presented in the python-hl7 documentation
    """
    message = HL7MessageBuilder()
    message.add_segment(
        "MSH|^~\&|OPENRIS|"+config.INSTITUTION_NAME+"|"+config.HIS_NAME+"|"+config.INSTITUTION_NAME+"|"+
        date+"||ORM^O01^ORM_O01|"+msg_id+"|D|2.8||\r"
    )
    message.add_segment(
        "PID|1||"+patient.get("_id", "")+"^5^M11^ADT1^MR^"+config.INSTITUTION_NAME+"||"+patient.get("name", "UNKNOWN")+
        "^"+patient.get("surname", "UNKNOWN")+"|\r"
    )
    message.add_segment(
        "ORC|"+status+"|"+order.get("placer_id", "")+"|"+order['_id']+"||"+status2+"||^^^"+
        order.get("examination_date", {}).get("date", "").replace("-", "")+
        order.get("examination_date", {}).get("start_time", "").replace(":", "")+"^"+
        order.get("examination_date", {}).get("date", "").replace("-", "")+
        order.get("examination_date", {}).get("end_time", "").replace(":", "")+"|||"+
        order.get("placer_physician", {}).get("_id", "")+"^"+order.get("placer_physician", {}).get("name", "")+"^"+
        order.get("placer_physician", {}).get("surname", "")+"|\r"
    )
    message.add_segment(
        "OBR|1|"+order.get("placer_id", "")+"|"+order['_id']+"|"+procedure.get("_id", "")+"^"+procedure.get("name", "")+
        "|\r"
    )
    return message.build()

def construct_adt_a08(patient: dict, date: str, msg_id: str) -> hl7.Message:
    """
    Function to create a HL7 message ADT^A08 with all the basic information about a patient
        :param @patient: A document stored in the "patients" collection of MongoDB with updated patient information
        :param @date: A string representing the date of the message
        :param @msg_id: A string representing the message ID following the uuid4 convention
    returns a Message as presented in the python-hl7 documentation
    """
    message = HL7MessageBuilder()
    message.add_segment(
        "MSH|^~\&|OPENRIS|"+config.INSTITUTION_NAME+"|"+config.HIS_NAME+"|"+config.INSTITUTION_NAME+"|" +
        date + "||ADT^A08^ADT_A08|" + msg_id + "|D|2.8||\r"
    )
    message.add_segment(
        "EVN||"+date+"||\r"
    )
    message.add_segment(
        "PID|1||"+patient.get("_id", "")+"^5^M11^ADT1^MR^"+config.INSTITUTION_NAME+"||"+patient.get("name", "UNKNOWN")+
        "^"+patient.get("surname", "UNKNOWN")+"||"+patient.get("dob", "").replace("-", "")+"|"+
        patient.get("sex", "U")+"||"+patient.get("ethnicity", "UNKNOWN")+"|"+
        patient.get("address", {}).get("address", "")+"^^"+patient.get("address", {}).get("city", "")+"^"+
        patient.get("address", {}).get("province", "")+"^"+patient.get("address", {}).get("zip_code", "")+"^"+
        patient.get("address", {}).get("country", "")+"||"+patient.get("phone_number", "")+"|"+
        patient.get("business_phone", "")+"|"+patient.get("language", "")+"|"+patient.get("marital-status", "")+"|"+
            patient.get("religion", "")+"||"+patient.get("ssn", "")+"||\r"
    )
    message.add_segment(
        "PV1||"+patient.get("patient-class", "I")+"||"+patient.get("admission-type", "R")+"||||"+
        patient.get("referring_physician", {}).get("_id", "UNKNOWN")+"^"+
        patient.get("referring_physician", {}).get("name", "UNKNOWN")+"^"+
        patient.get("referring_physician", {}).get("surname", "UNKNOWN")+"||||||||\r"
    )
    return message.build()

def construct_omi_023(patient: dict, procedure: dict, order: dict, msg_id: str, accession_nb: str, date: str, s_id: str) -> hl7.Message:
    """
    Function to create a HL7 message OMI^O23 with all the basic information. This message is used to communicate the
    information about an order to create a worklist in Orthanc.
        :param @patient: A document stored in the "patients" collection of MongoDB
        :param @procedure: A document stored in the "procedures" collection of MongoDB
        :param @order: A document stored in the "orders" collection of MongoDB
        :param @msg_id: A string representing the message ID following the uuid4 convention
        :param @accession_nb: A string representing the accession number simply current date + time + 2 first number of ms time
        :param @date: A string representing the date of the message
        :param @s_id: A string representing the study UID of the order such as presented in the DICOM protocol
    returns a HL7 Message as presented in the python-hl7 documentation
    """
    message = HL7MessageBuilder()
    message.add_segment(
        "MSH|^~\&|OPENRIS|"+config.INSTITUTION_NAME+"|"+config.ORTHANC_AET+"|"+config.INSTITUTION_NAME+"|"+date+
        "||OMI^O23^OMI_O23|"+msg_id+"|D|2.8||\r"
    )
    message.add_segment(
        "PID|1||"+patient['_id']+"^5^M11^ADT1^MR^"+config.INSTITUTION_NAME+"||"+patient.get("name", "UNKNOWN")+
        "^"+patient.get("surname", "UNKNOWN")+"||"+patient.get("dob", "").replace("-", "")+"|"+
        patient.get("sex", "U")+"||"+patient.get("ethnicity", "UNKNOWN")+"|"+
        patient.get("address", {}).get("address", "")+"^^"+patient.get("address", {}).get("city", "")+"^"+
        patient.get("address", {}).get("province", "")+"^"+patient.get("address", {}).get("zip_code", "")+"^"+
        patient.get("address", {}).get("country", "")+"||"+patient.get("phone_number", "")+"|"+
        patient.get("business_phone", "")+"|"+patient.get("language", "")+"|"+patient.get("marital-status", "")+"|"+
        patient.get("religion", "")+"||"+patient.get("ssn", "")+"||\r"
    )
    message.add_segment(
        "ORC|NW|"+order.get("placer_id", "")+"|"+order["_id"]+"||SC|\r"
    )
    message.add_segment(
        "OBR||||"+procedure['_id']+"^"+procedure['name']+"||"+order['examination_date']['date'].replace('-', '')+"^"+
        order['examination_date']['start_time'].replace(':', '')+"|\r"
    )
    message.add_segment(
        "IPC|"+accession_nb+"|"+procedure['_id']+"|"+s_id+"|"+procedure['_id']+"|"+order['modality']+"||||"+
        order['station_aet']+"|\r"
    )
    return message.build()

def construct_oru_r01(report: dict, procedure: dict, order: dict, patient: dict, msg_id: str, date: str) -> hl7.Message:
    """
    Function to create a HL7 message ORU^R01 with information about the result of a finished order. It basically contains
    study ID to access images from Orthanc, ID of the report to access the report from RIS and the report itself.
        :param @report: A document stored in the "reports" collection of MongoDB
        :param @procedure: A document stored in the "procedures" collection of MongoDB
        :param @order: A document stored in the "orders" collection of MongoDB
        :param @patient: A document stored in the "patients" collection of MongoDB
        :param @msg_id: A string representing the message ID following the uuid4 convention
        :param @date: A string representing the date the message was created
    returns a HL7 Message as presented in the python-hl7 documentation
    """
    message = HL7MessageBuilder()
    message.add_segment(
        "MSH|^~\&|OPENRIS|"+config.INSTITUTION_NAME+"|"+config.ORTHANC_AET+"|"+config.INSTITUTION_NAME+"|"+date+
        "||ORU^R01^ORU_R01|"+msg_id+"|D|2.8||\r"
    )
    message.add_segment(
        "PID|1||"+patient['_id']+"^5^M11^ADT1^MR^"+config.INSTITUTION_NAME+"||"+patient.get("name", "UNKNOWN")+"^"+
        patient.get("surname", "UNKNOWN")+"|\r"
    )
    message.add_segment(
        "OBR||"+order.get("placer_id", "")+"|"+order['_id']+"|"+procedure['_id']+"^"+procedure['name']+"^SNM|||"+
        order["examination_date"]["date"].replace("-", "")+order["executive-start-time"].replace(":", "")+"|"+
        order["examination_date"]["date"].replace("-", "")+order["executive-end-time"].replace(":", "")+"||||||||||||||"+
        report["date"].replace("-", "")+report["time"].replace(":", "")+"|||F|\r"
    )
    message.add_segment(
        "OBX|1|RP|study-id||"+order["orthanc_study_id"]+"||||||F|\r"
    )
    message.add_segment(
        "OBX|2|RP|report-id||"+report['_id']+"||||||F|\r"
    )
    message.add_segment(
        "OBX|3|TX|report-findings||"+report["findings-text"]+"||||||F|\r"
    )
    message.add_segment(
        "OBX|4|TX|report-impressions||"+report["impressions-text"]+"||||||F|\r"
    )
    message.add_segment(
        "OBX|5|TX|report-recommendations||"+report["recommendations"]+"||||||F|\r"
    )
    return message.build()
