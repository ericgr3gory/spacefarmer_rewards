import requests
import json
import sys
from dotenv import load_dotenv
import os
from time import sleep
import logging


load_dotenv()

TEMP_DIR = os.environ.get("TEMP_DIR")
CURRENT_DIR = os.getcwd()

logging.basicConfig(
    filename=f"{TEMP_DIR}/space.log",
    encoding="utf-8",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class APIHandler:

    def __init__(self) -> None:
        self.session = requests.Session()
        self.FARMER_ID = os.environ.get("FARMER_ID")
        self.API = "https://spacefarmers.io/api/farmers/"
        self.API_PAYOUTS = f"{self.API}{self.FARMER_ID}/payouts?page="
        self.API_BLOCKS = f"{self.API}{self.FARMER_ID}/blocks?page="
        self.API_PARTIALS = f"{self.API}{self.FARMER_ID}partials?page="
        self.API_PLOTS = f"{self.API}{self.FARMER_ID}plots?page="
        self.API_FARMER_SHOW = f"{self.API}{self.FARMER_ID}"


    def payouts(self, sync_d: int = 0):
        '''
        reteive payout data if syc_d is changed it will update until that time
        '''
        self.synced:int = sync_d
        logger.info('retreiving payout data')
        data:list = self.retrieve_data(api_addr=self.API_PAYOUTS)
        return self.sort_data(data)

    def blocks(self, sync_d: int = 0):
        '''
        reteive block data if syc_d is changed it will update until that time
        '''
        self.synced:int = sync_d
        logger.info('retreiving block data')
        data:list = self.retrieve_data(api_addr=self.API_BLOCKS)
        return self.sort_data(data)

    def partials(self, sync_d: int = 0):
        '''
        reteive partial data if syc_d is changed it will update until that time
        '''
        self.synced:int = sync_d
        logger.info('retreiving partials data')
        data:list = self.retrieve_data(api_addr=self.API_PARTIALS)
        return self.sort_data(data)

    def plots(self, sync_d: int = 0):
        '''
        reteive plot data if syc_d is changed it will update until that time
        '''
        self.synced:int = sync_d
        logger.info('retreiving plot data')
        data:list = self.retrieve_data(api_addr=self.API_PLOTS)
        return self.sort_data(data)


    def api_request(self, api:str) -> str:

        for _ in range(3):
            r = self.session.get(api)
            logger.info(f"connecting to {api}")
            if r.status_code == 200:
                logger.info(f"connected to {api}")
                return r.text
            else:
                logger.info(f"connection failed to {api}")
                logger.info(f"trying again")
                sleep(3)
        message = (
            "three attempts were made to contact api all failed.  Try again later..."
        )
        logger.warning(message)
        sys.exit(message)

    def number_pages(self, api:str) -> int:
        logger.info("finding number of pages containing data")
        api:str = f"{api}1"
        data:str = self.api_request(api)
        json_data:dict = json.loads(data)
        number_of_pages:int = int(json_data["links"]["total_pages"])
        logger.info(f"number of pages found {number_of_pages}")
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
                logger.info(f"getting data from page {page}")
                page_data:str = self.api_request(
                    api=f"{api_addr}{page}"
                )
                json_page:dict = json.loads(page_data)

                for i in json_page["data"]:

                    if self.is_update_needed(i):
                        logger.info("Updating..")
                        data.append(i["attributes"])
                    else:
                        logger.info("No More updates")
                        more_transaction = False
                        break
            else:
                break

        return data
