import requests
from datetime import datetime
import json
from datetime import timedelta
import argparse
import csv
import sys
from dotenv import load_dotenv
import os
from time import sleep
import logging

API = 'https://spacefarmers.io/api/farmers/'
API_PAYOUTS = '/payouts?page='
load_dotenv()
logging.basicConfig(filename='/tmp/space.log', encoding='utf-8', filemode='a', level=logging.DEBUG)
logger = logging.getLogger(__name__)

def api_request(api: str, session: object)->str:

    for _ in range(3):
        r = session.get(api)
        logger.info(f'connecting to {api}')
        if r.status_code == 200:
            logger.info(f'connected to {api}')
            return r.text
        else:
            logger.info(f'connection failed to {api}')
            logger.info(f'trying again')
            sleep(3)
    logger.warning('three attempts were made to contact api all failed.  Try again later...')
    sys.exit('three attempts were made to contact api all failed.  Try again later...')
    

def number_pages(farmer_id: str)-> int:
    logger.info('finding number of pages containing payout data')
    session = requests.Session()
    api = f'{API}{farmer_id}{API_PAYOUTS}1'
    data = api_request(api=api, session=session)
    json_data = json.loads(data)
    pages = int(json_data['links']['total_pages'])
    logger.info(f'number of pages found {pages}')
    return pages


def time_of_last_sync(data: list)-> int:
    logger.info('retrieving time and date of last syc')
    try:
        return int(data[-1]['timestamp'])
    
    except IndexError:
        logger.info('no data to retreive syc date and time from')
        return  0
        


def retrieve_data(farmer_id: str, pages: int, synced: int)-> list: 
    data = []
    session = requests.Session()
    
    for page in range(1, pages + 1):
        page = api_request(api=f'{API}{farmer_id}{API_PAYOUTS}{page}', session=session)
        json_page = json.loads(page)
        logger.info(f'getting data from{page}')
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
    logger.info(f'reading data from file {farmer_id}.csv')
    with open(f'{farmer_id}.csv', 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)

    return data

def convert_mojo_to_xch(mojos: int)->float:
    logger.info('converting mojo to xch')
    return int(mojos) / 10 ** 12


def convert_date_for_cointracker(date: int)->str:
    logger.info('converting date time to cointracker.com compatible format')
    time_utc = datetime.fromtimestamp(date)
    return time_utc.strftime("%m/%d/%Y %H:%M:%S")


def convert_to_cointracker(data: list)-> list:
    ct = []
    logger.info('converting data to cointracker.com campatiable format')
    for line in data:
        time_utc = convert_date_for_cointracker(line['timestamp'])
        xch_amount = convert_mojo_to_xch(line['amount'])
        cointrack = {"date": time_utc, "Received Quantity": xch_amount, "Received Currency": "XCH",
                     "Sent Quantity": None, "Sent Currency": None, "Fee Amount": None,
                     "Fee Currency": None, "Tag": "mined"}
        ct.append(cointrack)
    return ct


def write_csv(file_name: str, data: list, file_mode: str)->None:
    logger.info(f'writing csv file {file_name}')
    field_names = list(data[0].keys())
    with open(file_name, file_mode) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        if 'w' in file_mode:
            writer.writeheader()
            
        writer.writerows(data)

def arguments()->object:
    parser = argparse.ArgumentParser(description='Retreive block reward payments from SapceFarmers.com api and write to csv')
    parser.add_argument('-l', help='launcher_id', type=str)
    parser.add_argument('-a', help='retieve all payments from api', action="store_true")
    parser.add_argument('-u', help='update payments from api', action="store_true")
    args = parser.parse_args()
    
    if args.u and args.a:
        text = 'Can\'t both update payments and retrieve all payments please pick only one.'
        logger.warning(text)
        sys.exit(text)

    if not args.u and not args.a:
        text = 'need to either update payments or retrieve all payments please pick only one.'
        logger.warning(text)
        sys.exit(text)
    
    return args
    

def main()-> None:
    args = arguments()
    
    if args.l:
        farmer_id = args.l
    else:
        farmer_id = os.environ.get('FARMER_ID')
    
    

    pages = number_pages(farmer_id=farmer_id)
    
    if args.a:
        data = []
        file_mode = 'w'
        logger.info(f'-a all mode running for framer id {farmer_id}')

    if args.u:
        data = read_data(farmer_id=farmer_id)
        file_mode = 'a'
        logger.info(f'-u update mode running for framer id {farmer_id}')

    l_s = time_of_last_sync(data)   
    if data := retrieve_data(farmer_id=farmer_id, pages=pages, synced=l_s):
        write_csv(file_name=f"{farmer_id}.csv",data=data, file_mode=file_mode)
        write_csv(file_name=f"cointracker-{farmer_id}.csv", data=convert_to_cointracker(data=data), file_mode=file_mode)   
    else:
        logger.info('No Updates found.')
        sys.exit('No Updates')
    


if __name__ == '__main__':
    main()
