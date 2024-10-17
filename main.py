import json
import os
import threading
from platform import platform
from time import sleep

import qrcode
from kivy.base import EventLoop
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, DictProperty, ListProperty, BooleanProperty, Logger
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy import utils
from kivymd.toast import toast
from kivyauth.google_auth import initialize_google, login_google, logout_google
from kivymd.uix.behaviors import RectangularElevationBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem
import hyperlink_preview as HLP
import webbrowser

import GoogleKeys
from database import FirebaseManager as FM


Window.keyboard_anim_args = {"d": .2, "t": "linear"}
Window.softinput_mode = "below_target"
Clock.max_iteration = 250

if utils.platform != 'android':
    Window.size = (412, 732)

class Contacts(OneLineAvatarIconListItem):
    name = StringProperty("")
    image = StringProperty("")
    contact_id = StringProperty("")


class Spin(MDBoxLayout):
    pass

class Card(MDCard, RectangularElevationBehavior):
    pass

class View_account_details(MDBoxLayout):
    pass

class QRCodeDialog(MDBoxLayout):
    pass

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


    def on_start(self):
        print(self.size_x, self.size_y)
        self.keyboard_hooker()
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

            request_permissions([Permission.READ_CONTACTS, Permission.WRITE_CONTACTS, ], callback)

    def spin_dialog(self):
        if not self.dialog_spin:
            self.dialog_spin = MDDialog(
                type="custom",
                auto_dismiss=False,
                size_hint=(.43, None),
                content_cls=Spin(),
            )
        self.dialog_spin.open()


    """
        USER FUNCTIONS (CONTACTS)
    
    """
    @mainthread
    def login_optimization(self):
        self.spin_dialog()
        thr = threading.Thread(target=self.login_start)
        thr.start()

    def login_start(self):
        print(self.user_data)
        self.user_data_getter()
        Clock.schedule_once(lambda dt: self.add_contacts(), .1)
        Clock.schedule_once(lambda dt: self.dialog_spin.dismiss(), .1)
        Clock.schedule_once(lambda dt: self.screen_capture('home'), .1)


    def add_contacts(self):
        # self.screen_capture("contacts")
        self.root.ids.contact.data = {}
        index = 0
        data = FM.fetch_contacts(FM(), self.user_data['sub'])
        print(data)
        if data['code'] == 200:
            for x, y in data['data'].items():
                if y['picture'] == '':
                    y['picture'] = f"https://storage.googleapis.com/farmzon-abdcb.appspot.com/Letters/{y['family_name'][0]}"
                self.root.ids.contact.data.append(
                    {
                        "viewclass": "Contacts",
                        "name": y['name'],
                        "contact_id": y['sub'],
                        "image": y['picture'],
                        "id": y['sub'],
                        "selected": False,
                        "data_index": index
                    }
                )
                index += 1


            """
            SCREEN FUNCTIONS
            """

    def screen_capture(self, screen):
        sm = self.root
        sm.current = screen
        if screen in self.screens:
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

    action_name = StringProperty("view")
    account_link = StringProperty("#Empty")
    account_name = StringProperty("")
    account_id = StringProperty("")
    edit_hint = StringProperty("Edit link")
    edit_screen = StringProperty("edit_link")

    def add_save_account(self):
        FM.add_account(FM(), self.user_id, self.account_name, self.account_link)
        self.screen_capture("profile")

    def opt_preview(self):
        thr = threading.Thread(target=self.preview_link)
        thr.start()

    def view_account_details(self, account_name):
        data = FM.fetch_account_info(FM(), self.user_id, account_name)
        print(data)
        self.account_name = account_name
        if data['code'] == 200:
            if account_name == 'phone':
                self.action_name = 'call'
                self.edit_hint = "Enter phone"
                self.edit_screen = "edit_phone"
            data = data['data']
            self.account_name = data['account_name']
            self.account_link = data['account_link']
            self.account_id = data['account_id']
            self.show_account_dialog()
        elif data['code'] == 404:
            if account_name == 'phone':
                self.action_name = 'call'
                self.edit_hint = "Enter phone"
                self.edit_screen = "edit_phone"
            if account_name == 'whatsapp':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "https://wa.me/255replacethiswithphone"
            if account_name == 'instagram':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "https://www.instagram.com/enter_username_here"
            if account_name == 'linkedin':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "https://www.linkedin.com/in/enter_user_name_here_or_paste_link"
            if account_name == 'twitter':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "https://x.com/enter_user_name_here_or_paste_link"
            if account_name == 'github':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "https://github.com/enter_user_name_here_or_paste_link"
            if account_name == 'web':
                self.edit_screen = "edit_link"
                self.root.ids.link_field.text = "paste_your_web_link_here"
            self.action_name = "#Empty"
            self.account_link = "#Empty"
            self.screen_capture(self.edit_screen)
        else:
            toast(data['message'])

    def show_account_dialog(self):
        if not self.account_dialog:
            self.account_dialog = MDDialog(
                title="View Details",
                type="custom",
                content_cls=View_account_details(),
                buttons=[
                    MDFlatButton(
                        text="Edit",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=(lambda dt: self.edit_link_callback())
                    ),
                    MDFlatButton(
                        text=self.action_name,
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                    ),
                ],
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
            self.link_image = str("https://lh5.googleusercontent.com/proxy/8b31I_Jtp3hRBSUVSubNHO_6KFNvldAStfeqKwAFUf22WOuDDBUlI1t26OW0ZadJr7LAXt0rbBoray3mARaiIM4-7Z-kUPpx")
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
                self.link_image = str(link_data.get('image', 'https://lh5.googleusercontent.com/proxy/8b31I_Jtp3hRBSUVSubNHO_6KFNvldAStfeqKwAFUf22WOuDDBUlI1t26OW0ZadJr7LAXt0rbBoray3mARaiIM4-7Z-kUPpx'))
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

    """
        END OF SCREEN FUNCTIONS
    """


    """
        GOOGLE AUTHENTICATION FUNCTIONS
    
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
        if not self.qr_dialog:
            self.qr_dialog = MDDialog(
                title="",
                type="custom",
                content_cls=QRCodeDialog(),
            )
        self.qr_dialog.open()

    """
        END OF QRCODES FUNCTIONS
    
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
        self.save_user_info_to_json()

    def save_user_info_to_json(self):
        # Define the filename
        filename = 'user_info.json'

        # Write user data to the JSON file
        with open(filename, 'w') as json_file:
            json.dump(self.user_data, json_file, indent=4)  # Using indent for pretty printing

        self.qr_code(self.user_data['sub'])
        self.login_optimization()
        FM.register_user(FM(), self.user_data)
        print(f"User information has been written to {filename}.")

    def erro_login(self, *args):
        print("Booo!!")

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
                    # Optionally, you can call a function to proceed to the home screen

                    self.login_optimization()
                    return

        # If the user is not in the file, proceed with Google login
        login_google()

    @mainthread
    def user_data_getter(self):
        self.user_id = self.user_data['sub']
        self.user_name = self.user_data['name']
        self.user_email = self.user_data['email']
        self.user_pic = self.user_data['picture']
        self.user_qrcode = f"Qrcodes/{self.user_id}.png"

    def logout(self):
        logout_google(self.erro_login)

    """
        END OF GOOGLE AUTHENTICATION FUNCTIONS
    
    """

    def build(self):
        initialize_google(self.after_login, self.erro_login,
                          client_id=GoogleKeys.client_id2,
                          client_secret=GoogleKeys.client_secret2)
        self.theme_cls.material_style = "M3"


MainApp().run()