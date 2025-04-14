import sys
sys.path.append("/home/rencelotm/OpenRIS/.venv/lib/python3.12/site-packages")
import os.path
import pydicom
import json
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid
import datetime
import orthanc


WORKLIST_DIRECTORY = "/home/rencelotm/WorklistsDatabase"
MODALITY_WORKLIST_SOP_CLASS = "1.2.840.100008.5.1.4.31"


def create_worklist(data):
    ds = Dataset()
    # Meta Information
    ds.file_meta = FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = pydicom.uid.UID(MODALITY_WORKLIST_SOP_CLASS)   # Modality Worklist Information Model
    #ds.file_meta.MediaStorageSOPInstanceUID = generate_uid(prefix=MODALITY_WORKLIST_SOP_CLASS)    -> This fails
    ds.file_meta.MediaStorageSOPInstanceUID = generate_uid(prefix=None)
    ds.SpecificCharacterSet = "ISO_IR 6"
    ds.InstanceCreationDate = datetime.datetime.now().strftime("%Y%m%d")
    ds.InstanceCreationTime = datetime.datetime.now().strftime("%H%M%S")
    ds.AccessionNumber = data["_id"]
    ds.PatientName = f"{data['patient_name']}^{data['patient_surname']}"
    ds.PatientID = data["patient_id"]
    ds.PatientBirthDate = data["patient_dob"]
    ds.PatientSex = data["patient_sex"]
    ds.StudyInstanceUID = generate_uid()
    ds.RequestedProcedureDescription = data["procedure_name"]
    ds.RequestedProcedureStepID = data["procedure_id"]
    ds.ScheduledProcedureStepSequence = [Dataset()]
    ds.ScheduledProcedureStepSequence[0].Modality = data["modality"]
    ds.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = data["modality_station_ae"]
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate = data["examination_date"]["date"].replace("-", "")
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime = data["examination_date"]["time"].replace(":", "")
    ds.ScheduledProcedureStepSequence[0].ScheduledPerformingPhysicianName = f"{data['performing_physician_name']}^{data['performing_physician_surname']}"
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription = data["procedure_name"]
    return ds


def RegisterWorklist(output, uri, **request):
    if request['method'] != 'POST':
        output.SendMethodNotAllowed('GET')
    else:
        data = json.loads(request['body'])
        if not os.path.exists(WORKLIST_DIRECTORY):
            raise Exception(f"Worklist directory {WORKLIST_DIRECTORY} does not exist")
        resp = dict()
        worklist = create_worklist(data)
        # Save the worklist in the correct directory
        worklist.save_as(f"{WORKLIST_DIRECTORY}/wklist{data['_id']}.wl", write_like_original=False)
        resp['status'] = 200
        output.AnswerBuffer(json.dumps(resp, indent=3), 'application/json')


def test_endpoint(output, uri, **request):
    output.AnswerBuffer('ok', 'text/plain')

orthanc.RegisterRestCallback('/mwl/create_worklist', RegisterWorklist)
orthanc.RegisterRestCallback('/test', test_endpoint)
