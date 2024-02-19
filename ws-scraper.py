import json
import os
import subprocess
from datetime import datetime

print("Hello from Raspberry!")

command = ["rtl_433", "-C", "si", "-F", "json"]

# Open the subprocess and capture its output
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

sensors = []

def update_sensors(new_message):
    """
    TODO: Channel separate
    TODO: padding für 5 stellen statt 3 bei id
    TODO: mitschreiben in text file
    :param new_message:
    :return:
    """
    print(f"{new_message}")
    global sensors
    # Check if a message with the same model and id exists in the list
    for i, message in enumerate(sensors):
        if message['model'] == new_message['model'] and message['id'] == new_message['id']:

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
        id = str(item.get('id')).rjust(3)
        count = str(item.get('count')).rjust(4)
        interval = (str(item.get('suspect_interval'))+" s").rjust(8)
        ignore = ["time", "model", "id", "battery_ok", "mic", "suspect_interval", "count"]
        copied_dict = item.copy()
        for item in ignore:
            copied_dict.pop(item, None)

        print(f"{time} [{interval}, {count}] | {id} {model}  | {copied_dict}")
    print(80 * "-")

# Continuously read and process the output
while True:
    output = process.stdout.readline()  # Read a line from the output
    if output == '' and process.poll() is not None:  # If no more output and the process has terminated
        break
    if output:
        jstring = json.loads(output.strip())
        update_sensors(jstring)





# Ensure the process has finished and get its return code
return_code = process.wait()
print("Process finished with return code:", return_code)