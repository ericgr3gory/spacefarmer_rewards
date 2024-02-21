import requests
from datetime import datetime, date, timedelta
import json
import argparse
import csv
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
    
    def __init__(self, synced: int) -> None:
        self.session = requests.Session()
        self.farmer_id = os.environ.get("FARMER_ID")
        self.api_prefix = os.environ.get("API")
        self.api_blocks = os.environ.get("API_BLOCKS")
        self.api_payouts = os.environ.get("API_PAYOUTS")
        self.synced = synced
        
    def payouts(self):
        data = self.retrieve_data(api_endpoint_suffix=self.api_payouts)
        return self.sort_data(data)
    
    def blocks(self):
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
        message = "three attempts were made to contact api all failed.  Try again later..."
        logger.warning(message)
        sys.exit(message)


    def number_pages(self, api_endpoint_suffix)-> int:
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
        print(sorted(data, key=lambda x: x["timestamp"]))
        return sorted(data, key=lambda x: x["timestamp"])



    def retrieve_data(self, api_endpoint_suffix:str ) -> dict:
        data = []
        more_transaction = True
        pages = self.number_pages(api_endpoint_suffix=api_endpoint_suffix)
        for page in range(1, pages + 1):
            if more_transaction:
                logger.info(f"getting data from{page}")
                page = self.api_request(api=f"{self.api_prefix}{self.farmer_id}{api_endpoint_suffix}{page}")
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
    




class FileManager():

    def __init__(self, farmer_id: str, report_type: str) -> None:
        
        self.HOME = os.environ.get("HOME")
        
        self.api_blocks = os.environ.get("API_BLOCKS")
        self.api_payouts = os.environ.get("API_PAYOUTS")
        self.farmer_id : str = farmer_id
        self.file :str = self.file_name(report_type) 
        if 'update' in report_type:
            self.data: list = self.read_data()
        else:
            self.data: list = []
    
    def file_name(self, report_type: str)-> str:
        file_prefix = f'{self.farmer_id[:4]}_{self.farmer_id[-4:]}'
        file_extension = f'.csv'
        file_names = {
                    'update_blocks': f"-{self.api_blocks[1:6]}",
                    'update_payouts': f"-{self.api_payouts[1:6]}",
                    'normal_cointracker': f"-normal_cointracker",
                    'daily_cointracker': f"-daily_cointracker",
                    'weekly_cointracker': f"weekly_cointracker",
                    }
        return f'{file_prefix}{file_names[report_type]}{file_extension}'
    
    def file_mode(self):
        if 'update' in self.file:
            return 'a'
        else:
            return 'w'
        
    def read_data(self) -> list:
        data = []

        logger.info(f"reading data from file {self.file}")
        with open(file=self.file, mode='r') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                data.append(row)

        return data
    
    def write_csv(self) -> None:
        logger.info(f"writing csv file {self.file}")
        try:
            field_names = self.data
        except IndexError as e:
            logger.info(e)
            logger.info(f"No Updates to write to csv for {self.file}")
            sys.exit(f"No Updates to write to csv for {self.file}")
        with open(file=self.file, mode=self.file_mode()) as csvfile:
            logger.info(f"writing csv file {self.file}")
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            if "w" in self.file_mode():
                writer.writeheader()

            writer.writerows(self.data)

class DataProcessor:
    ...
    def time_of_last_sync(data: list) -> int:
        logger.info("retrieving time and date of last syc")
        try:
            return int(data[-1]["timestamp"])

        except IndexError:
            logger.info(
                "no data to retreive sync date and time from starting from begining"
            )
            return 0
    
    def convert_mojo_to_xch(mojos: int) -> float:
        logger.info("converting mojo to xch")
        return int(mojos) / 10**12


    def convert_date_for_cointracker(date: int) -> str:
        logger.info("converting date time to cointracker.com compatible format")
        time_utc = datetime.fromtimestamp(date)
        return time_utc.strftime("%m/%d/%Y %H:%M:%S")


    def check_transaction_id(data: list)-> list:
        new_list = []
        for line in data:
            
            if "transaction_id" in line:
                tid = line["transaction_id"]
                if tid == None:
                    ...
                if tid:
                    new_list.append(line)
            else:
                new_list.append(line)
        
        return new_list

    def day(d: int) -> str:
        d = datetime.fromtimestamp(d).date()
        d = datetime(
            year=d.year,
            month=d.month,
            day=d.day,
            hour=23,
            minute=59,
            second=59,
            microsecond=0,
        )
        logger.info(
            "converted daily timestamp to datetime of last second of day and coverted to cointracker formet"
        )
        return d.strftime("%m/%d/%Y %H:%M:%S")


    def week(d: int) -> str:
        d = datetime.fromtimestamp(d)
        monday = d - timedelta(days=d.weekday())
        sunday = monday + timedelta(days=6)
        sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=0)
        logger.info(
            "converted daily timestamp to datetime of last second of week and  coverted to cointracker formet"
        )
        return sunday.strftime("%m/%d/%Y %H:%M:%S")


