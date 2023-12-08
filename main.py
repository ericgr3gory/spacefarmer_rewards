import requests
from datetime import datetime
import json
from time import sleep
import ast
from datetime import timedelta
import argparse


def write_to_file(data, farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'):
    with open(f'/home/ericgr3gory/space_farmer_{farmer_id}.txt', 'a') as w:
        w.write(f'{data}\n')


def space_farmer_pages(farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'):
    api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page=1'
    r = requests.get(api)
    j = json.loads(r.text)
    return int(j['links']['total_pages'])


def update_mining_file(farmer_id, data, pages):
    date = first_available_date(data)
    new_data = []
    for page in range(1, pages + 1):
        api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page={page}'
        request = requests.get(api)
        json_page = json.loads(request.text)
        for i in json_page['data']:
            time_utc = datetime.fromtimestamp(i['attributes']['timestamp'])
            print(time_utc)
            if time_utc > date:
                new_data.append(i['attributes'])

            else:
                new_data = sorted(new_data, key=lambda x: x['timestamp'])
                for d in new_data:
                    write_to_file(d, farmer_id)
                return True


def space_farmer_write_data(farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794',
                            pages=1):
    data = []
    for page in range(1, pages + 1):
        api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page={page}'
        request = requests.get(api)
        json_page = json.loads(request.text)
        for i in json_page['data']:
            data.append(i['attributes'])

    sorted_data = sorted(data, key=lambda x: x['timestamp'])
    for d in sorted_data:
        write_to_file(d, farmer_id)


def read_data(farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'):
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
        space_farmer_write_data(farmer_id=farmer_id, pages=pages)

    if args.n:
        pages = space_farmer_pages(farmer_id=farmer_id)
        data = read_data(farmer_id=farmer_id)
        update_mining_file(farmer_id=farmer_id, data=data, pages=pages)

    data = read_data(farmer_id=farmer_id)
    starting_date = first_available_date(data=data)
    space_farmer_daily(starting_date=starting_date, data=data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SpaceFarmer\'s api tools')
    parser.add_argument('-l', help='launcher_id', type=str)
    parser.add_argument('-r', help='reload payments from api', action="store_true")
    parser.add_argument('-n', help='get new payments from api', action="store_true")
    args = parser.parse_args()
    main()
