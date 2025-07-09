from CMLS.owl_creator.models.Event import Event

class MicrobiologyEvent(Event):
    def __init__(self, microbiology_id,specimenType,time, organismName, antibiotic,interpretation,cultureResult, URI,antibiotic_URI,organism_URI,culture_URI,specimen_URI,antibiotic_test_URI,interpretation_URI):

        
        self.has_time = time
        self.URI = URI
        self.has_antibiotic_name = antibiotic
        self.has_interpretation = interpretation
        self.has_id = microbiology_id
        self.has_culture_result = cultureResult
        self.has_specimen_type = specimenType
        self.has_organism_name  = organismName

        self.antibiotic_URI = antibiotic_URI
        self.organism_URI = organism_URI
        self.culture_URI = culture_URI
        self.specimen_URI = specimen_URI
        self.antibiotictest_URI = antibiotic_test_URI
        self.interpretation_URI = interpretation_URI

    def time_formated(self):
        dt_py = self.has_time.astype('M8[s]').astype(object)
        return(dt_py.strftime('%Y%m%dT%H%M'))