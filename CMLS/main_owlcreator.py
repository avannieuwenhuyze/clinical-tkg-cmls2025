
from CMLS.owl_creator.applications.app_owl_creator import App_owl_creator

    
"""  
A SUPPRIMER DANS ONTOLOGIE:

  <owl:Ontology rdf:about="http://www.cnam.fr/MIMIC4-ICU-BSI/V1">
    <owl:imports rdf:resource="http://www.w3.org/2006/time#2016"/>
  </owl:Ontology>

"""
            
if __name__ == "__main__":
        
        # === Processus intanciation ===
        app_creator = App_owl_creator(mimic_ini= "ontologies/CMLS/owl_creator/config/mimic_owl.ini",
                                      ontology_name="INSTANCES-MIMIC-IV-Temporal-BSI-V1-0-1.rdf")


        # === Processus ===
        # LIMITS (number of patients, biomarker...) are defined in the mimic_owl.ini file
        app_creator.create_ontology()


    



    
    




