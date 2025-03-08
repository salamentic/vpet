"""
Digimon entity implementation for DigiPet application.
"""
import random
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
        
        # Handle walking animation steps if we're currently walking
        if self._current_walk and self.current_state == "walk" and not self.dragging:
            current_time = time.time()
            if current_time - self._current_walk['last_step_time'] >= self._current_walk['step_time']:
                # Time for the next step in the walking animation
                self._current_walk['last_step_time'] = current_time
                
                # Calculate current position
                start_x, start_y = self._current_walk['start_pos']
                target_x, target_y = self._current_walk['target_pos']
                steps = self._current_walk['steps']
                step_index = self._current_walk['step_index']
                
                # Linear interpolation between start and target position
                progress = min(1.0, (step_index + 1) / steps)
                new_x = start_x + (target_x - start_x) * progress
                new_y = start_y + (target_y - start_y) * progress
                
                # Update position
                self.set_position(int(new_x), int(new_y))
                
                # Update step index
                self._current_walk['step_index'] += 1
                
                # If we've finished all steps, clear the walk data
                if self._current_walk['step_index'] >= steps:
                    logger.debug(f"Walk animation completed: arrived at {self.position}")
                    self._current_walk = None
                    # Return to idle state when walking is complete
                    if self.current_state == "walk":
                        self.set_state("idle")
        
        # Check if it's time for a random behavior
        elif self.behavior_timer >= self.behavior_interval and not self.dragging and not self._current_walk:
            self.behavior_timer = 0
            self._perform_random_behavior()
        
        # Update stats over time
        self._update_stats(delta_time)
    
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
            
            # Calculate random distance to walk based on window size
            window_width, window_height = self.size
            max_distance = min(100, window_width // 2)  # Limit walk distance to half the window width
            distance = random.randint(20, max_distance)
            if direction == "left":
                distance = -distance
            
            # Dispatch move event with target position
            x, y = self.position
            target_x = max(0, min(x + distance, window_width - 32))  # 32 is approximate sprite width
            
            # If we hit a boundary, change direction
            if target_x <= 0:
                self.set_direction("right")
            elif target_x >= window_width - 32:
                self.set_direction("left")
            
            self._walk_to_position(target_x, y)
            
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
    
    def _walk_to_position(self, target_x: int, target_y: int, steps: int = 20, step_time: float = 0.05):
        """
        Create a walking animation to move to a target position.
        
        Args:
            target_x (int): Target X coordinate
            target_y (int): Target Y coordinate
            steps (int): Number of steps to take
            step_time (float): Time between steps in seconds
        """
        # Calculate step size
        start_x, start_y = self.position
        dx = (target_x - start_x) / steps
        
        # Set direction based on movement
        if dx > 0:
            self.set_direction("right")
        elif dx < 0:
            self.set_direction("left")
        
        # Create walk event with animation data
        self.event_dispatcher.dispatch_event(
            Event(EventType.START_WALK, self, {
                'target': self.name,
                'start_pos': (start_x, start_y),
                'target_pos': (target_x, target_y),
                'steps': steps,
                'step_time': step_time,
                'step_index': 0
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