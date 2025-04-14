import orthanc
import pydicom
import json
import datetime


def OnChange(change_type, level, resource):
    if change_type == orthanc.ChangeType.NEW_STUDY:
        orthanc.LogInfo('New study registered in Orthanc')


orthanc.RegisterOnChangeCallback(OnChange)