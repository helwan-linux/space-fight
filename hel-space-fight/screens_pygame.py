import pygame
import os
import sys

from utils import get_asset_path
from game_core_pygame import GameWidget_Pygame # Adjust import based on your structure

# --- Pygame Specific Implementations for Kivy Widgets ---

class PygameButton:
    def __init__(self, text, rect, action):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.action = action # This action is expected to be a callable method
        self.font = pygame.font.Font(None, 36)
        self.color = (0, 128, 255) # Blue
        self.text_color = (255, 255, 255) # White

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action() # Call the action here
            return True
        return False

class PygameSlider:
    def __init__(self, rect, min_val, max_val, initial_val, on_value_change):
        self.rect = pygame.Rect(rect)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.on_value_change = on_value_change
        self.is_dragging = False # حالة لتتبع ما إذا كان المزلاج يتم سحبه حالياً

        self.rail_color = (100, 100, 100) # Dark gray
        self.knob_color = (0, 180, 255) # Light blue
        self.knob_radius = 10

        self._update_knob_pos()

    def _update_knob_pos(self):
        # حساب موضع زر المزلاج بناءً على القيمة الحالية
        # تأكد من أن حساب النسبة المئوية صحيح لتجنب تجاوز المزلاج حدوده
        normalized_value = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.knob_x = self.rect.x + normalized_value * self.rect.width
        self.knob_pos = (self.knob_x, self.rect.centery)
        self.knob_rect = pygame.Rect(self.knob_pos[0] - self.knob_radius, self.knob_pos[1] - self.knob_radius,
                                     self.knob_radius * 2, self.knob_radius * 2)

    def _update_value_from_pos(self, mouse_x):
        # حساب القيمة بناءً على موضع الفأرة
        normalized_x = (mouse_x - self.rect.x) / self.rect.width
        # ضمان أن القيمة تظل بين 0 و 1 قبل تطبيق min_val و max_val
        normalized_x = max(0.0, min(1.0, normalized_x)) 
        
        self.value = self.min_val + normalized_x * (self.max_val - self.min_val)
        # لا داعي لـ clamp هنا إذا تم عمل clamp لـ normalized_x
        # self.value = max(self.min_val, min(self.max_val, self.value)) # Clamp value
        self.on_value_change(self, self.value) # استدعاء دالة رد الاتصال
        self._update_knob_pos() # تحديث موضع زر المزلاج بعد تغيير القيمة

    def draw(self, screen):
        # رسم المسار (rail)
        pygame.draw.line(screen, self.rail_color, self.rect.midleft, self.rect.midright, 5)
        # رسم زر المزلاج (knob)
        pygame.draw.circle(screen, self.knob_color, (int(self.knob_pos[0]), int(self.knob_pos[1])), self.knob_radius)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # النقر بالزر الأيسر
                # تحقق إذا تم النقر على زر المزلاج أو على المسار نفسه
                if self.knob_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                    self.is_dragging = True
                    self._update_value_from_pos(event.pos[0]) # تحديث فوري عند النقر
                    return True # تم التعامل مع الحدث
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # رفع الزر الأيسر
                if self.is_dragging: # تأكد أننا كنا نسحب قبل الرفع
                    self.is_dragging = False
                    return True # تم التعامل مع الحدث
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging: # فقط إذا كنا نسحب حالياً
                self._update_value_from_pos(event.pos[0]) # تحديث مستمر أثناء السحب
                return True # تم التعامل مع الحدث
        return False # لم يتم التعامل مع الحدث بواسطة هذا المزلاج

class PygameScreen:
    def __init__(self, name, app_ref):
        self.name = name
        self.app = app_ref
        self.buttons = []
        # Changed labels to store (text_str, text_surface, rect) for easier updates
        self.labels = [] # Stores (text_str, text_surface, rect) tuples
        self.sliders = [] # For settings screen

    def draw(self, screen):
        # Default draw method, can be overridden
        screen.fill((0, 0, 0)) # Black background
        # Iterate through labels and draw them
        for text_str, text_surface, rect in self.labels:
            screen.blit(text_surface, rect)
        for button in self.buttons:
            button.draw(screen)
        for slider in self.sliders:
            slider.draw(screen)

    def handle_event(self, event):
        # Default event handler, can be overridden
        # For buttons
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.handle_click(event.pos):
                    return True # Event handled by a button

        # For sliders (typically only in SettingsScreen)
        for slider in self.sliders:
            if slider.handle_event(event):
                return True # Event handled by a slider
        return False

    def on_enter(self):
        print(f"Pygame Screen: Entered {self.name}.")
        # Additional logic when screen is entered (e.g., play music)

    def on_leave(self):
        print(f"Pygame Screen: Left {self.name}.")
        # Additional logic when screen is left (e.g., stop music)

