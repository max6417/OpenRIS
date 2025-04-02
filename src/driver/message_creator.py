import hl7
import requests
from hl7_code import *

class MessageCreator:
    def __init__(self):
        self.msg = str()


class ADTMessageCreator(MessageCreator):
    def __init__(self):
        super().__init__()

    def create_message(self):
        pass

    def create_adt_a01(self):
        self.msg = hl7.parse("MSH|^~\&|ADT1|GOOD HEALTH HOSPITAL|GHH LAB, INC.|GOOD HEALTH HOSPITAL|198808181126|SECURITY|ADT^A01|MSG00001|P|2.8||\rEVN|A01|200708181123||\rPID|1||PATID1234^5^M11^ADT1^MR^GOOD HEALTH HOSPITAL~123456789^^^USSSA^SS||EVERYMAN^ADAM^A^III||19610615|M||C|2222 HOME STREET^^GREENSBORO^NC^27401-1020|GL|(555) 555-2004|(555)555-2004||S||PATID12345001^2^M10^ADT1^AN^A|444333333|987654^NC|\rNK1|1|NUCLEAR^NELDA^W|SPO^SPOUSE||||NK^NEXT OF KIN\rPV1|1|I|2000^2012^01||||004777^ATTEND^AARON^A|||SUR||||ADM|A0|\r")


if __name__ == "__main__":
    msg = ADTMessageCreator()
    msg.create_adt_a01()
    resp = requests.get("http://127.0.0.1:5000/receive", data=str(msg.msg))
    print(resp.text)