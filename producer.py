#!/usr/bin/env python

import argparse
import psutil
from time import sleep

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Gnocchi producer for system usage informations")
    parser.add_argument("-t", type=float, default=60,
                        help="Amount of seconds between measurements")
    parser.add_argument("--id", type=str, required=False,
                        help="Machine ID: measurements will be distinguished based on this value")
    args = parser.parse_args()

    while True:
        print(psutil.cpu_percent())
        sleep(args.t)



