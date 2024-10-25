import json

import firebase_admin
from firebase_admin import credentials, initialize_app, db, auth
from firebase_admin.exceptions import FirebaseError
from beem import sms




class FirebaseManager:
    def __init__(self):
        self.cred = credentials.Certificate("credential/farmzon-abdcb-c4c57249e43b.json")
        self.app_initialized = False
        self.database_url = 'https://farmzon-abdcb.firebaseio.com/'

    def refresh_user_info(self, user_data):
        filename = 'user_info.json'
        print("Looooooggggggggggs", user_data)
        # Write user data to the JSON file
        with open(filename, 'w') as json_file:
            json.dump(user_data, json_file, indent=4)


    def remove_comma(self, number):

        new_number = str(number).replace(',', '')

        return int(new_number)

    def get_user_local(self):
        with open("user_info.json", 'r') as json_file:
            user_data = json.load(json_file)

        return user_data

    def initialize_firebase(self):
        firebase_admin._apps.clear()
        if not self.app_initialized:
            print('buyer')
            try:
                initialize_app(self.cred, {'databaseURL': self.database_url})
                self.app_initialized = True
            except FirebaseError as e:
                print(f"Failed to initialize Firebase: {e}")
                return "No Internet!"

    def register_user(self, data):
        """Register a new user in the Firebase database under 'Users'. If the user already exists, skip the registration."""

        # Initialize Firebase (ensure it is initialized)
        self.initialize_firebase()
        if not self.app_initialized:
            return {"status": "error", "code": 500, "message": "Firebase initialization failed"}

        try:
            # Reference to the user's data node in the database
            user_ref = db.reference("ContactP").child("Users").child(data['sub']).child('User_info')

            # Check if the user already exists in the database
            if user_ref.get():
                # If user data exists, skip registration
                return {"status": "success", "code": 200, "message": "User already exists. No action needed."}

            # If the user does not exist, register the new user
            user_ref.set(data)

            # Return success status after successful registration
            return {"status": "success", "code": 200, "message": "User registered successfully"}

        except Exception as e:
            # Handle any exception that occurs during the registration process
            return {"status": "error", "code": 500, "message": f"An error occurred: {str(e)}"}

    def fetch_user_info(self, user_id):
        self.initialize_firebase()  # Ensure Firebase is initialized
        if not self.app_initialized:
            return {
                "status": "error",
                "code": 500,
                "message": "Firebase initialization failed"
            }

        try:
            # Reference to the user's general information in the database
            user_ref = db.reference("ContactP").child("Users").child(user_id).child('User_info')

            # Fetch the user information
            user_info = user_ref.get()

            # Check if the user exists
            if user_info:
                return {
                    "status": "success",
                    "code": 200,
                    "message": "User information fetched successfully",
                    "data": user_info
                }
            else:
                return {
                    "status": "error",
                    "code": 404,
                    "message": "User not found"
                }

        except Exception as e:
            # Handle any exception that occurs during the fetching process
            return {
                "status": "error",
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }

    def fetch_user_profile(self, user_id):
        # Initialize Firebase (ensure it is initialized)
        self.initialize_firebase()

        if not self.app_initialized:
            # Return error if Firebase initialization fails
            return {"status": "error", "code": 500, "message": "Firebase initialization failed"}

        try:
            # Reference to the user's data node in the database
            user_ref = db.reference("ContactP").child("Users").child(user_id)

            # Fetch user data
            user_data = user_ref.get()

            # Check if data is found
            if not user_data:
                return {"status": "error", "code": 404, "message": "User not found"}

            # Fetch user's accounts if present
            accounts_ref = user_ref.child('Accounts')
            accounts_data = accounts_ref.get() or {}

            # Fetch user's contacts if present
            contacts_ref = user_ref.child('Contacts')
            contacts_data = contacts_ref.get() or {}

            # Construct the final user data object with additional information
            full_user_data = {
                "user_info": user_data.get('User_info', {}),
                "accounts": accounts_data,
                "contacts": contacts_data
            }

            # Return success with full user data
            return {"status": "success", "code": 200, "message": "User account information fetched successfully",
                    "data": full_user_data}

        except Exception as e:
            # Handle any exceptions that occur during the fetching process
            return {"status": "error", "code": 500, "message": f"An error occurred: {str(e)}"}

    def add_contact(self, user_id, scanned_contact):
        # Fetch the new contact's information
        new_contact_data = self.fetch_user_info(scanned_contact)

        # If the contact doesn't exist, return an error
        if new_contact_data['code'] != 200:
            return {"status": "error", "code": 404, "message": "User not found"}

        # Initialize Firebase (ensure it is initialized)
        self.app_initialized = False
        self.initialize_firebase()

        # If Firebase initialization failed, return an error
        if not self.app_initialized:
            return {"status": "error", "code": 500, "message": "Firebase initialization failed"}

        try:
            # Reference to the user's Contacts node in the database
            user_ref = db.reference("ContactP").child("Users").child(user_id).child('Contacts').child(
                new_contact_data['data']['sub'])

            # Store the new contact's data
            user_ref.set(new_contact_data['data'])

            # add contact also to scanned_contact
            current_user_data = self.get_user_local()
            current_user_ref = db.reference("ContactP").child("Users").child(new_contact_data['data']['sub']).child('Contacts').child(
                current_user_data['sub'])
            current_user_ref.set(current_user_data)

            # Return success status
            return {"status": "success", "code": 200, "message": "Contact added successfully"}

        except Exception as e:
            # Handle any exception that occurs during the contact addition process
            return {"status": "error", "code": 500, "message": f"An error occurred: {str(e)}"}

    def fetch_contacts(self, user_id):
        self.initialize_firebase()  # Ensure Firebase is initialized
        if not self.app_initialized:
            return {
                "status": "error",
                "code": 500,
                "message": "Firebase initialization failed"
            }

        try:
            # Reference to the user's contacts in the database
            contacts_ref = db.reference("ContactP").child("Users").child(user_id).child('Contacts')

            # Fetch all contacts
            contacts = contacts_ref.get()

            if contacts is None:
                return {
                    "status": "success",
                    "code": 204,
                    "message": "No contacts found"
                }

            # Return success status with contacts data
            return {
                "status": "success",
                "code": 200,
                "message": "Contacts fetched successfully",
                "data": contacts
            }

        except Exception as e:
            # Handle any exception that occurs during the fetching process
            return {
                "status": "error",
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }

    def add_account(self, user_id, account_name, account_link):
        self.initialize_firebase()  # Ensure Firebase is initialized
        if not self.app_initialized:
            return {
                "status": "error",
                "code": 500,
                "message": "Firebase initialization failed"
            }

        try:
            # Generate a unique account ID (e.g., based on the account name or timestamp)
            account_id = f"{account_name}{user_id}"

            # Reference to the user's accounts in the database
            account_ref = db.reference("ContactP").child("Users").child(user_id).child('Accounts').child(account_id)

            # Data to be added
            account_data = {
                "account_id": account_id,
                "account_name": account_name,
                "account_link": account_link
            }

            # Store the account data
            account_ref.set(account_data)

            if account_name == 'phone':
                account_ref = db.reference("ContactP").child("Users").child(user_id).child('User_info')

                # Data to be added
                account_data = {
                    "account_phone": account_link,
                }

                # Store the account data
                account_ref.update(account_data)

                self.app_initialized = False
                data = self.fetch_user_info(user_id)
                self.refresh_user_info(data['data'])

            # Return success status
            return {
                "status": "success",
                "code": 200,
                "message": "Account added successfully",
                "data": account_data
            }

        except Exception as e:
            # Handle any exception that occurs during the process
            return {
                "status": "error",
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }

    def fetch_accounts(self, user_id):
        self.initialize_firebase()  # Ensure Firebase is initialized
        if not self.app_initialized:
            return {
                "status": "error",
                "code": 500,
                "message": "Firebase initialization failed"
            }

        try:
            # Reference to the user's accounts in the database
            accounts_ref = db.reference("ContactP").child("Users").child(user_id).child('Accounts')

            # Fetch all accounts for the user
            accounts_snapshot = accounts_ref.get()

            # Check if accounts exist for the user
            if accounts_snapshot:
                return {
                    "status": "success",
                    "code": 200,
                    "message": "Accounts fetched successfully",
                    "data": accounts_snapshot
                }
            else:
                return {
                    "status": "success",
                    "code": 200,
                    "message": "No accounts found for the user",
                    "data": {}
                }

        except Exception as e:
            # Handle any exception that occurs during the fetching process
            return {
                "status": "error",
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }

    def fetch_account_info(self, user_id, account_name):
        self.initialize_firebase()  # Ensure Firebase is initialized
        if not self.app_initialized:
            return {
                "status": "error",
                "code": 500,
                "message": "Firebase initialization failed"
            }

        try:
            account_id = f"{account_name}{user_id}"
            # Reference to the specific account under the user's accounts in the database
            account_ref = db.reference("ContactP").child("Users").child(user_id).child('Accounts').child(account_id)

            # Fetch the account information
            account_info = account_ref.get()

            # Check if the account exists
            if account_info:
                return {
                    "status": "success",
                    "code": 200,
                    "message": "Account information fetched successfully",
                    "data": account_info
                }
            else:
                return {
                    "status": "error",
                    "code": 404,
                    "message": "Account not found"
                }

        except Exception as e:
            # Handle any exception that occurs during the fetching process
            return {
                "status": "error",
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }

    def listen_to_contacts(self, user_id):
        """Set up a listener for changes in the user's contacts and fetch updates when any change occurs."""

        # Initialize Firebase if not already done
        self.initialize_firebase()
        if not self.app_initialized:
            print({"status": "error", "code": 500, "message": "Firebase initialization failed"})
            return {"status": "error", "code": 500, "message": "Firebase initialization failed"}

        try:
            # Reference to the user's contacts in the database
            contacts_ref = db.reference("ContactP").child("Users").child(user_id).child('Contacts')

            # Define the listener callback function
            def listener_callback(event):
                # Log that a change has been detected
                print("Change detected in contacts. Fetching updated contacts...")

                # Fetch updated contacts data
                # response = self.fetch_contacts(user_id)

                # Log or process the response as necessary
                # print(response)
                from main import MainApp

                MainApp.opt_sync_contact(MainApp())
                # If needed, you can add additional logic here to handle the response

            # Start listening to changes in the Contacts node
            contacts_ref.listen(listener_callback)
            print({"status": "success", "code": 200, "message": "Listener set up successfully for user contacts"})
            # Return success status to indicate that the listener has been set up
            return {"status": "success", "code": 200, "message": "Listener set up successfully for user contacts"}

        except Exception as e:
            # Handle any exceptions that occur during the listener setup
            print({"status": "error", "code": 500,
                    "message": f"An error occurred while setting up the listener: {str(e)}"})
            return {"status": "error", "code": 500,
                    "message": f"An error occurred while setting up the listener: {str(e)}"}

# data = {'sub': '114248626444216198151', 'name': 'Aqeglipa Mbuya', 'given_name': 'Aqeglipa', 'family_name': 'Mbuya', 'picture': 'https://lh3.googleusercontent.com/a/ACg8ocIT_d6PJsuw4KxtCBnprPf-jLSjDva0vCP6UJMSmzvE3qnwaEvY=s96-c', 'email': 'aqeglipambuya@gmail.com', 'email_verified': True}
#
# FirebaseManager.register_user(FirebaseManager(), data)
# x = FirebaseManager.add_account(FirebaseManager(), '114248626444216198151', 'phone', '0715700411')
# print(x)
# x = FirebaseManager.fetch_contacts(FirebaseManager(), '114248626444216198151')
# print(x)
# vv = FirebaseManager.add_contact(FirebaseManager(), '114248626444216198151', '114248626444216198151')
# print(vv)
# x = FirebaseManager.fetch_account_info(FirebaseManager(), '114248626444216198151', "phone")
# print(x)
# x = FirebaseManager.fetch_user_info(FirebaseManager(), '114248626444216198151')
# print(x)

# x = FirebaseManager.fetch_user_profile(FirebaseManager(), '114248626444216198151')
# print(x)

