# Class: CIT381, Spring 2025
# Names: Julianna Truitt, Ryan Arnzen, Corey Pitts, Kolya Cherepenin, and Nick Miller
# Description: Final project of implementing an on demand internet. Devices that need internet access will request into our influxdb bucket ("group1"). Requests are
#   handled based on priority (high or low) of the device. High priority devices get internet turned on immediatly when they send a request. Low priority devices will
#   wait a maximum of 10 minutes (or until at least 3 requests come in) to get the internet turned on. This is so we can wait to see if more requests will come in.

#import required modules
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from gpiozero import LED

# constants (DO NOT MODIFY) from team 7 to access influxDB
token = "CQxPVcrv6nB7b_W5_-SIJcr4kCOd02w7Z-qxiMQZ1O8GyEDtyIu1QZwT4BkU4UXkkcuO4KMXyUBTSWShkHdIqw=="
org = "NKU"
url = "http://10.5.12.45:8086"  #Pi at NKU
#url = "http://172.16.1.100:8086" #nicks pi
bucket = "group1"

# setup InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

# setup GPIO relay for internet control
relay = LED(6)

# variables to track state
internet_is_on = False # tracks when internet has been tuned on
internet_end_time = 0 # tracks when internet will turn off
current_requests = [] # tracks all the current requests
low_priority_end_timer = 0 # tracks when the low priority waiting time will end
low_priority_timer_started = False # tracks when the low priority timer has been started

# priority dictionary
device_priorities = {
    "device1": "high",
    "device2": "low",
    "device3": "low",
    "device4": "high",
}

# function to check recent internet requests
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

# function to start the 10 minute (max) waiting period for low priority request
def start_low_priority_timer():
    global low_priority_end_timer, low_priority_timer_started

    low_priority_timer_started = True
    # this sets the end of the waiting period for a low priority request to be processed to 10 minutes from the current time
    low_priority_end_timer = time.time() + 600

# function to activate internet
def turn_on_internet():
    global internet_is_on, relay, low_priority_timer_started, low_priority_end_timer, internet_end_time, current_requests

    # reset variables to original state
    low_priority_timer_started = False
    low_priority_end_timer = 0
    current_requests = []

    # turn relay on
    internet_is_on = True
    relay.on()

    # notify high priority devices immediately
    point_high = Point("internet_access").tag("priority", "high").field("available", True)
    write_api.write(bucket=bucket, org=org, record=point_high)
    print("High priority devices notified of internet ON")

    # delay 10 seconds before alerting low priority devices
    time.sleep(10)

    # notify low priority devices
    point_low = Point("internet_access").tag("priority", "low").field("available", True)
    write_api.write(bucket=bucket, org=org, record=point_low)
    print("Low priority devices notified of internet ON")

    # set the internet to turn off in 2 minutes (or 120 seconds)
    internet_end_time = time.time() + 120

# function to deactivate internet
def turn_off_internet():
    global internet_is_on, relay, internet_end_time

    internet_is_on = False
    internet_end_time = 0
    relay.off()

    # update database that internet is off
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
            # same request multiple times if we don't
            high_priority_requests = 0
            low_priority_requests = 0

            # counts how many low and high priority requests there are
            for request in current_requests:
                if request[1] == "high":
                    high_priority_requests = high_priority_requests + 1
                else:
                    low_priority_requests = low_priority_requests + 1
            print(f"number of high requests: ", high_priority_requests)
            print(f"number of low priority requests: ", low_priority_requests)

            # if there is a high priority request, we immediately turn on the internet
            if high_priority_requests > 0:
                turn_on_internet()
                print("Activating internet for received requests.")
                continue

            # will get to this line if there is not at least one high priority request, so we will need to
            # start the queue timer for low priority requests (maximum 10 minutes) if it is not already started
            if not low_priority_timer_started:
                start_low_priority_timer()

            # turn on internet if there are at least 3 low priority requests or if the 10 minute waiting period is done
            if low_priority_requests >= 3 or time.time() >= low_priority_end_timer:
                turn_on_internet()
                print("Activating internet for received requests.")
    else:
        # if the two minutes that internet has been on passes, we should turn off the internet
        if time.time() >= internet_end_time:
            print("No active requests. Deactivating internet.")
            turn_off_internet()

    time.sleep(1)
