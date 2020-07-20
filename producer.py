#!/usr/bin/env python

import argparse
import psutil
from time import sleep, time
import requests
import os

base_url = "http://252.3.47.9:8041/"
header = {}

def get_metric():
    r = requests.get(base_url + "/v1/metric", headers=headers)
    print(r.json())
    return r.json()[-1]['id'].encode('ascii', 'ignore')

def get_machine_uuid():
    try:
        f = open('uuid', 'r')
        return f.read().split('\n')[0]
    except:
        return os.popen('uuidgen | tee uuid').read().split('\n')[0]

def get_metrics(uuid):
    r = requests.get(base_url + '/v1/resource/generic/' + uuid, headers=headers)
    if r.status_code != 200:
        # we need to create the resource
        r = requests.post(base_url + '/v1/resource/generic', headers=headers, json={
                "id": uuid,
                "project_id": '3d22f640-84db-40ce-af49-44468443234f',
                "user_id": '3d22f640-84db-40ce-af49-44468443234f',
                "metrics": {
                    "cpu": {
                        "archive_policy_name": "high"
                    },
                    "memory": {
                        "archive_policy_name": "high"
                    }
                }
            } )
    
    return r.json()['metrics']

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Gnocchi producer for system usage informations")
    parser.add_argument("-i", "--interval", type=float, default=60,
                        help="Amount of seconds between measurements")
    parser.add_argument("-t", "--token",  type=str, required=True, help="Authentication token")
    args = parser.parse_args()
        
    headers = { 
        'X-AUTH-TOKEN': args.token,
        'Content-Type': 'application/json'
    }

    uuid = get_machine_uuid()
    print("Machine UUID:", uuid)

    metrics = get_metrics(uuid)
    print("Metrics: ", metrics)

    while True:
        data = {
            "timestamp": time(),
            "value": psutil.cpu_percent()
        }
        # Gnocchi returns ISO 8601 timestamps, but accepts different formats. Unix epoch is OK
        r = requests.post(base_url+"/v1/metric/"+metrics['cpu']+"/measures", headers=headers, json=[data])

        # virtual_memory()[3] returns the currently used memory
        data = {
            "timestamp": time(),
            "value": psutil.virtual_memory()[3]
        }

        r = requests.post(base_url+"/v1/metric/"+metrics['memory']+"/measures", headers=headers, json=[data])
        sleep(args.interval)
