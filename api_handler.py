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
        self.farmer_id = os.environ.get("FARMER_ID")
        self.api_prefix = os.environ.get("API")
        self.api_blocks = os.environ.get("API_BLOCKS")
        self.api_payouts = os.environ.get("API_PAYOUTS")

    def payouts(self, sync_d: int = 0):
        self.synced = sync_d
        data = self.retrieve_data(api_endpoint_suffix=self.api_payouts)
        return self.sort_data(data)

    def blocks(self, sync_d: int = 0):
        self.synced = sync_d
        data = self.retrieve_data(api_endpoint_suffix=self.api_blocks)
        return self.sort_data(data)

    def api_request(self, api) -> str:

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

    def number_pages(self, api_endpoint_suffix) -> int:
        logger.info("finding number of pages containing payout data")
        api = f"{self.api_prefix}{self.farmer_id}{api_endpoint_suffix}1"
        data = self.api_request(api)
        json_data = json.loads(data)
        page = int(json_data["links"]["total_pages"])
        logger.info(f"number of pages found {page}")
        return page

    def is_update_needed(self, line):
        time_utc = line["attributes"]["timestamp"]
        if time_utc > self.synced:
            return True
        else:
            return False

    def sort_data(self, data):

        return sorted(data, key=lambda x: x["timestamp"])

    def retrieve_data(self, api_endpoint_suffix: str) -> list:
        data = []
        more_transaction = True
        pages = self.number_pages(api_endpoint_suffix=api_endpoint_suffix)
        for page in range(1, pages + 1):
            if more_transaction:
                logger.info(f"getting data from{page}")
                page = self.api_request(
                    api=f"{self.api_prefix}{self.farmer_id}{api_endpoint_suffix}{page}"
                )
                json_page = json.loads(page)

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
