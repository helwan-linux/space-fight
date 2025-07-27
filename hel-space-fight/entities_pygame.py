# entities_pygame.py

import pygame
import os
import sys
import random

# Get asset path function (copied from main_pygame.py to ensure consistency)
def get_asset_path(filename):
    if hasattr(sys, '_MEIPASS'):
        path = os.path.join(sys._MEIPASS, 'assets', filename)
    else:
        path = os.path.join('assets', filename)
    # print(f"DEBUG: Attempting to load asset: {path}") # يمكن إزالة هذا في ملف entities إذا كان مزعجًا
    return path

# Constants for colors (optional, but good practice for clarity)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Dummy class for pygame.time.Clock.schedule_once equivalent
# since Kivy's Clock.schedule_once is used in original code
class PygameClock:
    _timer_events = []

    @classmethod
    def schedule_once(cls, callback, delay):
        # This is a very basic simulation. In a real Pygame app,
        # you'd manage timers using pygame.time.get_ticks()
        # and checking elapsed time in the main loop.
        # For now, it's a placeholder.
        event = {'callback': callback, 'end_time': pygame.time.get_ticks() + delay * 1000, 'canceled': False}
        cls._timer_events.append(event)
        return event # Return the event dict so it can be canceled

    @classmethod
    def tick(cls):
        current_time = pygame.time.get_ticks()
        for event in list(cls._timer_events): # Iterate over a copy to allow modification during loop
            if not event['canceled'] and current_time >= event['end_time']:
                event['callback']()
                cls._timer_events.remove(event)

    @classmethod
    def cancel(cls, event):
        if event in cls._timer_events:
            event['canceled'] = True # Mark as canceled, will be removed on next tick

# Base Entity class
class Entity:
    def __init__(self, pos=(0, 0), size=(50, 50), source="bullshit.png", game_ref=None):
        self._pos = list(pos) # Use list for mutable position
        self._size = list(size) # Use list for mutable size
        self._source = source
        self._image = None
        self.game = game_ref # Reference to GameWidget_Pygame
        self.load_image() # Load image when source is set

    def load_image(self):
        try:
            image_path = get_asset_path(self._source)
            if os.path.exists(image_path):
                self._image = pygame.image.load(image_path).convert_alpha()
                self._image = pygame.transform.scale(self._image, self._size) # Scale image to entity size
            else:
                print(f"Image file not found: {image_path}. Using dummy surface.")
                self._image = pygame.Surface(self._size, pygame.SRCALPHA) # Create a transparent dummy surface
                pygame.draw.rect(self._image, (255, 0, 255, 128), (0, 0, *self._size)) # Magenta transparent rect
        except pygame.error as e:
            print(f"Error loading image {self._source}: {e}")
            self._image = pygame.Surface(self._size, pygame.SRCALPHA)
            pygame.draw.rect(self._image, (255, 0, 255, 128), (0, 0, *self._size))


    @property
    def pos(self):
        return tuple(self._pos) # Return as tuple for consistency with original Kivy design

    @pos.setter
    def pos(self, value):
        self._pos[0] = value[0]
        self._pos[1] = value[1]

    @property
    def size(self):
        return tuple(self._size)

    @size.setter
    def size(self, value):
        self._size[0] = value[0]
        self._size[1] = value[1]
        # Rescale image if size changes
        if self._image and self._image.get_size() != tuple(self._size):
            self._image = pygame.transform.scale(self._image, self._size)


    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if self._source != value:
            self._source = value
            self.load_image() # Reload image when source changes

    def draw(self, screen):
        """Draws the entity's image on the screen."""
        if self._image:
            screen.blit(self._image, self.pos)
        else:
            # Fallback drawing if image failed to load
            pygame.draw.rect(screen, (255, 0, 255), (*self.pos, *self.size))

    def get_rect(self):
        """Returns a pygame.Rect object for collision detection."""
        return pygame.Rect(self._pos[0], self._pos[1], self._size[0], self._size[1])

