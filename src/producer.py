#!/usr/bin/env python3

import argparse
import psutil
from time import sleep
import os, sys
import gnocchi_api

verbose = False

# hardcoded project_id/user_id for development
DEFAULT_PROJECT_ID = '3d22f640-84db-40ce-af49-44468443234f'
DEFAULT_USER_ID = '3d22f640-84db-40ce-af49-44468443234f'

def get_machine_uuid():
    try:
        f = open('uuid', 'r') if os.path.isfile('uuid') else os.popen('uuidgen | tee uuid')
    except:
        print("Error retrieving UUID")
    return f.read().split('\n')[0]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gnocchi producer for system usage informations")
    parser.add_argument("-i", "--interval", type=float, default=60,
                        help="Amount of seconds between measurements")
    parser.add_argument("-t", "--token",  type=str, required=True, help="Authentication token")
    parser.add_argument("-u", "--url", type=str, default='http://252.3.47.9:8041/', help="Gnocchi listening URL")
    parser.add_argument("--user_id", type=str, default=DEFAULT_USER_ID, help="Openstack User ID")
    parser.add_argument("--project_id", type=str, default=DEFAULT_PROJECT_ID, help="Openstack project ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()

    verbose = args.verbose
    uuid = get_machine_uuid()
    print("Machine UUID: %s"%uuid)

    gnocchi = gnocchi_api.GnocchiAPI(args.url, args.token, 
            args.project_id, args.user_id)

    try:
        metrics = gnocchi.get_metrics_from_resource(uuid)
        print("Metrics: %s"%metrics)
    except gnocchi_api.AuthException:
        print("Authentication token has expired")
        sys.exit(1)
    except Exception as e:
        print("Application exception")
        print(e)
        sys.exit(1)

        

    while True:
        try:
            cpu_util = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            mem_util = float(mem[3])/mem[0]*100
            gnocchi.send_measure(metrics['cpu'], cpu_util)
            # virtual_memory()[3] returns the currently used memory
            gnocchi.send_measure(metrics['memory'], mem_util)

            if args.verbose:
                print("Pushed new measurement. CPU: %f%% Memory: %f%%"%(cpu_util, mem_util))
                
        except gnocchi_api.AuthException:
            print("Authentication token has expired")
            sys.exit(1)
        except Exception as e:
            print("Application exception")
            print(e)
            sys.exit(1)

        sleep(args.interval)
