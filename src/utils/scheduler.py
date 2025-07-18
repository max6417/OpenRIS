"""
La classe Scheduler correspond au code permettant de calculer et de renvoyer des slots horaires pour un certain examen,
patient, et modalité. Il fonctionne comme suit :
    - Extrait les données d'intérêts : Les examens déjà prévus par chaque station de la modalité concernée + les examens déjà prévu
    pour le patient.
    - Génère les slots théoriques pour l'examen qu'on veut schedule sans prendre en compte ceux déjà attribué ou qui overlap
    - On delete les slots qui sont déjà occupés ou partiellemet occupés pour ne garder que les bons (pour chacune des stations)
    - On formatte les slots restant pour les envoyer au server (date+heure+station) ou all si toutes les stations sont dispo --> On prend toujours la station la moins fréquentée s'il y en a plusieurs
Pas le plus opti mais c'est pas l'objet du mémoire d'avoir un système sous contrainte parfaite, ici c'est juste les premisses qui permettraient
par la suite d'avoir un système de scheduling plus complexe que celui-là.


La classe Slot représente un slot horaire pour la procédure cible. Elle contient les infos de timing + le nombre et nom(s)
des stations disponibles pour ce slot. Si plus de station disponible, le slot n'est pas pris en compte pour le calcul final

Si un patient n'est pas dispo pour un slot, alors il est également discard de la liste des slots disponibles.


Pour plus de complexité, on pourrait également se servir de ces classes pour ajouter la notion de priorité des ordres et de rescheduling
(à voir pour plus tard)


Pour le rescheduling, on doit ajouter de nouveaux bouton (rescheduler permettant d'ouvrir le scheduler) + RESCHEDULED status ordre + bouton pour valider la reschedulation et repasser à schedule
"""
from src.utils.MongoDBClient import MongoDBClient
import datetime


class Slot:

    def __init__(self, date, start_t, end_t, stations):
        """
        Slot is an object representing a Slot for an examen that can be booked
            @param date: the date of the slot (without hours)
            @param start_t: the start time of the slot
            @param end_t: the end time of the slot
            @param stations: a list reprensenting all the stations that can perform the examen
        """
        self.date = date
        self.start_t = start_t
        self.end_t = end_t
        self.stations = dict()
        self.is_active = True
        for station in stations:
            self.stations[station] = True
        self._nb_stations_available = len(self.stations)

    def disable_station(self, station: str):
        if not self.is_active:
            pass
        elif not self.stations[station]:
            pass
        else:
            self.stations[station] = False
            self._nb_stations_available -= 1
            self.check_activity()

    def disable_all_stations(self):
        for station in self.stations.keys():
            self.disable_station(station)

    def check_activity(self):
        if self._nb_stations_available <= 0:
            self.is_active = False


