import csv
import sys
from dotenv import load_dotenv
import os
import logging

load_dotenv()

TEMP_DIR = os.environ.get("TEMP_DIR")
CURRENT_DIR = os.getcwd()


logger = logging.getLogger(__name__)


class FileManager:
    """read, write and assign file names"""

    def __init__(
        self, report_type: str = "read", action: str = "r", data: list = []
    ) -> None:

        self.farmer_id = os.environ.get("FARMER_ID")
        self.api_blocks = os.environ.get("API_BLOCKS")
        self.api_payouts = os.environ.get("API_PAYOUTS")
        self.report_type: str = report_type
        self.file_mode = action
        self.data = data

        if "read" in report_type:
            self.all_transactions: dict = self.read_all_transactions()
        else:
            self.file_name = self.file_naming(report_type=report_type)

        if "w" in action or "a" in action:
            self.write_csv()

    def read_all_transactions(self) -> dict:
        keys = ["blocks", "payouts"]
        all_trans = {}
        for k in keys:
            file: str = self.file_naming(k)
            data: list = self.read_data(file=file)
            all_trans[k] = data

        return all_trans

    def file_naming(self, report_type) -> str:
        file_prefix = f"{self.farmer_id[:4]}_{self.farmer_id[-4:]}"
        file_extension = f".csv"
        file_names = {
            "blocks": f"-{self.api_blocks[1:6]}",
            "payouts": f"-{self.api_payouts[1:7]}",
            "batch_cointracker": f"-batch_cointracker",
            "daily_cointracker": f"-daily_cointracker",
            "weekly_cointracker": f"weekly_cointracker",
        }
        name = f"{file_prefix}{file_names[report_type]}{file_extension}"
        return name

    def read_data(self, file) -> list:
        data = []

        logger.info(f"reading data from file {file}")

        with open(file=file, mode="r") as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                data.append(row)

        return data

    def write_csv(self) -> None:

        try:
            field_names = self.data[0]
        except IndexError as e:
            logger.info(e)
            logger.info(f"No Updates to write to csv for {self.file_name}")
            sys.exit(f"No Updates to write to csv for {self.file_name}")
        with open(file=self.file_name, mode=self.file_mode) as csvfile:
            logger.info(f"writing csv file {self.file_name}")
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            if "w" in self.file_mode:
                writer.writeheader()

            writer.writerows(self.data)
