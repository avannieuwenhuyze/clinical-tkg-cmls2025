import configparser
import os
from rdflib import Graph, Namespace, RDF, RDFS, Literal, XSD, OWL



class OWL_exporter():

    def __init__(self,config_path,ontology_name):

        if os.path.exists(config_path):
            try:
                config = configparser.ConfigParser()
                config.read(config_path)

                self.g = Graph()
                self.g.parse(config["ONTOLOGY"].get("ontology_path"), 
                             format=config["ONTOLOGY"].get("format"))
                
                self.MIMIC = Namespace(config["ONTOLOGY"].get("mimic_name_space"))
                self.TIME = Namespace(config["ONTOLOGY"].get("time_name_space"))
                

           

                self.output_file = config["ONTOLOGY"].get("output_file_path")+ontology_name
              
            except Exception as e:
                self.logger.error(f"Erreur sur le fichier de configuration {e}")
        else:
            self.logger.error("Fichier de configuration non trouvé")



    def add_patient(self,patient):
   
        patient_uri = self.MIMIC[f"Patient_{patient.subject_id}"]
        self.g.add((patient_uri, RDF.type, OWL.NamedIndividual))
        self.g.add((patient_uri, RDF.type, self.MIMIC['Patient']))
        self.g.add((patient_uri, self.MIMIC['subject_id'], Literal(patient.subject_id, datatype=XSD.integer)))

        for admission in patient.admissions:
          self.add_admission(patient_uri, admission)
        

    def add_admission(self, patient_uri, admission):

        #Creation de l'admission
        admission_uri = self.MIMIC[f"Admission_{admission.hadm_id}"]
        self.g.add((admission_uri, RDF.type, OWL.NamedIndividual))
        self.g.add((admission_uri, RDF.type, self.MIMIC['Admission']))
        self.g.add((admission_uri, self.MIMIC['hadm_id'], Literal(admission.hadm_id, datatype=XSD.integer)))

        #Instant de début de l'admission
        instant_begin_uri = self.MIMIC[f"Instant_Admission_{admission.hadm_id}_Begin"]
        self.g.add((instant_begin_uri, RDF.type, OWL.NamedIndividual))
        self.g.add((instant_begin_uri, RDF.type, self.TIME.Instant))
        self.g.add((instant_begin_uri, self.TIME.inXSDDateTimeStamp, Literal(admission.admittime, datatype=XSD.dateTimeStamp)))

        self.g.add((admission_uri, self.TIME.hasBeginning, instant_begin_uri))

        #Instant de fin de l'admission (Si existant)
        if admission.dischtime:
            instant_end_uri = self.MIMIC[f"Instant_Admission_{admission.hadm_id}_End"]
            self.g.add((instant_end_uri, RDF.type, OWL.NamedIndividual))
            self.g.add((instant_end_uri, RDF.type, self.TIME.Instant))
            self.g.add((instant_end_uri, self.TIME.inXSDDateTimeStamp, Literal(admission.dischtime, datatype=XSD.dateTimeStamp)))

            self.g.add((admission_uri, self.TIME.hasEnd, instant_end_uri))


        #Lien patient / Admission
        self.g.add((patient_uri, self.MIMIC.hasAdmission, admission_uri))


    def add_tranfer(self, admission_uri, transfer):

        transfert_uri = self.EX[f"Transfer_{transfer.transfer_id}"]
        self.g.add((transfert_uri, RDF.type, self.EX.Transfer))

        # Début du transfert
        instant_begin_uri = self.EX[f"Instant_Transfer_{transfer.transfer_id}_Begin"]
        self.g.add((instant_begin_uri, RDF.type, self.TIME.Instant))
        self.g.add((instant_begin_uri, self.TIME.inXSDDateTimeStamp, Literal(transfer.intime, datatype=XSD.dateTimeStamp)))

        # Fin du transfert (si disponible)
        if transfer.outtime:
            instant_end_uri = self.EX[f"Instant_Transfer_{transfer.transfer_id}_End"]
            self.g.add((instant_end_uri, RDF.type, self.TIME.Instant))
            self.g.add((instant_end_uri, self.TIME.inXSDDateTimeStamp, Literal(transfer.outtime, datatype=XSD.dateTimeStamp)))

            # Relation hasEnd
            self.g.add((transfert_uri, self.TIME.hasEnd, instant_end_uri))


        # Relation hasBeginning
        self.g.add((transfert_uri, self.TIME.hasBeginning, instant_begin_uri))


        # Relation admission → transfert
        self.g.add((admission_uri, self.EX.hasTransfer, transfert_uri))



    def export(self):
        """Sérialise l'ontologie en OWL."""
        self.g.serialize(destination=self.output_file, format="pretty-xml")
        print(f"Ontologie générée avec succès : {self.output_file}")