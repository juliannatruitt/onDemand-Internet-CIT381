#CIT-381 Final Project InfluxDB Client template

#You will need to install the InfluxDB Client on your local machine. Python3 must be installed.
#run the command below to install InfluxDB Client:
#pip3 install influxdb-client

#Run this command in your terminal to save your token as an environment variable:
#export INFLUXDB_TOKEN=CQxPVcrv6nB7b_W5_-SIJcr4kCOd02w7Z-qxiMQZ1O8GyEDtyIu1QZwT4BkU4UXkkcuO4KMXyUBTSWShkHdIqw==

#import required modules
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from gpiozero import LED

# Constants (DO NOT MODIFY)
token = "CQxPVcrv6nB7b_W5_-SIJcr4kCOd02w7Z-qxiMQZ1O8GyEDtyIu1QZwT4BkU4UXkkcuO4KMXyUBTSWShkHdIqw=="
org = "NKU"
url = "http://10.5.12.45:8086"  #Pi at NKU
bucket = "group1"

# Setup InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

# Setup GPIO relay for internet control
relay = LED(6)


# State tracking variables
internet_is_on = False

# Secure priority registry
device_priorities = {
    "device1": "high",
    "device2": "low",
    "device3": "low",
    "device4": "high",
}

# Function to check recent internet requests
def check_for_requests():
    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -1m)
      |> filter(fn: (r) => r._measurement == "internet_request")
      |> filter(fn: (r) => r._field == "requesting")
      |> filter(fn: (r) => r._value == true)
    '''

    tables = query_api.query(query, org=org)

    requests_found = []
    for table in tables:
        for record in table.records:
            device_id = record.values.get("device_id", "unknown")
            priority = device_priorities.get(device_id, "low")
            requests_found.append((device_id, priority))
            print(f"Request from device: {device_id}, Priority: {priority}")

    return requests_found

# Function to activate internet access
def turn_on_internet():
    global internet_is_on, relay

    internet_is_on = True
    relay.on()

    print(f"internet is ", relay)

    # Notify high priority devices immediately
    point_high = Point("internet_access").tag("priority", "high").field("available", True)
    write_api.write(bucket=bucket, org=org, record=point_high)
    print("High priority devices notified of internet ON")

    time.sleep(10)

    # Notify low priority devices
    point_low = Point("internet_access").tag("priority", "low").field("available", True)
    write_api.write(bucket=bucket, org=org, record=point_low)
    print("Low priority devices notified of internet ON")

# Function to deactivate internet access
def turn_off_internet():
    global internet_is_on, relay

    internet_is_on = False
    relay.off()

    print(f"internet is ", relay)

    # Update database about internet off state
    for priority in ["high", "low"]:
        point_off = Point("internet_access").tag("priority", priority).field("available", False)
        write_api.write(bucket=bucket, org=org, record=point_off)

    print("Internet turned OFF")

# Main loop
while True:
    requests = check_for_requests()
    if requests:
        if not internet_is_on:
            print("Activating internet for received requests.")
            turn_on_internet()
    else:
        if internet_is_on:
            print("No active requests. Deactivating internet.")
            turn_off_internet()

    time.sleep(1)
