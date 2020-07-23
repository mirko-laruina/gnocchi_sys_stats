# gnocchi_sys_stats
Project for the course in Cloud Computing @ UniPi

It provides an application to visualize system statistics (CPU and memory usage), 
stored using Gnocchi with OpenStack.

## Usage

### Getting a token

Connect to a node from which you can connect to OpenStack, login using the
`admin.sh` script and request the issue of a new token.

```shell
$ source admin.sh
$ openstack token issue
```

Then copy the content of the id row, it will look like the following (I have 
wrapped the token over multiple lines for sake of visualization but usually 
it is not broken):

```
+------------+-----------------------------------------------------------------+
| Field      | Value                                                           |
+------------+-----------------------------------------------------------------+
| expires    | 2020-07-23T17:49:57+0000                                        |
| id         | gAAAAABfGb-1D4yI2O06fJj5rJwANTAWfGyIWHLRJezjlsYQXbrOkefOtdfmfkoe|
|            | jc4mgDquIJINY4pDyZJA5q3hhkCZckZDYMu5rQWsjt2dB85YfUQVCy04cqkb-bNC|
|            | UuH-lNYlxKtnjBepZyYgaSpTItZnxHBlFyX4xKVmK8BP_apvs7EM_VQ         |
| project_id | 56db67ef8e1d4ed78c7589bdd2fd73fc                                |
| user_id    | 5baa4ea88e9c4fc192b71bbcd24fd2a3                                |
+------------+-----------------------------------------------------------------+
```

### Running the producer
On the machine you want to monitor run the following:

```shell
$ cd src
$ TOKEN=<token>
$ python producer.py -t $TOKEN
```

You can also pass the following arguments to the script in case you need:
 - `-i`: changes update interval (in seconds)
 - `-u`: sets Gnocchi endpoint URL (defaults to the one we used in our experiments)
 - `--project_id`: sets project id (defaults to the one we used in our experiments)
 - `--user_id`: sets user id (defaults to the one we used in our experiments)

### Running the consumer
There are three modes of operation: `list`, `plot` and `dump`.

To all commands shown below, you can pass the following additional arguments:
 - `-u`: sets Gnocchi endpoint URL (defaults to the one we used in our experiments)
 - `--user_id`: sets user id (defaults to the one we used in our experiments)
 - `--project_id`: sets project id (defaults to the one we used in our experiments)

Use `list` to list all available resources along with available metrics:

```shell
$ cd src
$ TOKEN=<token>
$ python consumer.py list -t $TOKEN
```

Once you find the resource you want to monitor, you can copy its UUID and use 
the `plot` command to monitor one of its metrics:

```shell
$ cd src
$ TOKEN=<token>
$ python consumer.py plot <uuid> -t $TOKEN -m <metric>
```

You can add multiple resources by just adding their UUID after the one shown 
above.

You can also pass the following arguments to the script to change its behaviour:
 - `-g`: change granularity (default second) 
 - `-r`: resample the measures to a more coarse representation (e.g. 10s, 2m, ...)
 - `-a`: choose how to aggregate resampled measures (e.g. mean, max, min, ...)
  
If you prefer a command line representation of the incoming data, you can use
the `dump` command:

```shell
$ cd src
$ TOKEN=<token>
$ python consumer.py dump <uuid> -t $TOKEN -m <metric>
```

NB: this command can monitor only one resource at a time

You can also pass the following arguments to the script to change its behaviour:
 - `-g`: change granularity (default second) 
 - `-r`: resample the measures to a more coarse representation (e.g. 10s, 2m, ...)
 - `-a`: choose how to aggregate resampled measures (e.g. mean, max, min, ...)

### Bonus: running the consumer on your laptop through tunnelling
If the Gnocchi endpoint is not directly reachable from your computer's network, 
you can open a SSH tunnel as follows:

```shell
$ ssh -L localhost:8041:252.3.47.9:8041 ubuntu@172.16.3.47
```

This command connects to the user `ubuntu` at the (reachable) machine `172.16.3.47`
and opens a local tunnel that makes all connections to `localhost:8041` being 
redirected to `252.3.47.9:8041` (which is our Gnocchi endpoint). Remember not 
to close this ssh session otherwise the tunnel will be tear down.

Then you can just add `-u http://localhost:8041` to the commands shown earlier
to connect using the tunnel.
