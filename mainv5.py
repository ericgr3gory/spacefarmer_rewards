from datetime import datetime, date, timedelta
import argparse
import csv
import sys
from dotenv import load_dotenv
import os
from time import sleep
import logging
from api_handler import APIHandler

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


class DataProcessor:
    
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
    
    #ap = APIHandler(synced=1708368372)
    a = APIHandler()
    a.blocks(sync_d=1708368372)
    fm = FileManager()
    data = fm.read_all_transactions()
    print(data)
    
if __name__ == "__main__":
    main()
