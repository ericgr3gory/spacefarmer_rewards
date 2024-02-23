from dotenv import load_dotenv
import os
import logging
from data_parser import DataParser as Data

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


class ReportGenerator:

    def __init__(self, data: list) -> None:
        self.batch: list = self.batch_pay(data)
        self.daily_earnings: list = self.time_based_report(data=data, time_period="d")
        self.weekly_earnings: list = self.time_based_report(data=data, time_period="w")

    def batch_pay(self, data: list) -> dict:
        """
        creates a dictionary using keys based on payout transaction ID for normal payouts or farmed height for block rewards
        each key has three lists one for xch, one for usd price and one for timestamp
        this dictionay can be used to create a report based on when spacefarmers sent payouts to your wallet and when block rewards were sent to your wallet
        dates and amounts of xch should match the data viewable on the payouts page of spacefarmers.io.  it should mtach the batch payouts.
        """
        batch: dict = {}

        logger.info(f"creating spacefarmer dictionary with batch payout schedule")
        for line in data:
            if "transaction_id" in line:
                key = line["transaction_id"]

            if "farmed_height" in line:
                key = line["farmed_height"]

            if key not in batch:
                batch[key] = [[], [], []]

            if "farmer_reward_taken_by_gigahorse" in line:
                farmer_reward: bool = bool(line["farmer_reward_taken_by_gigahorse"])

                if farmer_reward:
                    xch_amount: float = int(line["farmer_reward"]) / 10**11
                    batch[key][0].append(xch_amount)
                    batch[key][2].append(int(line["timestamp"]))
                    continue

                if not farmer_reward:
                    batch[key][0].append(0)
                    batch[key][2].append(int(line["timestamp"]))
                    continue

            xch_amount: float = Data.convert_mojo_to_xch(int(line["amount"]))
            usd_price: float = float(line["xch_usd"])
            batch[key][0].append(xch_amount)
            batch[key][1].append(usd_price)
            batch[key][2].append(int(line["timestamp"]))

        logger.info(f"Completed spacefarmer dictionary with batch payouts")

        return self.batch_payout_parsed_ct(batch)

    def batch_payout_parsed_ct(self, batch_pay_data: list):
        """
        create a list with data parsed for cointracker
        """

        cointracker_data: list = []

        for batch in batch_pay_data:

            date: int = max(batch_pay_data[batch][2])
            date: str = Data.convert_date_for_cointracker(date)
            sum_xch: float = sum(batch_pay_data[batch][0])

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
            cointracker_data.append(cointrack)

        return cointracker_data

    def time_based_report(self, data: list, time_period: str):
        """
        takes a list of payouts and block wins.  Creates a dictionary with the keys being created as daily or weekly.
        can be used to show xch mined by day or weekly monday through sunday

        """
        space_report = {}
        logger.info(f"creating spacefarmer dictionary with time period = {time_period}")
        for line in data:

            if "w" in time_period:
                key = Data.week(int(line["timestamp"]))
            elif "d" in time_period:
                key = Data.day(int(line["timestamp"]))

            if key not in space_report:
                space_report[key] = [[], []]
            try:
                if line["farmer_reward_taken_by_gigahorse"] == "False":
                    xch_amount: float = int(line["farmer_reward"]) / 10**12
                    space_report[key][0].append(xch_amount)
                    continue

                elif line["farmer_reward_taken_by_gigahorse"] == "True":
                    continue

            except KeyError as e:
                ...

            xch_amount: float = Data.convert_mojo_to_xch(int(line["amount"]))
            usd_price: float = float(line["xch_usd"])
            space_report[key][0].append(xch_amount)
            space_report[key][1].append(usd_price)

        logger.info(
            f"Completed spacefarmer dictionary with time period = {time_period}"
        )

        return self.format_for_cointracker(space_report)

    def format_for_cointracker(self, space_dict: dict) -> list:
        ct: list = []

        for k in space_dict:
            sum_xch: float = sum(space_dict[k][0])
            average_usd_price: float = sum(space_dict[k][1]) / len(space_dict[k][1])
            daily_usd_revenue: float = sum_xch * average_usd_price
            logger.info(
                f"{k}, {round(sum_xch, 10)}, {round(average_usd_price, 2)}, {round(daily_usd_revenue, 2)}"
            )
            cointrack: dict = {
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
