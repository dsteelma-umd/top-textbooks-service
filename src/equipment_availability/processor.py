import datetime
import time
from os import environ
from typing import Any, Optional

import dateutil.parser as dateparser
import requests
from bs4 import BeautifulSoup, ResultSet
from bs4.element import Tag
from core.gateway import HttpGateway
from core.logging import create_logger
from dotenv import dotenv_values

logger = create_logger(__name__)

class AlmaLoanResponse:
    def __init__(self, mms_id: str, xmlResponse: str) -> None:
        self.mms_id = mms_id
        self.xmlResponse = xmlResponse

    def getDueDates(self) -> list[datetime.datetime]:
        """
        Returns the earliest due date after the given datetime, or None if
        no due date later than that time is found.
        """
        soup = BeautifulSoup(self.xmlResponse, 'lxml-xml')
        raw_due_dates = soup.find_all('due_date')
        due_dates = []
        for raw_due_date in raw_due_dates:
            due_date_str = raw_due_date.text
            # print(f"{due_date_str}")
            due_date = dateparser.parse(due_date_str)
            due_dates.append(due_date)
        print(f'due_dates={due_dates}')
        return due_dates

    def getEarliestDueDateAfter(self, now: datetime.datetime) -> Optional[datetime.datetime]:
        """
        Returns the earliest due date after the given datetime, or None if
        no due date later than that time is found.
        """
        earliest_due_date = None
        due_dates = self.getDueDates()
        for due_date in due_dates:
            if due_date > now and ((earliest_due_date is None) or due_date < earliest_due_date):
                earliest_due_date = due_date

        return earliest_due_date


class AlmaGateway:
    def __init__(self, config) -> None:
        # Probably a yaml file
        self.config = config
        self.api_key = environ.get('ALMA_API_KEY', '')

    def retrieveBibs(self, mms_ids: list[str]) -> ResultSet[Any]:
        print(f'config={self.config}')
        unique_mms_ids = set(mms_ids)
        print(f'# of unique mms_ids={len(unique_mms_ids)}')
        params = {
            'mms_id': ','.join(unique_mms_ids),
            'view': 'full',
            'expand': 'p_avail',
            'apikey': self.api_key,
        }
        url = self.config['host'] + self.config['endpoint']
        bibsResponse = HttpGateway.get(url, params)
        soup = BeautifulSoup(bibsResponse.decode('UTF-8'), 'lxml-xml')
        bibs = soup.find_all('bib')
        return bibs

    def retreiveBibLoanInformation(self, mms_id) -> AlmaLoanResponse:
        params = {'order_by': 'due_date', 'direction': 'asc', 'apikey': self.api_key}
        url = self.config['host'] + f'/almaws/v1/bibs/{mms_id}/loans'
        loans_response = HttpGateway.get(url, params)
        # loan_due_dates = AlmaServerGateway.process_loans_response_for_due_dates(loans_response)
        # return loans_response
        return AlmaLoanResponse(mms_id, loans_response.decode('UTF-8'))

    # def getRequest(host, endpoint, params):
    #     start_time = time.perf_counter()
    #     r = requests.get(host + endpoint, params)
    #     end_time = time.perf_counter()
    #     elapsed_time_seconds = end_time - start_time
    #     print(f'Request took {elapsed_time_seconds} seconds')
    #     return r


class EquipmentAvailability:
    def __init__(self, mms_id: str, count: int = 0, next_due_date: datetime.datetime = None, availability: str = ''):
        self.mms_id = mms_id
        self.count = count
        self.next_due_date = next_due_date
        self.availability = availability


