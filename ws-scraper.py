import json
import os
import subprocess
from datetime import datetime
import time
import paho.mqtt.client as mqtt

MQTT_SERVER = "bigblackbox.local"
MQTT_TOPIC = "433_scraper/"
MQTT_PORT = 1883

print("Hello from Raspberry!")

command = ["rtl_433", "-C", "si", "-F", "json"]

# Open the subprocess and capture its output

sensors = []

mqttc = mqtt.Client("weatherpi")
mqttc.connect(MQTT_SERVER, MQTT_PORT)
print(f"MQTT connected to {MQTT_SERVER}:{MQTT_PORT}")

def on_publish(client, userdata, message):
    pass
    # print(f"Published: {message}")

mqttc.on_publish = on_publish

process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

def send_over_mqtt(message):
    global mqttc
    print(message)

    model = message.get('model')
    id = message.get('id')
    subtopic = f"{model}/{id}"

    payload = str(message)

    mqttc.publish(MQTT_TOPIC + subtopic + "/json", payload)

    for key, value in message.items():
        mqttc.publish(MQTT_TOPIC + subtopic + "/" + key, value)

def update_sensors(new_message):
    """
    TODO: mitschreiben in text file
    :param new_message:
    :return:
    """
    print(f"{new_message}")
    global sensors
    # Check if a message with the same model and id exists in the list
    for i, message in enumerate(sensors):
        if message.get('model') == new_message.get('model') and message.get('id') == new_message.get('id') and message.get('channel') == new_message.get('channel'):

            date_format = '%Y-%m-%d %H:%M:%S'
            this_datetime = datetime.strptime(new_message.get("time"), date_format)
            last_datetime = datetime.strptime(message['time'], date_format)
            last_interval_s = (this_datetime - last_datetime).total_seconds()
            print(f"Seen {last_interval_s} seconds ago")
            if last_interval_s < 2:
                print("Ignoring message, too soon")
                break

            new_message['count'] = message['count'] + 1
            new_message['suspect_interval'] = last_interval_s
            # Update the existing message with the new values
            sensors[i] = new_message


            break
    else:
        print("New sensor found!")
        # If no existing message found, add the new message to the list
        new_message['count'] = 1
        sensors.append(new_message)

    dump_all_sensors(clear=True)

def dump_all_sensors(clear=False):
    print(f"- SENSORS [{len(sensors)}] ------------------------------------------------------------------")
    if clear:
        os.system('clear')
    for item in sensors:
        time = item.get('time').ljust(20)
        model = item.get('model').ljust(25)
        id = str(item.get('id')).rjust(8)
        count = str(item.get('count')).rjust(4)
        channel = str(item.get('channel'))
        interval = (str(item.get('suspect_interval'))+" s").rjust(8)
        ignore = ["time", "model", "id", "battery_ok", "mic", "suspect_interval", "count", "channel"]
        copied_dict = item.copy()
        for item in ignore:
            copied_dict.pop(item, None)

        print(f"{time} [{interval}, {count}] | {id} {model} CH{channel} | {copied_dict}")
    print(80 * "-")

mqttc.loop_start()

while True:
    output = process.stdout.readline()  # Read a line from the output
    if output == '' and process.poll() is not None:  # If no more output and the process has terminated
        break
    if output:
        jstring = json.loads(output.strip())
        # update_sensors(jstring)
        send_over_mqtt(jstring)

mqttc.loop_stop()

return_code = process.wait()
print("Process finished with return code:", return_code)