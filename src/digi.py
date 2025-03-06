#!/usr/bin/env python3
import tkinter as tk
from PIL import Image, ImageTk
import random
import time
import os
import importlib.util
import sys
import threading

# Constants
CONFIG_FILE = "pet_config.py"  # File that will be hot reloaded

class PetConfig:
    """Default configuration class that will be replaced when reloading."""
    # Spritesheet settings
    USE_SPRITESHEET = True
    SPRITESHEET_PATH = "pet_sprites.png"  # Path to your spritesheet
    
    # Sprite frame size (in pixels)
    SPRITE_WIDTH = 31
    SPRITE_HEIGHT = 31
    
    # Frame mapping - tells which frames to use for each animation state
    # Format: animation_state: [(row, col), (row, col), ...]
    SPRITE_MAPPING = {
        "idle_right": [(0, 0), (0, 1), (0, 2), (0, 3)],
        "idle_left": [(0, 0), (0, 1), (0, 2), (0, 3)],
        "walk_right": [(0, 4), (0, 5), (0, 6), (0, 7)],
        "walk_left": [(0, 4), (0, 5), (0, 6), (0, 7)],
        "talk_right": [(0, 0), (0, 1), (0, 2), (0, 3)],
        "talk_left": [(0, 0), (0, 1), (0, 2), (0, 3)],
        "sleep_right": [(0, 4), (0, 5), (0, 6), (0, 7)],
        "sleep_left": [(0, 4), (0, 5), (0, 6), (0, 7)]
    }
    
    # Colors for different states (used if no spritesheet)
    COLORS = {"idle": "#87CEFA", "walk": "#90EE90", "talk": "#FFB6C1", "sleep": "#D3D3D3"}
    
    # Background color
    BG_COLOR = "lightblue"
    TRANSPARENT_COLOR = None  # Set this to make a specific color transparent
    
    # Animation frames for each state
    ANIMATION_FRAMES = {
        "idle": 4,
        "walk": 4,
        "talk": 4,
        "sleep": 4
    }
    
    # Messages the pet can say
    MESSAGES = [
        "Hello there!",
        "Need any help?",
        "I'm your desktop buddy!",
        "Don't forget to take breaks!",
        "What are you working on?",
        "Remember to stay hydrated!",
        "You're doing great!",
        "*yawns*"
    ]
    
    # Pet dimensions (display size, scales the sprite)
    WIDTH = 120
    HEIGHT = 120
    
    # Animation timing (ms)
    ANIMATION_SPEED = 150
    BEHAVIOR_INTERVAL = 3000
    
    # Behavior probabilities (percent)
    WALK_PROBABILITY = 40
    TALK_PROBABILITY = 10
    SLEEP_PROBABILITY = 5
    # Idle probability is the remainder

