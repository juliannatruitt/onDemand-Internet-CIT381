#CIT-381 Final Project InfluxDB Client template

#You will need to install the InfluxDB Client on your local machine. Python3 must be installed.
#run the command below to install InfluxDB Client:
#pip3 install influxdb-client

#Run this command in your terminal to save your token as an environment variable:
#export INFLUXDB_TOKEN=CQxPVcrv6nB7b_W5_-SIJcr4kCOd02w7Z-qxiMQZ1O8GyEDtyIu1QZwT4BkU4UXkkcuO4KMXyUBTSWShkHdIqw==

#import required modules
from xmlrpc import client
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from gpiozero import LED

#DO NOT MODIFY
token = "CQxPVcrv6nB7b_W5_-SIJcr4kCOd02w7Z-qxiMQZ1O8GyEDtyIu1QZwT4BkU4UXkkcuO4KMXyUBTSWShkHdIqw=="
org = "NKU"
#Uncomment the desired IP.
#url = "http://10.15.8.77:8086"  #Pi at NKU
url = "http://172.16.1.100:8086" #Pi at Nick's VPN

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
bucket="group1"
write_api = write_client.write_api(write_options=SYNCHRONOUS)
query_api = write_client.query_api()

# relay for internet control
relay = LED(17)  # Replace with whatever GPIO pin

# global variables to track state
internet_is_on = False
internet_end_time = 0


# function to check for internet requests
def check_for_requests():
    # query for the most recent internet requests in the last 1 minutes
    query = f"""from(bucket: "{bucket}")
      |> range(start: -1m)
      |> filter(fn: (r) => r._measurement == "internet_request")
      |> filter(fn: (r) => r._field == "requesting")
      |> filter(fn: (r) => r.value == true)
      |> last()""" # use last to only get the most recent request if many are sent. this is probably best practice so that we do not need to go through many requests if multiple devices request (since we will turn on internet either way)

    tables = query_api.query(query, org=org)

    # process any requests found
    requests_found = False
    for table in tables:
        for record in table.records:
            requests_found = True
            device_id = record.values.get("device_id", "unknown")
            print(f"Found internet request from device: {device_id}")

    return requests_found

def turn_on_internet():
    global internet_is_on, internet_end_time

    # update the state variables
    internet_is_on = True
    internet_end_time = time.time() + (5 * 60) # will keep internet on for 5 minutes (or 300 seconds)

    # turn on the relay, which the internet is plugged into
    relay.on()

    # should we have an internet status point too in our bucket??

    point = Point("internet_access").tag("priority", "high").field("available", True).field("duration_in_minutes", 5)
    write_api.write(bucket=bucket, org=org, record=point)
    print("High priority devices notfied that internet is on for next 5 minutes")

    # delay of 10 seconds for low priority devices to be notified
    time.sleep(10)

    point = Point("internet_access").tag("priority", "low").field("available", True).field("duration_in_minutes", 5)
    write_api.write(bucket=bucket, org=org, record=point)
    print("Low priority devices notfied that internet is on for next 5 minutes")

def turn_off_internet():
    global internet_is_on, internet_end_time

    # update the state variables
    internet_is_on = False
    internet_end_time = 0

    #turn relay off
    relay.off()

    point = Point("internet_access").tag("priority", "high").field("available", False).field("duration_in_minutes", 0)
    write_api.write(bucket=bucket, org=org, record=point)

    point = Point("internet_access").tag("priority", "low").field("available", False).field("duration_in_minutes", 0)
    write_api.write(bucket=bucket, org=org, record=point)

    print("Internet turned off")


# function to determine when internet needs to be turned off (tracks the internet_end_time!)
def determine_when_to_turnoff_internet():
    global internet_is_on, internet_end_time

    # since internet_end_time is set as the current time + 5 minutes, this code will detect when 5 minutes has past if the current time is >= to the internet_end_time
    if internet_is_on and time.time() >= internet_end_time:
        turn_off_internet()

# main loop: checks if internet needs to be turned off, checks requests (if internet is not on), sleeps every second?
while True:
    if internet_is_on:
        determine_when_to_turnoff_internet()

    if not internet_is_on:
        check_requests = check_for_requests()
        if check_requests:
            turn_on_internet()

    # sleep for 1 second
    time.sleep(1)