class Bullet(Entity):
    def __init__(self, pos, speed=600, game_ref=None): # Increased speed for Pygame version
        super().__init__(pos=pos, size=(24, 48), source="bullet.png", game_ref=game_ref) # Bullet has specific size
        self.speed = speed
        self.damage = 50 # <--- تم التعديل هنا: زيادة ضرر الرصاصة
        self.game = game_ref
        
        self.bullet_sound = None
        sound_path = get_asset_path("bullet.wav")
        if os.path.exists(sound_path):
            try:
                self.bullet_sound = pygame.mixer.Sound(sound_path)
                # Set volume based on app's sfx_volume, assuming game_ref has access to app
                if self.game and hasattr(self.game, 'app') and hasattr(self.game.app, 'sfx_volume'):
                    self.bullet_sound.set_volume(self.game.app.sfx_volume)
                self.bullet_sound.play()
            except pygame.error as e:
                print(f"Could not load bullet sound {sound_path}: {e}")
        else:
            print(f"Bullet sound not found: {sound_path}")


    def update(self, dt):
        self._pos[1] -= self.speed * dt # تحريك الرصاصة للأعلى في Pygame (تقليل Y)
        if self._pos[1] < -self._size[1]: # إذا خرجت الرصاصة من أعلى الشاشة
            self.game.remove_entity(self)

class Enemy(Entity):
    def __init__(self, pos, speed=100, health=50, points_value=10, game_ref=None): # <--- تم التعديل هنا: تقليل صحة العدو الأساسي
        super().__init__(pos=pos, size=(80, 80), source="enemy.png", game_ref=game_ref)
        self.speed = speed
        self.health = health
        self.points_value = points_value
        self.game = game_ref # Reference to the GameWidget_Pygame

    def update(self, dt):
        self._pos[1] += self.speed * dt # تحريك العدو للأسفل في Pygame (زيادة Y)
        if self._pos[1] > self.game.app.screen_height: # إذا خرج العدو من أسفل الشاشة
            self.game.remove_entity(self)

    def take_damage(self, amount):
        self.health -= amount
        print(f"Enemy at {self.pos} took {amount} damage. Health: {self.health}")
        if self.health <= 0:
            print(f"Enemy at {self.pos} health reached 0. Adding explosion and removing.")
            self.game.add_explosion(self.pos, self.size) # Add explosion effect
            self.game.remove_entity(self) # Remove self
            self.game.add_score(self.points_value) # Add score

class Player(Entity):
    def __init__(self, pos, game_ref=None):
        super().__init__(pos=pos, size=(100, 100), source="player.png", game_ref=game_ref)
        self.health = 100
        self.speed = 400
        self.game = game_ref # Reference to the GameWidget_Pygame
        
        self._shoot_timer = 0.0
        self._initial_shoot_interval = 0.25 # Initial fire rate
        self._current_shoot_interval = self._initial_shoot_interval
        self._fire_rate_boost_active = False
        self._fire_rate_timer_event = None # To store the scheduled event for cancellation

        self.player_hit_sound = None
        # sound_path = get_asset_path("player_hit.wav") # <--- تم التعليق عليه
        # if os.path.exists(sound_path):
        #     try:
        #         self.player_hit_sound = pygame.mixer.Sound(sound_path)
        #         if self.game and hasattr(self.game, 'app') and hasattr(self.game.app, 'sfx_volume'):
        #             self.player_hit_sound.set_volume(self.game.app.sfx_volume)
        #     except pygame.error as e:
        #         print(f"Could not load player hit sound {sound_path}: {e}")
        # else:
        #     print(f"Player hit sound not found: {sound_path}")


    def take_damage(self, amount):
        self.health -= amount
        if self.player_hit_sound: # هذا الشرط سيمنع تشغيل الصوت لأنه None
            self.player_hit_sound.play()
        if self.health <= 0:
            print("Player destroyed!")
            self.game.end_game()

    def update(self, dt):
        if self.health <= 0:
            return

        step_size = self.speed * dt
        newx = self.pos[0]

        # Handle keyboard input from game_ref (GameWidget_Pygame)
        if "left" in self.game.keysPressed:
            newx -= step_size
        if "right" in self.game.keysPressed:
            newx += step_size

        # Clamp player position within screen bounds
        newx = max(0, min(newx, self.game.app.screen_width - self.size[0]))
        self.pos = (newx, self.pos[1])

        self._shoot_timer += dt

        if "spacebar" in self.game.keysPressed:
            if self._shoot_timer >= self._current_shoot_interval:
                x = self.pos[0] + self.size[0] / 2 - 12 # Adjust for bullet width
                y = self.pos[1] # الرصاصة تبدأ من أعلى اللاعب (تم التعديل هنا)
                self.game.add_entity(Bullet((x, y), game_ref=self.game))
                self._shoot_timer = 0.0
                # print("Bullet fired!") # No need to print every bullet

    def activate_fire_rate_boost(self, duration):
        print("Activating fire rate boost for player.")
        if self._fire_rate_timer_event:
            PygameClock.cancel(self._fire_rate_timer_event) # Cancel existing timer

        self._fire_rate_boost_active = True
        self._current_shoot_interval = 0.1 # Faster fire rate
        self._shoot_timer = 0.0 # Reset timer to allow immediate shot

        # Schedule deactivation
        self._fire_rate_timer_event = PygameClock.schedule_once(self.deactivate_fire_rate_boost, duration)
        print("Fire rate boost activated.")

    def deactivate_fire_rate_boost(self):
        print("Deactivating fire rate boost for player.")
        self._fire_rate_boost_active = False
        self._current_shoot_interval = self._initial_shoot_interval # Reset to initial fire rate
        self._fire_rate_timer_event = None # Clear the event reference
        print("Fire rate boost deactivated.")

