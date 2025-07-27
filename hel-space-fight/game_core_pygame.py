import pygame
import os
import sys
import random

# Pygame specific constants and initialization
# (Assume pygame is already initialized in main_pygame.py)

# Dummy class for Kivy's Window equivalent
class PygameWindow:
    width = 800  # Default width
    height = 600 # Default height

    @classmethod
    def get_size(cls):
        return (cls.width, cls.height)

    @classmethod
    def set_size(cls, size):
        cls.width = size[0]
        cls.height = size[1]
        
# Dummy class for Kivy's Clock.schedule_once equivalent
class PygameClock:
    _timer_events = []

    @classmethod
    def schedule_once(cls, callback, delay):
        event = {'callback': callback, 'end_time': pygame.time.get_ticks() + delay * 1000, 'canceled': False}
        cls._timer_events.append(event)
        return event

    @classmethod
    def tick(cls):
        current_time = pygame.time.get_ticks()
        for event in list(cls._timer_events):
            if not event['canceled'] and current_time >= event['end_time']:
                event['callback']()
                cls._timer_events.remove(event)

    @classmethod
    def cancel(cls, event):
        if event in cls._timer_events:
            event['canceled'] = True

# Get asset path function (copied from main_pygame.py for consistency)
def get_asset_path(filename):
    if hasattr(sys, '_MEIPASS'):
        path = os.path.join(sys._MEIPASS, 'assets', filename)
    else:
        path = os.path.join('assets', filename)
    # print(f"DEBUG: Attempting to load asset: {path}") # Keep for debugging if needed
    return path

# Import entities after defining get_asset_path if they use it directly on import
from entities_pygame import Bullet, Enemy, FastEnemy, ArmoredEnemy, PowerUp, FireRatePowerUp, Explosion, Player

