from jnius import autoclass, cast
from android import activity
from android.runnable import run_on_ui_thread

# Required Android classes
Intent = autoclass('android.content.Intent')
Contacts = autoclass("android.provider.ContactsContract$Contacts")
Insert = autoclass("android.provider.ContactsContract$Intents$Insert")
PythonActivity = autoclass('org.kivy.android.PythonActivity')


@run_on_ui_thread
def add_contact(name, phone, email):
    # Create the intent to add or edit a contact
    intent = Intent()
    intent.setAction(Intent.ACTION_INSERT_OR_EDIT)

    # Set the MIME type to specify that this is a contact insert or edit action
    intent.setType(Contacts.CONTENT_ITEM_TYPE)

    # Add the contact's details
    intent.putExtra(Insert.NAME, name)  # Contact Name
    intent.putExtra(Insert.PHONE, phone)  # Contact Phone
    intent.putExtra(Insert.EMAIL, email)  # Contact Email
    intent.putExtra(Insert.PHONE_TYPE, 3)  # Hardcoding TYPE_WORK for phone
    intent.putExtra(Insert.EMAIL_TYPE, 2)  # Hardcoding TYPE_WORK for email

    # Debugging: Log the inserted values
    print(f"Name: {name}, Phone: {phone}, Email: {email}")

    # Start the intent to open the contacts app
    current_activity = cast('android.app.Activity', PythonActivity.mActivity)
    current_activity.startActivity(intent)


# Example usage: Adding a contact with name, phone number, and email
# add_contact("Mbuya", "0788204327", "mbuya@gmail.com")
