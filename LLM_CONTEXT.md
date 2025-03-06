# DigiPet - Modular Desktop Digimon Pet System

## Architecture Overview

This project implements a modular desktop pet system with clear separation of concerns. The architecture follows these principles:
1. **Component-based**: Each functional unit is separated into its own component
2. **Plugin-based**: Features can be added through a plugin system
3. **Event-driven**: Components communicate through events
4. **Configuration-driven**: Behavior is controlled through configuration files

## Directory Structure

```
/
├── core/                       # Core system components
│   ├── __init__.py             # Package initialization
│   ├── application.py          # Main application container
│   ├── event_system.py         # Event dispatcher and handling
│   ├── plugin_manager.py       # Plugin loading and management 
│   └── config_manager.py       # Configuration handling
│
├── entities/                   # Entity system
│   ├── __init__.py             # Package initialization
│   ├── base_entity.py          # Base entity class
│   ├── digimon.py              # Digimon entity implementation
│   └── character_factory.py    # Factory for creating characters
│
├── renderers/                  # Visual rendering components
│   ├── __init__.py             # Package initialization
│   ├── base_renderer.py        # Abstract renderer interface
│   ├── tkinter_renderer.py     # Tkinter-based renderer
│   └── pygame_renderer.py      # Optional PyGame renderer
│
├── behaviors/                  # Behavior system components
│   ├── __init__.py             # Package initialization
│   ├── behavior_manager.py     # Orchestrates behaviors
│   ├── idle_behavior.py        # Idle behavior implementation
│   ├── walk_behavior.py        # Walking behavior
│   └── talk_behavior.py        # Talking behavior
│
├── sprites/                    # Sprite and animation handling
│   ├── __init__.py             # Package initialization 
│   ├── sprite_manager.py       # Manages sprites
│   ├── animation.py            # Animation system
│   └── sprite_sheet.py         # Sprite sheet handling
│
├── plugins/                    # Plugin system
│   ├── __init__.py             # Package initialization
│   ├── llm_integration/        # LLM integration plugin
│   │   ├── __init__.py         # Plugin initialization
│   │   ├── llm_connector.py    # LLM API connector
│   │   └── llm_behavior.py     # LLM-driven behaviors
│   └── weather_integration/    # Example weather plugin
│
├── utils/                      # Utility functions and tools
│   ├── __init__.py             # Package initialization
│   ├── logger.py               # Logging utilities
│   ├── spritesheet_tools.py    # Sprite processing tools
│   └── resource_loader.py      # Resource loading utilities
│
├── resources/                  # Resource files
│   ├── spritesheets/           # Digimon sprite sheets
│   │   ├── rookie/             # Rookie-level sprites
│   │   └── champion/           # Champion-level sprites
│   └── config/                 # Configuration files
│       ├── default_config.json # Default configuration
│       └── user_config.json    # User-specific configuration
│
├── tools/                      # Standalone tools
│   ├── sprite_scraper.js       # Sprite scraper
│   └── sprite_cropper.py       # Sprite cropping tool
│
├── main.py                     # Application entry point
└── README.md                   # Project documentation
```

## Core Components

### Entity System
- `BaseEntity`: Abstract base class for all entity types
- `Digimon`: Implementation for Digimon entities
- `CharacterFactory`: Creates entity instances based on configuration

### Renderer System
- `BaseRenderer`: Interface for rendering implementations
- `TkinterRenderer`: Tkinter implementation
- `PygameRenderer`: Alternative rendering option

### Behavior System
- `BehaviorManager`: Coordinates behaviors and transitions
- Individual behaviors (idle, walk, talk) as separate components
- LLM-driven behaviors available as plugins

### Sprite System
- `SpriteManager`: Loads and manages sprites
- `Animation`: Handles animation sequences
- `SpriteSheet`: Processes sprite sheets

### Event System
- `EventDispatcher`: Sends events throughout the system
- Event types for interactions, state changes, etc.

### Plugin System
- `PluginManager`: Loads and initializes plugins
- Individual plugins in separate directories
- Standard plugin interface for consistency

## Plugin Architecture
Plugins use a hook-based system to extend functionality:
1. Register with the plugin manager during initialization
2. Connect to event hooks they want to handle
3. Provide services through a defined interface

### LLM Integration Plugin
This plugin connects the pet with language models to:
- Generate dynamic conversation
- Adapt personality based on interactions
- Remember past interactions
- Drive behaviors based on contextual understanding

## Configuration System
- JSON-based configuration files
- Default configuration bundled with the application
- User-specific configuration in user's home directory
- Hot-reloading of configuration changes

## Event Flow
1. Input events (mouse, keyboard, timer) are captured
2. Events are dispatched to interested components
3. Components may trigger additional events
4. Rendering occurs at regular intervals

## Adding New Digimon
1. Add sprite sheets to the appropriate resource folder
2. Create a configuration entry in resources/config
3. Register the new Digimon in the character factory
4. No code changes required!

## Adding New Behaviors
1. Create a new behavior class in the behaviors package
2. Register the behavior with the behavior manager
3. Define behavior transitions in configuration

## Development Guidelines
- Maintain clear separation between components
- Use the event system for inter-component communication
- Keep UI logic out of entity and behavior classes
- Add new features as plugins when possible
- Document interfaces and events thoroughly