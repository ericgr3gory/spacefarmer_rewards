import requests
import json
import sys
from dotenv import load_dotenv
import os
from time import sleep
import logging



class APIHandler:

    logger = logging.getLogger(__name__)

    def __init__(self, FARMER_ID: str) -> None:
        self.session = requests.Session()
        self.FARMER_ID = FARMER_ID
        self.API = "https://spacefarmers.io/api/farmers/"
        self.API_PAYOUTS = f"{self.API}{self.FARMER_ID}/payouts?page="
        self.API_BLOCKS = f"{self.API}{self.FARMER_ID}/blocks?page="
        self.API_PARTIALS = f"{self.API}{self.FARMER_ID}partials?page="
        self.API_PLOTS = f"{self.API}{self.FARMER_ID}plots?page="
        self.API_FARMER_SHOW = f"{self.API}{self.FARMER_ID}"
        self.validate_farmer = self.is_farmer_id_valid()
        self.logger = logging.getLogger(__name__)
    
    
    
    def is_farmer_id_valid(self):
        '''
        validate farmer id for length and characters
        validate farmer id is on space farmers
        '''
        self.logger.info('validating farmer id')
        if len(self.FARMER_ID) == 64 and self.FARMER_ID.isalnum():
            check = self.api_request(f'{self.API}{self.FARMER_ID}')
            if 'error' in check:
                self.logger.info("farmer_id not on spacefarmers")
                raise FarmerNotFoundError(self.FARMER_ID)
        else:
            self.logger.info("check farmer_id")
            raise InvalidFarmerIDError(self.FARMER_ID)
            
        

    def payouts(self, sync_d: int = 0):
        '''
        reteive payout data if syc_d is changed it will update until that time
        '''
        self.synced:int = sync_d
        self.logger.info('retreiving payout data')
        data:list = self.retrieve_data(api_addr=self.API_PAYOUTS)
        return self.sort_data(data)

    def blocks(self, sync_d: int = 0):
        '''
        reteive block data if syc_d is changed it will update until that time
        '''
        self.synced:int = sync_d
        self.logger.info('retreiving block data')
        data:list = self.retrieve_data(api_addr=self.API_BLOCKS)
        return self.sort_data(data)

    def partials(self, sync_d: int = 0):
        '''
        reteive partial data if syc_d is changed it will update until that time
        '''
        self.synced:int = sync_d
        self.logger.info('retreiving partials data')
        data:list = self.retrieve_data(api_addr=self.API_PARTIALS)
        return self.sort_data(data)

    def plots(self, sync_d: int = 0):
        '''
        reteive plot data if syc_d is changed it will update until that time
        '''
        self.synced:int = sync_d
        self.logger.info('retreiving plot data')
        data:list = self.retrieve_data(api_addr=self.API_PLOTS)
        return self.sort_data(data)


    def api_request(self, api:str) -> str:
        '''
        makes atempts to conect to api sleeping 3 seconds in between
        '''
        for _ in range(3):
            r = self.session.get(api)
            self.logger.info(f"connecting to {api}")
            if r.status_code == 200:
                self.logger.info(f"connected to {api}")
                return r.text
            
            elif r.status_code == 404:
                self.logger.info(f"farm not found {api}")
                return r.text
            
            else:
                self.logger.info(f"connection failed to {api}")
                self.logger.info(f"trying again")
                sleep(3)
        message = (
            "three attempts were made to contact api all failed.  Try again later..."
        )
        self.logger.warning(message)
        raise ApiConnectionFailure(api)

    def number_pages(self, api:str) -> int:
        self.logger.info("finding number of pages containing data")
        api:str = f"{api}1"
        data:str = self.api_request(api)
        json_data:dict = json.loads(data)
        number_of_pages:int = int(json_data["links"]["total_pages"])
        self.logger.info(f"number of pages found {number_of_pages}")
        return number_of_pages

    def is_update_needed(self, line:dict):
        time_utc:int = line["attributes"]["timestamp"]
        if time_utc > self.synced:
            return True
        else:
            return False

    def sort_data(self, data:list):

        return sorted(data, key=lambda x: x["timestamp"])

    def retrieve_data(self, api_addr: str) -> list:
        data = []
        more_transaction = True
        number_of_pages:int = self.number_pages(api=api_addr)
        for page in range(1, number_of_pages + 1):
            if more_transaction:
                self.logger.info(f"getting data from page {page}")
                page_data:str = self.api_request(
                    api=f"{api_addr}{page}"
                )
                json_page:dict = json.loads(page_data)

                for i in json_page["data"]:

                    if self.is_update_needed(i):
                        self.logger.info(f"Updating..{i['attributes']}")
                        data.append(i["attributes"])
                    else:
                        self.logger.info("No More updates")
                        more_transaction = False
                        break
            else:
                break

        return data


class FarmerNotFoundError(Exception):
    """Exception raised when a farmer ID is not found."""
    def __init__(self, farmer_id, message="Farmer ID not found"):
        self.farmer_id = farmer_id
        self.message = message
        super().__init__(self.message)

class InvalidFarmerIDError(Exception):
    """Exception raised for invalid farmer IDs."""
    def __init__(self, farmer_id, message="Invalid Farmer ID"):
        self.farmer_id = farmer_id
        self.message = message
        super().__init__(self.message)


class ApiConnectionFailure(Exception):
    '''exception raised after 3 unsuccessful attempts to contact api'''
    def __init__(self, api, message='Unable to Connect to Api'):
        self.api = api
        self.message = message
        super().__init__(self.message)
