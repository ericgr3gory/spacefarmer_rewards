import requests
from datetime import datetime
import json
from time import sleep
import ast
from datetime import timedelta


def space_farmer(farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'):
    # farmer_id = '714d01d058b6e29f017bb5d0c6f25edd8ebb34715e168a10321e83ebf393780b'
    usd = 0
    xch = 0
    pre_day = 'new'
    daily_xch = 0
    daily_usd = 0
    with open(f'/home/ericgr3gory/space_farmer_{farmer_id}.txt', 'r') as file:

        for line in file:
            line = ast.literal_eval(line)
            time_utc = datetime.fromtimestamp(line['timestamp'])
            xch_amount = line['amount'] / 10 ** 12
            usd_amount = float(line['xch_usd']) * xch_amount
            #print(xch_amount, time_utc, usd_amount)
            day = time_utc.date()
            time = time_utc.time()
            dayy = datetime.fromisoformat('2023-11-27').date()
            if day == dayy:
                noon = time.fromisoformat('12:00:00')
                midnight = time.fromisoformat('23:59:00')
                if time > noon and time < midnight:
                    daily_xch += xch_amount
                    daily_usd += usd_amount
            if day == dayy + timedelta(days=1):
                ...



        print(daily_usd)
        print(daily_xch)


def main():
    farmer_id = '714d01d058b6e29f017bb5d0c6f25edd8ebb34715e168a10321e83ebf393780b'
    # pages = space_farmer_pages()
    # space_farmer_get_data(pages=pages)
    space_farmer()


if __name__ == '__main__':
    main()
