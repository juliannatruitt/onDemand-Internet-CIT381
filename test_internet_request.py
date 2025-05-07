# Class: CIT381, Spring 2025
# Names: Julianna Truitt, Ryan Arnzen, Corey Pitts, Kolya Cherepenin, and Nick Miller
# Description: Sends test requests to our on demand internet implementation to ensure it is working and set up properly.
#   It has three different methods to test 3 different senerios. One for showing that high priority requests turn the internet on right away,
#   another to show how sending one request that has low priority then waiting for the low priority wait time will turn internet on, and lastly
#   another to show that three low priority requests will turn the internet on.

import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# DO NOT MODIFY
token = "CQxPVcrv6nB7b_W5_-SIJcr4kCOd02w7Z-qxiMQZ1O8GyEDtyIu1QZwT4BkU4UXkkcuO4KMXyUBTSWShkHdIqw=="
org = "NKU"
# Uncomment the desired IP.
url = "http://10.5.12.45:8086"  # Pi at NKU
# url = "http://172.16.1.100:8086"  # Pi at Nick's VPN

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
bucket = "group1"
write_api = write_client.write_api(write_options=SYNCHRONOUS)
query_api = write_client.query_api()


# method to send an internet request. It includes the parameter "device" so you can input the device id
def send_internet_request(device):
    point = Point("internet_request").tag("device_id", device).field("requesting", True)
    write_api.write(bucket="group1", org=org, record=point)


# checks the internet status
def check_internet_status():
    query = f"""from(bucket: "group1")
    |> range(start: -2m)
    |> filter(fn: (r) => r._measurement == "internet_access")
    |> filter(fn: (r) => r._field == "available")
    |> last()"""

    tables = query_api.query(query, org=org)

    internet_available = False
    for table in tables:
        for record in table.records:
            # Access the value correctly
            internet_available = record.get_value()
            print(f"Internet available: {internet_available}")

    return internet_available


# test that will send one low priority request then wait for the low priority timer to end
def test_to_send_one_low_request_and_wait_for_timer_to_end():
    check_internet_status()
    print("sending request")
    send_internet_request(
        "device2")  # this device id is hardcoded as a low priority device on the on demand internet implementation code
    time.sleep(
        615)  # sleeping for 615 seconds since the wait time is 600 seconds (10 minutes) and low priority devices are alerted of the internet ending 10 seconds after high priority devices
    check_internet_status()


# test that will show how sending a high priority request will turn on the internet immediatly
def test_sending_one_high_request_turns_internet_on_immediately():
    check_internet_status()
    time.sleep(1)
    print("sending request")
    send_internet_request(
        "device1")  # this device id is hardcoded as a high priority device on the on demand internet implementation code
    time.sleep(15)
    check_internet_status()


# test to show that three low priority requests turns on the internet immediately.
def test_send_three_low_requests_turns_on_internet():
    check_internet_status()
    print("sending request: 1")
    send_internet_request(
        "device2")  # this device id is hardcoded as a low priority device on the on demand internet implementation code
    time.sleep(3)

    check_internet_status()
    print("sending request: 2")
    send_internet_request(
        "device3")  # this device id is hardcoded as a low priority device on the on demand internet implementation code
    time.sleep(3)

    check_internet_status()
    print("sending request: 3")
    send_internet_request("unknownDevice")  # unknown device is so priority will be treated as low priority

    time.sleep(15)
    check_internet_status()


while True:
    # Run tests by uncommenting which test you want to run (should only run 1 test at a time)
    # The time.sleep(1000) is set to allow for the test to run and it gives it more than enough time to run
    # (the sleep time is high due to the method test_to_send_one_low_request_and_wait_for_timer_to_end(), which needs 10 minutes to allow
    # for the time period to end and the internet to be turned on)

    # IMPORTANT NOTE: make sure you wait for the internet to turn off before stopping the program and running another test. If the internet is still on and you try to
    # run another test, there is a possibility it could produce incorrect results.

    test_to_send_one_low_request_and_wait_for_timer_to_end()
    # test_sending_one_high_request_turns_internet_on_immediately()
    # test_send_three_low_requests_turns_on_internet()

    time.sleep(1000)


