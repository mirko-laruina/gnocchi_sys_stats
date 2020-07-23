#!/usr/bin/env python3

import argparse
import psutil
from time import sleep
import os, sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from dateutil import parser as dateparser
from datetime import tzinfo, timedelta, datetime, timezone

import gnocchi_api

verbose = False

# hardcoded project_id/user_id for development
DEFAULT_PROJECT_ID = '3d22f640-84db-40ce-af49-44468443234f'
DEFAULT_USER_ID = '3d22f640-84db-40ce-af49-44468443234f'

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
    """
    Parses a string in the format Nu, where N is a number and u is a unit.

    The unit can be:
     - 's' for seconds
     - 'm' for minutes
     - 'h' for hours
     - 'd' for days
    E.g. "1s", "5m", ...
    """

    if s[-1] not in UNITS:
        print("Invalid time delta format: ", s)
        exit(1)
    else:
        unit = UNITS[s[-1]]
        return int(s[:-1])*unit

def list_resources(gnocchi):
    for res in gnocchi.list_resources():
        print(res['id'], ', '.join(res['metrics'].keys()))

def plot(gnocchi, hosts, metric, granularity, resample, aggregation, width=60):
    """
    Display a real-time plot of the given metric for the given hosts.
    """

    # Create figure for plotting
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    # initialize the dictionary that will contain the data fetched from Gnocchi
    hosts_data = {host_id:{} for host_id in hosts}

    # get metric UUID from Gnocchi
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
        # clear the plot
        ax.clear()

        for host_id in hosts:
            data = hosts_data[host_id]

            if data: 
                # if there is already some data, request only new information
                # setting the "start" parameter to the timestamp of the last
                # sample
                last_timestamp = sorted(list(data.keys()))[-1]
                measures = gnocchi.get_measures(metrics[host_id], resample=resample, granularity=granularity, start=last_timestamp, aggregation=aggregation, refresh=True)
            else:
                # otherwise query for any data in our window
                if resample:
                    from_time = time() - width*resample
                else:
                    from_time = time() - width*granularity
                    
                measures = gnocchi.get_measures(metrics[host_id], resample=resample, granularity=granularity, aggregation=aggregation, start=from_time, refresh=True)

            if verbose:
                print(measures)

            # update the data dictionary with new measures
            # (a dictionary is used to automatically fix conflicts)
            data.update({ts:val for ts, gran, val in measures})

            # Sort in ascending timestamp order and limit the number of items
            # to `width`
            keys = sorted(list(data.keys())[-width:])
            data = {k:data[k] for k in keys}

            # Compute x axis values
            # (distance in seconds from now to the timestamp of the measure)
            now = datetime.now(timezone.utc)
            xs = [(dateparser.parse(k)-now).total_seconds() for k in keys]

            # Get y axis values
            ys = [data[k] for k in keys]

            # Plot the line of this host
            ax.plot(xs, ys, label=host_id)

        # Format plot
        plt.title('%s (every %d seconds)' % (
            metric, 
            resample if resample else granularity
        ))

        plt.ylabel('%s load (%%)' % metric)
        plt.ylim(0, 100)
        plt.legend()
        plt.grid()

    # call animate the first time to initialize the plot
    animate(0, hosts_data)

    # Set up plot to call animate() function periodically
    # (every `granularity` seconds)
    ani = animation.FuncAnimation(fig, animate, fargs=(hosts_data,), interval=granularity*1000)

    # show plot
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gnocchi consumer for system usage informations")
    parser.add_argument("command",  type=str, nargs=1, choices=["list", "plot"], help="Command, one of: list, plot")
    parser.add_argument("args",  type=str, nargs='*', help="Depends on command. `list` has no arguments, `plot` gets a list of host_ids (at least one).")
    parser.add_argument("-t", "--token",  type=str, required=True, help="Authentication token")
    parser.add_argument("-g", "--granularity",  type=str, default="second", choices=["second", "minute", "hour", "day"], help="Granularity (only plot). Choices: second, minute, hour, day")
    parser.add_argument("-r", "--resample",  type=str, default=None, help="Resample measures to another interval. Format: 'Nu', N is a number, u is a unit ('s', 'm', 'h', 'd')")
    parser.add_argument("-m", "--metric",  type=str, default="cpu", help="Metric to show for the given host(s).")
    parser.add_argument("-a", "--aggregation",  type=str, default="mean", help="Aggregation method.")
    parser.add_argument("-u", "--url", type=str, default='http://252.3.47.9:8041/', help="Gnocchi listening URL")
    parser.add_argument("--user_id", type=str, default=DEFAULT_USER_ID, help="Openstack User ID")
    parser.add_argument("--project_id", type=str, default=DEFAULT_PROJECT_ID, help="Openstack project ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()

    verbose = args.verbose

    gnocchi = gnocchi_api.GnocchiAPI(args.url, args.token, 
            args.project_id, args.user_id)

    if verbose:
        print("Command:", args.command)
        print("Arguments:", args.args)

    # catch AuthException to print nice error message
    try: 
        if args.command[0] == 'list':
            list_resources(gnocchi)
        elif args.command[0] == 'plot':
            if not args.args:
                print("No host provided. Run with -h/--help to check usage", file=sys.stderr)
                exit(1)

            hosts = args.args
            gran_str = args.granularity

            # parse the resample time
            if args.resample:
                resample = parse_timedelta(args.resample)
            else:
                resample = None
            
            # parse the granularity
            if gran_str in GRANULARITIES:
                gran = GRANULARITIES[gran_str]
            else:
                print("Unknown granularity: ", gran_str)
                exit(1)

            # start plotting
            plot(gnocchi, hosts, args.metric, gran, resample, args.aggregation)
        else:
            print("Unknown command: " + args.command[0])
            exit(1)
    except gnocchi_api.AuthException:
        print("Authentication token expired")
        exit(1)