class PygameScreenManager:
    def __init__(self, app_ref, initial_width=800, initial_height=600):
        self.app = app_ref # Reference to the main app instance
        self.screens = {}
        self._current_screen = None
        self._previous_screen = None # To go back from settings

        # GameWidget is now directly part of the manager for easy access
        self.game_music_path = get_asset_path("background_music.ogg")
        self.game_widget = GameWidget_Pygame(self.app, self.game_music_path)

        self.add_screen(MainMenuScreen_Pygame(name='menu', app_ref=self.app))
        self.add_screen(SettingsScreen_Pygame(name='settings', app_ref=self.app))
        self.add_screen(GameScreen_Pygame(name='game', app_ref=self.app, game_widget=self.game_widget)) # Pass game_widget
        self.add_screen(PauseScreen_Pygame(name='pause', app_ref=self.app)) # This line is calling the constructor

        self.current = 'menu' # Set initial screen

    def add_screen(self, screen_obj):
        self.screens[screen_obj.name] = screen_obj

    @property
    def current(self):
        return self._current_screen.name if self._current_screen else None

    @current.setter
    def current(self, screen_name):
        if screen_name not in self.screens:
            print(f"Error: Screen '{screen_name}' does not exist.")
            return

        if self._current_screen:
            self._current_screen.on_leave() # Call on_leave for old screen

        print(f"DEBUG: Setting screen to: {screen_name}")
        self._current_screen = self.screens[screen_name]
        self._current_screen.on_enter() # Call on_enter for new screen

        # If transitioning to game screen, ensure game is running
        if screen_name == 'game':
            if not self.game_widget.is_game_running: # Only start if not already running
                 self.game_widget.start_game()
            else: # If resuming, ensure it's unpaused
                self.game_widget.resume_game()
        elif screen_name == 'pause':
            self.game_widget.pause_game()

    @property
    def current_screen(self):
        return self._current_screen

# --- Specific Screen Implementations ---

class MainMenuScreen_Pygame(PygameScreen):
    def __init__(self, name, app_ref, **kwargs):
        super().__init__(name, app_ref)

        button_width, button_height = 200, 80
        center_x = self.app.screen_width / 2

        # Title Label
        title_font = pygame.font.Font(None, 60)
        title_text_str = "Helwan Linux Game" # Store the raw text
        title_text_surf = title_font.render(title_text_str, True, (255, 255, 255))
        title_rect = title_text_surf.get_rect(center=(center_x, self.app.screen_height * 0.7))
        self.labels.append((title_text_str, title_text_surf, title_rect))

        # Buttons
        self.buttons.append(PygameButton("Start Game", (center_x - button_width/2, self.app.screen_height * 0.5 - button_height/2, button_width, button_height), self.start_game))
        self.buttons.append(PygameButton("Settings", (center_x - button_width/2, self.app.screen_height * 0.35 - button_height/2, button_width, button_height), self.open_settings))
        self.buttons.append(PygameButton("Exit", (center_x - button_width/2, self.app.screen_height * 0.2 - button_height/2, button_width, button_height), self.exit_game))

    def start_game(self):
        print("Pygame Main Menu: Start Game pressed.")
        self.app.root.current = 'game' # Change screen to game

    def open_settings(self):
        print("Pygame Main Menu: Settings pressed.")
        self.app.root._previous_screen = self.name # Store current screen to return to it
        self.app.root.current = 'settings'

    def exit_game(self):
        print("Pygame Main Menu: Exit pressed.")
        pygame.event.post(pygame.event.Event(pygame.QUIT)) # Post QUIT event to end game loop

