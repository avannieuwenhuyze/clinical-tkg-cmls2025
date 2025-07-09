from datetime import datetime, timezone

class ICUDay():

    def __init__(self,number,begin_datetime,end_datetime,URI):
        self.has_number = number
        self.has_beginning = begin_datetime
        self.has_end = end_datetime
        self.URI= URI


    