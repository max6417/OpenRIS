import logging
from src.config import HL7_LOGS_DIR, BASIC_LOGS_DIR, MAX_BYTES_PER_FILE, BACKUP_FILES
from logging.handlers import RotatingFileHandler


class HL7LogHandler():

    def __init__(self, file=HL7_LOGS_DIR, max_bytes=MAX_BYTES_PER_FILE, backup_files=BACKUP_FILES):
        self.__logger = logging.getLogger("hl7_logger")
        self.__logger.setLevel(logging.INFO)
        self.__file_handler = RotatingFileHandler(file, maxBytes=max_bytes, backupCount=backup_files)
        self.__file_handler.setLevel(logging.INFO)
        self.__file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.__logger.addHandler(self.__file_handler)


    def add_log(self, direction: str, message: str):
        self.__logger.info(f"{direction} -> {message}")


class AppLogHandler:
    def __init__(self, file=BASIC_LOGS_DIR, max_bytes=MAX_BYTES_PER_FILE, backup_files=BACKUP_FILES):
        self.__logger = logging.getLogger("app_logger")
        self.__logger.setLevel(logging.INFO)

        self.__file_handler = RotatingFileHandler(file, maxBytes=max_bytes, backupCount=backup_files)
        self.__file_handler.setLevel(logging.INFO)
        self.__file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        self.__logger.addHandler(self.__file_handler)

    def add_info_log(self, message: str):
        self.__logger.info(message)

    def add_error_log(self, message: str):
        self.__logger.error(message)