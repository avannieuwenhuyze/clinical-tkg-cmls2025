from datetime import datetime, timedelta
from datetime import timezone
import numpy as np

class ICUStay():

    def __init__(self,stay_id,begin_datetime,end_datetime,URI):
        """
            Initializes a new instance of the class representing a stay or visit.

            Parameters:
                stay_id (str): Unique identifier for the stay.
                begin_datetime (datetime): The starting date and time of the stay.
                end_datetime (datetime): The ending date and time of the stay.
                URI (str): The Uniform Resource Identifier associated with the stay.

            Attributes:
                has_stay_id (str): Stores the unique identifier of the stay.
                has_beginning (datetime): Stores the start datetime of the stay.
                has_end (datetime): Stores the end datetime of the stay.
                URI (str): Stores the RDF URI related to the stay.
        """
        self.has_stay_id = stay_id
        self.has_beginning = begin_datetime
        self.has_end = end_datetime
        self.URI= URI


    def duration(self):
        """
            Calculates the duration between the beginning and end datetimes of the stay.

            Returns:
                tuple: A tuple containing the duration in the format (days, hours, minutes).

            Raises:
                ValueError: If either the start or end datetime is not defined.

            Notes:
                - If the time difference is a NumPy timedelta64 object, it is converted to a standard timedelta.
                - The duration is calculated in total minutes and then broken down into days, hours, and minutes.
        """
  
        if not self.has_beginning or not self.has_end:
            raise ValueError("Start and end datetime must be defined.")

        delta = self.has_end - self.has_beginning

  
        if isinstance(delta, np.timedelta64):
            delta = timedelta(seconds=delta / np.timedelta64(1, 's'))


        total_minutes = int(delta.total_seconds() // 60)
        days = total_minutes // (24 * 60)
        hours = (total_minutes % (24 * 60)) // 60
        minutes = total_minutes % 60
        return days, hours, minutes
    

    def days(self):
        """
        Retourne une liste de tuples (jour, début, fin) au format numpy.datetime64.
        - Jour 1 : de has_beginning à fin du jour
        - Jours intermédiaires : 00:00 → 23:59:59
        - Dernier jour : 00:00 → has_end
        """
        start = self.has_beginning.astype('datetime64[s]')
        end = self.has_end.astype('datetime64[s]')

        start_date = start.astype('datetime64[D]')
        end_date = end.astype('datetime64[D]')
        total_days = int((end_date - start_date).astype(int)) + 1

        day_list = []

        for i in range(total_days):
            day_num = i + 1
            current_date = start_date + np.timedelta64(i, 'D')

            # Début du jour
            if i == 0:
                day_start = start
            else:
                day_start = np.datetime64(current_date, 's')

            # Fin du jour
            if i == total_days - 1:
                day_end = end
            else:
                day_end = np.datetime64(current_date + 1, 's') - np.timedelta64(1, 's')

            day_list.append((day_num, day_start, day_end))

        return day_list
    



    def day_number_for_datetime(self, dt):
        """
        Retourne le numéro du jour ICU correspondant à un datetime donné.

        Paramètres :
            dt (np.datetime64) : Date/heure à évaluer.

        Retour :
            int : Le numéro de jour (1-indexé) si dans la plage, sinon None.
        """
        days = self.days()
        for day_num, day_start, day_end in days:
            if day_start <= dt <= day_end:
                return day_num
        return None  # Si la date ne correspond à aucun jour du séjour


