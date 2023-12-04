import requests
from datetime import datetime
import json
from time import sleep
import ast
from datetime import timedelta
import sys




def space_farmer(farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'):
    # farmer_id = '714d01d058b6e29f017bb5d0c6f25edd8ebb34715e168a10321e83ebf393780b'
    usd = 0
    xch = 0
    pre_day = 'new'

    with open(f'/home/ericgr3gory/space_farmer_{farmer_id}.txt', 'r') as file:
        first_line = file.readline().strip('\n')
        first_line = ast.literal_eval(first_line)
        first_date = datetime.fromtimestamp(first_line['timestamp'])
        first_date = first_date.date()
        first_date = datetime.fromisoformat(f'{first_date} 12:00:00')
    while True:
        daily_xch = 0
        daily_usd = 0

        with open(f'/home/ericgr3gory/space_farmer_{farmer_id}.txt', 'r') as file:

            for line in file:
                line = ast.literal_eval(line)
                time_utc = datetime.fromtimestamp(line['timestamp'])
                xch_amount = line['amount'] / 10 ** 12
                usd_amount = float(line['xch_usd']) * xch_amount
                tfh = first_date + timedelta(hours=24)
                #print(f'{time_utc} >= {first_date} and {time_utc} <= {tfh}')
                #print(time_utc >= first_date and time_utc <= tfh)
                if time_utc >= first_date and time_utc <= tfh:
                    daily_xch += xch_amount
                    daily_usd += usd_amount
            print(f'{first_date} - {tfh}')
            print(daily_usd)
            print(daily_xch)
            first_date = first_date - timedelta(hours=24)

def main():
    farmer_id = '714d01d058b6e29f017bb5d0c6f25edd8ebb34715e168a10321e83ebf393780b'
    # pages = space_farmer_pages()
    # space_farmer_get_data(pages=pages)
    space_farmer()


if __name__ == '__main__':
    main()
