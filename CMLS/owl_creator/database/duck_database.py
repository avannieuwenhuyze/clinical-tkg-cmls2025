import duckdb
import configparser
from CMLS.owl_creator.tools.log_manager import get_logger
import os

class Duck_database:

    def __init__(self,config_path):

        self.logger = get_logger()

        if os.path.exists(config_path):
            try:
                config = configparser.ConfigParser()
                config.read(config_path)
                self.duckdb_path = config["DUCK_DB"].get("path")
                self.duckdb_db_name = config["DUCK_DB"].get("db_name")
                self.duck_db= self.duckdb_path+self.duckdb_db_name
            except Exception as e:
                self.logger.error(f"Erreur sur le fichier de configuration {e}")
        else:
            self.logger.error("Fichier de configuration non trouvé")


    def test(self):
        self.connect()
        self.close()


    def connect(self):
        try:
            self.conn = duckdb.connect(self.duck_db)
            return self.conn
        except Exception as e:
            self.logger.error(f"Connection DuckDb Failed {e}")
            self.conn = None  

       
    def close(self):
        try:
            self.conn.close()
        except Exception as e:
            self.logger.error("Déconnexion DuckDb Failed")


   
          

       