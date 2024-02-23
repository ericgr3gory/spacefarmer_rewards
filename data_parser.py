from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
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



class DataParser:
    def __init__(self) -> None:
        ...

    
    def time_of_last_sync(data:list) -> int:
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


    def day(d: int) -> str:
        '''
        converted daily timestamp to datetime of last second of day and coverted to cointracker formet
        can be used to generate daily rewards for cointracker format
        '''
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
        '''
        converted daily timestamp to datetime of last second of week and  coverted to cointracker format
        can be used to generate weekly rewards for cointracker format
        '''
        d = datetime.fromtimestamp(d)
        monday = d - timedelta(days=d.weekday())
        sunday = monday + timedelta(days=6)
        sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=0)
        logger.info(
            "converted daily timestamp to datetime of last second of week and  coverted to cointracker formet"
        )
        return sunday.strftime("%m/%d/%Y %H:%M:%S")
    
    
    def check_transaction_id(self, data: list) -> list:
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
