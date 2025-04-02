import hl7


class HL7MessageBuilder:

    def __init__(self, message_t: str):
        self.message_t = message_t
        self.segments = list()

    def add_segment(self, segment_name: str, fields: list):
        self.segments.append([segment_name] + fields)

    def build(self) -> str:
        return str(hl7.Message(self.segments))
