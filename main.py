import json
import os
import re
import socket
import threading
from time import sleep

import jwt
import qrcode
from PIL import Image
from camera4kivy import Preview
from kivy.base import EventLoop
from kivy.core.clipboard import Clipboard
from kivy.properties import NumericProperty, StringProperty, DictProperty, BooleanProperty, ObjectProperty
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy import utils
from kivymd.toast import toast
from kivyauth.google_auth import initialize_google, login_google, logout_google
from kivymd.uix.behaviors import RectangularElevationBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem, IRightBodyTouch
import hyperlink_preview as HLP
import webbrowser

from plyer import notification
from pyzbar.pyzbar import decode

import GoogleKeys
from database import FirebaseManager as FM
from offline_database import OfflineDatabase as OF


Window.keyboard_anim_args = {"d": .2, "t": "linear"}
Window.softinput_mode = "below_target"
Clock.max_iteration = 250

if utils.platform != 'android':
    Window.size = (412, 732)

class Contacts(OneLineAvatarIconListItem):
    name = StringProperty("")
    image = StringProperty("")
    contact_id = StringProperty("")
    phone = StringProperty("")

class CallContainer(IRightBodyTouch, MDBoxLayout):
    adaptive_width = True

class Spin(MDBoxLayout):
    pass

class Card(MDCard, RectangularElevationBehavior):
    pass

class View_account_details(MDBoxLayout):
    pass

class QRCodeDialog(MDBoxLayout):
    pass

class Scan_Analyze(Preview):
    extracted_data = ObjectProperty(None)

    def analyze_pixels_callback(self, pixels, image_size, image_pos, scale, mirror):

        pimage = Image.frombytes(mode='RGBA', size=image_size, data=pixels)
        list_of_all_barcodes = decode(pimage)

        if list_of_all_barcodes:
            if self.extracted_data:
                self.extracted_data(list_of_all_barcodes[0])
            else:
                print("NOt found")

