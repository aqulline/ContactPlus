import firebase_admin
from firebase_admin import credentials, initialize_app, db, auth
from firebase_admin.exceptions import FirebaseError
from beem import sms




class FirebaseManager:
    def __init__(self):
        self.cred = credentials.Certificate("credential/farmzon-abdcb-c4c57249e43b.json")
        self.app_initialized = False
        self.database_url = 'https://farmzon-abdcb.firebaseio.com/'

    def remove_comma(self, number):

        new_number = str(number).replace(',', '')

        return int(new_number)

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
        """Register a new user in the Firebase database under 'Users'."""
        self.initialize_firebase()  # Ensure Firebase is initialized
        if not self.app_initialized:
            return {"status": "error", "code": 500, "message": "Firebase initialization failed"}

        try:
            # Reference to the user data in the database
            user_ref = db.reference("ContactP").child("Users").child(data['sub']).child('User_info')

            # Store user data
            user_ref.set(data)

            # Return success status
            return {"status": "success", "code": 200, "message": "User registered successfully"}

        except Exception as e:
            # Handle any exception that occurs during the registration process
            return {"status": "error", "code": 500, "message": f"An error occurred: {str(e)}"}

    def add_contact(self, user_id, new_contact_data):
        self.initialize_firebase()  # Ensure Firebase is initialized
        if not self.app_initialized:
            return {"status": "error", "code": 500, "message": "Firebase initialization failed"}

        try:
            # Reference to the user data in the database
            user_ref = db.reference("ContactP").child("Users").child(user_id).child('Contacts').child(new_contact_data['sub'])

            # Store user data
            user_ref.set(new_contact_data)

            # Return success status
            return {"status": "success", "code": 200, "message": "Contact added successfully"}

        except Exception as e:
            # Handle any exception that occurs during the registration process
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

# data = {'sub': '114248626444216198151', 'name': 'Aqeglipa Mbuya', 'given_name': 'Aqeglipa', 'family_name': 'Mbuya', 'picture': 'https://lh3.googleusercontent.com/a/ACg8ocIT_d6PJsuw4KxtCBnprPf-jLSjDva0vCP6UJMSmzvE3qnwaEvY=s96-c', 'email': 'aqeglipambuya@gmail.com', 'email_verified': True}
#
# FirebaseManager.register_user(FirebaseManager(), data)
# x = FirebaseManager.add_account(FirebaseManager(), '114248626444216198151', 'phone', '0715700411')
# print(x)
# x = FirebaseManager.fetch_contacts(FirebaseManager(), '114248626444216198151')
# print(x)
# FirebaseManager.add_contact(FirebaseManager(), '114248626444216198151', data)
# x = FirebaseManager.fetch_account_info(FirebaseManager(), '114248626444216198151', "phone")
# print(x)