import requests
from datetime import datetime
import json
from datetime import timedelta
import argparse
import csv
import sys
from dotenv import load_dotenv
import os

API = 'https://spacefarmers.io/api/farmers/'
API_PAYOUTS = '/payouts?page='
load_dotenv()

def number_pages(farmer_id: str)-> int:
    r = requests.get(f'{API}{farmer_id}{API_PAYOUTS}1')
    
    if r.status_code == 200:
        j = json.loads(r.text)
    else:
        sys.exit('Space Farmers API in unavaible.  Check your farmer ID, Check your network connection or Try again later.')
    
    return int(j['links']['total_pages'])


def last_sync(data: list)-> int:
    try:
        return int(data[-1]['timestamp'])
    
    except IndexError:
        return  0
        


def retrieve_data(farmer_id: str, pages: int, synced: int)-> list: 
    data = []
    session = requests.Session()
    
    for page in range(1, pages + 1):
    
        request = session.get(f'{API}{farmer_id}{API_PAYOUTS}{page}')
        
        if request.status_code == 200:
            json_page = json.loads(request.text)
        
        else:
            sys.exit('Space Farmers API in unavaible.  Check your farmer ID, Check your network connection or Try again later.')
        
        
        
        for i in json_page['data']:
            time_utc = i['attributes']['timestamp']
            if time_utc > synced:
                data.append(i['attributes'])
                print(i['attributes'])
            else:
                return sorted(data, key=lambda x: x['timestamp'])
    
    return sorted(data, key=lambda x: x['timestamp'])



def read_data(farmer_id: str)->list:
    data = []
    with open(f'{farmer_id}.csv', 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)

    return data

def convert_mojo_to_xch(mojos: int)->float:
    return int(mojos) / 10 ** 12


def convert_date_for_cointracker(date: int)->str:
    time_utc = datetime.fromtimestamp(date)
    return time_utc.strftime("%m/%d/%Y %H:%M:%S")


def convert_to_cointracker(data: list)-> list:
    ct = []
    for line in data:
        time_utc = convert_date_for_cointracker(line['timestamp'])
        #time_utc = datetime.fromtimestamp(line['timestamp'])
        #time_utc = time_utc.strftime("%m/%d/%Y %H:%M:%S")
        xch_amount = convert_mojo_to_xch(line['amount'])
        #xch_amount = line['amount'] / 10 ** 12
        cointrack = {"date": time_utc, "Received Quantity": xch_amount, "Received Currency": "XCH",
                     "Sent Quantity": None, "Sent Currency": None, "Fee Amount": None,
                     "Fee Currency": None, "Tag": "mined"}
        ct.append(cointrack)
    return ct


def write_csv(file_name: str, data: list, file_mode: str):
    field_names = list(data[0].keys())
    with open(file_name, file_mode) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        if 'w' in file_mode:
            writer.writeheader()
            
        writer.writerows(data)



def main():
    parser = argparse.ArgumentParser(description='SpaceFarmer\'s api tools')
    parser.add_argument('-l', help='launcher_id', type=str)
    parser.add_argument('-a', help='retieve all payments from api', action="store_true")
    parser.add_argument('-u', help='update payments from api', action="store_true")
    args = parser.parse_args()
    
    if args.u and args.a:
        sys.exit('Can\'t both update payments and retrieve all payments please pick only one.')
    
    if args.l:
        farmer_id = args.l
    else:
        farmer_id = os.environ.get('FARMER_ID')
    
    pages = number_pages(farmer_id=farmer_id)
    
    if args.a:
        data = []
        file_mode = 'w'
        

    if args.u:
        data = read_data(farmer_id=farmer_id)
        file_mode = 'a'
    
    l_s = last_sync(data)   
    data = retrieve_data(farmer_id=farmer_id, pages=pages, synced=l_s)
    write_csv(file_name=f"{farmer_id}.csv",data=data, file_mode=file_mode)
    write_csv(file_name=f"cointracker-{farmer_id}.csv", data=convert_to_cointracker(data=data), file_mode=file_mode)


if __name__ == '__main__':
    main()
