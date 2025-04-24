# CIT 381: Internet of Things, Spring 2025
# Name: Julianna Truitt, Corey Pitts, Ryan Arnzen, Kolya Cherepenin, & Nick Miller
# Description: Creating an on demand internet for our final project

# Import the Required Modules for the Program
import time
from paho.mqtt import client as mqtt_client
from gpiozero import LED

# Define the MQTT Broker Address and the MQTT Topic
# broker = '' # IP Address of the MQTT Broker
# port =
# mqtt_client_id = f'python-mqtt-{time.time()}'
# mqtt_username = "" # This is setup in the Cedalo Console
# mqtt_password = "" # This is setup in the Cedalo Console

# possible topics to publish:
topic_high_priority = 'internet/priority/high'
topic_low_priority = 'internet/priority/low'

# possible topics to subscribe to (* is dependent on the device that is wanting internet access)
# topic_device1 = 'internet/request/*'

# state variable to track when the internet is on and off
internet_is_on = False

# define relay
# relay = LED(#)

# Functions for MQTT
# Function to Connect to the MQTT Broker
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(mqtt_client_id)
    client.username_pw_set(username=mqtt_username, password=mqtt_password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# Function to Publish the Data to the MQTT Broker
def publish(client, topic, msg):
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Sent `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

#Function to Subscribe to the MQTT Broker on a Specific Topic
def subscribe(client: mqtt_client, topic, on_message):
     client.subscribe(topic)
     # What to do when a message is recieved.
     client.on_message = on_message


# Main Program
# Connect to the MQTT Broker
client = connect_mqtt()
# Subscribe to the devices that will request internet access (not sure which all devices yet...). * can be replaced by the device name
# subscribe(client, 'internet/request/*')
# Start the MQTT Client
client.loop_start()
# Loop to Publish the Data to the MQTT Broker
while True:
