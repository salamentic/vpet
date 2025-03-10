"""
Tkinter renderer implementation for DigiPet application.
"""
import tkinter as tk
from typing import Dict, Any, Optional, List, Tuple
import logging
import time
from core.event_system import EventDispatcher, Event, EventType
from renderers.base_renderer import BaseRenderer

logger = logging.getLogger(__name__)

class SpeechBubble:
    """
    Helper class to manage speech bubble display.
    
    Attributes:
        canvas (tk.Canvas): The canvas to draw on
        entity: The entity speaking
        message (str): The message being displayed
        bubble_id: Canvas ID for the bubble shape
        text_id: Canvas ID for the text
        timer: Timer for auto-removal
        duration (int): How long to display the bubble (ms)
    """
    
    def __init__(self, canvas: tk.Canvas, entity, message: str, duration: int = 3000):
        """
        Initialize a speech bubble.
        
        Args:
            canvas (tk.Canvas): The canvas to draw on
            entity: The entity speaking
            message (str): The message to display
            duration (int, optional): How long to show the bubble (ms)
        """
        self.canvas = canvas
        self.entity = entity
        self.message = message
        self.bubble_id = None
        self.text_id = None
        self.timer = None
        self.duration = duration
        
        # Draw the bubble
        self._draw_bubble()
    
    def _draw_bubble(self):
        """Draw the speech bubble on the canvas."""
        # Calculate position above the entity
        entity_x, entity_y = self.entity.position
        
        # Try to get actual entity dimensions from sprite
        entity_width, entity_height = 32, 32  # Default fallback
        try:
            # Get current frame if available
            current_frame = self.entity.get_current_frame()
            if current_frame:
                if hasattr(current_frame, 'width') and hasattr(current_frame, 'height'):
                    entity_width = current_frame.width()
                    entity_height = current_frame.height()
        except:
            pass
        
        # Bubble dimensions and position - make it proportional to entity size
        bubble_width = min(120, max(80, entity_width * 3))
        bubble_height = 30
        
        # Position bubble directly above sprite with minimal gap
        bubble_x = entity_x + entity_width // 2 - bubble_width // 2
        bubble_y = entity_y - bubble_height - 5  # Only 5px gap for closer positioning
        
        # Ensure bubble is on screen
        bubble_x = max(5, min(bubble_x, self.canvas.winfo_width() - bubble_width - 5))
        bubble_y = max(5, bubble_y)
        
        # Draw bubble with rounded corners
        self.bubble_id = self.canvas.create_rectangle(
            bubble_x, bubble_y,
            bubble_x + bubble_width, bubble_y + bubble_height,
            fill="white", outline="black", width=1,
            tags=f"speech_{id(self.entity)}"
        )
        
        # Add small triangle pointing to entity
        pointer_x = entity_x + entity_width // 2
        pointer_y = bubble_y + bubble_height
        
        self.canvas.create_polygon(
            pointer_x - 10, pointer_y,
            pointer_x, pointer_y + 10,
            pointer_x + 10, pointer_y,
            fill="white", outline="black", width=1,
            tags=f"speech_{id(self.entity)}"
        )
        
        # Add text with bigger font and better formatting
        self.text_id = self.canvas.create_text(
            bubble_x + bubble_width // 2,
            bubble_y + bubble_height // 2,
            text=self.message,
            font=("Arial", 9, "bold"),  # Slightly bigger, bold font
            width=bubble_width - 10,
            fill="black",
            justify="center",  # Center-align text
            tags=f"speech_{id(self.entity)}"
        )
    
    def clear(self):
        """Remove the speech bubble from the canvas."""
        try:
            if self.timer:
                self.canvas.after_cancel(self.timer)
                self.timer = None
            
            self.canvas.delete(f"speech_{id(self.entity)}")
            
            self.bubble_id = None
            self.text_id = None
            logger.debug(f"Speech bubble cleared for {self.entity.name}")
        except Exception as e:
            logger.error(f"Error clearing speech bubble: {e}")
            # Make sure we don't leave stray tags on the canvas
            try:
                self.canvas.delete(f"speech_{id(self.entity)}")
            except:
                pass
    
    def set_auto_clear(self, master):
        """
        Set the bubble to automatically clear after duration.
        
        Args:
            master: The Tkinter master widget for scheduling
        """
        self.timer = master.after(self.duration, self.clear)


class TkinterRenderer(BaseRenderer):
    """
    Tkinter-based renderer implementation.
    
    Attributes:
        master (tk.Tk): The Tkinter root window
        canvas (tk.Canvas): The canvas for drawing
        is_dragging (bool): Whether dragging is in progress
        drag_data (dict): Data about the current drag operation
        speech_bubbles (dict): Active speech bubbles by entity
        animation_timer: Timer for animation updates
        close_button: Button to close the application
        minimize_button: Button to minimize the window
    """
    
    def __init__(self, width: int, height: int, event_dispatcher: EventDispatcher,
                 bg_color: str = "white", transparent_color: Optional[str] = None,
                 title: str = "DigiPet"):
        """
        Initialize the Tkinter renderer.
        
        Args:
            width (int): Width of the window
            height (int): Height of the window
            event_dispatcher (EventDispatcher): The event dispatcher
            bg_color (str, optional): Background color
            transparent_color (str, optional): Color to make transparent
            title (str, optional): Window title
        """
        super().__init__(width, height, event_dispatcher, bg_color, transparent_color)
        
        # Tkinter-specific attributes
        self.master = None
        self.canvas = None
        self.is_dragging = False
        self.drag_data = {"x": 0, "y": 0, "entity": None}
        self.speech_bubbles = {}
        self.animation_timer = None
        self.close_button = None
        self.minimize_button = None
        self.title = title
        
        # Animation timing
        self.animation_speed = 150  # ms between frames
        self.last_frame_time = 0
        
        logger.debug(f"Tkinter renderer created with size ({width}x{height})")
    
    def initialize(self):
        """Initialize the Tkinter window and canvas."""
        # Create Tkinter root if it doesn't exist
        if not self.master:
            self.master = tk.Tk()
            self.master.title(self.title)
        
        # Configure the window
        self.master.geometry(f"{self.master.winfo_screenwidth()}x{self.master.winfo_screenheight()}")
        self.master.overrideredirect(True)  # No window borders
        self.master.attributes('-topmost', True)  # Always on top
        
        # Set transparency if specified
        if self.transparent_color:
            try:
                self.master.wm_attributes('-transparentcolor', self.transparent_color)
            except Exception as e:
                logger.error(f"Error setting transparency: {e}")
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.master,
            width=self.width,
            height=self.height,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add control buttons
        button_size = 20
        button_margin = 2
        
        # Close button
        self.close_button = tk.Button(
            self.master,
            text="✕",
            command=self.handle_close,
            font=("Arial", 8),
            bg="red",
            fg="white",
            width=1,
            height=1,
            relief=tk.FLAT
        )
        self.close_button.place(
            x=self.width - button_size - button_margin,
            y=button_margin,
            width=button_size,
            height=button_size
        )
        
        # Minimize button
        self.minimize_button = tk.Button(
            self.master,
            text="_",
            command=self.handle_minimize,
            font=("Arial", 8),
            bg="gray",
            fg="white",
            width=1,
            height=1,
            relief=tk.FLAT
        )
        self.minimize_button.place(
            x=self.width - 2*button_size - 2*button_margin,
            y=button_margin,
            width=button_size,
            height=button_size
        )
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        
        # Start animation timer
        self.schedule_animation()
        
        logger.debug("Tkinter renderer initialized")
        
        return self.master
    
    def render(self):
        """Render all entities on the canvas."""
        # Clear canvas (except controls and speech bubbles)
        self.canvas.delete("entity")
        
        # Draw each entity
        for entity in self.entities:
            # Get current frame
            frame = entity.get_current_frame()
            
            if frame:
                # Draw the sprite
                self.canvas.create_image(
                    entity.position[0] + entity.size[0] // 2,
                    entity.position[1] + entity.size[1] // 2,
                    image=frame,
                    tags=f"entity entity_{id(entity)}"
                )
            else:
                # Fallback: draw a rectangle if no sprite available
                self.canvas.create_rectangle(
                    entity.position[0],
                    entity.position[1],
                    entity.position[0] + entity.size[0],
                    entity.position[1] + entity.size[1],
                    fill="blue",
                    tags=f"entity entity_{id(entity)}"
                )
        
        # Update speech bubble positions if entities have moved
        entities_to_update = list(self.speech_bubbles.keys())  # Create a copy to avoid modification during iteration
        for entity in entities_to_update:
            if entity in self.speech_bubbles and self.speech_bubbles[entity]:
                try:
                    bubble = self.speech_bubbles[entity]
                    message = bubble.message
                    duration = bubble.duration
                    
                    # Delete and redraw if the entity has moved
                    bubble.clear()
                    
                    # Create a new speech bubble at the updated position
                    self.speech_bubbles[entity] = SpeechBubble(
                        self.canvas, entity, message, duration
                    )
                    self.speech_bubbles[entity].set_auto_clear(self.master)
                except Exception as e:
                    logger.error(f"Error updating speech bubble: {e}")
                    if entity in self.speech_bubbles:
                        del self.speech_bubbles[entity]
        
        # Update the window
        self.master.update_idletasks()
    
    def cleanup(self):
        """Clean up resources when shutting down."""
        if self.animation_timer:
            self.master.after_cancel(self.animation_timer)
            self.animation_timer = None
        
        if self.master:
            self.master.destroy()
            self.master = None
        
        logger.debug("Tkinter renderer cleaned up")
    
    def convert_input_event(self, event_data: Dict[str, Any]) -> Optional[Event]:
        """
        Convert Tkinter events to system events.
        
        Args:
            event_data (dict): Tkinter event data
        
        Returns:
            Optional[Event]: Converted system event, or None if not relevant
        """
        event_type = event_data.get("type")
        
        if event_type == "mouse_press":
            return Event(EventType.MOUSE_CLICK, self, {
                "x": event_data.get("x", 0),
                "y": event_data.get("y", 0),
                "button": event_data.get("button", 1)
            })
        elif event_type == "mouse_drag":
            return Event(EventType.MOUSE_DRAG, self, {
                "x": event_data.get("x", 0),
                "y": event_data.get("y", 0),
                "dx": event_data.get("dx", 0),
                "dy": event_data.get("dy", 0)
            })
        elif event_type == "mouse_release":
            return Event(EventType.MOUSE_RELEASE, self, {
                "x": event_data.get("x", 0),
                "y": event_data.get("y", 0)
            })
        elif event_type == "double_click":
            return Event(EventType.MOUSE_DOUBLE_CLICK, self, {
                "x": event_data.get("x", 0),
                "y": event_data.get("y", 0)
            })
        
        return None
    
    def handle_speak_event(self, event: Event):
        """
        Handle speak events to display speech bubbles.
        
        Args:
            event (Event): The speak event
        """
        entity = event.source
        message = event.data.get('message', '')
        
        # Use longer duration (5000ms = 5 seconds) for better readability
        duration = event.data.get('duration', 5000)
        
        # Clear any existing speech bubble for this entity
        if entity in self.speech_bubbles and self.speech_bubbles[entity]:
            self.speech_bubbles[entity].clear()
        
        # Create new speech bubble
        self.speech_bubbles[entity] = SpeechBubble(
            self.canvas, entity, message, duration
        )
        
        # Set auto-clear timer
        self.speech_bubbles[entity].set_auto_clear(self.master)
    
    def handle_stop_speaking_event(self, event: Event):
        """
        Handle stop speaking events to remove speech bubbles.
        
        Args:
            event (Event): The stop speaking event
        """
        entity = event.source
        
        # Clear the speech bubble for this entity
        if entity in self.speech_bubbles and self.speech_bubbles[entity]:
            self.speech_bubbles[entity].clear()
            del self.speech_bubbles[entity]
    
    def handle_walk_event(self, event: Event):
        """
        Handle walk events to animate entity movement.
        
        Args:
            event (Event): The walk event
        """
        super().handle_walk_event(event)
        
        # Check if this is a movement event that requires renderer action
        if 'renderer_action' in event.data and event.data['renderer_action'] == 'move_entity_step_by_step':
            entity = event.source
            start_pos = event.data.get('start_pos')
            target_pos = event.data.get('target_pos')
            steps = event.data.get('steps', 20)
            step_time = event.data.get('step_time', 50)  # milliseconds
            
            # Start the step-by-step movement animation similar to digi.py
            self._move_entity_steps(entity, start_pos, target_pos, steps, step_time)
    
    def _move_entity_steps(self, entity, start_pos, target_pos, steps=25, step_time=20, step_count=0):
        """
        Animate entity movement in steps, similar to the digi.py implementation.
        Default values changed to: 25 steps at 20ms intervals for smoother animation.
        
        Args:
            entity: Entity to move
            start_pos: Starting position (x, y)
            target_pos: Target position (x, y)
            steps: Total number of steps
            step_time: Time between steps (ms)
            step_count: Current step number
        """
        if step_count < steps and entity.current_state == "walk":
            # Calculate new position using linear interpolation
            start_x, start_y = start_pos
            target_x, target_y = target_pos
            
            # Calculate progress (0.0 to 1.0)
            progress = (step_count + 1) / steps
            
            # Calculate new position
            new_x = start_x + (target_x - start_x) * progress
            new_y = start_y + (target_y - start_y) * progress
            
            # Update entity position
            entity.set_position(int(new_x), int(new_y))
            
            # Increment animation frame for walking (every 4 steps for smoother animation)
            if step_count % 4 == 0:
                entity.animation_frame = (entity.animation_frame + 1) % 4
            
            # Update the rendering
            self.render()
            
            # Add small bounce effect (only during active walking, not at beginning/end)
            if 5 < step_count < (steps - 5):
                if step_count % 4 == 0:
                    bounce = 1
                    self.master.geometry(f"+{self.master.winfo_x()}+{self.master.winfo_y() - bounce}")
                elif step_count % 4 == 2:
                    self.master.geometry(f"+{self.master.winfo_x()}+{self.master.winfo_y() + 1}")
            
            # Schedule next step with direct reference to avoid lambda overhead
            next_step = step_count + 1
            self.master.after(step_time, 
                lambda e=entity, s_pos=start_pos, t_pos=target_pos, s=steps, st=step_time, sc=next_step: 
                self._move_entity_steps(e, s_pos, t_pos, s, st, sc))
        else:
            # When walking is done, reset to idle state
            if entity.current_state == "walk":
                entity.set_state("idle")
                logger.debug(f"Entity {entity.name} finished walking, now idle")
                
                # Ensure we're at the exact target position
                entity.set_position(int(target_pos[0]), int(target_pos[1]))
    
    def handle_config_changed(self, event: Event):
        """
        Handle configuration change events.
        
        Args:
            event (Event): The configuration changed event
        """
        # Call parent handler
        super().handle_config_changed(event)
        
        # Update window if size changed
        if 'width' in event.data and 'height' in event.data:
            self.master.geometry(f"{self.width}x{self.height}")
            self.canvas.config(width=self.width, height=self.height)
            
            # Reposition buttons
            button_size = 20
            button_margin = 2
            
            self.close_button.place(
                x=self.width - button_size - button_margin,
                y=button_margin,
                width=button_size,
                height=button_size
            )
            
            self.minimize_button.place(
                x=self.width - 2*button_size - 2*button_margin,
                y=button_margin,
                width=button_size,
                height=button_size
            )
        
        # Update canvas background
        if 'bg_color' in event.data:
            self.canvas.config(bg=self.bg_color)
        
        # Update transparency
        if 'transparent_color' in event.data and self.transparent_color:
            try:
                self.master.wm_attributes('-transparentcolor', self.transparent_color)
            except Exception as e:
                logger.error(f"Error setting transparency: {e}")
        
        # Update animation speed if specified
        if 'animation_speed' in event.data:
            self.animation_speed = event.data['animation_speed']
    
    def handle_close(self):
        """Handle close button click."""
        # Dispatch shutdown event
        self.event_dispatcher.dispatch_event(
            Event(EventType.SHUTDOWN, self)
        )
        
        # Clean up resources
        self.cleanup()
    
    def handle_minimize(self):
        """Handle minimize button click."""
        self.master.iconify()
    
    def schedule_animation(self):
        """Schedule the next animation frame update."""
        if self.animation_timer:
            self.master.after_cancel(self.animation_timer)
        
        self.animation_timer = self.master.after(
            self.animation_speed, self.update_animation
        )
    
    def update_animation(self):
        """Update animation frames and render."""
        current_time = time.time()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        # Dispatch animation frame event
        self.event_dispatcher.dispatch_event(
            Event(EventType.ANIMATION_FRAME, self, {
                'delta_time': delta_time
            })
        )
        
        # Update entities
        for entity in self.entities:
            entity.update(delta_time)
        
        # Render updated state
        self.render()
        
        # Schedule next frame
        self.schedule_animation()
    
    def on_mouse_press(self, event):
        """
        Handle mouse press events.
        
        Args:
            event: Tkinter mouse event
        """
        # Convert Tkinter event to system event
        system_event = self.convert_input_event({
            "type": "mouse_press",
            "x": event.x,
            "y": event.y,
            "button": event.num
        })
        
        if system_event:
            # Find which entity was clicked, if any
            clicked_entity = None
            for entity in reversed(self.entities):  # Reverse to check top entities first
                if self._is_point_in_entity(event.x, event.y, entity):
                    clicked_entity = entity
                    break
            
            # Store drag data
            self.drag_data = {
                "x": event.x,
                "y": event.y,
                "entity": clicked_entity
            }
            
            if clicked_entity:
                # Add entity to event data
                system_event.data["entity"] = clicked_entity
                self.is_dragging = True
            
            # Dispatch the event
            self.event_dispatcher.dispatch_event(system_event)
    
    def on_mouse_drag(self, event):
        """
        Handle mouse drag events.
        
        Args:
            event: Tkinter mouse event
        """
        if not self.is_dragging:
            return
        
        # Calculate distance moved
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        # Update drag origin
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        
        # Convert to system event
        system_event = self.convert_input_event({
            "type": "mouse_drag",
            "x": event.x,
            "y": event.y,
            "dx": dx,
            "dy": dy
        })
        
        if system_event and self.drag_data["entity"]:
            # Add entity to event data
            system_event.data["entity"] = self.drag_data["entity"]
            
            # Dispatch the event
            self.event_dispatcher.dispatch_event(system_event)
            
            # Update entity position directly for smoother dragging
            entity = self.drag_data["entity"]
            x, y = entity.position
            entity.set_position(x + dx, y + dy)
            
            # Trigger render to update display
            self.render()
    
    def on_mouse_release(self, event):
        """
        Handle mouse release events.
        
        Args:
            event: Tkinter mouse event
        """
        if not self.is_dragging:
            return
        
        # Convert to system event
        system_event = self.convert_input_event({
            "type": "mouse_release",
            "x": event.x,
            "y": event.y
        })
        
        if system_event and self.drag_data["entity"]:
            # Add entity to event data
            system_event.data["entity"] = self.drag_data["entity"]
            
            # Dispatch the event
            self.event_dispatcher.dispatch_event(system_event)
        
        # Reset dragging state
        self.is_dragging = False
        self.drag_data = {"x": 0, "y": 0, "entity": None}
    
    def on_double_click(self, event):
        """
        Handle mouse double click events.
        
        Args:
            event: Tkinter mouse event
        """
        # Find which entity was clicked, if any
        clicked_entity = None
        for entity in reversed(self.entities):  # Reverse to check top entities first
            if self._is_point_in_entity(event.x, event.y, entity):
                clicked_entity = entity
                break
        
        if clicked_entity:
            # Convert to system event
            system_event = self.convert_input_event({
                "type": "double_click",
                "x": event.x,
                "y": event.y
            })
            
            if system_event:
                # Add entity to event data
                system_event.data["entity"] = clicked_entity
                
                # Dispatch the event
                self.event_dispatcher.dispatch_event(system_event)
    
    def _is_point_in_entity(self, x: int, y: int, entity) -> bool:
        """
        Check if a point is inside an entity.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            entity: The entity to check
        
        Returns:
            bool: True if the point is inside the entity
        """
        entity_x, entity_y = entity.position
        width, height = entity.size
        
        return (entity_x <= x <= entity_x + width and 
                entity_y <= y <= entity_y + height)
    
    def run(self):
        """Run the Tkinter main loop."""
        if self.master:
            self.master.mainloop()
