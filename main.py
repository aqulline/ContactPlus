import re
import threading
import webbrowser
from datetime import datetime
from IPython.utils.timing import clocks
from kivy.animation import Animation
from kivy.base import EventLoop
from kivy.properties import NumericProperty, StringProperty, DictProperty, ListProperty, BooleanProperty
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.clock import Clock
from kivy import utils
from kivymd.toast import toast
from kivyauth.google_auth import initialize_google, login_google, logout_google

Window.keyboard_anim_args = {"d": .2, "t": "linear"}
Window.softinput_mode = "below_target"
Clock.max_iteration = 250

if utils.platform != 'android':
    Window.size = (412, 732)



class MainApp(MDApp):
    # app
    size_x, size_y = Window.size

    # screen
    screens = ['home']
    screens_size = NumericProperty(len(screens) - 1)
    current = StringProperty(screens[len(screens) - 1])

    def on_start(self):
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

    def after_login(self, *args):
        print("Hurray")
        Clock.schedule_once(lambda dt: self.screen_capture("home"), 0)
        print(*args)

    def erro_login(self, *args):
        print("Booo!!")

    def login(self):
        login_google()

    def logout(self):
        logout_google(self.erro_login)

    def build(self):
        initialize_google(self.after_login, self.erro_login, client_id='240132364342-bpp6asa19iec10cvl67f6vujghin6e44.apps.googleusercontent.com', client_secret="vAoceO8PdEh84fD81YsXs9tq")
        self.theme_cls.material_style = "M3"


MainApp().run()