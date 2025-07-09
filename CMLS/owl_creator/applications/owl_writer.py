
#Logger
from CMLS.owl_creator.tools.log_manager import get_logger


import configparser
import os
from rdflib import Graph, Namespace, RDF, RDFS, Literal, XSD, OWL
from datetime import datetime
import shutil
from datetime import datetime, timedelta
from datetime import timezone


class OWL_Writer():

    def __init__(self,config_path,ontology_name):

        self.logger = get_logger()
        #self.logger.info("OWL Writer Initialisation")

        if os.path.exists(config_path):
            try:
                config = configparser.ConfigParser()
                config.read(config_path)

                #Ontology instanciation
                if not os.path.exists(config["ONTOLOGY"].get("ontology_path")):
                    self.logger.error(f"File of the ontology definition NOT FOUND...")
                    exit()

                self.g = Graph()
                try:
                    self.g.parse(config["ONTOLOGY"].get("ontology_path"), 
                             format=config["ONTOLOGY"].get("format"))
                    #self.logger.info(f"Ontology parsed successfully.")
                except Exception as e:
                    self.logger.error(f"Ontology definition PARSE ERROR...")
                    exit()

                #Mimic Namespace    
                self.MIMIC_Namespace = Namespace(config["ONTOLOGY"].get("mimic_name_space"))
                
                
                #OWL Time Namespace
                self.TIME_Namespace = Namespace(config["ONTOLOGY"].get("time_name_space"))
            
                #Output File
                self.output_file = config["ONTOLOGY"].get("output_file_path")+ontology_name
                self.backup_output_file_path = config["ONTOLOGY"].get("backup_output_file_path")
                
                #Backup existing output file if exist
                self.backup_existing_file(ontology_name)


                #List
                self.list_biomarker_type = []
                self.list_biomarker_category = []
                self.list_biomarker_specimen_type=[]
                self.list_clinicalsign_type = []
                self.list_clinicalsign_category = []
                self.list_unit = [] #Global to biomarkers and clinicals signs

                self.list_microbio_antibio = []
                self.list_microbio_specimen_type=[]
                self.list_microbio_culture_result = []
                self.list_microbio_interpretation = []
                self.list_microbio_organism = []

                self.list_icd = []
                self.list_comorbidity=[]



            except Exception as e:
                self.logger.error(f"Erreur sur le fichier de configuration {e}")
        else:
            self.logger.error("Fichier de configuration non trouvé")


    #======================================================
    # TOOLS
    #======================================================

    def backup_existing_file(self,ontology_name):

        if os.path.exists(self.output_file):
            os.makedirs(self.backup_output_file_path, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file_name = f"{ontology_name}_{timestamp}"
            backup_path = os.path.join(self.backup_output_file_path, new_file_name)
            shutil.copy2(self.output_file, backup_path)
            os.remove(self.output_file)


    def format_number(self,number,width):
        return f"{number:0{width}d}"
    

    def format_date(self,date_time):
        dt = date_time.astype('datetime64[s]').astype(datetime)
        date_with_z = dt.replace(tzinfo=timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        return date_with_z
    
    def duration_to_iso8601(self,days: int, hours: int = 0, minutes: int = 0):
        duration = "P"
        if days:
            duration += f"{days}D"
        if hours or minutes:
            duration += "T"
            if hours:
                duration += f"{hours}H"
            if minutes:
                duration += f"{minutes}M"
        return duration
    

    def write_instant(self,date_time,URI):
        date_time = self.format_date(date_time)
        self.g.add((URI, RDF.type, OWL.NamedIndividual))
        self.g.add((URI, RDF.type, self.TIME_Namespace['Instant']))
        self.g.add((URI,self.TIME_Namespace.inXSDDateTimeStamp, Literal(date_time,datatype=XSD.dateTimeStamp)))



    def write(self):
        try:
            with open(self.output_file, "wb+") as f:
                self.g.serialize(destination=f, format="pretty-xml")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exportation : {e}")


    #======================================================
    #ENTITIES
    #======================================================

    #-- PATIENT--
    def write_patient(self,patient):
        """
        Adds RDF triples describing a patient to the ontology graph.

        This method:
        - Declares the patient as an OWL NamedIndividual of type :Patient
        - Adds core data properties from the MIMIC-IV dataset:
            - hasAge (xsd:decimal)
            - hasGender (xsd:string)
            - hasSubjectId (xsd:integer)
        - Uses the patient's URI to uniquely identify the individual in the RDF graph
        - Commits the changes by writing to the graph storage

        Args:
            patient: An object containing patient-level information, including subject_id, age, and gender.
        """
        patient_URI = patient.URI
        self.g.add((patient_URI, RDF.type, OWL.NamedIndividual))
        self.g.add((patient_URI, RDF.type, self.MIMIC_Namespace['Patient']))
        self.g.add((patient_URI, self.MIMIC_Namespace['hasAge'], Literal(patient.has_age, datatype=XSD.decimal)))
        self.g.add((patient_URI, self.MIMIC_Namespace['hashasGender'], Literal(patient.has_gender, datatype=XSD.string)))
        self.g.add((patient_URI, self.MIMIC_Namespace['hasSubjectId'], Literal(patient.has_subject_id, datatype=XSD.integer)))
        self.g.add((patient_URI, self.MIMIC_Namespace['isMimicSepsis3'], Literal(patient.sepsis3, datatype=XSD.boolean)))
        self.g.add((patient_URI, RDFS.label, Literal("PA-"+str(patient.has_subject_id), lang="en")))
        self.write()


    #-- ICU STAY--
    def write_icustay(self,icustay,patient):
        icustay_URI = icustay.URI
        self.g.add((icustay_URI, RDF.type, OWL.NamedIndividual))
        self.g.add((icustay_URI, RDF.type, self.MIMIC_Namespace['ICUStay']))
        self.g.add((icustay_URI, RDFS.label, Literal("ST-"+str(icustay.has_stay_id), lang="en")))

        #Beginning
        begin_URI = self.MIMIC_Namespace[f"instant/ICUStayBegin_{str(icustay.has_stay_id)}"]
        self.write_instant(date_time=icustay.has_beginning, URI=begin_URI)
        self.g.add((icustay_URI,self.TIME_Namespace.hasBeginning,begin_URI))

        #End
        end_URI =  self.MIMIC_Namespace[f"instant/ICUStayEnd_{str(icustay.has_stay_id)}"]
        self.write_instant(date_time=icustay.has_end, URI=end_URI)
        self.g.add((icustay_URI,self.TIME_Namespace.hasEnd,end_URI))

        #Duration
        days, hours, minutes = icustay.duration()
        iso_duration = self.duration_to_iso8601(days, hours, minutes)
        self.g.add((icustay_URI,self.TIME_Namespace.hasDuration,Literal(iso_duration, datatype=XSD.duration)))

        #Duration description (more detailled)
        duration_URI = self.MIMIC_Namespace[f"duration/{str(icustay.has_stay_id)}"]
        self.g.add((duration_URI, RDF.type, self.TIME_Namespace.DurationDescription))
        if days > 0:
            self.g.add((duration_URI, self.TIME_Namespace.days, Literal(days, datatype=XSD.integer)))
        if hours > 0:
            self.g.add((duration_URI, self.TIME_Namespace.hours, Literal(hours, datatype=XSD.integer)))
        if minutes > 0:
            self.g.add((duration_URI, self.TIME_Namespace.minutes, Literal(minutes, datatype=XSD.integer)))
        self.g.add((icustay_URI, self.TIME_Namespace.hasDurationDescription, duration_URI))


        #ICUStay -- concernsPatient --> Patient
        self.g.add((icustay_URI,self.MIMIC_Namespace.concernsPatient, patient.URI))

        #Patient -- hasICUStay --> ICUStay
        self.g.add((patient.URI,self.MIMIC_Namespace.hasICUStay, icustay_URI))

        self.write()


    #-- ICU DAYS --
    def write_icuday(self,icustay,icuday):

        icuday_URI = icuday.URI

        self.g.add((icuday_URI, RDF.type, OWL.NamedIndividual))
        self.g.add((icuday_URI, RDF.type, self.MIMIC_Namespace['ICUDay']))
        self.g.add((icuday_URI, RDFS.label, Literal("DA-"+str(icuday.has_number), lang="en")))

        #Beginning
        begin_URI = self.MIMIC_Namespace[f"instant/ICUDayBegin_{str(icustay.has_stay_id)}_{str(icuday.has_number)}"]
        self.write_instant(date_time=icuday.has_beginning, URI=begin_URI)
        self.g.add((icuday_URI,self.TIME_Namespace.hasBeginning,begin_URI))

        #End
        end_URI =  self.MIMIC_Namespace[f"instant/ICUDayEnd_{str(icustay.has_stay_id)}_{str(icuday.has_number)}"]
        self.write_instant(date_time=icuday.has_end, URI=end_URI)
        self.g.add((icuday_URI,self.TIME_Namespace.hasEnd,end_URI))

        #ICUDay -- partOf --> ICUStay
        self.g.add((icuday_URI,self.MIMIC_Namespace.partOf, icustay.URI))

        #ICUStay -- hasICUDay --> ICUDay
        self.g.add((icustay.URI,self.MIMIC_Namespace.hasICUDay, icuday_URI))

        self.write()


    #-- BIOMARKER EVENT --
    def write_biomarkerevent(self,biomarkerevent,patient,icustay):

    
        #URI
        biomarkerevent_URI = biomarkerevent.URI
        self.g.add((biomarkerevent_URI, RDF.type, OWL.NamedIndividual))
        self.g.add((biomarkerevent_URI, RDF.type, self.MIMIC_Namespace['BiomarkerEvent']))
        self.g.add((biomarkerevent_URI, RDFS.label, Literal("BM-"+biomarkerevent.has_biomarker_name, lang="en")))

    
        #Type (create if not exist)
        typeURI = biomarkerevent.typeURI
        if typeURI not in self.list_biomarker_type:
            self.list_biomarker_type.append(typeURI)
            self.g.add((typeURI, RDF.type, OWL.NamedIndividual))
            self.g.add((typeURI, RDF.type, self.MIMIC_Namespace['BiomarkerType']))
            self.g.add((typeURI, RDFS.label, Literal(biomarkerevent.has_biomarker_name, lang="en")))
        self.g.add((biomarkerevent_URI, self.MIMIC_Namespace['hasBiomarkerType'], typeURI))


        #Category (create if not exist)
        category_URI = biomarkerevent.categoryURI
        if category_URI not in self.list_biomarker_category:
            self.list_biomarker_category.append(category_URI)
            self.g.add((category_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((category_URI, RDF.type, self.MIMIC_Namespace['BiomarkerCategory']))
            self.g.add((category_URI, RDFS.label, Literal(biomarkerevent.has_category, lang="en")))
        self.g.add((biomarkerevent_URI, self.MIMIC_Namespace['hasCategory'], category_URI))


        #Unit (create if not exist)
        unit_URI = biomarkerevent.unitURI
        if unit_URI not in self.list_unit:
            self.list_unit.append(unit_URI)
            self.g.add((unit_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((unit_URI, RDF.type, self.MIMIC_Namespace['Unit']))
            self.g.add((unit_URI, RDFS.label, Literal(biomarkerevent.has_unit, lang="en")))
        self.g.add((biomarkerevent_URI, self.MIMIC_Namespace['hasUnit'], unit_URI))

           
        #specimen
        specimen_URI = biomarkerevent.specimenURI
        if specimen_URI not in self.list_biomarker_specimen_type:
            self.list_biomarker_specimen_type.append(specimen_URI)
            self.g.add((specimen_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((specimen_URI, RDF.type, self.MIMIC_Namespace['SpecimenType']))
            self.g.add((specimen_URI, RDFS.label, Literal(biomarkerevent.has_specimen_type, lang="en")))
        self.g.add((biomarkerevent_URI, self.MIMIC_Namespace['hasSpecimenType'], specimen_URI))


        #value
        if biomarkerevent.value_type =="string":
            self.g.add((biomarkerevent_URI, self.MIMIC_Namespace['hasValue'], Literal(biomarkerevent.has_value, datatype=XSD.string)))
        if biomarkerevent.value_type =="decimal":
            self.g.add((biomarkerevent_URI, self.MIMIC_Namespace['hasValue'], Literal(biomarkerevent.has_value, datatype=XSD.decimal)))
        if biomarkerevent.value_type =="integer":
            self.g.add((biomarkerevent_URI, self.MIMIC_Namespace['hasValue'], Literal(biomarkerevent.has_value, datatype=XSD.integer)))


        #range lower and upper
        self.g.add((biomarkerevent_URI, self.MIMIC_Namespace['hasRefRangeLower'], Literal(biomarkerevent.has_range_lower, datatype=XSD.string)))
        self.g.add((biomarkerevent_URI, self.MIMIC_Namespace['hasRefRangeUpper'], Literal(biomarkerevent.has_range_upper, datatype=XSD.string)))


        #instant (hasTime)
        time_formatted = biomarkerevent.time_formated()

        instant_URI = self.MIMIC_Namespace[f"instant/BiomarkerEvent_{biomarkerevent.has_biomarker_type}_{str(patient.has_subject_id)}_{str(icustay.has_stay_id)}_{str(time_formatted)}"]
        self.write_instant(date_time=biomarkerevent.has_time, URI=instant_URI)
        self.g.add((biomarkerevent_URI,self.TIME_Namespace.hasTime,instant_URI))

        #BiomarkerEvent -- concernsPatient --> Patient
        self.g.add((biomarkerevent_URI,self.MIMIC_Namespace.concernsPatient, patient.URI))

        #BiomarkerEvent -- associatedWithICUStay --> ICUStay
        self.g.add((biomarkerevent_URI,self.MIMIC_Namespace.associatedWithICUStay, icustay.URI))

        #BiomarkerEvent -- associatedWithICUDay --> ICUDay
        day_number = icustay.day_number_for_datetime(biomarkerevent.has_time)

    
        day_URI = self.MIMIC_Namespace[f"icuday/{str(icustay.has_stay_id)}_{str(day_number)}"]
        self.g.add((biomarkerevent_URI,self.MIMIC_Namespace.associatedWithICUDay, day_URI))

        #Patient -- hasEvent --> BiomarkerEvent
        self.g.add((patient.URI,self.MIMIC_Namespace.hasEvent, biomarkerevent_URI))

        #ICUStay -- hasICUStayEvent --> BiomarkerEvent
        self.g.add((icustay.URI,self.MIMIC_Namespace.hasICUStayEvent, biomarkerevent_URI))

        #ICUDay -- hasICUDayEvent --> BiomarkerEvent
        self.g.add((day_URI,self.MIMIC_Namespace.hasICUDayEvent, biomarkerevent_URI))

        self.write()



    #-- CLINICAL SIGN EVENT --
    def write_clinicalsignevent(self,clinicalsignevent,patient,icustay):
       
        #URI
        clinicalsignevent_URI = clinicalsignevent.URI
        self.g.add((clinicalsignevent_URI, RDF.type, OWL.NamedIndividual))
        self.g.add((clinicalsignevent_URI, RDF.type, self.MIMIC_Namespace['ClinicalSignEvent']))
        self.g.add((clinicalsignevent_URI, RDFS.label, Literal("CS-"+clinicalsignevent.has_clinical_sign_name, lang="en")))

        #Value = DECIMAL
        self.g.add((clinicalsignevent_URI, self.MIMIC_Namespace['hasValue'], Literal(clinicalsignevent.has_value, datatype=XSD.decimal)))

        #Type (create if not exist)
        typeURI = clinicalsignevent.typeURI
        if typeURI not in self.list_clinicalsign_type:
            self.list_clinicalsign_type.append(typeURI)
            self.g.add((typeURI, RDF.type, OWL.NamedIndividual))
            self.g.add((typeURI, RDF.type, self.MIMIC_Namespace['ClinicalSignType']))
            self.g.add((typeURI, RDFS.label, Literal(clinicalsignevent.has_clinical_sign_name, lang="en")))
        self.g.add((clinicalsignevent_URI, self.MIMIC_Namespace['hasClinicalSignType'], typeURI))


        #Category (create if not exist)
        category_URI = clinicalsignevent.categoryURI
        if category_URI not in self.list_clinicalsign_category:
            self.list_clinicalsign_category.append(category_URI)
            self.g.add((category_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((category_URI, RDF.type, self.MIMIC_Namespace['ClinicalSignCategory']))
            self.g.add((category_URI, RDFS.label, Literal(clinicalsignevent.has_category, lang="en")))
        self.g.add((clinicalsignevent_URI, self.MIMIC_Namespace['hasCategory'], category_URI))

        #Unit (create if not exist)
        unit_URI = clinicalsignevent.unitURI
        if unit_URI not in self.list_unit:
            self.list_unit.append(unit_URI)
            self.g.add((unit_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((unit_URI, RDF.type, self.MIMIC_Namespace['Unit']))
            self.g.add((unit_URI, RDFS.label, Literal(clinicalsignevent.has_unit, lang="en")))
        self.g.add((clinicalsignevent_URI, self.MIMIC_Namespace['hasUnit'], unit_URI))


        #instant (hasTime)
        time_formatted = clinicalsignevent.time_formated()
        instant_URI = self.MIMIC_Namespace[f"instant/ClinicalSignEvent_{clinicalsignevent.has_clinical_sign_type}_{str(patient.has_subject_id)}_{str(icustay.has_stay_id)}_{str(time_formatted)}"]
        self.write_instant(date_time=clinicalsignevent.has_time, URI=instant_URI)
        self.g.add((clinicalsignevent_URI,self.TIME_Namespace.hasTime,instant_URI))

        #ClinicalSignEvent -- concernsPatient --> Patient
        self.g.add((clinicalsignevent_URI,self.MIMIC_Namespace.concernsPatient, patient.URI))

        #ClinicalSignEvent -- associatedWithICUStay --> ICUStay
        self.g.add((clinicalsignevent_URI,self.MIMIC_Namespace.associatedWithICUStay, icustay.URI))

        #ClinicalSignEvent -- associatedWithICUDay --> ICUDay
        day_number = icustay.day_number_for_datetime(clinicalsignevent.has_time)

        day_URI = self.MIMIC_Namespace[f"icuday/{str(icustay.has_stay_id)}_{str(day_number)}"]
        self.g.add((clinicalsignevent_URI,self.MIMIC_Namespace.associatedWithICUDay, day_URI))

        #Patient -- hasEvent --> ClinicalSignEvent
        self.g.add((patient.URI,self.MIMIC_Namespace.hasEvent, clinicalsignevent_URI))

        #ICUStay -- hasICUStayEvent --> ClinicalSignEvent
        self.g.add((icustay.URI,self.MIMIC_Namespace.hasICUStayEvent, clinicalsignevent_URI))

        #ICUDay -- hasICUDayEvent --> ClinicalSignEvent
        self.g.add((day_URI,self.MIMIC_Namespace.hasICUDayEvent, clinicalsignevent_URI))

        self.write()




    #-- MICROBIOLOGY EVENT --
    def write_microbiologyevent(self,microbiologyevent,patient,icustay):
        
        #URI
        microbiologyevent_URI = microbiologyevent.URI
        self.g.add((microbiologyevent_URI, RDF.type, OWL.NamedIndividual))
        self.g.add((microbiologyevent_URI, RDF.type, self.MIMIC_Namespace['MicroBiologyEvent']))
        self.g.add((microbiologyevent_URI, RDFS.label, Literal("MB-"+microbiologyevent.has_specimen_type, lang="en")))

        #Specimen URI(create if not exist) (default is Blood)
        specimen_URI = microbiologyevent.specimen_URI
        if specimen_URI not in self.list_microbio_specimen_type:
            self.list_microbio_specimen_type.append(specimen_URI)
            self.g.add((specimen_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((specimen_URI, RDF.type, self.MIMIC_Namespace['SpecimenType']))
            self.g.add((specimen_URI, RDFS.label, Literal(microbiologyevent.has_specimen_type, lang="en")))
        self.g.add((microbiologyevent_URI, self.MIMIC_Namespace['hasSpecimenType'], specimen_URI))

        #Culture URI (create if not exist)
        cultureresult_URI = microbiologyevent.culture_URI
        if cultureresult_URI not in self.list_microbio_culture_result:
            self.list_microbio_culture_result.append(cultureresult_URI)
            self.g.add((cultureresult_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((cultureresult_URI, RDF.type, self.MIMIC_Namespace['CultureResult']))
            self.g.add((cultureresult_URI, RDFS.label, Literal(microbiologyevent.has_culture_result, lang="en")))
        self.g.add((microbiologyevent_URI, self.MIMIC_Namespace['cultureResult'], cultureresult_URI))


        #instant (hasTime)
        time_formatted = microbiologyevent.time_formated()
        instant_URI = self.MIMIC_Namespace[f"instant/MicrobiologyEvent_{microbiologyevent.has_id}_{str(time_formatted)}"]
        self.write_instant(date_time=microbiologyevent.has_time, URI=instant_URI)
        self.g.add((microbiologyevent_URI,self.TIME_Namespace.hasTime,instant_URI))


        if microbiologyevent.organism_URI != None:
            
            #Organism URI
            organism_URI = microbiologyevent.organism_URI
            if organism_URI not in self.list_microbio_organism:
                self.list_microbio_culture_result.append(organism_URI)
                self.g.add((organism_URI, RDF.type, OWL.NamedIndividual))
                self.g.add((organism_URI, RDF.type, self.MIMIC_Namespace['Organism']))
                self.g.add((organism_URI, RDFS.label, Literal(microbiologyevent.has_organism_name, lang="en")))
            self.g.add((microbiologyevent_URI, self.MIMIC_Namespace['organismFound'], organism_URI))

            #Antibiotic
            antibiotic_URI = microbiologyevent.antibiotic_URI
            if antibiotic_URI not in self.list_microbio_antibio:
                self.list_microbio_antibio.append(antibiotic_URI)
                self.g.add((antibiotic_URI, RDF.type, OWL.NamedIndividual))
                self.g.add((antibiotic_URI, RDF.type, self.MIMIC_Namespace['Antibiotic']))
                self.g.add((antibiotic_URI, RDFS.label, Literal(microbiologyevent.has_antibiotic_name, lang="en")))

            #Interpretation
            interpretation_URI = microbiologyevent.interpretation_URI
            if interpretation_URI not in self.list_microbio_interpretation:
                self.list_microbio_antibio.append(interpretation_URI)
                self.g.add((interpretation_URI, RDF.type, OWL.NamedIndividual))
                self.g.add((interpretation_URI, RDF.type, self.MIMIC_Namespace['Interpretation']))
                self.g.add((interpretation_URI, RDFS.label, Literal(microbiologyevent.has_interpretation, lang="en")))

            #AntibioticTest
            antibiotictest_URI = microbiologyevent.antibiotictest_URI
            self.g.add((antibiotictest_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((antibiotictest_URI, RDF.type, self.MIMIC_Namespace['AntibioticTest']))
            self.g.add((antibiotictest_URI, self.MIMIC_Namespace['testedAntibiotic'],antibiotic_URI))
            self.g.add((antibiotictest_URI, self.MIMIC_Namespace['hasTestInterpretation'],interpretation_URI))
            self.g.add((microbiologyevent_URI, self.MIMIC_Namespace['hasAntibioticTest'], antibiotictest_URI))
        
        #MicrobiologyEvent -- concernsPatient --> Patient
        self.g.add((microbiologyevent_URI,self.MIMIC_Namespace.concernsPatient, patient.URI))

        #MicrobiologyEvent -- associatedWithICUStay --> ICUStay
        self.g.add((microbiologyevent_URI,self.MIMIC_Namespace.associatedWithICUStay, icustay.URI))

        #MicrobiologyEvent -- associatedWithICUDay --> ICUDay
        day_number = icustay.day_number_for_datetime(microbiologyevent.has_time)
        day_URI = self.MIMIC_Namespace[f"icuday/{str(icustay.has_stay_id)}_{str(day_number)}"]
        self.g.add((microbiologyevent_URI,self.MIMIC_Namespace.associatedWithICUDay, day_URI))

        #Patient -- hasEvent --> ClinicalSignEvent
        self.g.add((patient.URI,self.MIMIC_Namespace.hasEvent, microbiologyevent_URI))

        #ICUStay -- hasICUStayEvent --> ClinicalSignEvent
        self.g.add((icustay.URI,self.MIMIC_Namespace.hasICUStayEvent, microbiologyevent_URI))

        #ICUDay -- hasICUDayEvent --> ClinicalSignEvent
        self.g.add((day_URI,self.MIMIC_Namespace.hasICUDayEvent, microbiologyevent_URI))


        self.write()


    #-- ANTIBIOTIC PRESCRIPTION EVENT --
    def write_antibioticprescriptionevent(self,prescriptionevent,patient,icustay):

        #URI
        prescriptionevent_URI = prescriptionevent.URI
        self.g.add((prescriptionevent_URI, RDF.type, OWL.NamedIndividual))
        self.g.add((prescriptionevent_URI, RDF.type, self.MIMIC_Namespace['AntibioticPrescriptionEvent']))
        self.g.add((prescriptionevent_URI, RDFS.label, Literal("AB-"+prescriptionevent.has_drug_name, lang="en")))


        #Dose -- Must be a String
        self.g.add((prescriptionevent_URI, self.MIMIC_Namespace['hasDose'], Literal(prescriptionevent.has_dose, datatype=XSD.string)))

        #Route
        self.g.add((prescriptionevent_URI, self.MIMIC_Namespace['hasRoute'], Literal(prescriptionevent.has_route, datatype=XSD.string)))

        
        #Unit (create if not exist)
        unit_URI = prescriptionevent.unit_URI
        if unit_URI not in self.list_unit:
            self.list_unit.append(unit_URI)
            self.g.add((unit_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((unit_URI, RDF.type, self.MIMIC_Namespace['Unit']))
            self.g.add((unit_URI, RDFS.label, Literal(prescriptionevent.has_unit, lang="en")))
        self.g.add((prescriptionevent_URI, self.MIMIC_Namespace['hasUnit'], unit_URI))
        
        
        #Antibiotic (create if not exist)
        antibiotic_URI = prescriptionevent.antibiotic_URI
        if antibiotic_URI not in self.list_microbio_antibio:
            self.list_microbio_antibio.append(antibiotic_URI)
            self.g.add((antibiotic_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((antibiotic_URI, RDF.type, self.MIMIC_Namespace['Antibiotic']))
            self.g.add((antibiotic_URI, RDFS.label, Literal(prescriptionevent.has_drug_name, lang="en")))
        self.g.add((prescriptionevent_URI, self.MIMIC_Namespace['administersDrug'], antibiotic_URI))
        

        #Beginning
        begin_URI = self.MIMIC_Namespace[f"instant/AntibioticPrescriptionEventBegin_{prescriptionevent.has_id}"]
        self.write_instant(date_time=prescriptionevent.has_beginning, URI=begin_URI)
        self.g.add((prescriptionevent_URI,self.TIME_Namespace.hasBeginning,begin_URI))

        #End
        end_URI =  self.MIMIC_Namespace[f"instant/AntibioticPrescriptionEventEnd_{prescriptionevent.has_id}"]
        self.write_instant(date_time=prescriptionevent.has_end, URI=end_URI)
        self.g.add((prescriptionevent_URI,self.TIME_Namespace.hasEnd,end_URI))

        
        #AntibioticPrescriptionEvent -- concernsPatient --> Patient
        self.g.add((prescriptionevent_URI,self.MIMIC_Namespace.concernsPatient, patient.URI))

        #AntibioticPrescriptionEvent -- associatedWithICUStay --> ICUStay
        self.g.add((prescriptionevent_URI,self.MIMIC_Namespace.associatedWithICUStay, icustay.URI))

        #AntibioticPrescriptionEvent -- associatedWithICUDay --> ICUDay
        day_number = icustay.day_number_for_datetime(prescriptionevent.has_beginning)
        day_URI = self.MIMIC_Namespace[f"icuday/{str(icustay.has_stay_id)}_{str(day_number)}"]
        self.g.add((prescriptionevent_URI,self.MIMIC_Namespace.associatedWithICUDay, day_URI))

        #Patient -- hasEvent --> AntibioticPrescriptionEvent
        self.g.add((patient.URI,self.MIMIC_Namespace.hasEvent, prescriptionevent_URI))

        #ICUStay -- hasICUStayEvent --> AntibioticPrescriptionEvent
        self.g.add((icustay.URI,self.MIMIC_Namespace.hasICUStayEvent, prescriptionevent_URI))

        #ICUDay -- hasICUDayEvent --> AntibioticPrescriptionEvent
        self.g.add((day_URI,self.MIMIC_Namespace.hasICUDayEvent, prescriptionevent_URI))
        


        self.write()


    #-- DIAGNOSIS EVENT --
    def write_diagnosisevent(self,diagnosisevent,patient,icustay):

        #URI
        diagnosisevent_URI = diagnosisevent.URI
        self.g.add((diagnosisevent_URI, RDF.type, OWL.NamedIndividual))
        self.g.add((diagnosisevent_URI, RDF.type, self.MIMIC_Namespace['DiagnosisEvent']))
        self.g.add((diagnosisevent_URI, RDFS.label, Literal("DG-"+diagnosisevent.icd_label, lang="en")))

        #ICD CODE (create if not exist)
        icd_URI = diagnosisevent.icd_URI
        if icd_URI not in self.list_icd:
            self.list_icd.append(icd_URI)
            self.g.add((icd_URI, RDF.type, OWL.NamedIndividual))
            self.g.add((icd_URI, RDF.type, self.MIMIC_Namespace['ICDCode']))
            self.g.add((icd_URI, RDFS.label, Literal(diagnosisevent.icd_label, lang="en")))
            self.g.add((icd_URI, self.MIMIC_Namespace['codeValue'], Literal(diagnosisevent.icd_code, datatype=XSD.string)))
            self.g.add((icd_URI, self.MIMIC_Namespace['isSepsis'], Literal(diagnosisevent.is_sepsis(), datatype=XSD.boolean)))
            self.g.add((icd_URI, self.MIMIC_Namespace['icdVersion'], Literal(diagnosisevent.icd_version, datatype=XSD.string)))
        self.g.add((diagnosisevent_URI, self.MIMIC_Namespace['hasICD'], icd_URI))


        #DiagnosisEvent -- concernsPatient --> Patient
        self.g.add((diagnosisevent_URI,self.MIMIC_Namespace.concernsPatient, patient.URI))

        #DiagnosisEvent -- associatedWithICUStay --> ICUStay
        self.g.add((diagnosisevent_URI,self.MIMIC_Namespace.associatedWithICUStay, icustay.URI))
        
        #Patient -- hasEvent --> AntibioticPrescriptionEvent
        self.g.add((patient.URI,self.MIMIC_Namespace.hasEvent, diagnosisevent_URI))

        #ICUStay -- hasICUStayEvent --> AntibioticPrescriptionEvent
        self.g.add((icustay.URI,self.MIMIC_Namespace.hasICUStayEvent, diagnosisevent_URI))

        self.write()


    #-- COMORBIDITY --
    def write_comorbidity(self,patient):

        patient_URI = patient.URI

        #Charlson
        self.g.add((patient_URI, self.MIMIC_Namespace['charlson'], Literal(patient.charlson_score, datatype=XSD.integer)))

        #Comorbidity
        for c in patient.has_comorbidity:
            if c['exist']:
                comorbidity_URI = c['URI']
                if comorbidity_URI not in self.list_comorbidity:
                    self.list_comorbidity.append(comorbidity_URI)
                    self.g.add((comorbidity_URI, RDF.type, OWL.NamedIndividual))
                    self.g.add((comorbidity_URI, RDF.type, self.MIMIC_Namespace['Comorbidity']))
                    self.g.add((comorbidity_URI, RDFS.label, Literal("CO-"+c['label'], lang="en")))
                self.g.add((patient_URI, self.MIMIC_Namespace['hasComorbidity'], comorbidity_URI))

        self.write()
                
































  


        






