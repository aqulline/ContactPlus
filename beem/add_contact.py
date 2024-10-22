from jnius import autoclass, cast
from android import activity
from android.runnable import run_on_ui_thread

# Required Android classes
Intent = autoclass('android.content.Intent')
ContactsContract_Insert = autoclass('android.provider.ContactsContract$Intents$Insert')
ContactsContract_RawContacts = autoclass('android.provider.ContactsContract$RawContacts')
Uri = autoclass('android.net.Uri')
PythonActivity = autoclass('org.kivy.android.PythonActivity')

@run_on_ui_thread
def add_contact(name, phone, email):
    # Create the intent to add a contact
    intent = Intent(Intent.ACTION_INSERT)

    # Set the MIME type to specify that this is a contact insert action
    intent.setType(ContactsContract_RawContacts.CONTENT_TYPE)

    # Add the contact's email (use TYPE_WORK = 2)
    intent.putExtra(ContactsContract_Insert.EMAIL, email)
    intent.putExtra(ContactsContract_Insert.EMAIL_TYPE, 2)  # Hardcoding TYPE_WORK for email

    # Add the contact's phone number (use TYPE_WORK = 3)
    intent.putExtra(ContactsContract_Insert.PHONE, phone)
    intent.putExtra(ContactsContract_Insert.PHONE_TYPE, 3)  # Hardcoding TYPE_WORK for phone


    # Add the contact's name
    intent.putExtra(ContactsContract_Insert.NAME, name)

    # print(f"Intent data: name - {intent.getStringExtra(ContactsContract_Insert.N)}, phone - {intent.getStringExtra(ContactsContract_Insert.phone)}, email - {intent.getStringExtra(ContactsContract_Insert.email)}")
    print(f"Intent data:{intent.extras}")
    for key in intent.extras.keySet():
        value = intent.getStringExtra(key)
        print(f" this is key={key}: value={value}")
    # Start the intent to open the contacts app
    current_activity = cast('android.app.Activity', PythonActivity.mActivity)
    current_activity.startActivity(intent)

# Example usage: Adding a contact with name, phone number, and email
# add_contact("Programmer World", "11112222", "programmerworld1990@gmail.com")


