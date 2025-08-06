# TODO : Migrate all the const value s.a. ORTHANC server address and HIS server address

ORTHANC_SERVER = ""    # Enter the address to join orthanc
ORTHANC_AET = "ORTHANC"    # To retrieve HL7 message incoming from Orthanc (differently handled)
RIS_SERVER = ""    # Enter the address of OpenRIS
SECRET_KEY = "secret"

WORKLIST_DIR = ""    # Enter the worklist database directory (the same as indicated in config of Orthanc
HL7_LOGS_DIR = ""    # Enter the directory to store the log for HL7 communication
BASIC_LOGS_DIR = ""    # Enter the directory to store the log from the application

## HL7 Configuration files ##
MESSAGE_HL7_DIR = "configs/hl7_messages_config.json"    # indicate the json file used to store the config of HL7 message
SEGMENT_HL7_DIR = "configs/hl7_segment_config.json"    # indicate the json file used to store the config of segment HL7


INSTITUTION_NAME = "DEBUG HOSPITAL"    # To identify the institution that send HL7 message
HIS_NAME = "DEBUG HIS"    # To identify the HIS to send and receive message (ADT)
# Shift start is a string representing the start hour of the radiology department
SHIFT_START = "8:00"
SHIFT_END = "23:00"
# Number of day(s) to consider for the scheduler
D_RANGE = 7

## Logger configuration ##
MAX_BYTES_PER_FILE = 10000    # Number of bytes before file rolling
BACKUP_FILES = 10    # Number of file before rewriting the first one