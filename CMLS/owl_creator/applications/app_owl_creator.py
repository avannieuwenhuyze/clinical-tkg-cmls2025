
#Logger
from CMLS.owl_creator.tools.log_manager import get_logger

#DukeDatabase
from CMLS.owl_creator.database.duck_database import Duck_database

#Queries
from CMLS.owl_creator.database.queries import Queries

#Writer
from CMLS.owl_creator.applications.owl_writer import OWL_Writer


#Config parser
import configparser

#For the URI construction
from rdflib import Namespace

#Progress Bar
import os
from tqdm import tqdm
import time
from datetime import datetime


#-- 
# MODELS 
# --
from CMLS.owl_creator.models.Patient import Patient
from CMLS.owl_creator.models.ICUStay import ICUStay
from CMLS.owl_creator.models.ICUDay import ICUDay
from CMLS.owl_creator.models.BioMarkerEvent import BioMarkerEvent
from CMLS.owl_creator.models.ClinicalSignEvent import ClinicalSignsEvent
from CMLS.owl_creator.models.MicrobiologyEvent import MicrobiologyEvent
from CMLS.owl_creator.models.AntibioticPrescriptionEvent import AntibioticPrescriptionEvent
from CMLS.owl_creator.models.DiagnosisEvent import DiagnosisEvent


"""  
    !!
    DON'T FORGET TO CHANGE THE mimic_name_space PARAMETER IN THE CONFIG FILE.
    !!
"""

