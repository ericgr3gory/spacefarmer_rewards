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

API = "https://spacefarmers.io/api/farmers/"
API_PAYOUTS = "/payouts?page="
API_BLOCKS = "/blocks?page="
TEMP_DIR = os.environ.get("TEMP_DIR")
HOME = os.environ.get("HOME")
CURRENT_DIR = os.getcwd()


logging.basicConfig(
    filename=f"{TEMP_DIR}/space.log",
    encoding="utf-8",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
    logger.info('converted daily timestamp to datetime of last second of day and coverted to cointracker formet')
    return d.strftime("%m/%d/%Y %H:%M:%S")


def week(d: int) -> str:
    d = datetime.fromtimestamp(d)
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=0)
    logger.info('converted daily timestamp to datetime of last second of week and  coverted to cointracker formet')
    return sunday.strftime("%m/%d/%Y %H:%M:%S")


def space_farmer_report(data: list, time_period: str):
    
    space_report = {}
    logger.info(f'creating spacefarmer dictionary with time period = {time_period}')
    for line in data:

        if time_period == "w":
            key = week(int(line["timestamp"]))
        elif time_period == "d":
            key = day(int(line["timestamp"]))

        if key not in space_report:
            space_report[key] = [[], []]
        try:
            if line["farmer_reward_taken_by_gigahorse"] == "False":
                xch_amount: float = int(line["farmer_reward"])  / 10**11
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
        
    logger.info(f'Completed spacefarmer dictionary with time period = {time_period}')
    
    return format_for_cointracker(space_report)
    


def format_for_cointracker(space_dict: dict) -> list:
    ct = []

    for k in space_dict:
        sum_xch = sum(space_dict[k][0])
        average_usd_price = sum(space_dict[k][1]) / len(space_dict[k][1])
        daily_usd_revenue = sum_xch * average_usd_price
        logger.info(f'{k}, {round(sum_xch, 10)}, {round(average_usd_price, 2)}, {round(daily_usd_revenue, 2)}')
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

def api_request(api: str, session: object) -> str:

    for _ in range(3):
        r = session.get(api)
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


def number_pages(farmer_id: str) -> dict:
    pages = {}
    logger.info("finding number of pages containing payout data")
    session = requests.Session()
    apis = [API_PAYOUTS, API_BLOCKS]
    for a in apis:
        api = f"{API}{farmer_id}{a}1"
        data = api_request(api=api, session=session)
        json_data = json.loads(data)
        key = a
        pages[key] = (int(json_data["links"]["total_pages"]))
        #logger.info(f"number of pages found {json_data["links"]["total_pages"]}")
    return pages


def time_of_last_sync(data: list) -> int:
    logger.info("retrieving time and date of last syc")
    try:
        return int(data[-1]["timestamp"])

    except IndexError:
        logger.info(
            "no data to retreive sync date and time from starting from begining"
        )
        return 0


def retrieve_data(farmer_id: str, pages: dict, synced: int) -> dict:
    data = {}
    session = requests.Session()
    for key in pages:
        data[key]= []
        for page in range(1, pages[key] + 1):
            logger.info(f"getting data from{page}")
            page = api_request(api=f"{API}{farmer_id}{key}{page}", session=session)
            json_page = json.loads(page)
            for i in json_page["data"]:
                time_utc = i["attributes"]["timestamp"]
                if time_utc > synced:
                    logger.info('TRUE')
                    data[key].append(i["attributes"])
                else:
                    logger.info('FALSEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
                    break    
            
    
    return {key: sorted(value, key=lambda x: x["timestamp"]) for key, value in data.items()}


def read_data(file_names: list) -> dict:
    data = {}
    for file_name in file_names:
        data[file_name] = []
        logger.info(f"reading data from file {file_name}")
        with open(file_name, "r") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data[file_name].append(row)

    return data


def convert_mojo_to_xch(mojos: int) -> float:
    logger.info("converting mojo to xch")
    return int(mojos) / 10**12


def convert_date_for_cointracker(date: int) -> str:
    logger.info("converting date time to cointracker.com compatible format")
    time_utc = datetime.fromtimestamp(date)
    return time_utc.strftime("%m/%d/%Y %H:%M:%S")


def write_csv(file_name: str, data: list, file_mode: str) -> None:
    logger.info(f"writing csv file {file_name}")
    try:
        field_names = list(data[0].keys())
    except IndexError as e:
        logger.info(e)
        sys.exit('No Updates to write to csv')
    with open(file_name, file_mode) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        if "w" in file_mode:
            writer.writeheader()

        writer.writerows(data)


def arguments() -> argparse:
    logger.info('Retrieving arguments')
    parser = argparse.ArgumentParser(
        description="Retreive block reward payments from SapceFarmers.com api and write to csv"
    )
    parser.add_argument("-l", help="launcher_id", type=str)
    parser.add_argument("-a", help="retieve all payments from api", action="store_true")
    parser.add_argument("-u", help="update payments from api", action="store_true")
    parser.add_argument("-w", help="weekly earning report", action="store_true")
    parser.add_argument("-d", help="daily earning report", action="store_true")
    args = parser.parse_args()

    if args.u and args.a:
        text = (
            "Can't both update payments and retrieve all payments please pick only one."
        )
        logger.warning(text)
        sys.exit(text)

    if not args.u and not args.a and not args.w and not args.d:
        text = "need to either update payments or retrieve all payments please pick only one."
        logger.warning(text)
        sys.exit(text)

    return args


def main() -> None:
    logger.info('starting main')
    args = arguments()       

    if args.l:
        farmer_id = args.l
    else:
        farmer_id = os.environ.get("FARMER_ID")

    files = [f"{farmer_id[:4]}---{farmer_id[-4:]}-{API_BLOCKS[1:6]}.csv", 
            f"{farmer_id[:4]}---{farmer_id[-4:]}-{API_PAYOUTS[1:6]}.csv"]

    if args.a:
        last_sync = 0
        file_mode = "w"
        logger.info(f"-a all mode running for framer id {farmer_id}")

    if args.u:
        data = read_data(file_names=files)
        last_sync = time_of_last_sync(data[files[1]])

        file_mode = "a"
        logger.info(f"-u update mode running for framer id {farmer_id}")
    
    if args.u or args.a:    
        pages = number_pages(farmer_id=farmer_id)
        print(pages)
        
        

        print(last_sync)
        data = retrieve_data(farmer_id=farmer_id, pages=pages, synced=last_sync)
        for key, value in data.items() :
            print (key)

        for key in data:
            write_csv(file_name=f"{farmer_id[:4]}---{farmer_id[-4:]}-{key[1:6]}.csv", data=data[key], file_mode=file_mode)
        
    
    if args.d:
        data = []
        
        for file in files:
            data.extend(read_data(file_name=file))
        
        data = sorted(data, key=lambda x: x["timestamp"])    
        data = space_farmer_report(data=data, time_period="d")
        file_name = f"{CURRENT_DIR}/{farmer_id[:4]}---{farmer_id[-4:]}_daily_cointracker.csv"

    if args.w:
        data = []
        
        for file in files:
            data.extend(read_data(file_name=file))
            
        data = sorted(data, key=lambda x: x["timestamp"])   
        data = space_farmer_report(data=data, time_period="w")
        file_name = f"{CURRENT_DIR}/{farmer_id[:4]}---{farmer_id[-4:]}_weekly_cointracker.csv"
    
    if args.d or args.w:
        write_csv(
        file_name=file_name,
        data=data,
        file_mode="w",
    )    
        

if __name__ == "__main__":
    main()
