import requests
from datetime import datetime
import json
from time import sleep
import ast
from datetime import timedelta
import argparse
import csv


def write_to_file(data: list, farmer_id: str):
    with open(f'/home/ericgr3gory/space_farmer_{farmer_id}.txt', 'a') as w:
        for d in data:
            w.write(f'{d}\n')


def space_farmer_pages(farmer_id: str)-> int:
    api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page=1'
    r = requests.get(api)
    j = json.loads(r.text)
    return int(j['links']['total_pages'])


def update_mining_file(farmer_id: str, data: list, pages: int):
    date = first_available_date(data)
    new_data = []
    for page in range(1, pages + 1):
        api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page={page}'
        request = requests.get(api)
        json_page = json.loads(request.text)
        for i in json_page['data']:
            time_utc = datetime.fromtimestamp(i['attributes']['timestamp'])
            if time_utc > date:
                new_data.append(i['attributes'])
            
    return sorted(new_data, key=lambda x: x['timestamp'])


def retreive_spacefarmer_data(farmer_id: str, pages: int =1)-> list:
    data = []
    for page in range(1, pages + 1):
        api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page={page}'
        request = requests.get(api)
        json_page = json.loads(request.text)
        for i in json_page['data']:
            data.append(i['attributes'])

    return sorted(data, key=lambda x: x['timestamp'])



def read_data(farmer_id: str)->list:
    data = []

    with open(f'/home/ericgr3gory/space_farmer_{farmer_id}.txt', 'r') as file:
        for line in file:
            line = ast.literal_eval(line)
            data.append(line)

    return data


def last_available_date(data):
    return datetime.fromtimestamp(data[0]['timestamp'])


def first_available_date(data):
    return datetime.fromtimestamp(data[-1]['timestamp'])


def convert_to_cointracker(data: list)-> list:
    ct = []
    for line in data:
        time_utc = datetime.fromtimestamp(line['timestamp'])
        time_utc = time_utc.strftime("%m/%d/%Y %H:%M:%S")
        xch_amount = line['amount'] / 10 ** 12
        cointrack = {"date": time_utc, "Received Quantity": xch_amount, "Received Currency": "XCH",
                     "Sent Quantity": None, "Sent Currency": None, "Fee Amount": None,
                     "Fee Currency": None, "Tag": "mined"}
        ct.append(cointrack)
    return ct


def csv_cointracker(data):
    field_names = list(data[1].keys())
    with open('/home/ericgr3gory/cointracker.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(data)


def space_farmer_daily(starting_date, data):
    t_usd = 0
    t_xch = 0
    starting_date = datetime.fromisoformat(f'{starting_date.date()} 12:00:00')
    while starting_date > last_available_date(data):
        daily_xch = 0
        daily_usd = 0
        end_time = 0
        for line in data:
            time_utc = datetime.fromtimestamp(line['timestamp'])
            xch_amount = line['amount'] / 10 ** 12
            usd_amount = line['xch_usd'] * xch_amount
            end_time = starting_date + timedelta(hours=23, minutes=59, seconds=59)

            if starting_date <= time_utc <= end_time:
                daily_xch += xch_amount
                daily_usd += usd_amount

        print(f'{starting_date} - {end_time}')
        print(daily_usd)
        print(daily_xch)
        starting_date = starting_date - timedelta(hours=24)


def main():
    if args.l:
        farmer_id = args.l
    else:
        farmer_id = 'e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'
        # farmer_id = '714d01d058b6e29f017bb5d0c6f25edd8ebb34715e168a10321e83ebf393780b'

    if args.r:
        pages = space_farmer_pages(farmer_id=farmer_id)
        data = retreive_spacefarmer_data(farmer_id=farmer_id, pages=pages)
        write_to_file(data=data, farmer_id=farmer_id)

    if args.n:
        pages = space_farmer_pages(farmer_id=farmer_id)
        data = read_data(farmer_id=farmer_id)
        data = update_mining_file(farmer_id=farmer_id, data=data, pages=pages)
        write_to_file(data=data, farmer_id=farmer_id)

    data = read_data(farmer_id=farmer_id)
    csv_cointracker(convert_to_cointracker(data))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SpaceFarmer\'s api tools')
    parser.add_argument('-l', help='launcher_id', type=str)
    parser.add_argument('-r', help='reload payments from api', action="store_true")
    parser.add_argument('-n', help='get new payments from api', action="store_true")

    args = parser.parse_args()
    main()
