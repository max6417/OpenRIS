import hl7


def has_segment(message, segment_id):
    try:
        message.segment(segment_id)
        return True
    finally:
        return False


class Checker:

    def check_adt01(self, message):
        message = hl7.parse(message)
        print(message.extract_field("MSH", field_num=9, repeat_num=1, component_num=1, subcomponent_num=1))

    def __check_MSH(self, segment):
        pass

    def __check_EVN(self, segment):
        pass

    def __check_PID(self, segment):
        pass

    def __check_PV1(self, segment):
        pass
