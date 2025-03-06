"""
Sprite manager for DigiPet application.
Handles loading and managing sprite animations.
"""
import os
from typing import Dict, Any, List, Tuple, Optional
import logging
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)

class SpriteManager:
    """
    Manages sprite animations for entities.
    
    Attributes:
        sprite_path (str): Path to the sprite sheet
        sprite_size (tuple): Size of each sprite frame (width, height)
        display_size (tuple): Size to display sprites at (width, height)
        sprite_frames (dict): Dictionary of loaded animation frames
        sprite_counts (dict): Number of frames for each animation state
        transparent_color (str): Color to make transparent in sprites
    """
    
    def __init__(self, sprite_path: str, sprite_size: Tuple[int, int], 
                 display_size: Tuple[int, int] = None, 
                 transparent_color: str = None,
                 sprite_mapping: Dict[str, List[Tuple[int, int]]] = None):
        """
        Initialize the sprite manager.
        
        Args:
            sprite_path (str): Path to the sprite sheet
            sprite_size (tuple): Size of each sprite frame (width, height)
            display_size (tuple, optional): Size to display sprites at
            transparent_color (str, optional): Color to make transparent
            sprite_mapping (dict, optional): Mapping of states to frame coordinates
        """
        self.sprite_path = sprite_path
        self.sprite_size = sprite_size
        self.display_size = display_size or sprite_size
        self.transparent_color = transparent_color
        self.sprite_frames: Dict[str, List[Any]] = {}
        self.sprite_counts: Dict[str, int] = {}
        
        # Load sprite sheet if it exists and mapping is provided
        if os.path.exists(sprite_path) and sprite_mapping:
            self.load_sprites(sprite_mapping)
        else:
            logger.warning(f"Sprite sheet not found: {sprite_path} or no mapping provided")
    
    def load_sprites(self, sprite_mapping: Dict[str, List[Tuple[int, int]]]):
        """
        Load sprite animations from a sprite sheet.
        
        Args:
            sprite_mapping (dict): Mapping of animation states to frame coordinates
        """
        try:
            # Load the spritesheet
            spritesheet = Image.open(self.sprite_path)
            logger.debug(f"Loaded spritesheet: {self.sprite_path} ({spritesheet.width}x{spritesheet.height})")
            
            # Clear existing frames
            self.sprite_frames = {}
            
            # Extract frames based on the mapping
            for state, frames in sprite_mapping.items():
                # Create directional variants if needed
                if "_left" not in state and "_right" not in state:
                    self.sprite_frames[f"{state}_left"] = []
                    self.sprite_frames[f"{state}_right"] = []
                else:
                    self.sprite_frames[state] = []
                
                # Extract each frame
                for row, col in frames:
                    # Calculate position in spritesheet
                    width, height = self.sprite_size
                    x = col * width
                    y = row * height
                    
                    # Ensure position is within the spritesheet
                    if x + width <= spritesheet.width and y + height <= spritesheet.height:
                        # Extract the frame
                        frame = spritesheet.crop((x, y, x + width, y + height))
                        
                        # Resize if needed
                        if self.display_size != self.sprite_size:
                            frame = frame.resize(self.display_size, Image.LANCZOS)
                        
                        # Make transparent color transparent if specified
                        if self.transparent_color:
                            # Convert the image to RGBA if it's not already
                            if frame.mode != 'RGBA':
                                frame = frame.convert('RGBA')
                            
                            # Create a mask where transparent_color becomes transparent
                            data = frame.getdata()
                            new_data = []
                            for item in data:
                                # Check if this pixel matches the transparent color
                                if self._is_transparent_color(item, self.transparent_color):
                                    new_data.append((255, 255, 255, 0))  # Transparent
                                else:
                                    new_data.append(item)
                            frame.putdata(new_data)
                        
                        # Create PhotoImage for Tkinter
                        photo = ImageTk.PhotoImage(frame)
                        
                        # Add to the appropriate direction
                        if "_left" not in state and "_right" not in state:
                            # For normal states, create both left and right variants
                            self.sprite_frames[f"{state}_right"].append(photo)
                            # Create flipped version for left
                            flipped = frame.transpose(Image.FLIP_LEFT_RIGHT)
                            self.sprite_frames[f"{state}_left"].append(ImageTk.PhotoImage(flipped))
                        else:
                            # For directional states, add to that direction
                            self.sprite_frames[state].append(photo)
                    else:
                        logger.warning(f"Frame at row {row}, col {col} is outside spritesheet bounds")
                
                # Store the frame count for each animation
                if "_left" not in state and "_right" not in state:
                    self.sprite_counts[f"{state}_left"] = len(self.sprite_frames[f"{state}_left"])
                    self.sprite_counts[f"{state}_right"] = len(self.sprite_frames[f"{state}_right"])
                else:
                    self.sprite_counts[state] = len(self.sprite_frames[state])
                
                # Log how many frames were loaded
                if "_left" not in state and "_right" not in state:
                    logger.debug(f"Loaded {len(self.sprite_frames[f'{state}_left'])} frames for {state}_left")
                    logger.debug(f"Loaded {len(self.sprite_frames[f'{state}_right'])} frames for {state}_right")
                else:
                    logger.debug(f"Loaded {len(self.sprite_frames[state])} frames for {state}")
        
        except Exception as e:
            logger.error(f"Error loading sprites: {e}", exc_info=True)
            self.sprite_frames = {}
    
    def get_frame(self, state_key: str, frame_index: int) -> Optional[Any]:
        """
        Get a specific animation frame.
        
        Args:
            state_key (str): The animation state and direction (e.g., "idle_right")
            frame_index (int): The frame index
        
        Returns:
            Optional[Any]: The requested frame, or None if not found
        """
        if state_key in self.sprite_frames and self.sprite_frames[state_key]:
            # Use modulo to loop through available frames
            frames = self.sprite_frames[state_key]
            if frames:
                return frames[frame_index % len(frames)]
        return None
    
    def get_frame_count(self, state_key: str) -> int:
        """
        Get the number of frames for a specific animation state.
        
        Args:
            state_key (str): The animation state and direction (e.g., "idle_right")
        
        Returns:
            int: The number of frames, or 0 if state not found
        """
        return self.sprite_counts.get(state_key, 0)
    
    def _is_transparent_color(self, pixel, transparent_color: str) -> bool:
        """
        Check if a pixel matches the transparent color.
        
        Args:
            pixel: The pixel value
            transparent_color (str): The color to make transparent
        
        Returns:
            bool: True if the pixel should be transparent
        """
        # Handle hexadecimal color
        if transparent_color.startswith('#'):
            # Convert hex to RGB
            r = int(transparent_color[1:3], 16)
            g = int(transparent_color[3:5], 16)
            b = int(transparent_color[5:7], 16)
            
            # Check if pixel RGB values match within tolerance
            tolerance = 30  # Allow some variation in color matching
            if len(pixel) >= 3:
                pr, pg, pb = pixel[0], pixel[1], pixel[2]
                return (abs(pr - r) < tolerance and 
                        abs(pg - g) < tolerance and 
                        abs(pb - b) < tolerance)
        
        # Handle named colors (simplified - only exact matches for a few colors)
        elif transparent_color == "white":
            return pixel[0] > 240 and pixel[1] > 240 and pixel[2] > 240
        elif transparent_color == "black":
            return pixel[0] < 15 and pixel[1] < 15 and pixel[2] < 15
        elif transparent_color == "red":
            return pixel[0] > 230 and pixel[1] < 30 and pixel[2] < 30
        elif transparent_color == "green":
            return pixel[0] < 30 and pixel[1] > 230 and pixel[2] < 30
        elif transparent_color == "blue":
            return pixel[0] < 30 and pixel[1] < 30 and pixel[2] > 230
        elif transparent_color == "lightblue":
            return pixel[0] > 100 and pixel[0] < 180 and pixel[1] > 200 and pixel[2] > 230
        
        return False