class FastEnemy(Enemy):
    def __init__(self, pos, game_ref=None):
        super().__init__(pos, game_ref=game_ref)
        self.health = 50 # لم يتغير
        self.speed = 250 # أسرع من العدو العادي
        self.points_value = 20
        self.source = "fast_enemy.png"

class ArmoredEnemy(Enemy):
    def __init__(self, pos, game_ref=None):
        super().__init__(pos, game_ref=game_ref)
        self.health = 200 # لم يتغير (سيموت في 4 ضربات الآن بدلاً من 20)
        self.speed = 70 # أبطأ
        self.points_value = 50
        self.source = "armored_enemy.png"

class PowerUp(Entity):
    def __init__(self, pos, game_ref=None):
        super().__init__(pos=pos, size=(40, 40), source="powerup.png", game_ref=game_ref)
        self.speed = 150

    def update(self, dt):
        self._pos[1] += self.speed * dt # تحريك تعزيز القوة للأسفل في Pygame (زيادة Y)
        if self._pos[1] > self.game.app.screen_height: # إذا خرج تعزيز القوة من أسفل الشاشة
            self.game.remove_entity(self)

    def activate(self, player):
        """Called when player collects the power-up."""
        print("Generic PowerUp activated.")
        self.game.remove_entity(self) # Remove power-up after collection

class FireRatePowerUp(PowerUp):
    def __init__(self, pos, game_ref=None):
        super().__init__(pos, game_ref=game_ref)
        self.source = "powerup.png"
        self.duration = 10 # مدة التعزيز بالثواني

    def activate(self, player):
        print("Fire Rate PowerUp activated!")
        player.activate_fire_rate_boost(self.duration)
        self.game.remove_entity(self) # Remove power-up after collection

class Explosion(Entity):
    def __init__(self, pos, size, game_ref=None):
        super().__init__(pos=pos, size=size, source="explosion.png", game_ref=game_ref)
        self.animation_duration = 0.5 # Duration for the explosion animation
        self._timer = 0.0

        self.explosion_sound = None
        sound_path = get_asset_path("explosion.wav")
        if os.path.exists(sound_path):
            try:
                self.explosion_sound = pygame.mixer.Sound(sound_path)
                if self.game and hasattr(self.game, 'app') and hasattr(self.game.app, 'sfx_volume'):
                    self.explosion_sound.set_volume(self.game.app.sfx_volume)
                self.explosion_sound.play()
            except pygame.error as e:
                print(f"Could not load explosion sound {sound_path}: {e}")
        else:
            print(f"Explosion sound not found: {sound_path}")


    def update(self, dt):
        self._timer += dt
        if self._timer >= self.animation_duration:
            self.game.remove_entity(self) # Remove explosion after its duration
