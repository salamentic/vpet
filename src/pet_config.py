# Desktop Pet Configuration
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
        "idle": [(0, 6), (0, 7), (0, 6)],
        "walk": [(0, 3), (0, 4), (0, 5)],
        "talk": [(0, 6), (0, 7), (0, 8)],
        "sleep": [(0, 7), (0, 7), (0, 7)],
    }
    
    # Background color (used if TRANSPARENT_COLOR is None)
    BG_COLOR = "red"
    
    # Set this to make a specific color transparent
    # For your green spritesheet background, try:
    TRANSPARENT_COLOR = "white"  # Bright green
    # You can also use color names like "green" or other hex values
    
    # Pet dimensions (display size - will scale the sprites)
    WIDTH = 64
    HEIGHT = 64
    
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
