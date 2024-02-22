import csv
import sys
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


class FileManager():
    
    '''read, write and assign file names'''
    
    def __init__(self) -> None:
        
        self.farmer_id = os.environ.get("FARMER_ID")
        self.api_blocks = os.environ.get("API_BLOCKS")
        self.api_payouts = os.environ.get("API_PAYOUTS")
        self.all_transactions: dict = self.read_all_transactions()
    
    def read_all_transactions(self)->dict:
        all_trans ={'blocks': [], 'payouts': []}
        for t in all_trans:
            file: str = self.file_name(t)
            data: list = self.read_data(file=file)
            all_trans[t].append(data)
        
        return all_trans
        
        
    def file_name(self, report_type: str)-> str:
        file_prefix = f'{self.farmer_id[:4]}---{self.farmer_id[-4:]}'
        file_extension = f'.csv'
        file_names = {
                    'blocks': f"-{self.api_blocks[1:6]}",
                    'payouts': f"-{self.api_payouts[1:6]}",
                    'normal_cointracker': f"-normal_cointracker",
                    'daily_cointracker': f"-daily_cointracker",
                    'weekly_cointracker': f"weekly_cointracker",
                    }
        return f'{file_prefix}{file_names[report_type]}{file_extension}'
    
        
    def read_data(self, file) -> list:
        data = []
        
        logger.info(f"reading data from file {file}")
        
        with open(file=file, mode='r') as f:
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
