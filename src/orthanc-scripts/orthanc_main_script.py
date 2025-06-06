import sys
sys.path.append("/home/rencelotm/OpenRIS/.venv/lib/python3.12/site-packages")
import os
import os.path
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid
import datetime
import orthanc
import requests
import hl7

WORKLIST_DIRECTORY = "/home/rencelotm/WorklistsDatabase"
MODALITY_WORKLIST_SOP_CLASS = "1.2.840.100008.5.1.4.31"
RIS_SERVER = "http://localhost:5000/"
ORTHANC_SERVER = "http://localhost:8042/"


def create_worklist(data: hl7.Message):
    ds = Dataset()
    # Meta Information
    ds.file_meta = FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = pydicom.uid.UID(MODALITY_WORKLIST_SOP_CLASS)   # Modality Worklist Information Model
    #ds.file_meta.MediaStorageSOPInstanceUID = generate_uid(prefix=MODALITY_WORKLIST_SOP_CLASS)    -> This fails
    ds.file_meta.MediaStorageSOPInstanceUID = generate_uid(prefix=None)
    ds.SpecificCharacterSet = "ISO_IR 6"
    ds.InstanceCreationDate = datetime.datetime.now().strftime("%Y%m%d").replace("-", "")
    ds.InstanceCreationTime = datetime.datetime.now().strftime("%H%M%S").replace(":", "")
    ds.AccessionNumber = data.extract_field("IPC", field_num=1)
    ds.PatientName = f"{data.extract_field("PID", field_num=5, component_num=1)}^{data.extract_field("PID", field_num=5, component_num=2)}"
    ds.PatientID = data.extract_field("PID", field_num=3, component_num=1)
    ds.PatientBirthDate = data.extract_field("PID", field_num=7)
    ds.PatientSex = data.extract_field("PID", field_num=8) if data.extract_field("PID", field_num=8) else "U"
    ds.StudyInstanceUID = data.extract_field("IPC", field_num=3)
    ds.RequestedProcedureDescription = data.extract_field("OBR", field_num=4, component_num=2)
    ds.ScheduledProcedureStepID = data.extract_field("OBR", field_num=4, component_num=1)
    ds.ScheduledProcedureStepSequence = [Dataset()]
    ds.ScheduledProcedureStepSequence[0].Modality = data.extract_field("IPC", field_num=5)
    ds.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = data.extract_field("IPC", field_num=9)
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate = data.extract_field("OBR", field_num=6, component_num=1)
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime = data.extract_field("OBR", field_num=6, component_num=2)
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription = data.extract_field("OBR", field_num=4, component_num=2)
    return ds


def RegisterWorklist(output, uri, **request):
    if request['method'] != 'POST':
        output.SendMethodNotAllowed('GET')
    else:
        data = hl7.parse(request['body'].decode('utf-8'))
        if not os.path.exists(WORKLIST_DIRECTORY):
            raise Exception(f"Worklist directory {WORKLIST_DIRECTORY} does not exist")
        if data.extract_field("MSH", field_num=9, component_num=3) == "OMI_O23":
            worklist = create_worklist(data)
            # Save the worklist in the correct directory
            worklist.save_as(f"{WORKLIST_DIRECTORY}/wklist{data.extract_field("IPC", field_num=1)}.wl", write_like_original=False)
            output.AnswerBuffer(str(data.create_ack("AA", data.extract_field("MSH", field_num=10), "ORTHANC", "DEBUG HOSPITAL")), "application/json")
        else:
            output.AnswerBuffer(str(data.create_ack("AE", data.extract_field("MSH", field_num=10), "ORTHANC", "DEBUG HOSPITAL")), "application/json")


def OnChangeStudy(change_type, level, resource):
    if change_type == orthanc.ChangeType.NEW_STUDY:
        creation_time = datetime.datetime.now().strftime("%H:%M:%S")
        resp = requests.get(f"{ORTHANC_SERVER}studies/{resource}")
        data = {
            'accession-number': resp.json()["MainDicomTags"]["AccessionNumber"],
            'creation-time': creation_time
        }
        if resp and resp.status_code == 200:
            _ = requests.post(f"{RIS_SERVER}new_study_created", json=data)
    elif change_type == orthanc.ChangeType.STABLE_STUDY:
        creation_time = datetime.datetime.now().strftime("%H:%M:%S")
        resp = requests.get(f"{ORTHANC_SERVER}studies/{resource}")
        if resp.status_code == 200:
            resp = resp.json()
            data = {
                "ID": resp["ID"],
                "AccessionNumber": resp["MainDicomTags"]["AccessionNumber"],
                "Series": resp["Series"],
                "creation-time": creation_time
            }
            _ = requests.post(f"{RIS_SERVER}stable_study", json=data)
            # Delete worklist file
            os.remove(f"{WORKLIST_DIRECTORY}/wklist{data["AccessionNumber"]}.wl")


orthanc.RegisterOnChangeCallback(OnChangeStudy)
orthanc.RegisterRestCallback('/mwl/create_worklist', RegisterWorklist)