class App_owl_creator():

    def __init__(self,mimic_ini,ontology_name):
    

        #-- MIMIC CONFIG FILE--
        self.config_path = mimic_ini
        config = configparser.ConfigParser()
        config.read(self.config_path)

        #Mimic_namespace
        self.MIMIC_Namespace = Namespace(config["ONTOLOGY"].get("mimic_name_space"))


        #--- LOGGER ---
        self.logger = get_logger()
        #self.logger.info("OWL Creator initialisation")

        #--- DUCK DATABASE ---
        self.db = Duck_database(self.config_path)
        self.db.test()

        #--- SQL QUERIES ---
        self.queries = Queries(self.config_path)

        #--- OWL WRITER ---
        self.owl_writer = OWL_Writer(self.config_path,ontology_name)


        #--- SYNHETICS ID ---
        self.clinical_sign_id = 1
        self.antibiotic_test_id = 1
        self.antibiotic_prescription_id = 1
        self.diagnosis_id = 1

        #--- LIMITS --
        self.limit_patients = config["LIMITS"].get("patients_limit")
        self.limit_biomarkers = config["LIMITS"].get("biomarkers_limit")
        self.limit_clinicalsigns = config["LIMITS"].get("clinicals_signs_limit")
        self.limit_microbiology = config["LIMITS"].get("microbiology_limit")
        self.limit_antibiotics_prescription = config["LIMITS"].get("antibiotics_prescriptions_limit")
        self.limit_diagnosis = config["LIMITS"].get("diagnosis_limit")
        self.limit_comorbidity = config["LIMITS"].get("comorbidity_limit")
       



    def get_cohort(self):
        """
            Executes the cohort selection process and stores the result.

            This method logs the start of the cohort creation process, calls the cohort selection
            query, and stores the resulting DataFrame in `self.cohort`. It also logs the number of
            patients selected.

            Returns:
                dataframe
        """
        self.logger.info(">>  ============  COHORT CREATION ============")
        self.cohort = self.queries.cohort_selection(self.limit_patients)
        self.logger.info(">>... Number of patients : "+str(self.cohort.shape[0]))
        return self.cohort
    
    

    def create_ontology(self,cohort=None):
        
        if cohort is None:
            self.get_cohort()

        number_of_patients = self.cohort.shape[0]
        os.system('cls' if os.name == 'nt' else 'clear')
        self.logger.info(">>  ============  ONTOLOGY CREATION ============")
        self.logger.info(">>... Number of patients : "+str(number_of_patients))
        start_time = datetime.now()
        self.logger.info(">> Process started at : "+ start_time.strftime("%Y-%m-%d %H:%M:%S"))

        for i in tqdm(range(number_of_patients), desc="Ontology creation",colour="green"):

            data = self.cohort.iloc[i]

            subject_id = data['subject_id']
            hadm_id = data['hadm_id']
            stay_id = data['stay_id']

            #-- PATIENT --
            ##self.logger.info(">> .. Patients ["+str(subject_id)+"]  -> "+str(i+1)+"/"+str(number_of_patients))
            patient_informations = self.queries.get_patient_informations(subject_id,
                                                                         hadm_id)
            
            patient_sepsis3 = self.queries.get_sepsis3(subject_id,stay_id)

            if (patient_sepsis3['isSepsis'][0] == 1):
                sepsis3= True
            else:
                sepsis3 = False

            patient = Patient( subject_id=patient_informations["subject_id"][0],
                               gender= patient_informations["gender"][0],
                               age = patient_informations["age"][0],
                               URI = self.MIMIC_Namespace[f"patient/{str(subject_id)}"],
                               comorbidity=None,
                               charlson=None,
                               sepsis3=sepsis3)
            self.owl_writer.write_patient(patient)

            #-- ICU STAY --
            icustay_informations = self.queries.get_icustay_informations(subject_id=subject_id, 
                                                            hadm_id=hadm_id,
                                                            stay_id=stay_id)
            #self.logger.info(">>    + ICU Stay ["+str(stay_id)+"]")
            icustay = ICUStay(stay_id=stay_id,
                              begin_datetime=icustay_informations["hasBeginning"][0],
                              end_datetime=icustay_informations["hasEnd"][0],
                              URI=self.MIMIC_Namespace[f"icustay/{str(stay_id)}"])
            self.owl_writer.write_icustay(icustay=icustay, patient=patient)


            #-- ICU DAYS --
            days = icustay.days()
            for day in days:
                day_number = day[0]
                day_beginning = day[1]
                day_end = day[2]
                URI = self.MIMIC_Namespace[f"icuday/{str(stay_id)}_{str(day_number)}"]
                icuday = ICUDay(number=day_number,begin_datetime=day_beginning,end_datetime=day_end,URI=URI)
                #self.logger.info(">>    + ICU Day ["+str(day_number)+"]")
                self.owl_writer.write_icuday(icustay,icuday)


            #-- BIOMARKERS EVENT --
            biomarkers = self.queries.get_biomarkers(subject_id=subject_id,hadm_id=hadm_id,limit=self.limit_biomarkers,icu_begin=icustay.has_beginning, icu_end=icustay.has_end)
            nb_biomarkers = len(biomarkers['hasBiomarkerName'])
    
            for i in tqdm(range(nb_biomarkers), desc="  Biomarkers", position=1, leave=False,colour="cyan"):

                creation=True;

                #Name
                hasBiomarkerName = biomarkers['hasBiomarkerName'][i].replace("/","-").replace("%","")

                #Type
                hasBiomarkerType = biomarkers['hasBiomarkerName'][i].replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","")

                #URI
                hasBiomarkerName_URI = biomarkers['hasBiomarkerName'][i].replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","")
                URI_id = hasBiomarkerName_URI+'_'+str(biomarkers['id'][i])+"_"+str(subject_id)+"_"+str(stay_id)
                URI = self.MIMIC_Namespace[f"biomarkerevent/{URI_id}"]

                value = biomarkers['hasValue'][i]
                valueNum = biomarkers['hasValueNum'][i]
                valueText = biomarkers['hasValueText'][i]
                hasValueType = ""
                if not value and not valueNum and not valueText:
                    self.logger.error("         Rejet : aucune valeur renseignée")
                    creation = False
                elif valueNum and not value:
                    hasValueType = "decimal"
                    hasValue = valueNum
                elif value and not valueNum:
                    hasValueType = "string"
                    hasValue = value
                elif value and valueNum:
                    hasValueType = "decimal"
                    hasValue = valueNum
                elif not value and not valueNum and valueText:
                    hasValueType = "string"
                    hasValue = valueText

                hasUnit = biomarkers['hasUnit'][i]
                hasCategory = biomarkers['hasCategory'][i]
                hasSpecimenType = biomarkers['hasSpecimenType'][i].upper()
                hasTime = biomarkers['hasTime'][i]
                hasRangeLower = biomarkers['hasRefRangeLower'][i]
                hasRangeUpper = biomarkers['hasRefRangeUpper'][i]


                #URI for Type, category,unit and specimen
                typeURI = self.MIMIC_Namespace[f"biomarkertype/{hasBiomarkerType}"]
                category_URI = hasCategory.replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").upper()
                category_URI = self.MIMIC_Namespace[f"biomarkercategory/{category_URI}"]
                unit_URI =  str(hasUnit).replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").upper()
                unit_URI = self.MIMIC_Namespace[f"unit/{unit_URI}"]
                specimen_URI = hasSpecimenType.replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").upper()
                specimen_URI = self.MIMIC_Namespace[f"specimentype/{specimen_URI}"]

                if creation :
                    biomarkerevent = BioMarkerEvent(biomarkerName=hasBiomarkerName, 
                                                    biomarkerType=hasBiomarkerType,
                                            category=hasCategory,
                                            specimen_type=hasSpecimenType, 
                                            unit=hasUnit,URI=URI, 
                                            value=hasValue, 
                                            value_type=hasValueType, 
                                            time=hasTime,
                                            range_lower=hasRangeLower,
                                            ranger_upper=hasRangeUpper,
                                            specimenURI=specimen_URI,
                                            categoryURI=category_URI,
                                            typeURI=typeURI,
                                            unitURI=unit_URI)
                    #self.logger.info(">>    + BiomarkerEvent ["+str(hasBiomarkerType)+"]")
                    self.owl_writer.write_biomarkerevent(biomarkerevent=biomarkerevent, icustay=icustay, patient=patient)

            
            #-- CLINICAL EVENT --
            clinical_signs = self.queries.get_clinicals_signs(subject_id=subject_id,stay_id=stay_id,limit=self.limit_clinicalsigns,icu_begin=icustay.has_beginning,icu_end=icustay.has_end)
            nb_clinical_signs = len(clinical_signs['hasClinicalSignType'])
            
            for i in tqdm(range(nb_clinical_signs), desc="  Clinical signs", position=1, leave=False,colour="cyan"):
                
                #Name
          
                hasClinicalSignName = clinical_signs['hasClinicalSignType'][i].replace("/","-")
     
                #Type
                hasClinicalSignType = clinical_signs['hasClinicalSignType'][i].replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","")

                
                hasUnit = clinical_signs['hasUnit'][i]
                hasCategory = clinical_signs['hasCategory'][i]
                hasTime = clinical_signs['hasTime'][i]
                hasValue = clinical_signs['hasValue'][i]


                #Temperature conversion (°F to °C)
                if hasClinicalSignType == "TemperatureFahrenheit":
                    hasClinicalSignType = "TemperatureCelcius"
                    hasValue = round((float(hasValue)-32) * (5/9),1)
                    hasUnit = "°C"
                    

                #Event URI  
                URI_id = hasClinicalSignType+'_'+str(self.clinical_sign_id)+"_"+str(subject_id)+"_"+str(stay_id)
                self.clinical_sign_id +=1  
                URI_id = hasClinicalSignType+'_'+str(self.clinical_sign_id)+"_"+str(subject_id)+"_"+str(stay_id)
                URI = self.MIMIC_Namespace[f"clinicalsignevent/{URI_id}"]
                
                
                #URI
                type_URI = self.MIMIC_Namespace[f"clinicalsigntype/{hasClinicalSignType}"]
                category_URI = hasCategory.replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").upper()
                category_URI = self.MIMIC_Namespace[f"clinicalsigncategory/{category_URI}"]
                unit_URI =  str(hasUnit).replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").upper()
                unit_URI = self.MIMIC_Namespace[f"unit/{unit_URI}"]

          
                clinicalsignevent = ClinicalSignsEvent(URI=URI, 
                                                       category=hasCategory, 
                                                       clinicalsignName=hasClinicalSignName, 
                                                       clinicalsignType=hasClinicalSignType,
                                                       time=hasTime, 
                                                       unit=hasUnit, 
                                                       value=hasValue,
                                                       unitURI=unit_URI,
                                                       categoryURI=category_URI,
                                                       typeURI=type_URI)
                
                #self.logger.info(">>    + ClinicalSignEvent ["+str(hasClinicalSignType)+"]")
                self.owl_writer.write_clinicalsignevent(clinicalsignevent=clinicalsignevent,patient=patient,icustay=icustay)
                


            #-- MICROBIOLOGY EVENT --
            microbiology = self.queries.get_microbiology(subject_id=subject_id,hadm_id=hadm_id,limit=self.limit_microbiology,icu_begin=icustay.has_beginning,icu_end=icustay.has_end)
            nb_microbiology = len(microbiology['hasTime'])

            for i in tqdm(range(nb_microbiology), desc="  Microbiology", position=1, leave=False, colour="cyan"):

                antibiotic_URI = None
                antibiotic_test_URI = None
                culture_URI = None
                interpretation_URI = None
                organism_URI = None

                hasSpecimenType="Blood"
                organismFound = microbiology['hasOrganismName'][i]
                

                if (organismFound != "--"):
                    cultureResult = "Positive"
                else:
                    cultureResult = "Negative"

                antibiotic = microbiology['hasAntibioticName'][i]
                interpretation = microbiology['hasInterpretation'][i]
                hasTime = microbiology['hasTime'][i]

                #URI
                microbiology_id = microbiology['hasId'][i]
                URI = self.MIMIC_Namespace[f"microbiologyevent/{microbiology_id}"]

                if(antibiotic != "--"):
                    antibiotic_URI = antibiotic.replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").upper()
                    antibiotic_URI = self.MIMIC_Namespace[f"antibiotic/{antibiotic_URI}"]
                   


                if(organismFound != "--"):
                    organism_URI = organismFound.replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").upper()
                    organism_URI = self.MIMIC_Namespace[f"organism/{organism_URI}"]
                    


                if(organismFound != "--"):
                    culture_URI = "Positive"
                    culture_URI = self.MIMIC_Namespace[f"culture/{culture_URI}"]
                else:
                    culture_URI = "Negative"
                    culture_URI = self.MIMIC_Namespace[f"culture/{culture_URI}"]
                
                specimen_type = "Blood"
                specimen_URI = self.MIMIC_Namespace[f"specimentype/{specimen_type}"]

                if(organismFound != "--"):
                    antibiotic_test_URI = self.MIMIC_Namespace[f"antibiotictest/test_{microbiology_id}_{self.antibiotic_test_id}"]
                    self.antibiotic_test_id += 1


                if(organismFound != "--"):
                    if(interpretation != "--"):
                        if (interpretation=="R"):
                            interpretation_URI = self.MIMIC_Namespace[f"interpretation/R"]
                        if (interpretation=="S"):
                            interpretation_URI = self.MIMIC_Namespace[f"interpretation/S"]
                        if (interpretation=="I"):
                            interpretation_URI = self.MIMIC_Namespace[f"interpretation/I"]


                microbiologyevent = MicrobiologyEvent(microbiology_id=microbiology_id,
                                                      antibiotic=antibiotic,
                                                      organismName=organismFound,
                                                      antibiotic_test_URI=antibiotic_test_URI,
                                                      antibiotic_URI=antibiotic_URI,
                                                      culture_URI=culture_URI,
                                                      cultureResult=cultureResult,
                                                      interpretation=interpretation,
                                                      interpretation_URI=interpretation_URI,
                                                      organism_URI=organism_URI,
                                                      specimen_URI=specimen_URI,
                                                      specimenType=specimen_type,
                                                      time=hasTime,
                                                      URI=URI)
                
                #self.logger.info(">>    + MicrobilogyEvent ["+str(microbiology_id)+"]")
                self.owl_writer.write_microbiologyevent(microbiologyevent=microbiologyevent,patient=patient,icustay=icustay)

            
            #-- ANTIBIOTIC PRESCRIPTION EVENT --
            antibiotics = self.queries.get_antibiotics_prescriptions(subject_id=subject_id,hadm_id=hadm_id,limit=self.limit_antibiotics_prescription,icu_begin=icustay.has_beginning,icu_end=icustay.has_end)
            nb_antibiotics = len(antibiotics['hasBeginning'])

            for i in tqdm(range(nb_antibiotics), desc="  Antibiotics", position=1, leave=False,colour="cyan"):

                #URI
                hasId = self.antibiotic_prescription_id
                URI = self.MIMIC_Namespace[f"AntibioticPrescriptionEvent/Prescription_{hasId}"]
                self.antibiotic_prescription_id +=1

                #ANTIBIOTIC
                antibiotic = antibiotics['administerDrug'][i]
                antibiotic_URI = antibiotic.replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").replace(".","").upper()
                antibiotic_URI = self.MIMIC_Namespace[f"antibiotic/{antibiotic_URI}"]

                #DOSE
                dose = antibiotics['hasDose'][i]

                #UNIT
                hasUnit = antibiotics['hasUnit'][i]
                unit_URI =  str(hasUnit).replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").replace(".","").upper()
                unit_URI = self.MIMIC_Namespace[f"unit/{unit_URI}"]

                #ROUTE
                hasRoute = antibiotics['hasRoute'][i]

                #PERIOD
                hasBeginning = antibiotics['hasBeginning'][i]
                hasEnd = antibiotics['hasEnd'][i]
                hasDuration = antibiotics['hasDuration'][i]

                antibioticprescriptionevent = AntibioticPrescriptionEvent(id=hasId,
                                                                          drug =antibiotic,
                                                                          antibioticURI=antibiotic_URI,
                                                                          beginning=hasBeginning,
                                                                          dose=dose,
                                                                          duration=hasDuration,
                                                                          end=hasEnd,
                                                                          route=hasRoute,
                                                                          unit=hasUnit,
                                                                          unitURI=unit_URI,
                                                                          URI=URI)
                
                #self.logger.info(">>    + AntibioticPrescriptionEvent ["+str(hasId)+"]")
                self.owl_writer.write_antibioticprescriptionevent(prescriptionevent=antibioticprescriptionevent,patient=patient,icustay=icustay)



            #--- DIAGNOSIS ---
            #-- There is no date for the diagnosis --
            diagnosis = self.queries.get_diagnosis(subject_id=subject_id,hadm_id=hadm_id,limit=self.limit_diagnosis)
            nb_diagnosis = len(diagnosis['hasICDCode'])

            for i in tqdm(range(nb_diagnosis), desc="  Diagnosis", position=1, leave=False,colour="cyan"):

                #URI
                hasId = self.diagnosis_id
                URI = self.MIMIC_Namespace[f"DiagnosisEvent/Diagnosis_{hasId}"]
                self.diagnosis_id +=1

                #ICDCode
                hasICDCode = diagnosis['hasICDCode'][i]
                icdcode_URI = str(hasICDCode).replace(" ","").replace("/","-").replace("(","").replace(")","").replace(",","_").replace("%","").replace(".","").upper()
                icdcode_URI = "ICD_"+str(icdcode_URI)
                icdcode_URI = self.MIMIC_Namespace[f"icdcode/{icdcode_URI}"]

                #ICDVersion
                hasICDVersion = diagnosis['hasICDVersion'][i]

                #ICDLabel
                hasDiagnosisLabel = diagnosis['diagnosis_label'][i]

                diagnosisevent = DiagnosisEvent(id=hasId, icd_code=hasICDCode, icd_label=hasDiagnosisLabel, icd_URI=icdcode_URI,icd_version=hasICDVersion,URI=URI)

                #self.logger.info(">>    + DiagnosisEvent ["+str(hasICDCode)+"]")
                self.owl_writer.write_diagnosisevent(diagnosisevent=diagnosisevent,patient=patient,icustay=icustay)


            #-- COMORBIDITY --
            comorbidity = self.queries.get_comorbidity(subject_id=subject_id,hadm_id=hadm_id,limit=self.limit_comorbidity)
            nb_comorbidity = len(comorbidity['subject_id'])
            for i in tqdm(range(nb_comorbidity), desc="  Comorbidities", position=1, leave=False,colour="cyan"):

                patient.has_comorbidity = [
                        {'URI': self.MIMIC_Namespace[f"comorbidity/MyocardialInfarct"],'label':'Myocardial infarction','exist':bool(comorbidity['myocardial_infarct'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/CongestiveHeartFailure"],'label':'Congestive heart failure','exist':bool(comorbidity['congestive_heart_failure'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/PeripheralVascularDisease"],'label':'Peripheral vascular disease','exist':bool(comorbidity['peripheral_vascular_disease'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/CerebrovascularDisease"],'label':'Cerebrovascular disease','exist':bool(comorbidity['cerebrovascular_disease'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/Dementia"],'label':'Dementia','exist':bool(comorbidity['dementia'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/ChronicPulmonaryDisease"],'label':'Chronic pulmonary disease','exist':bool(comorbidity['chronic_pulmonary_disease'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/RheumaticDisease"],'label':'Rheumatic disease','exist':bool(comorbidity['rheumatic_disease'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/PepticUlcerDisease"],'label':'Peptic ulcer disease','exist':bool(comorbidity['peptic_ulcer_disease'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/MildLiverDisease"],'label':'Mild liver disease','exist':bool(comorbidity['mild_liver_disease'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/DiabetesWithoutComplication"],'label':'Diabetes without chronic complication','exist':bool(comorbidity['diabetes_without_cc'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/DiabetesWithComplication"],'label':'Diabetes with chronic complication','exist':bool(comorbidity['diabetes_with_cc'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/Paraplegia"],'label':'Paraplegia or hemiplegia','exist':bool(comorbidity['paraplegia'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/RenalDisease"],'label':'Renal disease','exist':bool(comorbidity['renal_disease'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/MalignantCancer"],'label':'Malignant cancer','exist':bool(comorbidity['malignant_cancer'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/SevereLiverDisease"],'label':'Moderate or severe liver disease','exist':bool(comorbidity['severe_liver_disease'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/MetastaticSolidTumor"],'label':'Metastatic solid tumor','exist':bool(comorbidity['metastatic_solid_tumor'][i])},
                        {'URI': self.MIMIC_Namespace[f"comorbidity/AIDS"],'label':'AIDS or HIV infection','exist':bool(comorbidity['aids'][i])},
                ]

                patient.charlson_score = comorbidity['charlson_comorbidity_index'][i]


                self.owl_writer.write_comorbidity(patient=patient)
            

            #Pause before the next patient
            time.sleep(0.1)

        
        end_time = datetime.now()
        duration = end_time - start_time
        self.logger.info(">> Process completed at : "+ start_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.logger.info(">> Duration :" +str(duration))
           

              








                



















            




            



                    






        




        





            






        

