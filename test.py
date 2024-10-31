import json
import socket

data = {'account_phone': '0715700411', 'email': 'aqeglipambuya@gmail.com', 'family_name': 'Mbuya', 'given_name': 'Aqeglipa', 'name': 'Aqeglipa Mbuya', 'picture': 'https://lh3.googleusercontent.com/a/ACg8ocIT_d6PJsuw4KxtCBnprPf-jLSjDva0vCP6UJMSmzvE3qnwaEvY', 'sub': '114248626444216198151'}


def isonline():
    """Check if the device is offline by attempting to connect to a known host."""
    try:
        # Attempt to create a socket connection to a known reliable host
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        # If connection is successful, device is online
        return True
    except OSError:
        # If there is an error, assume device is offline
        return False

def load():
    with open('contacts.json', "r") as file:
        initial_data = json.load(file)
    return initial_data

def write(data):
    with open('contacts.json', "w") as file:
        initial_data = json.dumps(data, indent=4)
        file.write(initial_data)

def offline_write(data):
    data = process(data)
    with open('offline_contacts.json', "w") as file:
        initial_data = json.dumps(data, indent=4)
        file.write(initial_data)

def process(data):
    data = {f"{data['sub']}":data}
    return data

def update_data(data):
    initial_data = load()
    final_data = process(data)
    initial_data.update(final_data)
    write(initial_data)
    if not isonline():
        offline_write(data)


update_data(data)