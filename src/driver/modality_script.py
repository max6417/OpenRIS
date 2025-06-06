import datetime

import pydicom
from pydicom import Dataset
from pydicom.dataset import FileMetaDataset
from pydicom.uid import generate_uid, ExplicitVRLittleEndian
import sys
import requests
import json
import numpy as np

AET="ORTHANC"
ORTHANC_SERVER = "http://localhost:8042/"


def get_worklist(accession_number):
    data_to_query = {
        "AccessionNumber": accession_number,
        "PatientName": "",
        "PatientID": "",
        "PatientBirthDate": "",
        "StudyInstanceUID": "",
        "ScheduledProcedureStepSequence": ""
    }
    try:
        resp = requests.post(f"{ORTHANC_SERVER}modalities/{AET}/find-worklist", data=json.dumps(data_to_query)).json()
        print(resp)
        return resp[0]
    except Exception:
        return dict()


def generate_false_instance(worklist_info):
    if worklist_info:
        ds = Dataset()
        ds.file_meta = FileMetaDataset()
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
        ds.SOPInstanceUID = generate_uid()
        ds.StudyInstanceUID = worklist_info["StudyInstanceUID"]
        ds.SeriesInstanceUID = generate_uid()
        ds.PatientName = worklist_info["PatientName"]
        ds.PatientID = worklist_info["PatientID"]
        ds.AccessionNumber = worklist_info["AccessionNumber"]
        ds.StudyDate = datetime.datetime.now().strftime("%Y%m%d")
        ds.Modality = worklist_info["ScheduledProcedureStepSequence"][0]["Modality"]

        ds.PixelData = np.random.randint(0, 256, size=(100, 100), dtype=np.uint8).tobytes()
        ds.Rows = 100
        ds.Columns = 100
        ds.SamplesPerPixel = 1
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        ds.save_as("instance.dcm")



def main():
    accession_number = sys.argv[1]
    worklist_infos = get_worklist(accession_number)
    generate_false_instance(worklist_infos)
    with open("instance.dcm", "rb") as file:
        resp = requests.post(f"{ORTHANC_SERVER}instances", data=file.read())
    print(resp)

if __name__ == "__main__":
    main()