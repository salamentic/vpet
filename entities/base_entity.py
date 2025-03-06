"""
Base entity module for DigiPet application.
Provides an abstract base class for all entities in the system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import logging
from core.event_system import EventDispatcher, Event, EventType

logger = logging.getLogger(__name__)

class BaseEntity(ABC):
    """
    Abstract base class for all entities.
    
    Attributes:
        name (str): The entity's name
        current_state (str): The entity's current state
        position (tuple): The entity's current position (x, y)
        size (tuple): The entity's size (width, height)
        properties (dict): Additional properties for the entity
        event_dispatcher (EventDispatcher): The event dispatcher
    """
    
    def __init__(self, name: str, event_dispatcher: EventDispatcher, 
                 position: Tuple[int, int] = (0, 0), 
                 size: Tuple[int, int] = (100, 100),
                 properties: Dict[str, Any] = None):
        """
        Initialize a base entity.
        
        Args:
            name (str): The entity's name
            event_dispatcher (EventDispatcher): The event dispatcher
            position (tuple, optional): Initial position (x, y)
            size (tuple, optional): Entity size (width, height)
            properties (dict, optional): Additional properties
        """
        self.name = name
        self.current_state = "idle"
        self.position = position
        self.size = size
        self.properties = properties or {}
        self.event_dispatcher = event_dispatcher
        self.direction = "right"  # Default direction
        self.animation_frame = 0
        self.dragging = False
        
        # Register for events
        self._register_event_handlers()
        
        logger.debug(f"Entity '{name}' initialized at position {position}")
    
    def _register_event_handlers(self):
        """Register for the events this entity is interested in."""
        self.event_dispatcher.register_listener(EventType.MOUSE_CLICK, self.handle_mouse_click)
        self.event_dispatcher.register_listener(EventType.MOUSE_DRAG, self.handle_mouse_drag)
        self.event_dispatcher.register_listener(EventType.MOUSE_RELEASE, self.handle_mouse_release)
        self.event_dispatcher.register_listener(EventType.MOUSE_DOUBLE_CLICK, self.handle_mouse_double_click)
        self.event_dispatcher.register_listener(EventType.ANIMATION_FRAME, self.handle_animation_frame)
        
        # Register for behavior change events
        self.event_dispatcher.register_listener(EventType.START_IDLE, self.handle_state_change)
        self.event_dispatcher.register_listener(EventType.START_WALK, self.handle_state_change)
        self.event_dispatcher.register_listener(EventType.START_TALK, self.handle_state_change)
        self.event_dispatcher.register_listener(EventType.START_SLEEP, self.handle_state_change)
    
    def set_state(self, new_state: str):
        """
        Change the entity's state and dispatch an event.
        
        Args:
            new_state (str): The new state to transition to
        """
        if new_state != self.current_state:
            old_state = self.current_state
            self.current_state = new_state
            
            # Reset animation frame on state change
            self.animation_frame = 0
            
            # Dispatch state changed event
            self.event_dispatcher.dispatch_event(
                Event(EventType.STATE_CHANGED, self, {
                    'old_state': old_state,
                    'new_state': new_state
                })
            )
            logger.debug(f"Entity '{self.name}' changed state from '{old_state}' to '{new_state}'")
    
    def set_position(self, x: int, y: int):
        """
        Set the entity's position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        self.position = (x, y)
    
    def move(self, dx: int, dy: int):
        """
        Move the entity by the specified amount.
        
        Args:
            dx (int): Change in x coordinate
            dy (int): Change in y coordinate
        """
        x, y = self.position
        self.position = (x + dx, y + dy)
    
    def set_direction(self, direction: str):
        """
        Set the direction the entity is facing.
        
        Args:
            direction (str): The direction ("left" or "right")
        """
        if direction in ["left", "right"] and direction != self.direction:
            self.direction = direction
    
    def speak(self, message: str, duration: int = 3000):
        """
        Make the entity speak a message.
        
        Args:
            message (str): The message to speak
            duration (int, optional): How long to show the message (ms)
        """
        # Change to talking state
        self.set_state("talk")
        
        # Dispatch speak event
        self.event_dispatcher.dispatch_event(
            Event(EventType.SPEAK, self, {
                'message': message,
                'duration': duration
            })
        )
        logger.debug(f"Entity '{self.name}' speaking: '{message}'")
    
    def handle_mouse_click(self, event: Event):
        """
        Handle mouse click events.
        
        Args:
            event (Event): The mouse click event
        """
        # Only handle events within our bounds
        if not self._is_point_inside(event.data.get('x', 0), event.data.get('y', 0)):
            return
        
        self.dragging = True
        
        # You can respond to clicks here
        logger.debug(f"Entity '{self.name}' clicked")
    
    def handle_mouse_drag(self, event: Event):
        """
        Handle mouse drag events.
        
        Args:
            event (Event): The mouse drag event
        """
        if not self.dragging:
            return
        
        # Update position based on drag
        dx = event.data.get('dx', 0)
        dy = event.data.get('dy', 0)
        self.move(dx, dy)
        
        logger.debug(f"Entity '{self.name}' dragged to {self.position}")
    
    def handle_mouse_release(self, event: Event):
        """
        Handle mouse release events.
        
        Args:
            event (Event): The mouse release event
        """
        self.dragging = False
        logger.debug(f"Entity '{self.name}' released")
    
    def handle_mouse_double_click(self, event: Event):
        """
        Handle mouse double-click events.
        
        Args:
            event (Event): The mouse double-click event
        """
        # Only handle events within our bounds
        if not self._is_point_inside(event.data.get('x', 0), event.data.get('y', 0)):
            return
        
        # Example: Speak a greeting on double-click
        self.speak("Hello there!")
        logger.debug(f"Entity '{self.name}' double-clicked")
    
    def handle_animation_frame(self, event: Event):
        """
        Handle animation frame events.
        
        Args:
            event (Event): The animation frame event
        """
        # Increment animation frame counter
        self.animation_frame += 1
    
    def handle_state_change(self, event: Event):
        """
        Handle state change events.
        
        Args:
            event (Event): The state change event
        """
        # Only respond to events targeted at this entity
        if event.data.get('target') == self.name:
            if event.event_type == EventType.START_IDLE:
                self.set_state("idle")
            elif event.event_type == EventType.START_WALK:
                self.set_state("walk")
                # Update direction if specified
                if 'direction' in event.data:
                    self.set_direction(event.data['direction'])
            elif event.event_type == EventType.START_TALK:
                self.set_state("talk")
            elif event.event_type == EventType.START_SLEEP:
                self.set_state("sleep")
    
    def _is_point_inside(self, x: int, y: int) -> bool:
        """
        Check if a point is inside the entity's bounds.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        
        Returns:
            bool: True if the point is inside, False otherwise
        """
        entity_x, entity_y = self.position
        width, height = self.size
        
        return (entity_x <= x <= entity_x + width and 
                entity_y <= y <= entity_y + height)
    
    @abstractmethod
    def update(self, delta_time: float):
        """
        Update the entity's state based on elapsed time.
        
        Args:
            delta_time (float): Time elapsed since last update (in seconds)
        """
        pass
    
    @abstractmethod
    def get_current_frame(self) -> Any:
        """
        Get the current animation frame for the entity.
        
        Returns:
            Any: The current animation frame (implementation-dependent)
        """
        pass