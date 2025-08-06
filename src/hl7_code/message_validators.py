"""
This file contains all the code to validate the message before processing it. It is based on a set of rule defined by
several JSON files representing the structure of each message used and the structure of each segment and the pattern
required for each field, component, subcomponent. In order to have a unique validator foreach message.
This file shouldn't be modified but all the JSON files has to be in order to fit the workflow of the organisation
"""
import json
import re
from abc import ABC, abstractmethod
import hl7
from uuid import uuid4


def extract_information(message: hl7.Message, segment: str, segment_num=1, field_num=1, repeat_num=1, component_num=1, subcomponent_num=1) -> str | None:
    """
    Function to extract specific information from a HL7 message
        :param @message: A hl7.Message object representing the message where the information has to be extracted
        :param @segment: the segment ID where the information has to be extracted
        :param @segment_num: the segment number where the information has to be extracted if applicable
        :param @field_num: the field number where the information has to be extracted
        :param @repeat_num: the repeat number where the information has to be extracted if applicable
        :param @component_num: the component number where the information has to be extracted
        :param @subcomponent_num: the subcomponent number where the information has to be extracted if applicable
    returns the information extracted from the @message, None if a KeyError is raise
    """
    try:
        return message.extract_field(segment, segment_num, field_num, repeat_num, component_num, subcomponent_num)
    except KeyError:
        return None


class PatternValidator:

    def __init__(self, message_conf_f: str, segment_conf_f: str):
        self.s_config = dict()
        self.m_config = dict()
        with open(message_conf_f, 'r') as file:
            self.s_config = json.load(file)
        with open(segment_conf_f, 'r') as file:
            self.m_config = json.load(file)

    def validate_pattern(self, message: hl7.Message) -> bool:
        msg_t = extract_information(message, "MSH", field_num=9, component_num=3)
        if msg_t is None:
            return False
        msg_config = self.m_config.get("messages", {}).get(msg_t, None)
        if msg_config is None:
            return True    # No config find for this message -> Pattern always valid
        for segment_name, segment_config in msg_config.items():
            if not self.__validate_segment_pattern(message, segment_name, segment_config.get("required", False)):
                return False
        return True

    def __validate_segment_pattern(self, message: hl7.Message, seg_name: str, required: bool) -> bool:
        if extract_information(message, seg_name) is None and required:
            return False
        if extract_information(message, seg_name) is None and not required:
            return True    # If a segment not required is not present : this segment is valid
        for field_i, field_conf in self.s_config.get("segments", {}).get(seg_name, {}).get("fields", {}).items():
            if not self.__validate_field_pattern(message, seg_name, int(field_i.split("-")[1]), field_conf):
                return False
        return True

    def __validate_field_pattern(self, message: hl7.Message, seg_name: str, field_idx: int, field_conf: dict) -> bool:
        if extract_information(message, segment=seg_name, field_num=field_idx) is None and field_conf.get("required", False):
            return False
        if extract_information(message, segment=seg_name, field_num=field_idx) is None and not field_conf.get("required", False):
            return True    # If a field is not present and not required its pattern is valid
        # Check if components
        if len(field_conf.get("components", {}) > 0):
            for component_i, component_conf in field_conf.get("components", {}).items():
                if not self.__validate_component_pattern(message, seg_name, field_idx, int(component_i.split(".")[1]), component_conf):
                    return False
            return True
        else:
            pattern = field_conf.get("pattern", None)
            if pattern is None:
                raise ValueError(f"No pattern found for {seg_name}-{str(field_idx)}") # Should not happen
            if not re.match(pattern, extract_information(message, seg_name, field_num=field_idx)):
                return False
            return True

    def __validate_component_pattern(self, message: hl7.Message, seg_name: str, field_idx: int, component_idx: int, component_conf: dict) -> bool:
        target_component = extract_information(message, seg_name, field_num=field_idx, component_num=component_idx)
        if target_component is None and component_conf.get("required", False):
            return False
        if target_component is None and not component_conf.get("required", False):
            return True    # If a component not present and not required, pattern valid
        pattern = component_conf.get("pattern", None)
        if pattern is None:
            raise ValueError(f"No pattern found for {seg_name}-{str(field_idx)}.{str(component_idx)}")    # Should not happen
        if not re.match(pattern, target_component):
            return False
        return True


#### VALIDATOR SECTION ####
# Only useful if you want to add additional check more specific rules
# Each class represents the validation of one specific message, at the moment all have the same code but it let each
# institution extends the classes for more advanced verification

class MessageValidator(ABC):
    @abstractmethod
    def validate_and_ack(self, message: hl7.Message, pattern_validator: PatternValidator, facility: str, application: str) -> hl7.Message:
        pass


class ADTA01Validator(MessageValidator):

    def validate_and_ack(self, message: hl7.Message, pattern_validator: PatternValidator, facility: str, application: str) -> hl7.Message:
        message_id = uuid4()
        if pattern_validator.validate_pattern(message) and extract_information(message, "MSH", field_num=5) != "OPENRIS":
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)
        elif pattern_validator.validate_pattern(message):
            return message.create_ack("AA", message_id=message_id, facility=facility, application=application)
        else:
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)


class OMIO23Validator(MessageValidator):

    def validate_and_ack(self, message: hl7.Message, pattern_validator: PatternValidator, facility: str, application: str) -> hl7.Message:
        message_id = uuid4()
        if pattern_validator.validate_pattern(message) and extract_information(message, "MSH", field_num=5) != "OPENRIS":
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)
        elif pattern_validator.validate_pattern(message):
            return message.create_ack("AA", message_id=message_id, facility=facility, application=application)
        else:
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)


class ADTA08Validator(MessageValidator):

    def validate_and_ack(self, message: hl7.Message, pattern_validator: PatternValidator, facility: str, application: str) -> hl7.Message:
        message_id = uuid4()
        if pattern_validator.validate_pattern(message) and extract_information(message, "MSH", field_num=5) != "OPENRIS":
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)
        elif pattern_validator.validate_pattern(message):
            return message.create_ack("AA", message_id=message_id, facility=facility, application=application)
        else:
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)


class ADTA04Validator(MessageValidator):

    def validate_and_ack(self, message: hl7.Message, pattern_validator: PatternValidator, facility: str, application: str) -> hl7.Message:
        message_id = uuid4()
        if pattern_validator.validate_pattern(message) and extract_information(message, "MSH", field_num=5) != "OPENRIS":
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)
        elif pattern_validator.validate_pattern(message):
            return message.create_ack("AA", message_id=message_id, facility=facility, application=application)
        else:
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)


class ORMO01Validator(MessageValidator):

    def validate_and_ack(self, message: hl7.Message, pattern_validator: PatternValidator, facility: str, application: str) -> hl7.Message:
        message_id = uuid4()
        if pattern_validator.validate_pattern(message) and extract_information(message, "MSH", field_num=5) != "OPENRIS":
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)
        elif pattern_validator.validate_pattern(message):
            return message.create_ack("AA", message_id=message_id, facility=facility, application=application)
        else:
            return message.create_ack("AR", message_id=message_id, facility=facility, application=application)