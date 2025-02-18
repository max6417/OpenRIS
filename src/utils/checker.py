import hl7


def has_segment(message, segment_id):
    try:
        message.segment(segment_id)
        return True
    finally:
        return False


class Checker:

    def check_message_type(self, message):
        message = hl7.parse(message)
        mess_type = message.extract_field("MSH", field_num=9, repeat_num=1, component_num=1, subcomponent_num=1) + message.extract_field("MSH", field_num=9, repeat_num=1, component_num=2, subcomponent_num=1)
        match mess_type:
            case "ADT^01":
                return self.check_adt01(message)


class ADT01Checker:

    def check(self, parsed_message):
        return self.__check_MSH(parsed_message) and self.__check_EVN(parsed_message) and self.__check_PID(parsed_message) and self.__check_PV1(parsed_message)

    def __check_MSH(self, message):
        try:
            has_segment(message, "MSH")
            if message.extract_field("MSH", field_num=2, repeat_num=1, component_num=1, subcomponent_num=1) != "^~\&":
                return False
            if not len(message.extract_field("MSH", field_num=7, repeat_num=1, component_num=1, subcomponent_num=1)) >= 12:
                return False
            if message.extract_field("MSH", field_num=10, repeat_num=1, component_num=1, subcomponent_num=1) == "":
                return False
            if message.extract_field("MSH", field_num=11, repeat_num=1, component_num=1, subcomponent_num=1) not in ["D", "T", "P"]:
                return False
            if message.extract_field("MSH", field_num=12, repeat_num=1, component_num=1, subcomponent_num=1) == "":
                return False
            return True
        finally:
            return False

    def __check_EVN(self, message):
        try:
            if not has_segment(message, "EVN"):
                return False
            if len(message.extract_field("EVN", field_num=2, repeat_num=1, component_num=1, subcomponent_num=1)) >= 12:
                return False
            return True
        finally:
            return False

    def __check_PID(self, message):
        # Check PID.3 and PID.5
        try:
            if not has_segment(message, "PID"):
                return False
            if message.extract_field("PID", field_num=3, repeat_num=1, component_num=1, subcomponent_num=1) == "":
                return False
            if message.extract_field("PID", field_num=5, repeat_num=1, component_num=1, subcomponent_num=1) == "":
                return False
            return True
        finally:
            return False

    def __check_PV1(self, message):
        try:
            if not has_segment(message, "PV1"):
                return False
            if message.extract_field("PV1", field_num=2, repeat_num=1, component_num=1, subcomponent_num=1) not in "BEIOPR":
                return False
            return True
        finally:
            return False
    # Check PV1.14 -> Admit source to know how the patient is
