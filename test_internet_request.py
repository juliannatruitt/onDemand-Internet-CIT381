# creating testing request

import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
# from gpiozero import LED

# DO NOT MODIFY
token = "CQxPVcrv6nB7b_W5_-SIJcr4kCOd02w7Z-qxiMQZ1O8GyEDtyIu1QZwT4BkU4UXkkcuO4KMXyUBTSWShkHdIqw=="
org = "NKU"
# Uncomment the desired IP.
# url = "http://10.15.8.77:8086"  #Pi at NKU
url = "http://172.16.1.100:8086"  # Pi at Nick's VPN

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
bucket = "group1"
write_api = write_client.write_api(write_options=SYNCHRONOUS)
query_api = write_client.query_api()


def send_internet_request():
    point = Point("internet_request").tag("device_id", "device1").field("requesting", True)
    write_api.write(bucket="group1", org=org, record=point)


def check_internet_status():
    query = f"""from(bucket: "group1")
    |> range(start: -1m)
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


while True:
    print("sending request")
    print(check_internet_status())
    send_internet_request()
    time.sleep(10)
    print(check_internet_status())
    time.sleep(350)