class MainApp(MDApp):
    # app
    size_x, size_y = Window.size
    dialog_spin = None
    account_dialog = None
    qr_dialog = None

    # screen
    screens = ['home']
    screens_size = NumericProperty(len(screens) - 1)
    current = StringProperty(screens[len(screens) - 1])

    # user info
    user_data = DictProperty({})
    user_id = StringProperty("")
    user_name = StringProperty("")
    user_email = StringProperty("")
    user_pic = StringProperty("")
    user_qrcode = StringProperty("")

    # link preview
    link_image = StringProperty("https://lh5.googleusercontent.com/proxy/8b31I_Jtp3hRBSUVSubNHO_6KFNvldAStfeqKwAFUf22WOuDDBUlI1t26OW0ZadJr7LAXt0rbBoray3mARaiIM4-7Z-kUPpx")
    link_title = StringProperty("")
    link_url = StringProperty("")
    link_description = StringProperty("")
    link_site_name = StringProperty("")
    link_domain = StringProperty("")

    # Contact vars
    selected_contact = StringProperty("")
    contact_phone = StringProperty("")
    contact_name = StringProperty("")
    contact_email = StringProperty("")
    contact_pic = StringProperty("")

    # account validator
    social_account = DictProperty({"github": True, "whatsapp": True, "instagram": True, "web": True, "linkedin": True,
                                   "phone": True, "twitter": True})

    # account view vars
    action_name = StringProperty("view")
    account_link = StringProperty("#Empty")
    account_name = StringProperty("")
    account_id = StringProperty("")
    edit_hint = StringProperty("Edit link")
    edit_screen = StringProperty("edit_link")

    # save Contacts
    local_contacts = DictProperty({})

    personal_or_contact = BooleanProperty(True)

    notification_count = NumericProperty(0)

    online_is_yes = False

    def on_start(self):
        self.keyboard_hooker()
        Clock.schedule_once(lambda dt: self.login(), .1)
        # Clock.schedule_interval(self.isonline, 4)
        if utils.platform == 'android':
            self.request_android_permissions()


    def keyboard_hooker(self, *args):
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *largs):
        print(self.screens_size)
        if key == 27 and self.screens_size > 0:
            print(f"your were in {self.current}")
            last_screens = self.current
            self.screens.remove(last_screens)
            print(self.screens)
            self.screens_size = len(self.screens) - 1
            self.current = self.screens[len(self.screens) - 1]
            self.screen_capture(self.current)
            return True
        elif key == 27 and self.screens_size == 0:
            toast('Press Home button!')
            return True

    def request_android_permissions(self):
        if utils.platform == 'android':
            from android.permissions import request_permissions, Permission

            def callback(permissions, results):
                if all([res for res in results]):
                    print("callback. All permissions granted.")
                else:
                    print("callback. Some permissions refused.")

            request_permissions([Permission.READ_CONTACTS, Permission.WRITE_CONTACTS, Permission.CAMERA, Permission.CALL_PHONE, Permission.POST_NOTIFICATIONS], callback)

    def spin_dialog(self):
        if not self.dialog_spin:
            self.dialog_spin = MDDialog(
                type="custom",
                auto_dismiss=False,
                size_hint=(.43, None),
                content_cls=Spin(),
            )
        self.dialog_spin.open()

    def isonline(self, dt):
        """Check if the device is offline by attempting to connect to a known host."""
        print("Checking....")
        try:
            # Attempt to create a socket connection to a known reliable host
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            # If connection is successful, device is online

            if not self.online_is_yes:
                self.local_login_optimization()
                self.fetch_offline_contacts_opt()
                self.online_is_yes = True
                toast("Device online!")
            # load offline contacts
            # refresh contacts and other infos
            return True
        except Exception as e:
            # If there is an error, assume device is offline
            self.online_is_yes = False
            toast("Device offline!")

            return False

    """
        USER FUNCTIONS (CONTACTS)
    
    """

    @mainthread
    def user_data_getter(self):
        self.user_id = self.user_data['sub']
        self.user_name = self.user_data['name']
        self.user_email = self.user_data['email']
        self.user_pic = self.user_data['picture'] if self.user_data[
                                                         'picture'] != '' else f"https://storage.googleapis.com/farmzon-abdcb.appspot.com/Letters/{self.user_name[0]}"
        self.user_qrcode = f"Qrcodes/{self.user_id}.png"
        if os.path.exists(f"Qrcodes/offline/{self.user_id}.png"):
            self.user_qrcode = f"Qrcodes/offline/{self.user_id}.png"

        self.refresh_user_opt()
        self.notifi()

    def fetch_user_local(self):
        filename = 'user_info.json'

        # Check if the file exists
        if os.path.exists(filename):
            # Read the user info from the JSON file
            with open(filename, 'r') as json_file:
                user_data = json.load(json_file)
                # Assuming the user data has an email field
                user_email = user_data.get('email')
                if user_email:
                    print(f"User found: {user_email}")
                    self.user_data = user_data
                    self.user_data_getter()

    def refresh_user_opt(self):
        thr = threading.Thread(target=self.refresh_user_local)
        thr.start()

    def refresh_user_local(self):
        data = FM.fetch_user_profile(FM(), self.user_id)

        if data['code'] == 200:
            FM.refresh_user_info(FM(), data['data']['user_info'])
        else:
            pass

    def save_user_info_to_json(self):
        # Define the filename
        filename = 'user_info.json'

        data = FM.register_user(FM(), self.user_data)
        if  data['code'] == 200:
            # Write user data to the JSON file
            with open(filename, 'w') as json_file:
                json.dump(self.user_data, json_file, indent=4)  # Using indent for pretty printing
            OF.update_offline_data(OF(), self.user_data)
            self.qr_code(self.user_data['sub'])
        else:
            toast(data['message'], 4)

    @mainthread
    def login_optimization(self):
        self.spin_dialog()
        thr = threading.Thread(target=self.login_start)
        thr.start()

    def local_login_optimization(self):
        thr = threading.Thread(target=self.login_start)
        thr.start()

    def login_start(self):
        self.save_user_info_to_json()
        self.user_data_getter()
        Clock.schedule_once(lambda dt: self.add_contacts(), .1)
        Clock.schedule_once(lambda dt: self.dialog_spin.dismiss() if self.dialog_spin is not None else print(), .1)
        Clock.schedule_once(lambda dt: self.screen_capture('home'), .1)
        Clock.schedule_interval(self.isonline, 4)

    def opt_sync_contact(self):
        thr = threading.Thread(target=self.sync_contact)
        thr.start()

    def sync_contact(self):
        contacts_file = 'contacts.json'
        data = FM.fetch_contacts(FM(), self.user_data['sub'])
        if data['code'] == 200:
            try:
                with open(contacts_file, 'w') as file:
                    json.dump(data['data'], file)

                Clock.schedule_once(lambda dt: self.load_contacts_to_ui(data['data']), .1)
            except Exception as e:
                print(f"Error code 243")

    def load_contacts_to_ui(self, contacts_data):
        """Helper function to load contacts into the UI."""
        self.root.ids.contact.data = {}
        index = 0
        for x, y in contacts_data.items():
            if y['picture'] == '':
                y['picture'] = f"https://storage.googleapis.com/farmzon-abdcb.appspot.com/Letters/{y['family_name'][0]}"
            if not self.online_is_yes:
                y['picture'] = 'components/account.png'
            if 'account_phone' not in y:
                toast(f"Phone missing for {y['name']}")
                y['account_phone'] = '0715000000'
            self.root.ids.contact.data.append(
                {
                    "viewclass": "Contacts",
                    "name": y['name'],
                    "contact_id": y['sub'],
                    "image": y['picture'],
                    "id": y['sub'],
                    "selected": False,
                    "data_index": index,
                    "phone": y['account_phone']
                }
            )
            index += 1

    def is_phone(self):
        with open('user_info.json') as file:
            data = json.load(file)

        if 'account_phone' in data:
            return True
        else:
            return False

    def add_contacts(self):
        # Path to local JSON file to store contacts
        contacts_file = 'contacts.json'
        self.opt_sync_contact()
        # Check if contacts are already saved in the local JSON file
        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r') as file:
                    saved_data = json.load(file)
                    self.local_contacts = saved_data
                    self.load_contacts_to_ui(saved_data)  # Load contacts into UI from the local file
                    return
            except Exception as e:
                toast("Fail to load contacts!")

        # If no local data, fetch contacts from server
        data = FM.fetch_contacts(FM(), self.user_data['sub'])

        # If the response is successful, save the contacts to local file and load into UI
        if data['code'] == 200:
            try:
                # Save the fetched data to local JSON file
                with open(contacts_file, 'w') as file:
                    json.dump(data['data'], file)

                # Load contacts into UI from fetched data
                self.load_contacts_to_ui(data['data'])
            except Exception as e:
                toast(f"Error code 243")

    def add_save_account_opt(self):
        self.spin_dialog()
        thr = threading.Thread(target=self.add_save_account)
        thr.start()

    def validate_phone(self, phone_number):
        # Regular expression pattern for a valid Tanzanian phone number
        pattern = r'^0[67][0-9]{8}$'

        # Use re.match to check if the phone number matches the pattern
        if re.match(pattern, phone_number):
            return True
        else:
            return False

    def add_save_account(self):
        if self.account_name == 'phone':
            if not self.validate_phone(self.account_link):
                Clock.schedule_once(lambda dt: toast("Enter a valid phone"), .1)

                return
        if self.account_link != '':
            FM.add_account(FM(), self.user_id, self.account_name, self.account_link)
            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), .1)
            Clock.schedule_once(lambda dt: self.screen_capture("profile"), .1)
        else:
            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), .1)
            Clock.schedule_once(lambda dt: toast("Enter a valid url"), .1)

    def opt_preview(self):
        thr = threading.Thread(target=self.preview_link)
        thr.start()

    def view_account_details_opt(self):
        self.spin_dialog()
        thr = threading.Thread(target=self.view_account_details)
        thr.start()

    def view_account_details_contact_opt(self):
        self.spin_dialog()
        thr = threading.Thread(target=self.view_account_details_contact)
        thr.start()

    @mainthread
    def link_quick(self, url):
        self.root.ids.link_field.text = url


    def view_account_details(self):
        data = FM.fetch_account_info(FM(), self.user_id, self.account_name)
        print(data)
        account_name = self.account_name
        if data['code'] == 200:
            if account_name == 'phone':
                self.action_name = 'call'
                self.edit_hint = "Enter phone"
                self.edit_screen = "edit_phone"
            else:
                self.edit_screen = "edit_link"
                self.action_name = 'view'
            data = data['data']
            self.account_name = data['account_name']
            self.account_link = data['account_link']
            self.account_id = data['account_id']
            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), .1)
            Clock.schedule_once(lambda dt: self.show_account_dialog(), .1)
        elif data['code'] == 404:
            if account_name == 'phone':
                self.action_name = 'call'
                self.edit_hint = "Enter phone"
                self.edit_screen = "edit_phone"
            elif account_name == 'whatsapp':
                self.edit_screen = "edit_link"
                self.link_quick("https://wa.me/255replacethiswithphone")
            elif account_name == 'instagram':
                self.edit_screen = "edit_link"
                self.link_quick("https://www.instagram.com/enter_username_here")
            elif account_name == 'linkedin':
                self.edit_screen = "edit_link"
                self.link_quick( "https://www.linkedin.com/in/enter_user_name_here_or_paste_link")
            elif account_name == 'twitter':
                self.edit_screen = "edit_link"
                self.link_quick("https://x.com/enter_user_name_here_or_paste_link")
            elif account_name == 'github':
                self.edit_screen = "edit_link"
                self.link_quick("https://github.com/enter_user_name_here_or_paste_link")
            elif account_name == 'web':
                self.edit_screen = "edit_link"
                self.link_quick("paste_your_web_link_here")
            if account_name != 'phone':
                self.action_name = 'view'
            self.action_name = "#Empty"
            self.account_link = "#Empty"

            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), .1)
            Clock.schedule_once(lambda dt: self.screen_capture(self.edit_screen), .1)
        else:
            Clock.schedule_once(lambda dt: toast(data['message']), .1)
            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), .1)

    def view_account_details_contact(self):
        data = FM.fetch_account_info(FM(), self.selected_contact, self.account_name)
        print(data)
        account_name = self.account_name
        if data['code'] == 200:
            if account_name == 'phone':
                self.action_name = 'call'
                self.edit_hint = "Enter phone"
                self.edit_screen = "edit_phone"
            else:
                self.edit_screen = "edit_link"
                self.action_name = 'view'
            data = data['data']
            self.account_name = data['account_name']
            self.account_link = data['account_link']
            self.account_id = data['account_id']
            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), .1)
            Clock.schedule_once(lambda dt: self.show_account_dialog(), .1)
        elif data['code'] == 404:
            if account_name == 'phone':
                self.action_name = 'call'
                self.edit_hint = "Enter phone"
                self.edit_screen = "edit_phone"
            elif account_name == 'whatsapp':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "https://wa.me/255replacethiswithphone"
            elif account_name == 'instagram':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "https://www.instagram.com/enter_username_here"
            elif account_name == 'linkedin':
                self.edit_screen = "edit_link"
                @mainthread
                def link_quick():
                    self.root.ids.link_field.text = "https://www.linkedin.com/in/enter_user_name_here_or_paste_link"
                Clock.schedule_once(lambda dt: link_quick(), 0)
            elif account_name == 'twitter':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "https://x.com/enter_user_name_here_or_paste_link"
            elif account_name == 'github':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "https://github.com/enter_user_name_here_or_paste_link"
            elif account_name == 'web':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "paste_your_web_link_here"
            if account_name != 'phone':
                self.action_name = 'view'
            self.action_name = "#Empty"
            self.account_link = "#Empty"

            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), .1)
            Clock.schedule_once(lambda dt: self.screen_capture(self.edit_screen), .1)
        else:
            Clock.schedule_once(lambda dt: toast(data['message']), .1)

    def show_account_dialog(self):
        if not self.account_dialog:
            self.account_dialog = MDDialog(
                title="View Details",
                type="custom",
                content_cls=View_account_details(),

            )
        self.account_dialog.open()

    def edit_link_callback(self):
        self.screen_capture(self.edit_screen)
        self.root.ids.sms_edit.text = self.account_link
        self.root.ids.link_field.text = self.account_link
        print(self.account_link)
        self.account_dialog.dismiss()

    def preview_link(self):
        try:
            link = self.root.ids.link_field.text
            hlp = HLP.HyperLinkPreview(url=str(link))
            print(link)
            if hlp.is_valid:
                sleep(.3)
                preview_data = hlp.get_data()
                Clock.schedule_once(lambda dt: self.update_preview(preview_data), .1)
        except Exception as e:
            # Catch any errors that occur, such as network errors, invalid URLs, etc.
            # Optionally, you can set default or error values for these fields if the link preview fails.
            self.link_title = "Error"
            self.link_image = str(
                "https://lh5.googleusercontent.com/proxy/8b31I_Jtp3hRBSUVSubNHO_6KFNvldAStfeqKwAFUf22WOuDDBUlI1t26OW0ZadJr7LAXt0rbBoray3mARaiIM4-7Z-kUPpx")
            self.link_url = str(None)
            self.link_description = "None"
            self.link_site_name = "Unknown"
            self.link_domain = "Unknown"

    def update_preview(self, link_data):
        try:
            print(link_data)
            # Make sure that each expected key exists in the link_data and handle any missing values
            if link_data:
                self.link_title = str(link_data.get('title', 'No Title'))
                self.link_image = str(link_data.get('image',
                                                    'https://lh5.googleusercontent.com/proxy/8b31I_Jtp3hRBSUVSubNHO_6KFNvldAStfeqKwAFUf22WOuDDBUlI1t26OW0ZadJr7LAXt0rbBoray3mARaiIM4-7Z-kUPpx'))
                self.link_url = str(link_data.get('url', 'No URL'))
                self.link_description = str(link_data.get('description', 'No Description'))
                self.link_site_name = str(link_data.get('site_name', 'No Site Name'))
                self.link_domain = str(link_data.get('domain', 'No Domain'))
        except Exception as e:
            self.link_title = "Error"
            self.link_image = str(
                "https://lh5.googleusercontent.com/proxy/8b31I_Jtp3hRBSUVSubNHO_6KFNvldAStfeqKwAFUf22WOuDDBUlI1t26OW0ZadJr7LAXt0rbBoray3mARaiIM4-7Z-kUPpx")
            self.link_url = str(None)
            self.link_description = "None"
            self.link_site_name = "Unknown"
            self.link_domain = "Unknown"

    def open_link(self, url):
        webbrowser.open(url)

    def call(self, phone):
        # from call import Actions as AC
        from beem import call as CL
        CL.Actions.call(CL.Actions(), phone)

    def add_C(self):
        from beem import add_contact

        Clipboard.copy(f"{self.contact_phone} {self.contact_name}")

        toast("User name and phone is copied to the clipboard!, just paste", 5)

        add_contact.add_contact('Mbuya', '0788204327', 'mbuya@gmail.com')

    """
    END USER FUNCTIONS
    """

    """
    CONTACT FUNCTIONS
    """
    def search_contacts(self, text):
        pass

    def fetch_contact_opt(self):
        self.spin_dialog()
        thr = threading.Thread(target=self.fetch_contact)
        thr.start()

    def fetch_contact(self):
        data = FM.fetch_user_profile(FM(), self.selected_contact)

        if data['code']==200:
            Clock.schedule_once(lambda dt: self.upddate_contact_info(data), 0)
        else:
            Clock.schedule_once(lambda dt: toast(data['message']), 0)
            Clock.schedule_once(lambda dt: self.screen_capture("home"), 0)
            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), 0)

    def upddate_contact_info(self, data):
        contact_info = data['data']['user_info']
        self.contact_name = contact_info['name']
        self.contact_email = contact_info['email']
        self.contact_pic = contact_info['picture'] if contact_info[
                                                          'picture'] != '' else f"https://storage.googleapis.com/farmzon-abdcb.appspot.com/Letters/{contact_info['name'][0]}"

        contact_account = data['data']['accounts']
        if contact_account:
            for i, y in data['data']['accounts'].items():
                self.social_account[y['account_name']] = False


        Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), .1)

    def search_contact(self, text):
        data = self.local_contacts

        self.load_contacts_to_ui(data)

    def fetch_offline_contacts_opt(self):
        thr = threading.Thread(target=self.fetch_offline_contacts)
        thr.start()


    def fetch_offline_contacts(self):
        OF.file_name = 'offline_contacts.json'
        data = OF.load(OF())
        new_data = data.copy()
        for key in data:
            if key == self.user_id:
                pass
            else:
                FM.add_contact(FM(), self.user_id, key)
                new_data.pop(key)

        OF.write(OF(), new_data)
    """
    END OF CONTACT
    """

    """
    SCAN QRCODE
    """
    barcode = StringProperty("")

    def get_details(self):
        self.root.ids.details_scan.connect_camera(enable_analyze_pixels=True, default_zoom=0.0)
        print("connected")

    def stop_camera_detail(self):
        self.root.ids.details_scan.disconnect_camera()

    @mainthread
    def get_QRcode(self, result):
        barcode = result.data
        code_type = str(result.type)
        print("COde=", barcode)

        if barcode:
            if code_type == "QRCODE":
                barcode = barcode.decode("utf-8")

                self.barcode = barcode
                if not self.barcode.count('.') == 2:
                    toast("Unsupported qrcode!")
                    self.screen_capture("profile")

                    return
                self.spin_dialog()
                # guest_data = FB.search_id(FB(), barcode)

                thr = threading.Thread(target=self.get_data)
                thr.start()
            else:
                toast("Not a QRCODE!")
                self.screen_capture("profile")

    def get_data(self):
        print(self.barcode)
        decoded_data = jwt.decode(jwt=self.barcode,
                                  key='secret',
                                  algorithms=["HS256"])
        new_barcode = decoded_data
        print(new_barcode)
        if 'sub' in new_barcode:
            OF.update_data(OF(), new_barcode)
            self.add_contacts()
            Clock.schedule_once(lambda dt: self.screen_capture("home"), 0)
            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), 0)
            self.root.ids.details_scan.disconnect_camera()
            if self.online_is_yes:
                data = FM.add_contact(FM(), self.user_id, new_barcode['sub'])
                if data['code'] == 200:
                    self.login_start()
                    self.root.ids.details_scan.disconnect_camera()
                else:
                    Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), 0)
                    Clock.schedule_once(lambda dt: toast(data['message']), 0)
                    self.root.ids.details_scan.disconnect_camera()
        else:
            Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), 0)
            Clock.schedule_once(lambda dt: self.screen_capture('profile'))
            self.root.ids.details_scan.disconnect_camera()

    def to_json(self, data):
        data = data.replace("\'", "\"")
        print(data)

        json_data = data

        cleaned_json_string = json_data.strip('"')

        # Now parse the cleaned string as JSON
        print(cleaned_json_string)

        json_data = json.loads(cleaned_json_string)
        print(json_data)


        return json_data

    def add_local_contact(self):
        print()
    """
    END OF SCAN QRCODE
    """

    """
    
        QRCODES FUCNTIONS
    
    """

    def qr_code(self, id_gen):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(id_gen)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="#eaf4f4")
        img.save(f"Qrcodes/{id_gen}.png")

    def show_qrcode_dialog(self):
        if self.is_phone():
            if not self.qr_dialog:
                self.qr_dialog = MDDialog(
                    title="",
                    type="custom",
                    content_cls=QRCodeDialog(),
                )
            self.qr_dialog.open()
        else:
            toast("Please add phone number!",None, 3.0)

    """
        END OF QRCODES FUNCTIONS
    
    """

    """
            GOOGLE AUTHENTICATION FUNCTIONS

    """

    def after_login(self, *args):
        print(args)
        if utils.platform == 'android':
            keys = ['sub', 'name', 'email', 'family_name', 'given_name',  'picture']
            user_dict = dict(zip(keys, args))
            self.user_data = user_dict
            print(f"Login: user data {self.user_data}")
        else:
            self.user_data = args[0]
            print(self.user_data)
        self.login_optimization()

    def erro_login(self, *args):
        toast("failed to login!")

    def login(self):
        # Define the filename for the user info
        filename = 'user_info.json'

        # Check if the file exists
        if os.path.exists(filename):
            # Read the user info from the JSON file
            with open(filename, 'r') as json_file:
                user_data = json.load(json_file)
                # Assuming the user data has an email field
                user_email = user_data.get('email')
                if user_email:
                    print(f"User found: {user_email}")
                    self.user_data = user_data
                    self.add_contacts()
                    self.screen_capture("home")
                    # Optionally, you can call a function to proceed to the home screen
                    self.local_login_optimization()

                    return

        # If the user is not in the file, proceed with Google login
        login_google()

    def logout(self):
        logout_google(self.erro_login)

    """
        END OF GOOGLE AUTHENTICATION FUNCTIONS
    
    """

    """
    SCREEN FUNCTIONS
    """

    def screen_capture(self, screen):
        sm = self.root
        sm.current = screen
        if screen == 'detail_scanner':
            return 0
        elif screen in self.screens:
            pass
        else:
            self.screens.append(screen)
        print(self.screens)
        self.screens_size = len(self.screens) - 1
        self.current = self.screens[len(self.screens) - 1]
        print(f'size {self.screens_size}')
        print(f'current screen {screen}')

    def screen_leave(self):
        print(f"your were in {self.current}")
        last_screens = self.current
        self.screens.remove(last_screens)
        print(self.screens)
        self.screens_size = len(self.screens) - 1
        self.current = self.screens[len(self.screens) - 1]
        self.screen_capture(self.current)

    """
        END OF SCREEN FUNCTIONS
    """

    my_stream = None

    def stream_handler(self, message):
        if True:
            print(f"{message} La maSIA!!!!!!!!!!!")
            self.opt_sync_contact()
            if self.notification_count == 0:
                self.notification_count += 1
                return notification.notify(title='App started', message='Lets connect', app_icon='components/icon_contact.png')
            else:
                return notification.notify(title='Contact Update', message='New changes in contact', app_icon='components/icon_contact.png')

    def notifi(self):
        try:
            import firebase_admin
            firebase_admin._apps.clear()
            from firebase_admin import credentials, initialize_app, db
            cred = credentials.Certificate("credential/farmzon-abdcb-c4c57249e43b.json")
            initialize_app(cred, {'databaseURL': 'https://farmzon-abdcb.firebaseio.com/'}, name='worker')
            self.my_stream = db.reference("ContactP").child("Users").child(self.user_id).child('Contacts').listen(
                self.stream_handler)

        except Exception as e:
            print(f"you did good! {self.user_data} {e}")

    def build(self):
        initialize_google(self.after_login, self.erro_login,
                          client_id=GoogleKeys.client_id2,
                          client_secret=GoogleKeys.client_secret2)
        self.theme_cls.material_style = "M3"

if __name__ == '__main__':
    MainApp().run()