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
# from gpiozero import LED

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

def send_internet_request():
    point = Point("internet_request").tag("device_id", "alarm").tag("priority", "high").field("requesting", True)
    write_api.write(bucket="group1", org=org, record=point)

while True:
    print("sending request")
    send_internet_request()
    print("request sent")
    time.sleep(350)