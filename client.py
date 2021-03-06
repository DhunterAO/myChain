import hashlib
from constant import SERVER_ADDRESS
from account import Account
from dataURL import DataURL
from constant import server_address
import hashlib
import requests
import logging
import json
import time
import os
from argparse import ArgumentParser
from util import verify_signature

from output import Output


class Client:
    def __init__(self, account=Account(), data_path='./database', outputs=None):
        self._account = account
        self._path = data_path
        if outputs is None:
            self._outputs = set()
        else:
            self._outputs = outputs

    # some universal functions
    def to_json(self):
        # print(type(self._account.to_json()))
        return self._account.to_json()

    # some functions about account

    def create_address(self):
        self._account.create_address()
        return

    def load_account(self, file='account.txt'):
        account_path = os.path.join(self._path, file)
        with open(account_path, 'r') as f:
            account = f.read()
        print(account)
        address_list = json.loads(account)["address_list"]
        for a in address_list:
            # print(a["private_key"])
            self._account.add_address_from_private_key(a["private_key"])

        # print(account)
        # print(type(json.loads(account)))
        return

    def store_account(self, file='account.txt'):
        account_path = os.path.join(self._path, file)
        with open(account_path, 'w') as f:
            f.write(json.dumps(self.to_json()))
        return

    # some functions about outputs

    def update_outputs(self, server_address, address_index=0):
        public_key = self._account.get_address(address_index).get_pubkey()
        timestamp = time.time()
        hash = hashlib.sha256((str(timestamp)).encode()).hexdigest()
        signature = self._account.sign_message(hash, address_index)
        send_json = {
            'public_key': public_key,
            'timestamp': timestamp,
            'signature': signature
        }
        response = requests.post(f"http://{server_address}/outputs/update", json=json.dumps(send_json))

        if response.status_code == 200:
            return_json = response.json()['data_url']
            new_outputs = return_json['new_outputs']
            for out in new_outputs:
                self._outputs.add(out)
        else:
            logging.error('invalid response')
            return False

    # some option about data

    def upload_data(self, server_address, data, address_index=0):
        """
        Upload data to server and get back the dataURL

        :param server_address: x.x.x.x:port
        :param data: data you want to upload
        :param address_index: address index in address_list
        :return: dataURL where the data stores
        """
        public_key = self._account.get_address(address_index).get_pubkey()
        timestamp = time.time()
        hash = hashlib.sha256((str(data)+str(timestamp)+str(0)).encode()).hexdigest()
        signature = self._account.sign_message(hash, address_index)
        send_json = {
            'public_key': public_key,
            'data': data,
            'timestamp': timestamp,
            'op': 0,
            'signature': str(signature)
        }
        # print(signature)
        # print(type(signature))
        # b = str(signature)
        # print(b)
        # print(type(b))
        # c = eval(b)
        # print(c)
        # print(type(c))
        # print(verify_signature(public_key, hash, c))

        response = requests.post(f"http://{server_address}/data/upload", json=send_json)

        if response.status_code == 200:
            get_json = response.json()
            required = ['data_url', 'limit', 'signature']
            if not all(k in get_json for k in required):
                return 'Missing values', 400

            data_url = DataURL(get_json['data_url']['start'], get_json['data_url']['end'])
            out = Output(public_key, data_url, 7)
            self._outputs.add(out)
            return True
        else:
            # print(response)
            return False

    def delete_data(self, server_address, data_url, address_index=0):
        """

        :param server_address:
        :param data_url:
        :param address_index:
        :return:
        """
        public_key = self._account.get_address(address_index).get_pubkey()
        timestamp = time.time()

        hash = hashlib.sha256((str(data_url)+str(timestamp)+str(output_position)+str(1)).encode()).hexdigest()
        signature = self._account.sign_message(hash, address_index)
        send_json = {
            'public_key': public_key,
            'data_url': data_url.to_json(),
            'timestamp': timestamp,
            'output_position': output_position,
            'op': 1,
            'signature': signature
        }

        response = requests.post(f"http://{server_address}/data/delete", json=send_json)
        if response.status_code == 200:
            return True
        else:
            logging.error('invalid response')
            return False

    def update_data(self, server_address, data, data_url, address_index=0):
        """
        Upload data to server and get back the dataURL

        :param server_address: x.x.x.x:port
        :param data: data you want to update
        :param data_url: data position
        :param address_index: address index in address_list
        :return: dataURL where the data stores
        """
        public_key = self._account.get_address(address_index).get_pubkey()
        now_time = time.time()
        hash = hashlib.sha256((str(data)+str(data_url)+str(now_time)+str(2)).encode()).hexdigest()
        signature = self._account.sign_message(hash, address_index)
        send_json = {
            'public_key': public_key,
            'data': data,
            'data_url': data_url,
            'timestamp': now_time,
            'op': 2,
            'signature': signature
        }
        response = requests.post(f"http://{server_address}/data/update", json=send_json)

        if response.status_code == 200:
            return True
        else:
            logging.error('invalid response')
            return False

    def read_data(self, server_address, data_url, output, address_index=0):
        """

        :param server_address:
        :param data_url:
        :param output:
        :param address_index:
        :return:
        """
        public_key = self._account.get_address(address_index).get_pubkey()
        timestamp = time.time()
        hash = hashlib.sha256((str(data_url)+str(timestamp)+str(3)).encode()).hexdigest()
        signature = self._account.sign_message(hash, address_index)
        send_json = {
            'public_key': public_key,
            'data_url': data_url.to_json(),
            'output_position': output,
            'timestamp': timestamp,
            'op': 3,
            'signature': str(signature)
        }

        response = requests.post(f"http://{server_address}/data/read", json=send_json)
        if response.status_code == 200:
            get_json = response.json()
            required = ['data_url', 'limit', 'signature']
            if not all(k in get_json for k in required):
                return 'Missing values', 400
            output = Output(public_key, get_json['data_url'], limit=get_json['limit'])
            return True
        else:
            logging.error('invalid response')
            return False


if __name__ == '__main__':


    client = Client()
    #client.create_address()
    # client.store_account()
    client.load_account()

    #client.upload_data(server_address, 'hello')

    data_url = DataURL(0,1)
    output_position = {
        'block_number': 1,
        'authorization_number': 0,
        'output_number': 0
    }
    client.read_data(server_address, data_url, output_position)

