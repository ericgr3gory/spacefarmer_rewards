import argparse
import sys
from dotenv import load_dotenv
import os
from time import sleep
import logging
from logging_config import setup_rich_logging, setup_log
from file_managment import FileManager
from data_parser import DataParser as Data
from api_handler import APIHandler
from report_generator import ReportGenerator
from rich import print as rprint

load_dotenv()

TEMP_DIR = os.environ.get("TEMP_DIR")
HOME = os.environ.get("HOME")
CURRENT_DIR = os.getcwd()


logger = logging.getLogger(__name__)


def arguments() -> argparse:

    parser = argparse.ArgumentParser(
        description="Retreive block reward payments from SapceFarmers.com api and write to csv"
    )
    parser.add_argument(
        "-v",
        help="verbose mode prints logging to console will slow down execution",
        action="store_true",
    )
    parser.add_argument("-l", help="launcher_id", type=str)
    parser.add_argument("-a", help="retieve all payments from api", action="store_true")
    parser.add_argument("-u", help="update payments from api", action="store_true")
    parser.add_argument("-w", help="weekly earning report", action="store_true")
    parser.add_argument("-d", help="daily earning report", action="store_true")
    parser.add_argument("-p", help="current price of xch", action="store_true")
    parser.add_argument(
        "-b", help="space farmer batch payout report", action="store_true"
    )
    args = parser.parse_args()

    if args.u and args.a:
        text = (
            "Can't both update payments and retrieve all payments please pick only one."
        )
        logger.warning(text)
        sys.exit(text)

    if not args.u and not args.a and not args.w and not args.d and not args.b and not args.p:
        text = "need to either update payments or retrieve all payments please pick only one."
        logger.info(text)
        sys.exit(text)

    return args


def main() -> None:

    args = arguments()

    if args.v:
        setup_rich_logging()
    else:
        setup_log()

    logger = logging.getLogger(__name__)
    logger.info("starting main")
    if args.l:
        farmer_id = args.l
    else:
        farmer_id = os.environ.get("FARMER_ID")

    space_api = APIHandler(FARMER_ID=farmer_id)


    if args.p:
        xch = space_api.xch
        print(xch)
    
    if args.a:
        logger.info(f"-a all mode running for framer id {farmer_id}")
        blocks = space_api.blocks()
        payouts = space_api.payouts()
        payouts = Data.check_transaction_id(payouts)
        FileManager(action="w", report_type="payouts", data=payouts)
        FileManager(action="w", report_type="blocks", data=blocks)

    if args.u:
        logger.info(f"-u update mode running for framer id {farmer_id}")
        data = FileManager(report_type="read").all_transactions
        last = Data.time_of_last_sync(data["payouts"])
        blocks = space_api.blocks(sync_d=last)
        payouts = space_api.payouts(sync_d=last)
        payouts = Data.check_transaction_id(payouts)
        FileManager(action="a", report_type="payouts", data=payouts)
        FileManager(action="a", report_type="blocks", data=blocks)

    if args.b:
        logger.info(f"-b mode running for framer id {farmer_id}")
        data = FileManager(report_type="read").all_transactions
        data_list = []
        for key in data:
            data_list.extend(data[key])

        data = sorted(data_list, key=lambda x: x["timestamp"])
        reports = ReportGenerator(data=data)
        report_data = reports.batch_pay()
        FileManager(action="w", report_type="batch_cointracker", data=report_data)
    
    if args.d or args.w:
        logger.info(f"-d mode running for framer id {farmer_id}")
        data = FileManager(report_type="read").all_transactions
        data_list = []
        for key in data:
            data_list.extend(data[key])

        data = sorted(data_list, key=lambda x: x["timestamp"])
        reports = ReportGenerator(data=data)
        if args.d:
            reports.daily_report()
        if args.w:
            reports.weekly_report()
        
    

if __name__ == "__main__":
    main()