class AlmaBibProcessor:
    def __init__(self, gateway: AlmaGateway):
        self.gateway = gateway

    def process(self, bib: Tag, now: datetime.datetime) -> EquipmentAvailability:
        ava = bib.find('datafield', attrs={'tag': 'AVA'})  # Assumes only one AVA datafield per bib

        equipment_availability = None
        if ava is not None:
            equipment_availability = self.processAva(ava, now)
        else:
            equipment_availability = self.processNoAva(bib, now)

        return equipment_availability

    def processNoAva(self, bib, now) -> EquipmentAvailability:
        mms_id = bib.find('mms_id').text
        loanResponse = self.gateway.retreiveBibLoanInformation(mms_id)
        next_due_date = loanResponse.getEarliestDueDateAfter(now)
        return EquipmentAvailability(mms_id=mms_id, count=0, next_due_date=next_due_date, availability='no_ava')

    def processAvaAvailable(self, ava) -> EquipmentAvailability:
        mms_id = ava.find('subfield', attrs={'code': '0'}).text
        total_items_count_field = ava.find('subfield', attrs={'code': 'f'})
        unavailable_items_count_field = ava.find('subfield', attrs={'code': 'g'})
        availability = ava.find('subfield', attrs={'code': 'e'}).text

        total_items_count = 0
        try:
            if total_items_count_field is not None:
                total_items_count = int(total_items_count_field.text)
        except ValueError:
            print(
                f"WARNING: Non-numeric value '{total_items_count_field.text} in AVA subfield 'f' for mms_id: {mms_id}"
            )

        unavailable_items_count = 0
        try:
            if unavailable_items_count_field is not None:
                unavailable_items_count = int(unavailable_items_count_field.text)
        except ValueError:
            print(
                f"WARNING: Non-numeric value '{unavailable_items_count_field.text} in AVA subfield 'g' for mms_id: {mms_id}"
            )

        available_count = total_items_count - unavailable_items_count

        return EquipmentAvailability(
            mms_id=mms_id, count=available_count, next_due_date=None, availability=availability
        )

    def processAva(self, ava, now: datetime.datetime):
        availability = ava.find('subfield', attrs={'code': 'e'}).text

        if availability == 'available':
            return self.processAvaAvailable(ava)
        else:
            return self.processAvaOther(ava, now)

    def processAvaOther(self, ava, now: datetime.datetime):
        """
        If AVA "availability" field is "unavailable" or "check_holdings"
        """
        mms_id = ava.find('subfield', attrs={'code': '0'}).text
        availability = ava.find('subfield', attrs={'code': 'e'}).text
        loanResponse = self.gateway.retreiveBibLoanInformation(mms_id)
        next_due_date = loanResponse.getEarliestDueDateAfter(now)
        return EquipmentAvailability(mms_id=mms_id, count=0, next_due_date=next_due_date, availability=availability)

class EquipmentAvailabilityResponse:
    def generateResponse(requested_mms_ids: list[str], equipment_availabilities: list[EquipmentAvailability]) -> list[dict]:
        response = []

        for e in equipment_availabilities:
            due_date = e.next_due_date if e.next_due_date else ""
            response.append({'mms_id': e.mms_id, 'count': e.count, 'due_date': due_date, 'status': e.availability})

        mms_ids_with_alma_response = set([e.mms_id for e in equipment_availabilities])
        missing_mms_ids = set(requested_mms_ids) - mms_ids_with_alma_response
        for mms_id in missing_mms_ids:
            response.append({'mms_id': mms_id, 'count': 0, 'due_date': '', 'status': 'nodata'})

        return response

class EquipmentAvailabilityProcessor:
    def __init__(self, gateway: AlmaGateway, bibProcessor: AlmaBibProcessor):
        self.gateway = gateway
        self.bibProcessor = bibProcessor


    def process(self, requested_mms_ids: list[str], now: datetime.datetime) -> dict[str, dict]:
        bibs = self.gateway.retrieveBibs(requested_mms_ids)
        equipment_availabilities = []

        for bib in bibs:
            equipment_availability = self.bibProcessor.process(bib, now)
            equipment_availabilities.append(equipment_availability)

        return EquipmentAvailabilityResponse.generateResponse(requested_mms_ids, equipment_availabilities)
