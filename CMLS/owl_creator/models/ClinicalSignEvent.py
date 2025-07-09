from CMLS.owl_creator.models.Event import Event

class ClinicalSignsEvent(Event):

    def __init__(self,clinicalsignName,clinicalsignType,value,unit,category,time,URI,typeURI,unitURI,categoryURI):
        self.has_clinical_sign_name = clinicalsignName
        self.has_clinical_sign_type = clinicalsignType
        self.has_value = value
        self.has_unit = unit
        self.has_category = category
        self.has_time = time
        self.URI= URI
        self.typeURI = typeURI
        self.categoryURI = categoryURI
        self.unitURI = unitURI
    
    def time_formated(self):
        dt_py = self.has_time.astype('M8[s]').astype(object)
        return(dt_py.strftime('%Y%m%dT%H%M'))