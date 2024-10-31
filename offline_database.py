import json
import socket


class OfflineDatabase:

    file_name = ''

    def load(self):
        with open(self.file_name, "r") as file:
            initial_data = json.load(file)
        return initial_data

    def write(self, data):
        with open(self.file_name, "w") as file:
            initial_data = json.dumps(data, indent=4)
            file.write(initial_data)

    def process(self, data):
        data = {f"{data['sub']}":data}
        return data

    def update_data(self, data):
        self.file_name = 'contacts.json'
        initial_data = self.load()
        final_data = self.process(data)
        initial_data.update(final_data)
        self.write(initial_data)
        if not self.isonline():
            self.update_offline_data(data)

    def update_offline_data(self, data):
        self.file_name = 'offline_contacts.json'
        initial_data = self.load()
        final_data = self.process(data)
        initial_data.update(final_data)
        self.write(initial_data)

    def isonline(self):
        """Check if the device is offline by attempting to connect to a known host."""
        try:
            # Attempt to create a socket connection to a known reliable host
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            # If connection is successful, device is online
            return True
        except OSError:
            # If there is an error, assume device is offline
            return False

# update_data(data)
# OfflineDatabase.file_name = 'offline_contacts.json'
# print(OfflineDatabase.load(OfflineDatabase()))