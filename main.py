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

#DO NOT MODIFY
token = "CQxPVcrv6nB7b_W5_-SIJcr4kCOd02w7Z-qxiMQZ1O8GyEDtyIu1QZwT4BkU4UXkkcuO4KMXyUBTSWShkHdIqw=="
org = "NKU"
#Uncomment the desired IP.
url = "http://10.15.8.77:8086"  #Pi at NKU
#url = "http://172.16.1.100:8086" #Pi at Nick's VPN

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
bucket="group1" #Put in your bucket information here (group1-8): e.g., group1, group2, group3...
write_api = write_client.write_api(write_options=SYNCHRONOUS)


#Example for sending data. This defines 5 data points and writes each one to InfluxDB.
#Each of the 5 points we write has a field and a tag. These tags are not required but are helpful to sort data.
for value in range(5):
  point = Point("sensor_data").tag("location", "lab1").field("temperature", value)
            #Measurement name     Tag key/value pair    Field key/value pair
  write_api.write(bucket=bucket, org=org, record=point) #Writes the data
  time.sleep(1) #Waits 1 second to separate points (do not remove)


#Example of a simple query
query_api = write_client.query_api()

#InfluxDB uses Flux for querying the database. Select the bucket, the range (in this case, data from the last 10 minutes)
#Then specify the measurement (in this case, sensor_data)
query = """from(bucket: "group1")  
 |> range(start: -10m)
 |> filter(fn: (r) => r._measurement == "sensor_data")"""
tables = query_api.query(query, org=org) #Stores the data in the variable tables

#Prints the table information in the terminal.
for table in tables:
  for record in table.records:
    print(record)


#Example of an aggregate query
#These queries take the values of all rows in a table and use them to perform an aggregate operation.
#The result is output as a new value in a single-row table.
query_api = write_client.query_api()

#This query pulls all information from the group1 bucket in the last 10 minutes, filters only sensor_data,
#Then calculates the mean.
query = """from(bucket: "group1")
  |> range(start: -10m)
  |> filter(fn: (r) => r._measurement == "sensor_data")
  |> mean()"""
tables = query_api.query(query, org=org) #Stores information in the table variable.

#Prints the information in the terminal.
for table in tables:
    for record in table.records:
        print(record)