class SettingsScreen_Pygame(PygameScreen):
    def __init__(self, name, app_ref, **kwargs):
        super().__init__(name, app_ref)

        button_width, button_height = 150, 60
        slider_width, slider_height = 400, 20
        
        center_x = self.app.screen_width / 2

        # Fonts
        self.title_font = pygame.font.Font(None, 50)
        self.label_font = pygame.font.Font(None, 36)

        # Title Label (stored as (text_str, text_surf, rect))
        title_text_str = "Settings"
        title_text_surf = self.title_font.render(title_text_str, True, (255, 255, 255))
        title_rect = title_text_surf.get_rect(center=(center_x, self.app.screen_height * 0.85))
        self.labels.append((title_text_str, title_text_surf, title_rect))

        # Music Volume Label (initially rendered)
        music_label_str = f"Music Volume: {self.app.music_volume:.2f}"
        music_label_surf = self.label_font.render(music_label_str, True, (255, 255, 255))
        self.music_label_rect = music_label_surf.get_rect(center=(center_x, self.app.screen_height * 0.65 + 30))
        # Store a placeholder for music volume, it will be updated in draw
        self.labels.append(("Music Volume", music_label_surf, self.music_label_rect)) 

        self.music_slider = PygameSlider(
            (center_x - slider_width/2, self.app.screen_height * 0.65, slider_width, slider_height),
            0.0, 1.0, self.app.music_volume, self.on_music_volume_change
        )
        self.sliders.append(self.music_slider)

        # SFX Volume Label (initially rendered)
        sfx_label_str = f"SFX Volume: {self.app.sfx_volume:.2f}"
        sfx_label_surf = self.label_font.render(sfx_label_str, True, (255, 255, 255))
        self.sfx_label_rect = sfx_label_surf.get_rect(center=(center_x, self.app.screen_height * 0.45 + 30))
        # Store a placeholder for SFX volume, it will be updated in draw
        self.labels.append(("SFX Volume", sfx_label_surf, self.sfx_label_rect))

        self.sfx_slider = PygameSlider(
            (center_x - slider_width/2, self.app.screen_height * 0.45, slider_width, slider_height),
            0.0, 1.0, self.app.sfx_volume, self.on_sfx_volume_change
        )
        self.sliders.append(self.sfx_slider)

        # Back Button
        self.buttons.append(PygameButton("Back", (center_x - button_width/2, self.app.screen_height * 0.2 - button_height/2, button_width, button_height), self.go_back))

    def draw(self, screen):
        screen.fill((0, 0, 0)) # Black background

        # Render and blit dynamic labels (Music and SFX volume)
        current_music_text = f"Music Volume: {self.app.music_volume:.2f}"
        music_text_surf = self.label_font.render(current_music_text, True, (255, 255, 255))
        screen.blit(music_text_surf, self.music_label_rect)

        current_sfx_text = f"SFX Volume: {self.app.sfx_volume:.2f}"
        sfx_text_surf = self.label_font.render(current_sfx_text, True, (255, 255, 255))
        screen.blit(sfx_text_surf, self.sfx_label_rect)
        
        # Draw static labels (like "Settings" title)
        for text_str, text_surface, rect in self.labels:
            if text_str == "Settings": # Check for the specific string
                screen.blit(text_surface, rect)

        for button in self.buttons:
            button.draw(screen)
        for slider in self.sliders:
            slider.draw(screen)

    def handle_event(self, event):
        # Handle mouse button clicks for buttons and sliders
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.handle_click(event.pos):
                    return True # Event handled by a button
            for slider in self.sliders:
                if slider.handle_event(event): # Slider handles its own events
                    return True # Event handled by a slider
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for slider in self.sliders:
                if slider.handle_event(event): # Ensure slider stops dragging
                    return True # Event handled
        elif event.type == pygame.MOUSEMOTION:
            # Only propagate MOUSEMOTION if a slider is actively dragging
            for slider in self.sliders:
                if slider.is_dragging: # Check if this slider is currently being dragged
                    if slider.handle_event(event):
                        return True # Event handled by the currently dragging slider
        return False # Event not handled

    def on_music_volume_change(self, slider, value):
        self.app.music_volume = value
        pygame.mixer.music.set_volume(value)
        print(f"Music Volume: {value:.2f}")

    def on_sfx_volume_change(self, slider, value):
        self.app.sfx_volume = value
        # In a real game, you'd set volume for all active sound effects or future ones
        print(f"SFX Volume: {value:.2f}")

    def go_back(self):
        print("Settings screen: Back pressed.")
        self.app.save_game_data() # Save settings when going back
        # Go back to the previous screen (menu or pause)
        if self.app.root._previous_screen:
            self.app.root.current = self.app.root._previous_screen
            self.app.root._previous_screen = None # Clear it
        else:
            self.app.root.current = 'menu' # Default to menu if no previous screen set

