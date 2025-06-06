import hl7


class HL7MessageBuilder:

    def __init__(self):
        self.__message = ""

    def add_segment(self, segment: str):
        self.__message = self.__message + segment

    def build(self) -> hl7.Message:
        return hl7.parse(self.__message)

    def get_message(self):
        return self.__message