"""
This file contained all the utils function. For now, most of the function here are not use anymore.
"""
import uuid


def generate_uuid() -> str:
    """
    Function that generates a unique id for each request by following UUID4.
    """
    return str(uuid.uuid4())


def generate_patient_id(patient_name: str, patient_dob: str, patient_sex: str):
    """
    Outdated
    """
    patient_dob = patient_dob.join('-')
    patient_name = patient_name.upper()
    patient_sex = patient_sex.upper()
    return f"{patient_name[:4]}{patient_dob}{patient_sex}"
