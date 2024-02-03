import requests
from datetime import datetime
import json
from time import sleep
import ast
from datetime import timedelta
import argparse
import csv


def space_farmer_pages(farmer_id: str)-> int:
    api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page=1'
    r = requests.get(api)
    j = json.loads(r.text)
    return int(j['links']['total_pages'])


def update_spacfarmer_data(farmer_id: str, data: list, pages: int):
    
    date = int(data[-1]['timestamp'])
    new_data = []
    
    for page in range(1, pages + 1):
        api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page={page}'       
        request = requests.get(api)
        json_page = json.loads(request.text)
        
        for i in json_page['data']:
            time_utc = i['attributes']['timestamp']
            if time_utc > date:
                new_data.append(i['attributes'])
                print(i['attributes'])
            else:
                return sorted(new_data, key=lambda x: x['timestamp'])


def retreive_spacefarmer_data(farmer_id: str, pages: int = 1)-> list:
    data = []
    for page in range(1, pages + 1):
        api = f'https://spacefarmers.io/api/farmers/{farmer_id}/payouts?page={page}'
        request = requests.get(api)
        json_page = json.loads(request.text)
        for i in json_page['data']:
            data.append(i['attributes'])
            print(i['attributes'])

    return sorted(data, key=lambda x: x['timestamp'])



def read_data(farmer_id: str)->list:
    data = []
    with open(f'{farmer_id}.csv', 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)

    return data


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


def write_csv(file_name, data):
    field_names = list(data[1].keys())
    with open(file_name, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(data)



def main():
    parser = argparse.ArgumentParser(description='SpaceFarmer\'s api tools')
    parser.add_argument('-l', help='launcher_id', type=str)
    parser.add_argument('-r', help='reload payments from api', action="store_true")
    parser.add_argument('-n', help='get new payments from api', action="store_true")
    args = parser.parse_args()
    
    if args.l:
        farmer_id = args.l
    else:
        farmer_id = 'e357cc6b9efe3d487308a0faf1085b2eeb30f66be2b4ebe1f2f81bdede3b6794'
        # farmer_id = '714d01d058b6e29f017bb5d0c6f25edd8ebb34715e168a10321e83ebf393780b'
    
    pages = space_farmer_pages(farmer_id=farmer_id)
    
    if args.r:
        data = retreive_spacefarmer_data(farmer_id=farmer_id, pages=pages)
        

    if args.n:
        data = read_data(farmer_id=farmer_id)
        data = update_spacfarmer_data(farmer_id=farmer_id, data=data, pages=pages)
       
        

    write_csv(file_name=f"{farmer_id}.csv",data=data)
    write_csv(file_name=f"cointracker-{farmer_id}.csv", data=convert_to_cointracker(data=data))


if __name__ == '__main__':
    main()
