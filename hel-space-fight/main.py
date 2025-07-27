
# main.py

from kivy.app import App
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.screenmanager import ScreenManager

import json
import os
import sys
from kivy.resources import resource_add_path
from kivy.config import Config

# استيراد الشاشات من ملف screens.py
from screens import MainMenuScreen, SettingsScreen, GameScreen, PauseScreen

# هذا الجزء يحدد الواجهة الخلفية للرسومات بشكل صريح
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'resizable', '1')
Config.set('graphics', 'borderless', '0')
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'show_cursor', '1')
Config.set('kivy', 'keyboard_mode', 'systemanddock')
Config.set('graphics', 'backend', 'sdl2')

# هذا الجزء يخبر Kivy أين يبحث عن الأصول عند تشغيل التطبيق المجمع بواسطة PyInstaller
if hasattr(sys, '_MEIPASS'):
    resource_add_path(os.path.join(sys._MEIPASS, 'assets'))
    print(f"DEBUG: Running from PyInstaller bundle. Assets path: {os.path.join(sys._MEIPASS, 'assets')}")
    print(f"DEBUG: Assets path exists: {os.path.exists(os.path.join(sys._MEIPASS, 'assets'))}")
    print(f"DEBUG: Content of assets path: {os.path.listdir(os.path.join(sys._MEIPASS, 'assets')) if os.path.exists(os.path.join(sys._MEIPASS, 'assets')) else 'Path does not exist'}")
else:
    resource_add_path('assets')
    print("DEBUG: Running from source. Assets path: assets")

Window.icon = 'assets/icon.png'

class MyScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_file = 'game_data.json'
        self.high_score = 0
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        self.test_sfx_sound = None
        self.previous_screen = None
        self.game_music_sound = None

        self.load_game_data()

        self.game_music_sound = SoundLoader.load("assets/music.wav")
        if self.game_music_sound:
            self.game_music_sound.loop = True
            self.game_music_sound.volume = self.music_volume
            print("MyScreenManager: Game music sound loaded.")
        else:
            print("MyScreenManager: WARNING: music.wav not found or could not be loaded.")

        self.test_sfx_sound = SoundLoader.load("assets/test_sfx.wav")
        if self.test_sfx_sound:
            print("Test SFX sound loaded.")
            self.test_sfx_sound.volume = self.sfx_volume
        else:
            print("WARNING: test_sfx.wav not found or could not be loaded. SFX volume feedback will not work.")

        self.menu_screen = MainMenuScreen(name='menu')
        self.settings_screen = SettingsScreen(name='settings')
        self.game_screen = GameScreen(name='game', game_music_sound=self.game_music_sound)
        self.pause_screen = PauseScreen(name='pause')

        self.add_widget(self.menu_screen)
        self.add_widget(self.settings_screen)
        self.add_widget(self.game_screen)
        self.add_widget(self.pause_screen)

        self.current = 'menu'

    def load_game_data(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.high_score = data.get('high_score', 0)
                self.music_volume = data.get('music_volume', 1.0)
                self.sfx_volume = data.get('sfx_volume', 1.0)
            print("Game data loaded successfully.")
        except FileNotFoundError:
            print("Game data file not found. Starting with default settings.")
        except json.JSONDecodeError:
            print("Error decoding game data. Starting with default settings.")
        except Exception as e:
            print(f"An unexpected error occurred while loading game data: {e}")

    def save_game_data(self):
        data = {
            'high_score': self.high_score,
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume
        }
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f)
            print("Game data saved successfully.")
        except Exception as e:
            print(f"An error occurred while saving game data: {e}")

# class MyApp(App):
    # def build(self):
        # self.root = MyScreenManager()
        # return self.root
        
class MyApp(App):
    def build(self):
        return MyScreenManager()


if __name__ == "__main__":
    app = MyApp()
    app.run()
