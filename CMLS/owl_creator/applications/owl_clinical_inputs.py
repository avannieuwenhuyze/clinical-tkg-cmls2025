#Logger
from CMLS.owl_creator.tools.log_manager import get_logger
import configparser
import os
import pandas as pd

class Owl_Clinical_Inputs():

    def __init__(self,config_path):
        if os.path.exists(config_path):
            try:
                config = configparser.ConfigParser()
                config.read(config_path)

                #Biomarkers
                self.biomarkers_list = pd.read_csv(config["CLINICAL_INPUTS"].get("biomarkers_list"))

            except Exception as e:
                self.logger.error(f"Error in configuration file {e}")