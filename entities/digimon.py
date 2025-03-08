"""
Digimon entity implementation for DigiPet application.
"""
import random
import time
from typing import Dict, Any, List, Optional, Tuple
import logging
from core.event_system import EventDispatcher, Event, EventType
from entities.base_entity import BaseEntity
from sprites.sprite_manager import SpriteManager

logger = logging.getLogger(__name__)

class Digimon(BaseEntity):
    """
    Digimon entity class.
    
    Attributes:
        digimon_type (str): The type of Digimon (e.g., 'Rookie', 'Champion')
        sprite_manager (SpriteManager): Manager for this Digimon's sprites
        stats (dict): Digimon statistics (e.g., health, energy)
        evolution_level (str): Current evolution level
        possible_evolutions (list): List of possible evolutions
        messages (list): List of possible messages this Digimon can say
    """
    
    def __init__(self, name: str, digimon_type: str, event_dispatcher: EventDispatcher,
                 sprite_manager: SpriteManager, position: Tuple[int, int] = (0, 0),
                 size: Tuple[int, int] = (100, 100), properties: Dict[str, Any] = None):
        """
        Initialize a Digimon entity.
        
        Args:
            name (str): The Digimon's name
            digimon_type (str): The type of Digimon (e.g., 'Rookie', 'Champion')
            event_dispatcher (EventDispatcher): The event dispatcher
            sprite_manager (SpriteManager): Manager for this Digimon's sprites
            position (tuple, optional): Initial position (x, y)
            size (tuple, optional): Digimon size (width, height)
            properties (dict, optional): Additional properties
        """
        super().__init__(name, event_dispatcher, position, size, properties)
        
        self.digimon_type = digimon_type
        self.sprite_manager = sprite_manager
        
        # Initialize stats with default values
        self.stats = {
            'health': 100,
            'energy': 100,
            'happiness': 100,
            'hunger': 0,
            'age': 0
        }
        
        # Digimon-specific properties
        self.evolution_level = properties.get('evolution_level', 'Rookie')
        self.possible_evolutions = properties.get('possible_evolutions', [])
        self.messages = properties.get('messages', [
            "Hello there!",
            "Need any help?",
            "I'm your desktop buddy!",
            "Don't forget to take breaks!",
            "What are you working on?",
            "Remember to stay hydrated!",
            "You're doing great!",
            "*yawns*"
        ])
        
        # Behavior properties
        self.behavior_timer = 0
        self.behavior_interval = properties.get('behavior_interval', 3000) / 1000.0  # Convert to seconds
        self.walk_probability = properties.get('walk_probability', 40)
        self.talk_probability = properties.get('talk_probability', 10)
        self.sleep_probability = properties.get('sleep_probability', 5)
        
        # Register for additional events
        self.event_dispatcher.register_listener(EventType.LLM_RESPONSE, self.handle_llm_response)
        
        logger.debug(f"Digimon '{name}' of type '{digimon_type}' initialized")
    
    def update(self, delta_time: float):
        """
        Update the Digimon's state based on elapsed time.
        
        Args:
            delta_time (float): Time elapsed since last update (in seconds)
        """
        # Update behavior timer
        self.behavior_timer += delta_time
        
        # Check if it's time for a random behavior (only if not dragging or walking)
        if self.behavior_timer >= self.behavior_interval and not self.dragging and self.current_state != "walk":
            self.behavior_timer = 0
            self._perform_random_behavior()
        
        # Update animation frame (every ~150ms for smooth animation)
        # Update stats over time
        self._update_stats(delta_time)
        
        # Advance animation frame every few frames for smoother animation
        if hasattr(self, '_animation_timer'):
            self._animation_timer += delta_time
            if self._animation_timer >= 0.15:  # 150ms between frame changes
                self._animation_timer = 0
                self.animation_frame = (self.animation_frame + 1) % 4
        else:
            self._animation_timer = 0
    
    def get_current_frame(self) -> Any:
        """
        Get the current animation frame for the Digimon.
        
        Returns:
            Any: The current sprite frame
        """
        # Get state and direction-specific frame
        state_key = f"{self.current_state}_{self.direction}"
        return self.sprite_manager.get_frame(state_key, self.animation_frame)
    
    def _perform_random_behavior(self):
        """Randomly select and perform a behavior based on probabilities."""
        choice = random.randint(1, 100)
        
        if choice <= self.walk_probability:
            # Walk in a random direction
            direction = random.choice(["left", "right"])
            self.event_dispatcher.dispatch_event(
                Event(EventType.START_WALK, self, {
                    'target': self.name,
                    'direction': direction
                })
            )
            
            # Similar to digi.py's walk_randomly method
            window_width, window_height = self.size
            sprite_width = 32  # Sprite width
            
            # Get current position
            current_x, current_y = self.position
            
            # Calculate max position that keeps sprite on screen
            max_x = window_width - sprite_width
            
            # Random distance between 30-80% of the screen width
            distance = random.randint(int(max_x * 0.3), int(max_x * 0.8))
            
            # Apply direction
            if direction == "left":
                distance = -distance
                
            # Calculate target position
            target_x = current_x + distance
            
            # Check screen boundaries
            if target_x < 0:
                target_x = 0
                self.set_direction("right")
            elif target_x > max_x:
                target_x = max_x
                self.set_direction("left")
                
            logger.debug(f"Walking from {current_x} to {target_x} (distance: {distance})")
            self._walk_to_position(target_x, current_y)
            
        elif choice <= self.walk_probability + self.talk_probability:
            # Say something random
            if self.messages:
                message = random.choice(self.messages)
                self.speak(message)
                
        elif choice <= self.walk_probability + self.talk_probability + self.sleep_probability:
            # Take a nap
            self.event_dispatcher.dispatch_event(
                Event(EventType.START_SLEEP, self, {
                    'target': self.name,
                    'duration': random.randint(3, 8)  # Sleep for 3-8 seconds
                })
            )
            
        else:
            # Default to idle
            self.event_dispatcher.dispatch_event(
                Event(EventType.START_IDLE, self, {
                    'target': self.name
                })
            )
    
    def _walk_to_position(self, target_x: int, target_y: int, steps: int = 20, step_time: int = 50):
        """
        Create a walking animation to move to a target position.
        Implemented similarly to digi.py using renderer's after method.
        
        Args:
            target_x (int): Target X coordinate
            target_y (int): Target Y coordinate
            steps (int): Number of steps to take
            step_time (int): Time between steps in milliseconds
        """
        # Calculate step size
        start_x, start_y = self.position
        
        # Set direction based on movement
        if target_x > start_x:
            self.set_direction("right")
        elif target_x < start_x:
            self.set_direction("left")
        
        # Tell the system we're starting to walk
        self.event_dispatcher.dispatch_event(
            Event(EventType.START_WALK, self, {
                'target': self.name,
                'direction': self.direction,
                'renderer_action': 'move_entity_step_by_step',
                'start_pos': (start_x, start_y),
                'target_pos': (target_x, target_y),
                'steps': steps,
                'step_time': step_time,
                'entity_id': id(self)
            })
        )
    
    def _update_stats(self, delta_time: float):
        """
        Update the Digimon's stats based on elapsed time.
        
        Args:
            delta_time (float): Time elapsed since last update (in seconds)
        """
        # Decrease energy while active
        if self.current_state in ["walk", "talk"]:
            self.stats["energy"] = max(0, self.stats["energy"] - 0.5 * delta_time)
        
        # Increase energy while sleeping
        if self.current_state == "sleep":
            self.stats["energy"] = min(100, self.stats["energy"] + 2 * delta_time)
        
        # Increase hunger over time
        self.stats["hunger"] = min(100, self.stats["hunger"] + 0.2 * delta_time)
        
        # Decrease happiness if hungry
        if self.stats["hunger"] > 70:
            self.stats["happiness"] = max(0, self.stats["happiness"] - 0.3 * delta_time)
        
        # Age increases over time (1 unit per minute)
        self.stats["age"] += delta_time / 60
    
    def feed(self, food_value: int = 20):
        """
        Feed the Digimon to reduce hunger.
        
        Args:
            food_value (int): How much to reduce hunger by
        """
        self.stats["hunger"] = max(0, self.stats["hunger"] - food_value)
        self.stats["happiness"] = min(100, self.stats["happiness"] + 5)
        
        # Say something about being fed
        self.speak("Yum! Thank you!")
    
    def play(self, fun_value: int = 15):
        """
        Play with the Digimon to increase happiness.
        
        Args:
            fun_value (int): How much to increase happiness by
        """
        self.stats["happiness"] = min(100, self.stats["happiness"] + fun_value)
        self.stats["energy"] = max(0, self.stats["energy"] - 10)
        
        # Say something about playing
        self.speak("That was fun!")
    
    def handle_llm_response(self, event: Event):
        """
        Handle LLM response events.
        
        Args:
            event (Event): The LLM response event
        """
        # Only handle events targeted at this entity
        if event.data.get('target') == self.name:
            # Extract message from LLM response
            message = event.data.get('message', "")
            if message:
                self.speak(message)
                
                # If the message includes an action, perform it
                actions = event.data.get('actions', [])
                for action in actions:
                    if action == 'feed':
                        self.feed()
                    elif action == 'play':
                        self.play()
                    # Add more actions as needed