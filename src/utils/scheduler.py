"""
This file contains all the logic about the scheduling of an order. It generates all the possible slot to book for a
specific order and patient, including the constraint of a shift and a range of day. It works as following :
    - Extract the examens already reserved for each station of the concerned modality + examens already scheduled for a certain patient (avoid overlapping)
    - Generate all the possible slots given a shift and a range of day
    - Delete already booked slots or overlapping slot with existing orders
    - Returns all the remaining slot that can be booked
"""
from src.utils.MongoDBClient import MongoDBClient
from typing import Any
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
        """
        Function that disables a station from a slot (self). If a slot has no remaining station available
        the slot is disabled and cannot be returned by the scheduler.
            @param station: the station to disable
        """
        if not self.is_active:
            pass
        elif not self.stations[station]:
            pass
        else:
            self.stations[station] = False
            self._nb_stations_available -= 1
            self.check_activity()

    def disable_all_stations(self):
        """
        Function to disable all the stations and so disable the slot
        """
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

    def __extract_stations_scheduled_orders(self, stations: list, m_client: MongoDBClient) -> dict:
        """
        Function that extracts all the orders scheduled in DB using one of the stations in @stations.
            @pre stations: a list of stations (str)
            @pre m_client: MongoDB client object
        returns a dictionary {station: list of orders}
        """
        result = dict()
        for station in stations:
            result[station] = m_client.get_documents(
                "orders",
                {
                    "station_aet": station,
                    "status": {
                        "$in": ["SCHEDULED", "GENERATED", "IN PROGRESS"]
                    },
                    "examination_date": {
                        "date": {"$gte": datetime.datetime.now().strftime("%Y-%m-%d")}
                    }
                }
            )
        return result

    def __extract_patient_scheduled_orders(self, patient_id: str, m_client: MongoDBClient) -> list[dict[str, Any]]:
        """
        Function that extracts all the orders scheduled in DB concerning the patient with @patient_id
            @pre patient_id: the patient ID
            @pre m_client: MongoDB client object
        return a list of orders concerning patient with @patient_id
        """
        return m_client.get_documents('orders', {
            "patient_id": patient_id,
            "status": {
                "$in": ["SCHEDULED", "GENERATED", "IN PROGRESS"]
            },
            "examination_date": {
                "date": {"$gte": datetime.datetime.now().strftime("%Y-%m-%d")}
            }
        })

    def __create_possible_slots(self, duration: int, stations: list[str]) -> dict[datetime.datetime, list[Slot]]:
        """
        Function that creates all the possible slots (Slot) for a certain order duration starting from the start shift @d_start
        ending from the end shift @d_end and for a number of day @d_range.
            @pre duration: an integer representing the duration in minutes of the procedure to schedule
            @pre stations: a list of stations (str)
        return a dictionary {date: list of slots}
        """
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

    def get_possible_schedules(self, duration: int, patient_id: str, stations: list, m_client: MongoDBClient) -> list[tuple[str, Slot]]:
        """
        Function that delete impossible slot and only return the possible slots to be scheduled. This is the entry point
        to get the possible slot to schedule a new order
            @pre duration: an integer representing the duration in minutes of the procedure to schedule
            @pre patient_id: the patient ID
            @pre stations: a list of stations (str)
            @pre m_client: MongoDB client object
        """
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

        current_time = datetime.datetime.now().time()
        for i in range(len(planning[start_date])):
            if planning[start_date][i].start_t.time() < current_time:
                planning[start_date][i].disable_all_stations()
        for station, orders in stations_scheduled_orders.items():
            for order in orders:
                date = datetime.datetime.strptime(order["examination_date"]["date"], "%Y-%m-%d").date()
                o_start_t = datetime.datetime.combine(date, datetime.datetime.strptime(order["examination_date"]["start_time"], "%H:%M").time())
                o_end_t = datetime.datetime.combine(date, datetime.datetime.strptime(order["examination_date"]["end_time"], "%H:%M").time())
                for i in range(len(planning[date])):
                    if self.__is_overlapping(planning[date][i].start_t, planning[date][i].end_t, o_start_t, o_end_t):
                        planning[date][i].disable_station(station)
        for order in patient_scheduled_orders:
            date = datetime.datetime.strptime(order["examination_date"]["date"], "%Y-%m-%d").date()
            o_start_t = datetime.datetime.combine(date, datetime.datetime.strptime(order["examination_date"]["start_time"], "%H:%M").time())
            o_end_t = datetime.datetime.combine(date, datetime.datetime.strptime(order["examination_date"]["end_time"], "%H:%M").time())
            for i in range(len(planning[date])):
                if self.__is_overlapping(planning[date][i].start_t, planning[date][i].end_t, o_start_t, o_end_t):
                    planning[date][i].disable_all_stations()
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
        """
        Simple function that checks whether a slot is overlapping with an already scheduled order.
            @pre t_start_slot: the start time of the slot
            @pre t_end_slot: the end time of the slot
            @pre t_start_order: the start time of the order
            @pre t_end_order: the end time of the order
        returns True if overlapping, False otherwise
        """
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