class GameScreen_Pygame(PygameScreen):
    def __init__(self, name, app_ref, game_widget, **kwargs):
        super().__init__(name, app_ref)
        self.game_widget = game_widget # GameWidget instance is passed in
        # Add background image directly to this screen if it's static
        self.background_image = None
        background_path = get_asset_path("background.png")
        if os.path.exists(background_path):
            try:
                self.background_image = pygame.image.load(background_path).convert()
                self.background_image = pygame.transform.scale(self.background_image, (self.app.screen_width, self.app.screen_height))
            except pygame.error as e:
                print(f"Error loading background image {background_path}: {e}")
        else:
            print(f"Background image file not found: {background_path}")


    def draw(self, screen):
        if self.background_image:
            screen.blit(self.background_image, (0,0))
        else:
            screen.fill((0, 0, 0)) # Default black if no background

        self.game_widget.draw(screen) # Draw the game content

    def update(self, dt):
        self.game_widget.update(dt) # Update game logic

    def handle_event(self, event):
        # Pass relevant events to game_widget (player movement, shooting, pause)
        self.game_widget.handle_event(event) # Player input handling
        return False # Event might be handled by game_widget, but allow others if needed

    def on_enter(self):
        super().on_enter()
        # GameWidget.start_game is called by PygameScreenManager.current.setter
        # when screen is set to 'game'
        pass

    def on_leave(self):
        super().on_leave()
        # GameWidget.pause_game is called by PygameScreenManager.current.setter
        # when screen is set away from 'game' (e.g., to 'pause')
        pass


class PauseScreen_Pygame(PygameScreen):
    def __init__(self, name, app_ref, **kwargs):
        super().__init__(name, app_ref)

        button_width, button_height = 250, 80
        center_x = self.app.screen_width / 2

        # Title Label
        title_font = pygame.font.Font(None, 60)
        title_text_str = "PAUSED"
        title_text_surf = title_font.render(title_text_str, True, (255, 255, 255))
        title_rect = title_text_surf.get_rect(center=(center_x, self.app.screen_height * 0.7))
        self.labels.append((title_text_str, title_text_surf, title_rect))

        # Buttons
        self.buttons.append(PygameButton("Resume Game", (center_x - button_width/2, self.app.screen_height * 0.5 - button_height/2, button_width, button_height), self.resume_game))
        self.buttons.append(PygameButton("Settings", (center_x - button_width/2, self.app.screen_height * 0.35 - button_height/2, button_width, button_height), self.open_settings))
        self.buttons.append(PygameButton("Exit to Main Menu", (center_x - button_width/2, self.app.screen_height * 0.2 - button_height/2, button_width, button_height), self.exit_to_menu))

    def draw(self, screen):
        # Draw a semi-transparent overlay
        s = pygame.Surface((self.app.screen_width, self.app.screen_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128)) # Semi-transparent black
        screen.blit(s, (0,0))

        # Draw labels and buttons on top
        for text_str, text_surface, rect in self.labels:
            screen.blit(text_surface, rect)
        for button in self.buttons:
            button.draw(screen)

    # These methods are correctly defined here as part of the class
    def resume_game(self):
        print("Pause screen: Resume Game pressed.")
        self.app.root.current = 'game'

    def open_settings(self):
        print("Pause screen: Settings pressed.")
        self.app.root._previous_screen = self.name # Store current screen to return to it
        self.app.root.current = 'settings'

    def exit_to_menu(self):
        print("Pause screen: Exit to Main Menu pressed.")
        self.app.root.screens['game'].game_widget.end_game() # Ensure game state is reset
        self.app.root.current = 'menu' # Change screen to main menu