class ReportGenerator():

    def space_farmer_payout(data: list):
        space_report = {}

        logger.info(f"creating spacefarmer dictionary with normal payout schedule")
        for line in data:
            if "transaction_id" in line:
                key = line["transaction_id"]

            if "farmed_height" in line:
                key = line["farmed_height"]

            if key not in space_report:
                space_report[key] = [[], [], []]

            if "farmer_reward_taken_by_gigahorse" in line:
                farmer_reward = bool(line["farmer_reward_taken_by_gigahorse"])

                if farmer_reward:
                    xch_amount: float = int(line["farmer_reward"]) / 10**11
                    space_report[key][0].append(xch_amount)
                    space_report[key][2].append(int(line["timestamp"]))
                    continue

                if not farmer_reward:
                    space_report[key][0].append(0)
                    space_report[key][2].append(int(line['timestamp']))
                    continue

            xch_amount: float = convert_mojo_to_xch(int(line["amount"]))
            usd_price: float = float(line["xch_usd"])
            space_report[key][0].append(xch_amount)
            space_report[key][1].append(usd_price)
            space_report[key][2].append(int(line["timestamp"]))

        logger.info(f"Completed spacefarmer dictionary with normal payouts")

        ct = []

        for k in space_report:
            
            date = max(space_report[k][2])
            date = convert_date_for_cointracker(date)
            sum_xch = sum(space_report[k][0])

            cointrack = {
                "date": date,
                "Received Quantity": sum_xch,
                "Received Currency": "XCH",
                "Sent Quantity": None,
                "Sent Currency": None,
                "Fee Amount": None,
                "Fee Currency": None,
                "Tag": "mined",
            }
            ct.append(cointrack)
        return ct


    def space_farmer_report(data: list, time_period: str):

        space_report = {}
        logger.info(f"creating spacefarmer dictionary with time period = {time_period}")
        for line in data:

            if time_period == "w":
                key = week(int(line["timestamp"]))
            elif time_period == "d":
                key = day(int(line["timestamp"]))

            if key not in space_report:
                space_report[key] = [[], []]
            try:
                if line["farmer_reward_taken_by_gigahorse"] == "False":
                    xch_amount: float = int(line["farmer_reward"]) / 10**11
                    space_report[key][0].append(xch_amount)
                    continue

                elif line["farmer_reward_taken_by_gigahorse"] == "True":
                    continue

            except KeyError as e:
                ...

            xch_amount: float = convert_mojo_to_xch(int(line["amount"]))
            usd_price: float = float(line["xch_usd"])
            space_report[key][0].append(xch_amount)
            space_report[key][1].append(usd_price)

        logger.info(f"Completed spacefarmer dictionary with time period = {time_period}")

        return format_for_cointracker(space_report)


    def format_for_cointracker(space_dict: dict) -> list:
        ct = []

        for k in space_dict:
            sum_xch = sum(space_dict[k][0])
            average_usd_price = sum(space_dict[k][1]) / len(space_dict[k][1])
            daily_usd_revenue = sum_xch * average_usd_price
            logger.info(
                f"{k}, {round(sum_xch, 10)}, {round(average_usd_price, 2)}, {round(daily_usd_revenue, 2)}"
            )
            cointrack = {
                "date": k,
                "Received Quantity": sum_xch,
                "Received Currency": "XCH",
                "Sent Quantity": None,
                "Sent Currency": None,
                "Fee Amount": None,
                "Fee Currency": None,
                "Tag": "mined",
            }
            ct.append(cointrack)

        return ct





    













def arguments() -> argparse:
    logger.info("Retrieving arguments")
    parser = argparse.ArgumentParser(
        description="Retreive block reward payments from SapceFarmers.com api and write to csv"
    )
    parser.add_argument("-l", help="launcher_id", type=str)
    parser.add_argument("-a", help="retieve all payments from api", action="store_true")
    parser.add_argument("-u", help="update payments from api", action="store_true")
    parser.add_argument("-w", help="weekly earning report", action="store_true")
    parser.add_argument("-d", help="daily earning report", action="store_true")
    parser.add_argument(
        "-p", help="space farmer normal payout report", action="store_true"
    )
    args = parser.parse_args()

    if args.u and args.a:
        text = (
            "Can't both update payments and retrieve all payments please pick only one."
        )
        logger.warning(text)
        sys.exit(text)

    if not args.u and not args.a and not args.w and not args.d and not args.p:
        text = "need to either update payments or retrieve all payments please pick only one."
        logger.warning(text)
        sys.exit(text)

    return args


def main() -> None:
    logger.info("starting main")
    # args = arguments()
    
    ap = APIHandler(synced=1708368372)
    ap.payouts()
if __name__ == "__main__":
    main()
