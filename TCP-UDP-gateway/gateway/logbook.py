"""
Nazwa projektu: System konwersji TCP/UDP - “SensNet”
Autor: Jakub Kowalczyk
Data utworzenia: 14.01.2024 r.
"""
import logging

class LogBook:
    def __init__(self, filename='gateway.log', disable_console=False, disable_file=False):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        if(not disable_console):
            self.set_console_handler(formatter)
        if(not disable_file):
            self.set_file_handler(filename, formatter)
        

    def set_file_handler(self, filename, formatter):
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def set_console_handler(self, formatter):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def info(self, event):
        self.logger.info(event)

    def error(self, event):
        self.logger.error(event)
    
    def warning(self, event):
        self.logger.warning(event)

    def debug(self, event):
        self.logger.debug(event)

    def critical(self, event):
        self.logger.critical(event)