class Scheduler:

    def __init__(self, d_range: int, d_start: datetime.datetime.time, d_end: datetime.datetime.time):
        """
        Constructor for Scheduler instance.
        @pre d_range: an integer representing the number of days to search and schedule an order
        @pre d_start: an object representing the work day' start time
        @pre d_end: an object representing the work day's end time
        """
        self.d_range = d_range
        self.d_start = d_start
        self.d_end = d_end

    def __extract_stations_scheduled_orders(self, stations: list, m_client: MongoDBClient):
        result = dict()
        for station in stations:
            result[station] = m_client.get_documents(
                "orders",
                {
                    "station_aet": station,
                    "status": {
                        "$in": ["SCHEDULED", "RESCHEDULED", "GENERATED", "IN PROGRESS"]
                    }
                }
            )
        return result

    def __extract_patient_scheduled_orders(self, patient_id: str, m_client: MongoDBClient):
        return m_client.get_documents('orders', {
            "patient_id": patient_id,
            "status": {
                "$in": ["SCHEDULED", "RESCHEDULED", "GENERATED", "IN PROGRESS"]
            }
        })

    def __create_possible_slots(self, duration, stations):
        current_date = datetime.date.today()   # Date without time
        dates = [current_date + datetime.timedelta(days=i) for i in range(self.d_range + 1)]
        planning = dict()
        # Generate all the timing for 1 day
        for date in dates:
            planning[date] = list()
            current_start_time = datetime.datetime.combine(date, self.d_start)
            current_end_time = current_start_time + datetime.timedelta(minutes=duration)
            while current_end_time.time() <= self.d_end:
                planning[date].append(
                    Slot(
                        date=date,
                        start_t=current_start_time,
                        end_t=current_end_time,
                        stations=stations
                    )
                )
                current_start_time = current_end_time
                current_end_time = current_start_time + datetime.timedelta(minutes=duration)
        return planning

    def get_possible_schedules(self, duration: int, patient_id: str, stations: list, m_client: MongoDBClient):
        start_date = datetime.date.today()
        end_date = datetime.date.today() + datetime.timedelta(days=self.d_range)
        stations_scheduled_orders = self.__extract_stations_scheduled_orders(stations, m_client)
        patient_scheduled_orders = self.__extract_patient_scheduled_orders(patient_id, m_client)
        planning = self.__create_possible_slots(duration, stations)
        # Inferring the workload of each possible station :
        stations_workload = dict()
        for station in stations:
            stations_workload[station] = 0
        for station, orders in stations_scheduled_orders.items():
            stations_workload[station] = len(orders)
        # TODO : finish the planning slot by deleting already booked ones

        # TODO : delete slot already passed time (current time > slot start time)
        current_time = datetime.datetime.now().time()
        for i in range(len(planning[start_date])):
            if planning[start_date][i].start_t.time() < current_time:
                planning[start_date][i].disable_all_stations()
        # TODO : delete slot and stations already reserved
        for station, orders in stations_scheduled_orders.items():
            for order in orders:
                date = datetime.datetime.strptime(order["examination_date"]["date"], "%Y-%m-%d").date()
                o_start_t = datetime.datetime.combine(date, datetime.datetime.strptime(order["examination_date"]["start_time"], "%H:%M").time())
                o_end_t = datetime.datetime.combine(date, datetime.datetime.strptime(order["examination_date"]["end_time"], "%H:%M").time())
                for i in range(len(planning[date])):
                    if self.__is_overlapping(planning[date][i].start_t, planning[date][i].end_t, o_start_t, o_end_t):
                        planning[date][i].disable_station(station)
        # TODO : delete slot already in use for the patient
        for order in patient_scheduled_orders:
            date = datetime.datetime.strptime(order["examination_date"]["date"], "%Y-%m-%d").date()
            o_start_t = datetime.datetime.combine(date, datetime.datetime.strptime(order["examination_date"]["start_time"], "%H:%M").time())
            o_end_t = datetime.datetime.combine(date, datetime.datetime.strptime(order["examination_date"]["end_time"], "%H:%M").time())
            for i in range(len(planning[date])):
                if self.__is_overlapping(planning[date][i].start_t, planning[date][i].end_t, o_start_t, o_end_t):
                    planning[date][i].disable_all_stations()
        # TODO : Format the response to return it to the server [(id: date+time+station, date+time), ...] + decide which station to use with respect to the least frequented station if several choices are possible
        result = list()
        for date, slots in planning.items():
            for slot in slots:
                if slot.is_active:
                    available_stations = [station for station, val in slot.stations.items() if val]
                    if len(available_stations) == 1:
                        result.append((available_stations[0], slot))
                    else:
                        filtered_stations_workload = {station: workload for station, workload in stations_workload.items() if station in available_stations}
                        result.append((min(filtered_stations_workload, key=filtered_stations_workload.get), slot))
        return result

    def __is_overlapping(self, t_start_slot: datetime.datetime, t_end_slot: datetime.datetime, t_start_order: datetime.datetime, t_end_order: datetime.datetime) -> bool:
        if t_start_order < t_start_slot < t_end_order:
            return True
        elif t_start_order < t_end_slot < t_end_order:
            return True
        elif t_start_slot == t_start_order and t_end_slot == t_end_order:
            return True
        elif t_start_slot < t_start_order and t_end_slot > t_end_order:
            return True
        elif t_start_slot > t_start_order and t_end_slot < t_end_order:
            return True
        else:
            return False