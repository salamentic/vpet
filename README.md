# DigiPet - Desktop Digimon Pet

A modular desktop pet application featuring Digimon sprites with a plugin-based architecture.

## Features

- Desktop pet that lives on your screen
- Various animation states (idle, walk, talk, sleep)
- Multiple Digimon types
- Pluggable architecture for easy extension
- Optional LLM integration for dynamic responses
- Hot-reloadable configuration

## Installation

### Prerequisites

- Python 3.8 or higher
- Tkinter (usually included with Python)
- PIL (Pillow) for image processing

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/salamentic/vpet.git
   cd vpet
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Directory Structure

```
/
├── core/                       # Core system components
│   ├── application.py          # Main application container
│   ├── event_system.py         # Event dispatcher and handling
│   ├── plugin_manager.py       # Plugin loading and management 
│   └── config_manager.py       # Configuration handling
│
├── entities/                   # Entity system
│   ├── base_entity.py          # Base entity class
│   ├── digimon.py              # Digimon entity implementation
│   └── character_factory.py    # Factory for creating characters
│
├── renderers/                  # Visual rendering components
│   ├── base_renderer.py        # Abstract renderer interface
│   ├── tkinter_renderer.py     # Tkinter-based renderer
│   └── pygame_renderer.py      # Optional PyGame renderer
│
├── behaviors/                  # Behavior system components
│   ├── behavior_manager.py     # Orchestrates behaviors
│   ├── idle_behavior.py        # Idle behavior implementation
│   └── walk_behavior.py        # Walking behavior
│
├── sprites/                    # Sprite and animation handling
│   ├── sprite_manager.py       # Manages sprites
│   └── animation.py            # Animation system
│
├── plugins/                    # Plugin system
│   └── llm_integration/        # LLM integration plugin
│
├── utils/                      # Utility functions and tools
│   └── spritesheet_tools.py    # Sprite processing tools
│
├── resources/                  # Resource files
│   ├── spritesheets/           # Digimon sprite sheets
│   └── config/                 # Configuration files
│
├── tools/                      # Standalone tools
│   ├── sprite_scraper.js       # Sprite scraper
│   └── sprite_cropper.py       # Sprite cropping tool
│
├── main.py                     # Application entry point
└── README.md                   # This file
```

## Usage

### Basic Controls

- **Click and drag** the Digimon to move it around
- **Double-click** to make it speak
- **X button** to close the application
- **- button** to minimize the window

### Command Line Options

```bash
python main.py --help
```

Available options:
- `--config PATH`: Specify custom configuration file path
- `--debug`: Enable debug logging
- `--digimon TYPE`: Specify Digimon type (e.g., Rookie, Champion)

### Configuration

The application is configured using JSON files in the `resources/config` directory. The main configuration file is `default_config.json`.

You can customize:
- Window size and appearance
- Animation speed and behavior intervals
- Digimon type and behaviors
- Plugin settings
- Sprite paths and dimensions

The configuration is hot-reloaded, so changes take effect immediately without restarting.

## Extending the Application

### Adding New Digimon

1. Add sprite sheets to `resources/spritesheets/[TYPE]/`
2. Update sprite dimensions and mapping in configuration
3. Register the new Digimon in `entities/character_factory.py`

### Creating Plugins

Plugins must implement the `PluginInterface` class from `core/plugin_manager.py`:

1. Create a new directory in `plugins/` with your plugin name
2. Implement the required methods:
   - `initialize()`
   - `shutdown()`
   - `update()`
   - `get_info()`
3. Enable the plugin in the configuration

See the `llm_integration` plugin for an example.

### LLM Integration

To use the LLM integration plugin:

1. Obtain an API key from OpenAI or compatible service
2. Add the API key to your configuration:
   ```json
   "plugins": {
     "enabled": ["llm_integration"],
     "llm_integration": {
       "api_key": "your-api-key",
       "model": "gpt-3.5-turbo"
     }
   }
   ```

Without an API key, the plugin will use a mock implementation with predefined responses.

## Tools

### Sprite Scraper

The project includes a Node.js based sprite scraper in `tools/sprite_scraper.js` that can download Digimon sprites from online resources:

```bash
cd tools
npm install
node sprite_scraper.js
```

### Sprite Cropper

The sprite cropper tool helps process sprite sheets into individual animation frames:

```bash
python tools/sprite_cropper.py --input path/to/spritesheet.png --output path/to/output
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.