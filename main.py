import requests
from datetime import datetime
import json
from time import sleep
import ast


def xch_scan():
    xch_address = 'xch1jfay8srrwhxjaezvsytsgf9dc326njwelannj7jwrkx8z3ytjz8qr5zwle'
    api_key = 'd99ac4dd-fe16-4702-8db5-bbcd2d3edd48'
    for off_set in range(1, 250):
        xch = (f'https://xchscan.com/api/account/txns?address={xch_address}&limit=10&offset={off_set}')
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


def space_farmer_get_data(farmer_id='e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794',
                          pages=1):
    for page in range(1, pages + 1):
        api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page={page}'
        request = requests.get(api)
        json_page = json.loads(request.text)
        for i in json_page['data']:
            write_to_file(i['attributes'])


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

            if day == pre_day:
                daily_xch += xch_amount
                daily_usd += usd_amount
            else:
                print(pre_day, daily_xch, daily_usd)
                daily_xch = xch_amount
                daily_usd = usd_amount
            usd += usd_amount
            xch += xch_amount
            pre_day = day

        print(usd)
        print(xch)


def main():
    farmer_id = '714d01d058b6e29f017bb5d0c6f25edd8ebb34715e168a10321e83ebf393780b'
    # pages = space_farmer_pages()
    # space_farmer_get_data(pages=pages)
    space_farmer()


if __name__ == '__main__':
    main()
