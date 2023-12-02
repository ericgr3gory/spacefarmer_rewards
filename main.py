import requests
from datetime import datetime
import json
from time import sleep
import ast
from datetime import timedelta


def xch_scan():
    xch_address = 'xch1jfay8srrwhxjaezvsytsgf9dc326njwelannj7jwrkx8z3ytjz8qr5zwle'

    for off_set in range(1, 250):
        xch = f'https://xchscan.com/api/account/txns?address={xch_address}&limit=10&offset={off_set}'
        request = requests.get(xch)

        xch_json = json.loads(request.text)
        for i in xch_json['txns']:
            time_utc = datetime.fromtimestamp(i['timestamp'])
            print(f'{i["amount"]}  {time_utc}')
        sleep(2.2)


def write_to_file(data, farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'):
    with open(f'/home/ericgr3gory/space_farmer_{farmer_id}.txt', 'a') as w:
        w.write(f'{data}\n')


def space_farmer_pages(farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'):
    api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page=1'
    r = requests.get(api)
    j = json.loads(r.text)
    return int(j['links']['total_pages'])


def space_farmer_write_data(farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794',
                            pages=1):
    for page in range(1, pages + 1):
        api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page={page}'
        request = requests.get(api)
        json_page = json.loads(request.text)
        for i in json_page['data']:
            write_to_file(i['attributes'], farmer_id)


def read_data(farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'):
    data = []

    with open(f'/home/ericgr3gory/space_farmer_{farmer_id}.txt', 'r') as file:
        for line in file:
            line = ast.literal_eval(line)
            data.append(line)

    return data


def last_available_date(data):
    return datetime.fromtimestamp(data[-1]['timestamp'])


def first_available_date(data):
    first_date = datetime.fromtimestamp(data[0]['timestamp']).date()
    return datetime.fromisoformat(f'{first_date} 12:00:00')


def space_farmer_daily(starting_date, data):
    t_usd = 0
    t_xch = 0
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
    # farmer_id = '714d01d058b6e29f017bb5d0c6f25edd8ebb34715e168a10321e83ebf393780b'
    farmer_id = 'e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'
    # pages = space_farmer_pages(farmer_id=farmer_id)
    # space_farmer_write_data(farmer_id=farmer_id, pages=pages)
    data = read_data(farmer_id=farmer_id)
    starting_date = first_available_date(data=data)
    space_farmer_daily(starting_date=starting_date, data=data)


if __name__ == '__main__':
    main()
