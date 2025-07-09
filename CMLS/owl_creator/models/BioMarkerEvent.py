from CMLS.owl_creator.models.Event import Event

class BioMarkerEvent(Event):

    def __init__(self,biomarkerName,biomarkerType, value,value_type,unit,specimen_type,category,time,range_lower,ranger_upper,URI,typeURI,categoryURI,unitURI,specimenURI):
        self.has_biomarker_name = biomarkerName
        self.has_biomarker_type = biomarkerType
        self.has_value = value
        self.value_type = value_type
        self.has_unit = unit
        self.has_specimen_type = specimen_type
        self.has_category = category
        self.has_time = time
        self.has_range_upper = ranger_upper
        self.has_range_lower = range_lower
        self.URI = URI
        self.typeURI = typeURI
        self.categoryURI = categoryURI
        self.unitURI = unitURI
        self.specimenURI = specimenURI

    def time_formated(self):
        dt_py = self.has_time.astype('M8[s]').astype(object)
        return(dt_py.strftime('%Y%m%dT%H%M'))
    
    
        



    
