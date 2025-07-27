import pygame
import os
import sys
import json

# Setup Pygame
pygame.init()
pygame.mixer.init() # Ensure mixer is initialized early

# Dummy class for Kivy's Config
class PygameConfig:
    _settings = {}

    @classmethod
    def set(cls, section, key, value):
        if section not in cls._settings:
            cls._settings[section] = {}
        cls._settings[section][key] = value
        # print(f"Config set: [{section}] {key} = {value}") # For debugging

    @classmethod
    def get(cls, section, key):
        return cls._settings.get(section, {}).get(key)

# Replace Kivy's Config with PygameConfig
Config = PygameConfig

# Set default window size based on original Kivy config
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')
# Other Kivy Configs might not have direct Pygame equivalents or are handled differently
# Config.set('graphics', 'fullscreen', 'auto')
# Config.set('graphics', 'resizable', '1')
# Config.set('graphics', 'borderless', '0')
# Config.set('graphics', 'show_cursor', '1')
# Config.set('kivy', 'keyboard_mode', 'systemanddock')
# Config.set('graphics', 'backend', 'sdl2')

# تم التعديل: استيراد get_asset_path من utils
from utils import get_asset_path

# Import Pygame-specific screens and game core
from screens_pygame import PygameScreenManager, MainMenuScreen_Pygame, SettingsScreen_Pygame, GameScreen_Pygame, PauseScreen_Pygame
# from game_core_pygame import GameWidget_Pygame # GameWidget is imported by PygameScreenManager internally

class PygameApp:
    def __init__(self):
        # Set up display
        self.screen_width = int(Config.get('graphics', 'width'))
        self.screen_height = int(Config.get('graphics', 'height'))
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Helwan Linux Game")

        self.running = True
        self.clock = pygame.time.Clock()

        self.data_file = get_asset_path('game_data.json') # Path for game data

        # Game state/data
        self.high_score = 0
        self.music_volume = 1.0
        self.sfx_volume = 1.0

        self.load_game_data() # Load data before setting up screens that might use volumes

        # PygameScreenManager acts as the Kivy ScreenManager
        self.root = PygameScreenManager(app_ref=self, initial_width=self.screen_width, initial_height=self.screen_height)
        # game_widget is now directly accessible via self.root.game_widget

    def load_game_data(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.high_score = data.get('high_score', 0)
                self.music_volume = data.get('music_volume', 1.0)
                self.sfx_volume = data.get('sfx_volume', 1.0)
            
            # Set initial volumes
            if pygame.mixer.get_init(): # Check if mixer is initialized
                pygame.mixer.music.set_volume(self.music_volume)
                # For SFX, you'd usually set volume on individual sound objects when played
            
            print("Game data loaded successfully.")
        except FileNotFoundError:
            print("Game data file not found. Starting with default settings.")
            # Save defaults if file not found to create it
            self.save_game_data()
        except json.JSONDecodeError:
            print("Error decoding game data. Starting with default settings.")
            # Attempt to reset and save defaults on decode error
            self.high_score = 0
            self.music_volume = 1.0
            self.sfx_volume = 1.0
            self.save_game_data()
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
                json.dump(data, f, indent=4) # Use indent for readability
            print("Game data saved successfully.")
        except Exception as e:
            print(f"An error occurred while saving game data: {e}")

    def run(self):
        dt = 0 # Delta time for game updates

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Delegate event handling to the current screen
                if self.root.current_screen:
                    self.root.current_screen.handle_event(event)

            # Update current screen's content (if it has an update method)
            if hasattr(self.root.current_screen, 'update'):
                self.root.current_screen.update(dt)
            
            # Draw current screen's content
            if self.root.current_screen:
                self.root.current_screen.draw(self.screen)

            pygame.display.flip() # Update the full display Surface to the screen
            dt = self.clock.tick(60) / 1000.0 # Limit to 60 FPS and get delta time in seconds

        print("DEBUG: PygameApp.run() loop finished. Quitting Pygame.")
        self.save_game_data() # Save data on exit
        pygame.quit()
        sys.exit() # Ensure process exits

if __name__ == '__main__':
    app = PygameApp()
    app.run()
