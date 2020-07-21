#!/usr/bin/env python

import argparse
import psutil
from time import sleep
import os, sys
import gnocchi_api
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from dateutil import parser as dateparser
from datetime import tzinfo, timedelta, datetime, timezone

verbose = False

GRANULARITIES = {
    'second': 1,
    'minute': 60,
    'hour': 3600,
    'day': 3600*24,
}

UNITS = {
    's': 1,
    'm': 60,
    'h': 3600,
    'd': 3600*24,
}

def parse_timedelta(s):
    if s[-1] not in UNITS:
        print("Invalid time delta format: ", s)
        exit(1)
    else:
        unit = UNITS[s[-1]]
        return int(s[:-1]*unit)

def list_resources(gnocchi):
    for res in gnocchi.list_resources():
        print(res['id'], ', '.join(res['metrics'].keys()))

def plot(gnocchi, hosts, metric, granularity, resample, aggregation, width=60):
    # Create figure for plotting
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    hosts_data = {host_id:{} for host_id in hosts}

    metrics = {}
    for host_id in hosts:
        host_metrics = gnocchi.get_metrics_from_resource(host_id)

        if metric not in host_metrics:
            print("Unavailable metric %s for host %s" % (metric, host_id))
            print("Available metrics: ", host_metrics)
            exit(1)
        else:
            metrics[host_id] = host_metrics[metric]

    # This function is called periodically from FuncAnimation
    def animate(i, hosts_data):
        ax.clear()
        for host_id in hosts:
            data = hosts_data[host_id]
            if data:
                measures = gnocchi.get_measures(metrics[host_id], resample=resample, granularity=granularity, start=sorted(list(data.keys()))[-1], aggregation=aggregation, refresh=True)
            else:
                measures = gnocchi.get_measures(metrics[host_id], resample=resample, granularity=granularity, aggregation=aggregation, refresh=True)

            if verbose:
                print(measures)

            data.update({m[0]:m[2] for m in measures})

            # Limit x and y lists to width items
            keys = sorted(list(data.keys())[-width:])
            data = {k:data[k] for k in keys}

            # Draw x and y lists
            now = datetime.now(timezone.utc)
            xs = [(dateparser.parse(k)-now).total_seconds() for k in keys]
            ys = [data[k] for k in keys]
            ax.plot(xs, ys, label=host_id)

        # Format plot
        # plt.xticks(rotation=45, ha='right')
        # plt.subplots_adjust(bottom=0.30)
        plt.title('%s (every %d seconds)' % (metric, resample))
        plt.ylabel('%s load (%%)' % metric)
        plt.ylim(0, 100)
        plt.legend()
        plt.grid()

    animate(0, hosts_data)
    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, animate, fargs=(hosts_data,), interval=granularity*1000)
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gnocchi producer for system usage informations")
    parser.add_argument("command",  type=str, nargs=1, help="Command, one of: list, plot")
    parser.add_argument("args",  type=str, nargs='*', help="Depends on command. `list` has no arguments, `plot` has two arguments: host_id and granulatity (one of second, minute, hour, day)")
    parser.add_argument("-t", "--token",  type=str, required=True, help="Authentication token")
    parser.add_argument("-g", "--granularity",  type=str, default="second", help="Granularity (only plot). Choices: second, minute, hour, day")
    parser.add_argument("-r", "--resample",  type=str, default=None, help="Resample measures to another interval. Format: 'Nu', N is a number, u is a unit ('s', 'm', 'h', 'd')")
    parser.add_argument("-m", "--metric",  type=str, default="cpu", help="Metric to show for the given host(s).")
    parser.add_argument("-a", "--aggregation",  type=str, default="average", help="Aggregation method.")
    parser.add_argument("-u", "--url", type=str, default='http://252.3.47.9:8041/', help="Gnocchi listening URL")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()

    verbose = args.verbose

    # Commands:
    # - list: shows available hosts (aka hosts)
    # - plot <host_id> <metric> <granularity=second>: plots real-time plot
    #[- distribution: plots distribution of load among all hosts (?)]

    gnocchi = gnocchi_api.GnocchiAPI(args.url, args.token)

    if verbose:
        print("Command:", args.command)
        print("Arguments:", args.args)

    if args.command[0] == 'list':
        list_resources(gnocchi)
    elif args.command[0] == 'plot':
        if not args.args:
            print("Usage: python3 consumer.py plot <hostid> [<other_host>...]", file=sys.stderr)
            exit(1)
        hosts = args.args
        metric = args.metric
        gran_str = args.granularity
        aggr = args.aggregation
        if args.resample:
            resample = parse_timedelta(args.resample)
        else:
            resample = None
        
        if gran_str in GRANULARITIES:
            gran = GRANULARITIES[gran_str]
        else:
            print("Unknown granularity: ", gran_str)
            exit(1)

        plot(gnocchi, hosts, metric, gran, resample, aggr)
    else:
        print("Unknown command: " + args.command[0])
        exit(1)