# Define a simple App class structure for volume access, if not already in main_pygame.py
class DummyPygameApp:
    def __init__(self, screen_width=800, screen_height=600):
        self.root = None # Will be set to the ScreenManager
        self.music_volume = 0.5 # Default
        self.sfx_volume = 0.5 # Default
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._previous_screen = None # To store previous screen in app.root

    # This method is just a placeholder to mimic Kivy's App.get_running_app()
    @classmethod
    def get_running_app(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance


class GameWidget_Pygame:
    def __init__(self, app_ref, game_music_sound_path=None):
        self.app = app_ref # Reference to the main PygameApp instance
        self.entities = []
        self.score = 0
        self.player = None
        self.is_game_running = False
        self.is_paused = False # New flag for pause state
        self.game_over_visible = False # New flag to track game over screen visibility

        # Pygame specific: store keyboard state
        self.keysPressed = set()

        # Load music using pygame.mixer.music (for background music)
        self.game_music_sound_path = game_music_sound_path
        if self.game_music_sound_path and os.path.exists(self.game_music_sound_path):
            try:
                pygame.mixer.music.load(self.game_music_sound_path)
                pygame.mixer.music.set_volume(self.app.music_volume)
                # Music will be played in start_game
            except pygame.error as e:
                print(f"Could not load background music {self.game_music_sound_path}: {e}")
        else:
            print(f"Background music file not found: {self.game_music_sound_path}")

        # Load heart image
        self.heart_image = None
        heart_path = get_asset_path("heart.png")
        print(f"DEBUG Heart Load: Attempting to load heart from: {heart_path}")
        if os.path.exists(heart_path):
            try:
                self.heart_image = pygame.image.load(heart_path).convert_alpha()
                self.heart_image = pygame.transform.scale(self.heart_image, (30, 30)) # Scale to desired size
                print(f"DEBUG Heart Load: Successfully loaded heart image. Image object: {self.heart_image}")
            except pygame.error as e:
                print(f"DEBUG Heart Load: Error loading heart image {heart_path}: {e}")
        else:
            print(f"DEBUG Heart Load: Heart image file not found at: {heart_path}. Using red squares.")


        # Timer for enemy spawning
        self._enemy_spawn_timer = 0.0
        self._enemy_spawn_interval = 2.0 # Spawn an enemy every 2 seconds

    def update(self, dt):
        if not self.is_game_running or self.is_paused: # Only update if game is running AND not paused
            return

        PygameClock.tick() # Process scheduled events for things like power-ups

        # Update all entities
        entities_to_remove = []
        for entity in list(self.entities): # Iterate over a copy to allow modification
            entity.update(dt)
            # Collect entities that went off screen or marked for removal
            if isinstance(entity, (Bullet, Enemy, PowerUp, Explosion)) and (
                entity.pos[1] < -entity.size[1] or entity.pos[1] > self.app.screen_height + entity.size[1]
            ):
                # This needs to be handled by each entity's update method itself, calling remove_entity
                # The entities' update methods already check for off-screen and call self.game.remove_entity(self)
                pass # No need for a generic check here if entities remove themselves

        # Process removals (entities removed by their own update methods or collision checks)
        # The actual removal from self.entities happens in self.remove_entity

        # Check collisions
        self.check_collisions()

        # Spawn new enemies
        self._enemy_spawn_timer += dt
        if self._enemy_spawn_timer >= self._enemy_spawn_interval:
            self.spawn_enemy()
            self._enemy_spawn_timer = 0.0

    def draw(self, screen):
        # Draw background (handled by screen.draw method)
        # Draw all entities
        for entity in self.entities:
            entity.draw(screen)
        
        # Draw score (simplified for Pygame)
        font = pygame.font.Font(None, 36) # Default font, size 36
        score_text = font.render(f"Score: {self.score}", True, (255, 255, 255)) # White color
        screen.blit(score_text, (10, self.app.screen_height - 40)) # Position at bottom left

        # Draw player health (using heart image or red squares)
        health_icon_size = 30
        health_padding = 5
        
        # Determine number of "hearts" based on health (e.g., 10 health per heart)
        num_hearts = self.player.health // 10
        if num_hearts < 0: num_hearts = 0

        for i in range(num_hearts):
            # Use heart image if available, otherwise use red square
            if self.heart_image:
                screen.blit(self.heart_image, (self.app.screen_width - (i + 1) * (health_icon_size + health_padding), 10))
            else:
                pygame.draw.rect(screen, (255, 0, 0), (self.app.screen_width - (i + 1) * (health_icon_size + health_padding), 10, health_icon_size, health_icon_size)) # Top right


        # Draw game over screen if active
        if self.game_over_visible:
            # Darken background
            s = pygame.Surface((self.app.screen_width, self.app.screen_height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 128)) # Semi-transparent black
            screen.blit(s, (0,0))

            # Game Over text
            font = pygame.font.Font(None, 60)
            game_over_text = font.render("GAME OVER", True, (255, 0, 0))
            text_rect = game_over_text.get_rect(center=(self.app.screen_width / 2, self.app.screen_height / 2 - 50))
            screen.blit(game_over_text, text_rect)

            # Score text
            score_font = pygame.font.Font(None, 40)
            score_text = score_font.render(f"Final Score: {self.score}", True, (255, 255, 255))
            score_rect = score_text.get_rect(center=(self.app.screen_width / 2, self.app.screen_height / 2))
            screen.blit(score_text, score_rect)
            
            # CORRECTED: Access high_score directly from app
            high_score_text = score_font.render(f"High Score: {self.app.high_score}", True, (255, 255, 255))
            high_score_rect = high_score_text.get_rect(center=(self.app.screen_width / 2, self.app.screen_height / 2 + 50))
            screen.blit(high_score_text, high_score_rect)


            # Restart button (simplified) - Kivy buttons are complex in Pygame, just draw a rect and check clicks
            button_width, button_height = 200, 80
            restart_button_rect = pygame.Rect(self.app.screen_width / 2 - button_width / 2, self.app.screen_height / 2 + 100, button_width, button_height)
            pygame.draw.rect(screen, (0, 128, 255), restart_button_rect) # Blue button
            
            button_font = pygame.font.Font(None, 36)
            restart_text = button_font.render("Restart", True, (255, 255, 255))
            restart_text_rect = restart_text.get_rect(center=restart_button_rect.center)
            screen.blit(restart_text, restart_text_rect)

            # Store the button rect for click detection
            self._restart_button_rect = restart_button_rect

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.keysPressed.add("left")
            elif event.key == pygame.K_RIGHT:
                self.keysPressed.add("right")
            elif event.key == pygame.K_SPACE:
                self.keysPressed.add("spacebar")
            elif event.key == pygame.K_ESCAPE: # Escape for pausing
                if self.is_game_running and not self.game_over_visible:
                    self.app.root.current = 'pause' # Change screen to pause

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.keysPressed.discard("left")
            elif event.key == pygame.K_RIGHT:
                self.keysPressed.discard("right")
            elif event.key == pygame.K_SPACE:
                self.keysPressed.discard("spacebar")
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                if self.game_over_visible and hasattr(self, '_restart_button_rect') and self._restart_button_rect.collidepoint(event.pos):
                    self.restart_game()

    def start_game(self):
        print("GameWidget: Starting game.")
        self.is_game_running = True
        self.is_paused = False
        self.game_over_visible = False
        self.score = 0
        self.entities = []
        self.keysPressed.clear()

        # Initialize player
        player_x = self.app.screen_width / 2 - 50 # Center player horizontally
        player_y = self.app.screen_height - 120 # Place player near bottom
        self.player = Player((player_x, player_y), game_ref=self)
        self.add_entity(self.player)

        # Play background music
        if self.game_music_sound_path and os.path.exists(self.game_music_sound_path):
            if not pygame.mixer.music.get_busy(): # Only play if not already playing
                pygame.mixer.music.play(-1) # Loop indefinitely
                pygame.mixer.music.set_volume(self.app.music_volume) # Set initial volume
        
        # Reset any game state if necessary
        # e.g., self._enemy_spawn_timer = 0.0

    def pause_game(self):
        if self.is_game_running and not self.is_paused:
            print("GameWidget: Pausing game.")
            self.is_paused = True
            pygame.mixer.music.pause()
            # Unbind keyboard to prevent input during pause, if desired
            # (In Pygame, you'd usually handle this by checking self.is_paused in handle_event)


    def resume_game(self):
        if self.is_game_running and self.is_paused:
            print("GameWidget: Resuming game.")
            self.is_paused = False
            pygame.mixer.music.unpause()
            # Rebind keyboard if it was unbound

    def end_game(self):
        if self.is_game_running:
            print("GameWidget: Stopping game.")
            self.is_game_running = False
            self.is_paused = True # Game is effectively paused at end screen
            self.game_over_visible = True
            
            pygame.mixer.music.stop()

            # CORRECTED: Access high_score directly from app
            if self.score > self.app.high_score:
                self.app.high_score = self.score
                self.app.save_game_data() # Save new high score

            # Schedule showing the game over screen, handled by draw() method now
            # In Pygame, you don't "add" a Kivy widget, you change the drawing state.
            # self.app.root.current = 'game_over' # Kivy specific

    def restart_game(self):
        print("Restarting game.")
        # Reset game state and restart
        self.app.root.current = 'game' # Go back to game screen
        self.start_game() # Call start_game to re-initialize everything

    def add_entity(self, entity):
        self.entities.append(entity)

    def remove_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)

    def add_score(self, points):
        self.score += points

    def spawn_enemy(self):
        # Decide which type of enemy to spawn
        enemy_type = random.choices([Enemy, FastEnemy, ArmoredEnemy], weights=[0.6, 0.3, 0.1], k=1)[0]
        
        # Random x position, ensuring enemy is within screen bounds
        enemy_x = random.randint(0, self.app.screen_width - 80) # Assuming enemy width is 80
        
        # Start enemy slightly off-screen at the top
        enemy_y = -80 # Assuming enemy height is 80
        
        self.add_entity(enemy_type((enemy_x, enemy_y), game_ref=self))

        # Randomly spawn a power-up sometimes
        if random.random() < 0.15: # 15% chance to spawn a power-up
            powerup_x = random.randint(0, self.app.screen_width - 40) # Assuming powerup width is 40
            powerup_y = -40 # Start power-up off-screen
            self.add_entity(FireRatePowerUp((powerup_x, powerup_y), game_ref=self))

    def check_collisions(self):
        player_rect = self.player.get_rect()

        # Check bullet-enemy collisions
        bullets_to_remove = []
        for bullet in [e for e in self.entities if isinstance(e, Bullet)]:
            bullet_rect = bullet.get_rect()
            for enemy in [e for e in self.entities if isinstance(e, Enemy)]:
                enemy_rect = enemy.get_rect()
                if bullet_rect.colliderect(enemy_rect):
                    enemy.take_damage(bullet.damage)
                    bullets_to_remove.append(bullet)
                    # Enemy might be removed by take_damage, so we don't add to enemies_to_remove directly
                    break # Bullet hits only one enemy

        for bullet in bullets_to_remove:
            self.remove_entity(bullet)

        # Check player-enemy collisions
        enemies_to_remove_on_player_hit = []
        powerups_to_collect = []
        for entity in [e for e in self.entities if isinstance(e, (Enemy, PowerUp))]:
            entity_rect = entity.get_rect()
            if player_rect.colliderect(entity_rect):
                if isinstance(entity, Enemy):
                    self.player.take_damage(20) # Player takes 20 damage on enemy collision
                    self.add_explosion(entity.pos, entity.size) # Explosion on enemy
                    enemies_to_remove_on_player_hit.append(entity)
                elif isinstance(entity, PowerUp):
                    entity.activate(self.player) # Power-up affects player
                    powerups_to_collect.append(entity) # Power-up removes itself in activate method

        for enemy in enemies_to_remove_on_player_hit:
            self.remove_entity(enemy)
        for powerup in powerups_to_collect:
            self.remove_entity(powerup) # Powerup.activate already calls remove_entity(self) for itself

    def add_explosion(self, pos, size):
        self.add_entity(Explosion(pos, size, game_ref=self))