class DesktopPet:
    def __init__(self, master):
        self.master = master
        
        # Load initial configuration
        self.config = self.load_config()
        
        # Setup file watcher thread for hot reloading
        self.watcher_thread = threading.Thread(target=self.watch_config_file, daemon=True)
        self.watcher_thread.start()
        
        # Configure the window
        self.master.overrideredirect(True)  # No window borders
        self.master.attributes('-topmost', True)  # Always on top
        
        # Try to set transparency if configured
        try:
            if self.config.TRANSPARENT_COLOR:
                self.master.wm_attributes('-transparentcolor', "red")
                self.bg_color = self.config.TRANSPARENT_COLOR
            else:
                self.bg_color = self.config.BG_COLOR
        except:
            self.bg_color = self.config.BG_COLOR
        
        # Set initial window size
        self.width = self.config.WIDTH
        self.height = self.config.HEIGHT
        self.master.geometry(f"{self.width}x{self.height}+{self.master.winfo_screenwidth() - 200}+{self.master.winfo_screenheight() - 200}")

        # Create a canvas to draw the pet on
        self.canvas = tk.Canvas(master, width=self.width, height=self.height, 
                           bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Pet state attributes
        self.dragging = False
        self.drag_x = 0
        self.drag_y = 0
        self.animation_state = "idle"
        self.direction = "right"
        self.frame = 0
        
        # Spritesheet handling
        self.sprite_frames = {}
        self.load_sprites()
        
        # Set up speech bubble
        self.speech_text = None
        self.speech_bubble = None
        self.speech_timer = None
        
        # Add a close button
        #close_btn = tk.Button(self.master, text="X", command=self.master.destroy, 
        #                    font=("Arial", 8), bg="red", fg="white", width=2)
        #close_btn.place(x=self.width-20, y=0)
        #
        ## Minimize button
        #min_btn = tk.Button(self.master, text="_", command=self.minimize, 
        #                   font=("Arial", 8), bg="gray", fg="white", width=2)
        #min_btn.place(x=self.width-40, y=0)
        #
        ## Reload button
        #reload_btn = tk.Button(self.master, text="↻", command=self.manual_reload, 
        #                     font=("Arial", 8), bg="green", fg="white", width=2)
        #reload_btn.place(x=self.width-60, y=0)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        
        # Set up animation timer
        self.animation_timer = self.master.after(self.config.ANIMATION_SPEED, self.update_animation)
        
        # Set up behavior timer
        self.behavior_timer = self.master.after(self.config.BEHAVIOR_INTERVAL, self.random_behavior)
        
        # Initial drawing
        self.update_sprite()
        
        # Start with a greeting
        self.master.after(500, lambda: self.speak("Hello! Edit pet_config.py to customize me!"))
        
        # Setup a timer to give focus back to the previously focused window
        self.focus_timer = None
        
        # Create default config file if it doesn't exist
        if not os.path.exists(CONFIG_FILE):
            self.create_default_config()
    
    def load_sprites(self):
        """Load sprites from spritesheet"""
        try:
            # Check if required configuration attributes exist
            if not hasattr(self.config, 'USE_SPRITESHEET') or not self.config.USE_SPRITESHEET:
                print("Spritesheet usage is disabled in config")
                return
                
            if not hasattr(self.config, 'SPRITESHEET_PATH'):
                print("SPRITESHEET_PATH not defined in config")
                return
                
            if not os.path.exists(self.config.SPRITESHEET_PATH):
                print(f"Spritesheet file not found: {self.config.SPRITESHEET_PATH}")
                return
                
            if not hasattr(self.config, 'SPRITE_MAPPING') or not self.config.SPRITE_MAPPING:
                print("SPRITE_MAPPING not defined in config")
                return
                
            if not hasattr(self.config, 'SPRITE_WIDTH') or not hasattr(self.config, 'SPRITE_HEIGHT'):
                print("SPRITE_WIDTH or SPRITE_HEIGHT not defined in config")
                return
            
            # Get sprite dimensions
            sprite_width = self.config.SPRITE_WIDTH
            sprite_height = self.config.SPRITE_HEIGHT
            
            # Load the spritesheet
            spritesheet = Image.open(self.config.SPRITESHEET_PATH)
            print(f"Loaded spritesheet: {self.config.SPRITESHEET_PATH} ({spritesheet.width}x{spritesheet.height})")
            
            # Clear existing frames
            self.sprite_frames = {}
            
            # Extract and store each frame based on the mapping
            for state, frames in self.config.SPRITE_MAPPING.items():
                self.sprite_frames[state] = []
                for row, col in frames:
                    try:
                        # Calculate position in spritesheet
                        x = col * (sprite_width+2)
                        y = 0
                        
                        # Check if coordinates are within the spritesheet bounds
                        print(x,y)
                        print(spritesheet.width, spritesheet.height)
                        if x + sprite_width <= spritesheet.width and y + sprite_height <= spritesheet.height:
                            # Extract the frame
                            frame = spritesheet.crop((x, y, x + sprite_width, y + sprite_height))
                            
                            # Resize if needed
                            if self.width != sprite_width or self.height != sprite_height:
                                frame = frame.resize((self.width, self.height), Image.LANCZOS)
                            
                            # Convert to PhotoImage for tkinter
                            photo = ImageTk.PhotoImage(frame)
                            self.sprite_frames[state].append(photo)
                        else:
                            print(f"Warning: Frame at row {row}, col {col} is outside spritesheet bounds")
                    except Exception as frame_error:
                        print(f"Error loading frame at row {row}, col {col}: {frame_error}")
                
                print(f"Loaded {len(self.sprite_frames[state])} frames for state '{state}'")
            
            print(f"Successfully loaded {len(self.sprite_frames)} animation states from spritesheet")
            
        except Exception as e:
            print(f"Error loading sprites: {e}")
            # Fall back to drawing shapes
            self.sprite_frames = {}
    
    def load_config(self):
        """Load or reload the configuration from the config file."""
        if os.path.exists(CONFIG_FILE):
            try:
                # Load the module
                spec = importlib.util.spec_from_file_location("pet_config", CONFIG_FILE)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                
                # Check if it has a PetConfig class
                if hasattr(config_module, "PetConfig"):
                    return config_module.PetConfig
                else:
                    print("Warning: PetConfig class not found in config file, using defaults")
                    return PetConfig
            except Exception as e:
                print(f"Error loading config: {e}")
                return PetConfig
        else:
            return PetConfig
    
    def create_default_config(self):
        """Create a default configuration file."""
        with open(CONFIG_FILE, "w") as f:
            f.write("""# Desktop Pet Configuration
# Edit this file to customize your pet
# The application will hot reload when you save changes

class PetConfig:
    # Spritesheet settings
    USE_SPRITESHEET = True
    SPRITESHEET_PATH = "pet_sprites.png"  # Path to your spritesheet
    
    # Sprite frame size (in pixels)
    # Adjust these to match the size of each frame in your spritesheet
    SPRITE_WIDTH = 32
    SPRITE_HEIGHT = 32
    
    # Frame mapping - tells which frames to use for each animation state
    # Format: animation_state: [(row, col), (row, col), ...]
    # Row 0 is the top row, Col 0 is the leftmost column
    # 
    # For the spritesheet in your example image, you might use something like:
    # - First row (0) seems to have 6 frames of an animation
    # - Second row (1) seems to have 6 frames of another animation
    #
    # Modify this mapping to match your spritesheet's layout:
    SPRITE_MAPPING = {
        # First two rows of animation frames
        "idle_right": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)],
        "idle_left": [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)],
        
        # You can change these to match your spritesheet
        "walk_right": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)],
        "walk_left": [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)],
        "talk_right": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)],
        "talk_left": [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)],
        "sleep_right": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)],
        "sleep_left": [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)]
    }
    
    # Background color (used if TRANSPARENT_COLOR is None)
    BG_COLOR = "lightblue"
    
    # Set this to make a specific color transparent
    # For your green spritesheet background, try:
    TRANSPARENT_COLOR = "#00FF00"  # Bright green
    # You can also use color names like "green" or other hex values
    
    # Pet dimensions (display size - will scale the sprites)
    WIDTH = 120
    HEIGHT = 120
    
    # Animation timing (ms)
    ANIMATION_SPEED = 150  # Time between frames
    BEHAVIOR_INTERVAL = 3000  # Time between behavior changes
    
    # Behavior probabilities (percent)
    WALK_PROBABILITY = 40
    TALK_PROBABILITY = 10
    SLEEP_PROBABILITY = 5
    # Idle probability is the remainder
    
    # Messages the pet can say
    MESSAGES = [
        "Hello there!",
        "Need any help?",
        "I'm your desktop buddy!",
        "Don't forget to take breaks!",
        "What are you working on?",
        "Remember to stay hydrated!",
        "You're doing great!",
        "*yawns*"
    ]
""")
        print(f"Created default configuration file: {CONFIG_FILE}")
    
    def watch_config_file(self):
        """Watch the config file for changes and reload when it changes."""
        last_mod_time = 0
        if os.path.exists(CONFIG_FILE):
            last_mod_time = os.path.getmtime(CONFIG_FILE)
        
        while True:
            try:
                if os.path.exists(CONFIG_FILE):
                    mod_time = os.path.getmtime(CONFIG_FILE)
                    if mod_time > last_mod_time:
                        last_mod_time = mod_time
                        # Schedule the reload on the main thread
                        self.master.after(100, self.reload_config)
                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"Error watching config file: {e}")
                time.sleep(5)  # Wait longer if there's an error
    
    def reload_config(self):
        """Reload the configuration and update the pet."""
        old_config = self.config
        self.config = self.load_config()
        
        # Update window transparency if needed
        try:
            if hasattr(self.config, 'TRANSPARENT_COLOR') and self.config.TRANSPARENT_COLOR:
                self.master.wm_attributes('-transparentcolor', self.config.TRANSPARENT_COLOR)
                self.bg_color = self.config.TRANSPARENT_COLOR
            else:
                self.bg_color = self.config.BG_COLOR
                
            self.canvas.config(bg=self.bg_color)
        except Exception as e:
            print(f"Error setting transparency: {e}")
        
        # Reload sprites if spritesheet settings changed
        reload_sprites = (
            not hasattr(old_config, 'USE_SPRITESHEET') or
            not hasattr(old_config, 'SPRITESHEET_PATH') or
            not hasattr(old_config, 'SPRITE_WIDTH') or
            not hasattr(old_config, 'SPRITE_HEIGHT') or
            not hasattr(old_config, 'SPRITE_MAPPING') or
            old_config.USE_SPRITESHEET != self.config.USE_SPRITESHEET or
            old_config.SPRITESHEET_PATH != self.config.SPRITESHEET_PATH or
            old_config.SPRITE_WIDTH != self.config.SPRITE_WIDTH or
            old_config.SPRITE_HEIGHT != self.config.SPRITE_HEIGHT or
            old_config.SPRITE_MAPPING != self.config.SPRITE_MAPPING
        )
        
        if reload_sprites:
            self.load_sprites()
        
        # Update window size if needed
        if old_config.WIDTH != self.config.WIDTH or old_config.HEIGHT != self.config.HEIGHT:
            self.width = self.config.WIDTH
            self.height = self.config.HEIGHT
            self.master.geometry(f"{self.width}x{self.height}+{self.master.winfo_x()}+{self.master.winfo_y()}")
            self.canvas.config(width=self.width, height=self.height)
            
            # Reposition buttons
            for widget in self.master.winfo_children():
                if isinstance(widget, tk.Button):
                    if widget['text'] == 'X':  # Close button
                        widget.place(x=self.width-20, y=0)
                    elif widget['text'] == '_':  # Minimize button
                        widget.place(x=self.width-40, y=0)
                    elif widget['text'] == '↻':  # Reload button
                        widget.place(x=self.width-60, y=0)
            
            # Reload sprites with new size
            if self.config.USE_SPRITESHEET:
                self.load_sprites()
        
        # Update animation timers if needed
        if old_config.ANIMATION_SPEED != self.config.ANIMATION_SPEED:
            self.master.after_cancel(self.animation_timer)
            self.animation_timer = self.master.after(self.config.ANIMATION_SPEED, self.update_animation)
            
        if old_config.BEHAVIOR_INTERVAL != self.config.BEHAVIOR_INTERVAL:
            self.master.after_cancel(self.behavior_timer)
            self.behavior_timer = self.master.after(self.config.BEHAVIOR_INTERVAL, self.random_behavior)
        
        # Force redraw
        self.update_sprite()
        
        # Notify that config was reloaded
        self.speak("Config reloaded!")
    
    def manual_reload(self):
        """Manually trigger a config reload."""
        self.reload_config()
    
    def minimize(self):
        """Minimize the pet (hide it)"""
        self.master.iconify()
    
    def update_animation(self):
        """Update animation frame and schedule next update"""
        # Default to 4 frames if animation frames not defined
        frames_count = 4
        
        # Try to get frame count from config
        if hasattr(self.config, 'ANIMATION_FRAMES') and isinstance(self.config.ANIMATION_FRAMES, dict):
            frames_count = self.config.ANIMATION_FRAMES.get(self.animation_state, 4)
        
        # If using sprites, get frame count from sprite mapping
        if hasattr(self.config, 'USE_SPRITESHEET') and self.config.USE_SPRITESHEET and self.sprite_frames:
            state_key = f"{self.animation_state}_{self.direction}"
            if state_key in self.sprite_frames:
                frames_count = len(self.sprite_frames[state_key])
        
        self.frame = (self.frame + 1) % frames_count
        self.update_sprite()
        
        # Default animation speed if not defined
        animation_speed = 150
        if hasattr(self.config, 'ANIMATION_SPEED'):
            animation_speed = self.config.ANIMATION_SPEED
            
        self.animation_timer = self.master.after(animation_speed, self.update_animation)
        
    def update_sprite(self):
        """Draw the pet sprite based on current state"""
        self.canvas.delete("sprite")
        
        # Try to use spritesheet first
        if self.config.USE_SPRITESHEET and self.sprite_frames:
            state_key = f"{self.animation_state}_{self.direction}"
            
            if state_key in self.sprite_frames and self.sprite_frames[state_key]:
                # Get the current frame from the sprite mapping
                frames = self.sprite_frames[state_key]
                if frames:
                    # Use modulo to handle different frame counts
                    frame_index = self.frame % len(frames)
                    frame = frames[frame_index]
                    
                    # Draw the sprite
                    self.canvas.create_image(
                        self.width // 2, self.height // 2,
                        image=frame, tags="sprite"
                    )
                    
                    # For walking animation, add some bounce
                    if self.animation_state == "walk":
                        bounce = 2 if self.frame % 2 == 0 else 0
                        x = self.master.winfo_x()
                        y = self.master.winfo_y() - bounce
                        self.master.geometry(f"+{x}+{y}")
                    
                    return
        
        # Fall back to drawing shapes if spritesheet failed or isn't configured
        try:
            color = self.config.COLORS.get(self.animation_state, "#87CEFA")
        except:
            color = "#87CEFA"
        outline_color = "black"
        
        # Draw the basic sprite
        body_x = self.width // 6
        body_y = self.height // 6
        body_width = self.width * 2 // 3
        body_height = self.height * 2 // 3
        
        # Body (circle/oval)
        self.canvas.create_oval(
            body_x, body_y, 
            body_x + body_width, body_y + body_height, 
            fill=color, outline=outline_color, width=2, tags="sprite"
        )
        
        # Eyes and mouth - different based on direction
        if self.direction == "right":
            # Right facing eyes
            eye_offset_x = body_width // 4
            self.canvas.create_oval(
                body_x + body_width - eye_offset_x, body_y + body_height // 4, 
                body_x + body_width - eye_offset_x + body_width // 10, body_y + body_height // 4 + body_height // 10, 
                fill="white", outline=outline_color, tags="sprite"
            )
            self.canvas.create_oval(
                body_x + body_width - eye_offset_x * 2, body_y + body_height // 4, 
                body_x + body_width - eye_offset_x * 2 + body_width // 10, body_y + body_height // 4 + body_height // 10, 
                fill="white", outline=outline_color, tags="sprite"
            )
            
            # Pupils
            pupil_offset = body_width // 40
            self.canvas.create_oval(
                body_x + body_width - eye_offset_x + pupil_offset, body_y + body_height // 4 + pupil_offset, 
                body_x + body_width - eye_offset_x + body_width // 10 - pupil_offset, body_y + body_height // 4 + body_height // 10 - pupil_offset, 
                fill=outline_color, tags="sprite"
            )
            self.canvas.create_oval(
                body_x + body_width - eye_offset_x * 2 + pupil_offset, body_y + body_height // 4 + pupil_offset, 
                body_x + body_width - eye_offset_x * 2 + body_width // 10 - pupil_offset, body_y + body_height // 4 + body_height // 10 - pupil_offset, 
                fill=outline_color, tags="sprite"
            )
            
            # Animate mouth based on state and frame
            mouth_y = body_y + body_height * 2 // 3
            if self.animation_state == "talk":
                mouth_open = self.frame % 2 == 0
                if mouth_open:
                    self.canvas.create_oval(
                        body_x + body_width - eye_offset_x * 1.5, mouth_y, 
                        body_x + body_width - eye_offset_x / 2, mouth_y + body_height // 6, 
                        fill=outline_color, tags="sprite"
                    )
                else:
                    self.canvas.create_line(
                        body_x + body_width - eye_offset_x * 1.5, mouth_y + body_height // 12, 
                        body_x + body_width - eye_offset_x / 2, mouth_y + body_height // 12, 
                        fill=outline_color, width=2, tags="sprite"
                    )
            elif self.animation_state == "sleep":
                # ZZZ for sleeping
                self.canvas.create_text(
                    body_x + body_width + 10, body_y, 
                    text="Z", fill=outline_color, font=("Arial", 12, "bold"), tags="sprite"
                )
                self.canvas.create_text(
                    body_x + body_width, body_y + 10, 
                    text="Z", fill=outline_color, font=("Arial", 10, "bold"), tags="sprite"
                )
                self.canvas.create_text(
                    body_x + body_width - 10, body_y + 20, 
                    text="Z", fill=outline_color, font=("Arial", 8, "bold"), tags="sprite"
                )
                # Closed eyes
                self.canvas.create_line(
                    body_x + body_width - eye_offset_x, body_y + body_height // 4 + body_height // 20, 
                    body_x + body_width - eye_offset_x + body_width // 10, body_y + body_height // 4 + body_height // 20, 
                    fill=outline_color, width=2, tags="sprite"
                )
                self.canvas.create_line(
                    body_x + body_width - eye_offset_x * 2, body_y + body_height // 4 + body_height // 20, 
                    body_x + body_width - eye_offset_x * 2 + body_width // 10, body_y + body_height // 4 + body_height // 20, 
                    fill=outline_color, width=2, tags="sprite"
                )
            else:
                # Normal mouth for other states
                mouth_y = body_y + body_height * 2 // 3 + (self.frame % 2) * (body_height // 30)
                self.canvas.create_line(
                    body_x + body_width - eye_offset_x * 1.5, mouth_y, 
                    body_x + body_width - eye_offset_x / 2, mouth_y, 
                    fill=outline_color, width=2, tags="sprite"
                )
        else:
            # Left facing eyes and features
            eye_offset_x = body_width // 4
            self.canvas.create_oval(
                body_x + eye_offset_x - body_width // 10, body_y + body_height // 4, 
                body_x + eye_offset_x, body_y + body_height // 4 + body_height // 10, 
                fill="white", outline=outline_color, tags="sprite"
            )
            self.canvas.create_oval(
                body_x + eye_offset_x * 2 - body_width // 10, body_y + body_height // 4, 
                body_x + eye_offset_x * 2, body_y + body_height // 4 + body_height // 10, 
                fill="white", outline=outline_color, tags="sprite"
            )
            
            # Pupils
            pupil_offset = body_width // 40
            self.canvas.create_oval(
                body_x + eye_offset_x - body_width // 10 + pupil_offset, body_y + body_height // 4 + pupil_offset, 
                body_x + eye_offset_x - pupil_offset, body_y + body_height // 4 + body_height // 10 - pupil_offset, 
                fill=outline_color, tags="sprite"
            )
            self.canvas.create_oval(
                body_x + eye_offset_x * 2 - body_width // 10 + pupil_offset, body_y + body_height // 4 + pupil_offset, 
                body_x + eye_offset_x * 2 - pupil_offset, body_y + body_height // 4 + body_height // 10 - pupil_offset, 
                fill=outline_color, tags="sprite"
            )
            
            # Similar animation logic as the right side (code omitted for brevity)
            mouth_y = body_y + body_height * 2 // 3
            if self.animation_state == "talk":
                mouth_open = self.frame % 2 == 0
                if mouth_open:
                    self.canvas.create_oval(
                        body_x + eye_offset_x / 2, mouth_y, 
                        body_x + eye_offset_x * 1.5, mouth_y + body_height // 6, 
                        fill=outline_color, tags="sprite"
                    )
                else:
                    self.canvas.create_line(
                        body_x + eye_offset_x / 2, mouth_y + body_height // 12, 
                        body_x + eye_offset_x * 1.5, mouth_y + body_height // 12, 
                        fill=outline_color, width=2, tags="sprite"
                    )
            elif self.animation_state == "sleep":
                # ZZZ for sleeping
                self.canvas.create_text(
                    body_x - 10, body_y, 
                    text="Z", fill=outline_color, font=("Arial", 12, "bold"), tags="sprite"
                )
                self.canvas.create_text(
                    body_x, body_y + 10, 
                    text="Z", fill=outline_color, font=("Arial", 10, "bold"), tags="sprite"
                )
                self.canvas.create_text(
                    body_x + 10, body_y + 20, 
                    text="Z", fill=outline_color, font=("Arial", 8, "bold"), tags="sprite"
                )
                # Closed eyes
                self.canvas.create_line(
                    body_x + eye_offset_x - body_width // 10, body_y + body_height // 4 + body_height // 20, 
                    body_x + eye_offset_x, body_y + body_height // 4 + body_height // 20, 
                    fill=outline_color, width=2, tags="sprite"
                )
                self.canvas.create_line(
                    body_x + eye_offset_x * 2 - body_width // 10, body_y + body_height // 4 + body_height // 20, 
                    body_x + eye_offset_x * 2, body_y + body_height // 4 + body_height // 20, 
                    fill=outline_color, width=2, tags="sprite"
                )
            else:
                # Normal mouth for other states
                mouth_y = body_y + body_height * 2 // 3 + (self.frame % 2) * (body_height // 30)
                self.canvas.create_line(
                    body_x + eye_offset_x / 2, mouth_y, 
                    body_x + eye_offset_x * 1.5, mouth_y, 
                    fill=outline_color, width=2, tags="sprite"
                )
                
        # For walking animation, add some bounce
        if self.animation_state == "walk":
            bounce = 2 if self.frame % 2 == 0 else 0
            x = self.master.winfo_x()
            y = self.master.winfo_y() - bounce
            self.master.geometry(f"+{x}+{y}")
    
    def random_behavior(self):
        """Randomly select and perform a behavior"""
        # Don't change behavior if currently being dragged
        if self.dragging:
            behavior_interval = 3000
            if hasattr(self.config, 'BEHAVIOR_INTERVAL'):
                behavior_interval = self.config.BEHAVIOR_INTERVAL
                
            self.behavior_timer = self.master.after(behavior_interval, self.random_behavior)
            return
            
        choice = random.randint(1, 100)
        
        # Default probabilities if not defined
        walk_prob = 40
        talk_prob = 10
        sleep_prob = 5
        
        # Use config values if available
        if hasattr(self.config, 'WALK_PROBABILITY'):
            walk_prob = self.config.WALK_PROBABILITY
        if hasattr(self.config, 'TALK_PROBABILITY'):
            talk_prob = self.config.TALK_PROBABILITY
        if hasattr(self.config, 'SLEEP_PROBABILITY'):
            sleep_prob = self.config.SLEEP_PROBABILITY
        
        if choice < walk_prob:  # Chance to walk
            self.walk_randomly()
        elif choice < walk_prob + talk_prob:  # Chance to talk
            if hasattr(self.config, 'MESSAGES') and self.config.MESSAGES:
                self.speak(random.choice(self.config.MESSAGES))
            else:
                self.speak("Hello there!")
        elif choice < walk_prob + talk_prob + sleep_prob:  # Chance to sleep
            self.animation_state = "sleep"
        else:  # Remainder chance to be idle
            self.animation_state = "idle"
            
        # Schedule next behavior change
        behavior_interval = 3000
        if hasattr(self.config, 'BEHAVIOR_INTERVAL'):
            behavior_interval = self.config.BEHAVIOR_INTERVAL
            
        self.behavior_timer = self.master.after(behavior_interval, self.random_behavior)
    
    def walk_randomly(self):
        """Make the pet walk in a random direction"""
        self.animation_state = "walk"
        
        # Decide direction
        if random.choice([True, False]):
            self.direction = "right"
            distance = random.randint(50, 150)
        else:
            self.direction = "left"
            distance = -random.randint(50, 150)
        
        # Calculate target position with screen boundaries
        current_x = self.master.winfo_x()
        current_y = self.master.winfo_y()
        target_x = current_x + distance
        
        # Check screen boundaries
        if target_x < 0:
            target_x = 0
            self.direction = "right"
        elif target_x > self.master.winfo_screenwidth() - self.width:
            target_x = self.master.winfo_screenwidth() - self.width
            self.direction = "left"
        
        # Set up walking animation
        steps = 20
        step_size = (target_x - current_x) / steps
        
        def move_step(step_count=0):
            if step_count < steps and self.animation_state == "walk":
                new_x = current_x + int(step_size * step_count)
                self.master.geometry(f"+{new_x}+{current_y}")
                self.master.after(50, lambda: move_step(step_count + 1))
            else:
                # Reset to idle when done walking
                if self.animation_state == "walk":
                    self.animation_state = "idle"
        
        # Start the walking animation
        move_step()
    
    def speak(self, message):
        """Display a speech bubble with text"""
        # Remove any existing speech bubble
        self.clear_speech()
        
        # Switch to talking animation
        old_state = self.animation_state
        self.animation_state = "talk"
        
        # Draw speech bubble
        bubble_x = 10
        bubble_y = 10
        
        # Draw the bubble background
        self.speech_bubble = self.canvas.create_rectangle(
            bubble_x, bubble_y, 
            bubble_x + self.width - 20, bubble_y + 30, 
            fill="white", outline="black", tags="speech"
        )
        
        # Add the text
        self.speech_text = self.canvas.create_text(
            bubble_x + (self.width - 20)//2, bubble_y + 15,
            text=message, fill="black", font=("Arial", 8), 
            width=self.width - 30, tags="speech"
        )
        
        # Schedule removal of speech bubble
        self.speech_timer = self.master.after(3000, lambda: self.clear_speech(old_state))
    
    def clear_speech(self, revert_state=None):
        """Clear the speech bubble"""
        # Remove the speech elements
        self.canvas.delete("speech")
        
        # Cancel any pending speech timers
        if self.speech_timer:
            self.master.after_cancel(self.speech_timer)
            self.speech_timer = None
            
        # Revert animation state if provided
        if revert_state and self.animation_state == "talk":
            self.animation_state = revert_state
    
    def on_mouse_press(self, event):
        """Handle mouse button press"""
        self.dragging = True
        self.drag_x = event.x
        self.drag_y = event.y
        
        # Cancel any pending focus reset
        if self.focus_timer:
            self.master.after_cancel(self.focus_timer)
            self.focus_timer = None
            
        # Speak occasionally when grabbed
        if random.random() < 0.3:
            self.speak("Where are we going?")
        
    def on_mouse_drag(self, event):
        """Handle mouse dragging"""
        if self.dragging:
            # Calculate new position
            x = self.master.winfo_x() + (event.x - self.drag_x)
            y = self.master.winfo_y() + (event.y - self.drag_y)
            
            # Keep on screen
            x = max(0, min(x, self.master.winfo_screenwidth() - self.width))
            y = max(0, min(y, self.master.winfo_screenheight() - self.height))
            
            # Move the window
            self.master.geometry(f"+{x}+{y}")
    
    def on_mouse_release(self, event):
        """Handle mouse button release"""
        self.dragging = False
        
        # Schedule a focus reset (This is a workaround that will "de-focus" the window after a short delay)
        self.focus_timer = self.master.after(100, self.reset_focus)
    
    def reset_focus(self):
        """Reset focus by triggering a keyboard event elsewhere"""
        # This is a hacky workaround - it creates a temporary window, focuses it, then destroys it
        # This can help in some X11 window managers
        temp = tk.Toplevel(self.master)
        temp.geometry("1x1+0+0")  # Tiny window
        temp.focus_force()
        self.master.after(50, temp.destroy)
        
        # Ensure pet window stays on top
        self.master.attributes('-topmost', False)
        self.master.attributes('-topmost', True)
        
        self.focus_timer = None
    
    def on_double_click(self, event):
        """Handle mouse double click"""
        self.speak("Double click! Edit pet_config.py to customize me!")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Desktop Pet")
    
    # Create pet
    pet = DesktopPet(root)
    
    # Start the main loop
    root.mainloop()
