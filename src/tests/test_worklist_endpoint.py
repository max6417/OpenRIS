import requests
import json
import os
import pydicom


ORTHANC_URL = "http://localhost:8042"
ENDPOINT = "/mwl/create_worklist"


data_test = {
    "_id": "TEST123",
    "patient_name": "John",
    "patient_surname": "DOE",
    "patient_id": "PID123456",
    "patient_dob": "19800101",
    "patient_sex": "M",
    "procedure_name": "CT ABDOMEN",
    "procedure_id": "PROC789",
    "modality": "CT",
    "modality_station_ae": "CTSCANNER1",
    "examination_date": {
        "date": "2023-05-15",
        "time": "14:30:00"
    },
    "performing_physician_name": "Jane",
    "performing_physician_surname": "SMITH"
}


def test_worklist_endpoint():
    url = f"{ORTHANC_URL}{ENDPOINT}"
    headers = {"Content-Type": "application/json"}

    print(f"Test endpoint: {url}")

    try:
        response = requests.post(
            url,
            data=json.dumps(data_test),
            headers=headers,
        )
    except requests.exceptions.RequestException as e:
        print("Connection failed: ", e)
        return False

    if response.status_code != 200:
        print("Bad Status Code response: ", response.status_code)
        return False
    print("Status code: ", response.status_code)



if __name__ == "__main__":
    success = test_worklist_endpoint()