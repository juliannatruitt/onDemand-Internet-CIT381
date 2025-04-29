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
# from gpiozero import LED

# Constants (DO NOT MODIFY)
token = "CQxPVcrv6nB7b_W5_-SIJcr4kCOd02w7Z-qxiMQZ1O8GyEDtyIu1QZwT4BkU4UXkkcuO4KMXyUBTSWShkHdIqw=="
org = "NKU"
# url = "http://10.5.12.45:8086"  #Pi at NKU
url = "http://172.16.1.100:8086" #nicks pi
bucket = "group1"

# Setup InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

# Setup GPIO relay for internet control
relay = "OFF"
# relay = LED(6)


# State tracking variables
internet_is_on = False
internet_end_time = 0
current_requests = []
queue_end_timer = 0
queue_timer_started = False

# Secure priority registry
device_priorities = {
    "device1": "high",
    "device2": "low",
    "device3": "low",
    "device4": "high",
}

# Function to check recent internet requests
def check_for_requests():
    global current_requests

    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -1m)
      |> filter(fn: (r) => r._measurement == "internet_request")
      |> filter(fn: (r) => r._field == "requesting")
      |> filter(fn: (r) => r._value == true)
    '''

    tables = query_api.query(query, org=org)
    print(current_requests)
    for table in tables:
        for record in table.records:
            device_id = record.values.get("device_id", "unknown")
            # checking if the device id is in current request will avoid duplicate requests from being counted
            if any(device_id == req[0] for req in current_requests):
                continue
            priority = device_priorities.get(device_id, "low")
            current_requests.append((device_id, priority))
            print(f"Request from device: {device_id}, Priority: {priority}")

def start_queue_timer():
    global queue_end_timer, queue_timer_started

    queue_timer_started = True
    # this set the end of the queue (waiting period for a low priority request to be processed)
    # to 10 minuted from the current time. This will give low priority requests a maximum of 10 minutes before
    # internet is turned on to see if more requests come in
    queue_end_timer = time.time() + 600

# Function to activate internet access
def turn_on_internet():
    global internet_is_on, relay, queue_timer_started, queue_end_timer, internet_end_time, current_requests

    # reset variables to original state
    queue_timer_started = False
    queue_end_timer = 0
    current_requests = []

    internet_is_on = True
    relay="ON"


    # Notify high priority devices immediately
    point_high = Point("internet_access").tag("priority", "high").field("available", True)
    write_api.write(bucket=bucket, org=org, record=point_high)
    print("High priority devices notified of internet ON")

    time.sleep(10)

    # Notify low priority devices
    point_low = Point("internet_access").tag("priority", "low").field("available", True)
    write_api.write(bucket=bucket, org=org, record=point_low)
    print("Low priority devices notified of internet ON")

    # set the internet to turn off in 2 minutes
    internet_end_time = time.time() + 120

# Function to deactivate internet access
def turn_off_internet():
    global internet_is_on, relay, internet_end_time

    internet_is_on = False
    internet_end_time = 0
    relay="OFF"

    # Update database about internet off state
    for priority in ["high", "low"]:
        point_off = Point("internet_access").tag("priority", priority).field("available", False)
        write_api.write(bucket=bucket, org=org, record=point_off)

    print("Internet turned OFF")

# Main loop
while True:

    if not internet_is_on:
        check_for_requests()

        if current_requests:

            # we have to set these to 0 before counting requests each time or else it will keep counting the
            # same request multiple times. when we initalize it to 0 before counting each time, we get an accurate
            # number of the amount of requests being recieved
            high_priority_requests = 0
            low_priority_requests = 0

            for request in current_requests:
                if request[1] == "high":
                    high_priority_requests = high_priority_requests + 1
                else:
                    low_priority_requests = low_priority_requests + 1
            print(f"number of high requests: ", high_priority_requests)
            print(f"number of low priority requests: ", low_priority_requests)

            # if there is a high priority request, we immediatly turn on the internet
            if high_priority_requests > 0:
                turn_on_internet()
                print("Activating internet for received requests.")
                continue

            # will get to this line if there is not at least one high priority request, so we will need to
            # start the queue timer for low priority requests (maximum 10 minutes) if it is not already started
            if not queue_timer_started:
                start_queue_timer()

            # turn on internet if there are at least 3 low priority requests or if the 10 minute waiting period is done
            if low_priority_requests >= 3 or time.time() >= queue_end_timer:
                turn_on_internet()
                print("Activating internet for received requests.")
    else:
        # if the two minutes that internet has been on passes, we should turn off the internet
        if time.time() >= internet_end_time:
            print("No active requests. Deactivating internet.")
            turn_off_internet()

    time.sleep(1)
