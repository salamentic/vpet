# digi.py Documentation

`digi.py` is the core implementation of the DigiPet desktop application. It provides a simple but effective virtual pet that lives on your desktop with various animations and interactive behaviors.

## Overview

The application creates a virtual pet that:
- Follows a customizable spritesheet-based animation system
- Demonstrates different behaviors (idle, walking, talking, sleeping)
- Responds to user interactions (dragging, clicking, double-clicking)
- Features speech bubbles for communication
- Supports hot-reloading of configuration files for real-time customization

## Class Structure

### PetConfig

Default configuration class that defines the pet's appearance and behavior:

- **Spritesheet Settings**: Paths and dimensions for sprite animations
- **Animation Frames**: Mapping of visual states to spritesheet coordinates
- **Window Properties**: Size, colors, transparency
- **Behavior Parameters**: Probabilities for different actions
- **Messages**: Text the pet can display in speech bubbles

### DesktopPet

Main class that manages the pet's functionality:

- **Initialization**: Sets up window, canvas, and event bindings
- **Sprite Management**: Loads and displays animations from spritesheets
- **Configuration Management**: Includes hot-reloading capabilities
- **Behavior System**: Random behaviors with configurable probabilities
- **Interaction Handling**: Mouse events for dragging and clicking
- **Animation System**: Frame-by-frame sprite animation
- **Speech System**: Display and manage speech bubbles

## Key Features

### Hot-Reloading Configuration

The application watches for changes to `pet_config.py` and automatically applies changes without requiring a restart:

1. A background thread continuously monitors the config file for changes
2. When changes are detected, the application reloads the configuration
3. UI elements and behaviors update immediately based on new settings

### Spritesheet Animation

The pet uses a flexible spritesheet system:

- Loads sprite frames from an image file based on configured coordinates
- Supports directional animations (left/right facing)
- Handles multiple animation states (idle, walk, talk, sleep)
- Falls back to simple shape drawing if spritesheet loading fails

### Random Behaviors

The pet demonstrates autonomous behaviors:

- Randomly selects actions based on configurable probabilities
- Walking: Moves across the screen in random directions
- Talking: Displays random messages in speech bubbles
- Sleeping: Shows a sleeping animation
- Idle: Default state when no other actions are occurring

### User Interaction

Supports several forms of user interaction:

- **Drag and Drop**: Click and drag to move the pet around the screen
- **Double-Click**: Triggers special messages from the pet
- **Config Editing**: Edit the config file for immediate customization

## Configuration Options

The `pet_config.py` file provides extensive customization options:

### Spritesheet Configuration
```python
# Spritesheet settings
USE_SPRITESHEET = True
SPRITESHEET_PATH = "pet_sprites.png"
SPRITE_WIDTH = 32
SPRITE_HEIGHT = 32
```

### Animation Mapping
```python
# Maps animation states to sprite coordinates
SPRITE_MAPPING = {
    "idle": [(0, 0), (0, 1), (0, 2), (0, 3)],
    "walk": [(0, 4), (0, 5), (0, 6), (0, 7)],
    # ... other states
}
```

### Appearance
```python
# Window and background settings
BG_COLOR = "lightblue"
TRANSPARENT_COLOR = "lightblue"  # Set to make a color transparent
WIDTH = 120  # Window width
HEIGHT = 120  # Window height
```

### Behavior Configuration
```python
# Timing and probability settings
ANIMATION_SPEED = 150  # ms between frames
BEHAVIOR_INTERVAL = 3000  # ms between behavior changes

# Behavior probabilities (percent)
WALK_PROBABILITY = 40
TALK_PROBABILITY = 10
SLEEP_PROBABILITY = 5
# Idle probability is the remainder
```

### Customizable Messages
```python
# Messages the pet can say
MESSAGES = [
    "Hello there!",
    "Need any help?",
    # ... other messages
]
```

## Usage

To run the application:

```bash
python src/digi.py
```

## Implementation Notes

1. **Window Management**:
   - Uses Tkinter for window creation and canvas rendering
   - Applies transparency for a seamless desktop experience
   - Maintains "always on top" property to keep pet visible

2. **Error Handling**:
   - Gracefully falls back to simple shape rendering if sprite loading fails
   - Error messages are printed to console for troubleshooting
   - Creates default configuration file if none exists

3. **Focus Management**:
   - Implements special handling to avoid stealing focus from other applications
   - Creates temporary workarounds for X11 window managers

4. **Mobile Limitations**:
   - The implementation is designed for desktop environments
   - Not suitable for mobile deployment due to Tkinter dependencies

## Extending the Pet

To create custom pets:
1. Replace the spritesheet with your own pet graphics
2. Adjust the `SPRITE_MAPPING` to match your spritesheet's layout
3. Customize the `MESSAGES` to fit your pet's personality
4. Adjust behavior probabilities to create different pet temperaments

## Future Improvement Areas

Potential areas for enhancement:
- Additional animation states and behaviors
- Sound effects for different actions
- More extensive user interaction options
- Plugin system for custom behaviors
- State persistence between sessions