# Xbox Remote Play Bot

A modern Python bot for Xbox Remote Play that simulates Xbox controller inputs with image-based game state recognition. Designed specifically for games like Stumble Guys but can be adapted for other games.

## Features

- **Xbox Controller Simulation**: True Xbox controller input simulation using XInput (with keyboard fallback)
- **Image Recognition**: OpenCV-based template matching for reliable game state detection
- **Modern GUI**: User-friendly interface with separate tabs for running and configuration
- **Template Configuration**: Easy button/state configuration by capturing screenshots around cursor
- **Real-time Status**: Live bot status and statistics display
- **Adaptive Logic**: Smart bot behavior that adapts to different game states

## Installation

1. **Install Python 3.8 or higher**

2. **Clone or download this repository**

3. **Install required packages:**

   ```bash
   pip install -r requirements.txt
   ```

4. **For Xbox controller simulation (optional but recommended):**
   - Make sure you have XInput drivers installed (usually included with Windows)
   - For best results, connect a physical Xbox controller first to ensure drivers are present

## Usage

### Initial Setup

1. **Start Xbox Remote Play** and connect to your Xbox
2. **Launch the bot:**
   ```bash
   python xbox_remote_bot.py
   ```

### Configuration

1. **Switch to the Configuration tab**
2. **Capture templates for each game state:**

   - Enter a template name (e.g., "main_menu", "game_running", "game_lost")
   - Position your cursor over the button/element you want to detect
   - Click "Capture Template (F9)" or press F9
   - Adjust confidence threshold if needed (0.8 is usually good)
   - Repeat for all important game states

3. **Recommended templates to capture:**

   - `main_menu`: The "Play" or "Join Game" button
   - `game_running`: Some element that's only visible during gameplay
   - `game_lost`: The "Try Again" or similar button when you lose
   - `game_results`: Results screen elements
   - `get_reward`: Reward collection buttons

4. **Save your configuration**

### Running the Bot

1. **Switch to the Run tab**
2. **Set the target window** (usually "Xbox" or the specific game title)
3. **Adjust settings:**
   - Check Interval: How often to check game state (1.5s recommended)
4. **Click "Start Bot"**

The bot will:

- Automatically detect the current game state
- Take appropriate actions (start games, simulate movement, collect rewards)
- Display real-time status and statistics
- Continue running until stopped

## Game State Logic

The bot operates based on detected game states:

- **Main Menu**: Automatically starts new games
- **Game Running**: Simulates realistic player movement and actions
- **Game Lost**: Returns to menu to start a new game
- **Game Results**: Waits on results screen or continues
- **Get Reward**: Automatically collects rewards

## Controller Simulation

### XInput (Recommended)

- Provides true Xbox controller simulation
- Works with all Xbox Remote Play games
- More reliable and harder to detect

### Keyboard Fallback

- Falls back to keyboard simulation if XInput fails
- Maps controller buttons to keyboard keys
- May not work with all games

## Configuration File

Settings are saved in `bot_config.json`:

```json
{
  "window_title": "Xbox",
  "check_interval": 1.5,
  "templates": {
    "main_menu": {
      "path": "templates/main_menu.png",
      "confidence": 0.8,
      "size": [100, 100],
      "created": "2024-01-01 12:00:00"
    }
  },
  "controller_settings": {
    "stick_deadzone": 0.1,
    "trigger_threshold": 0.5
  }
}
```

## Troubleshooting

### Common Issues

1. **"Window not found"**

   - Make sure Xbox Remote Play is running
   - Check the window title matches exactly
   - Use the "Detect" button to auto-find Xbox windows

2. **"No templates configured"**

   - You need to capture at least one template before running
   - Go to Configuration tab and capture game state templates

3. **Templates not matching**

   - Lower the confidence threshold (try 0.6-0.7)
   - Recapture templates with the current game resolution
   - Test templates using the "Test Template" button

4. **Controller not working**
   - Make sure XInput drivers are installed
   - Try connecting a physical Xbox controller first
   - Check if keyboard fallback mode is working

### Performance Tips

- Keep the Xbox Remote Play window active and visible
- Use a consistent resolution/window size
- Capture templates at the same resolution you'll be playing
- Adjust check interval based on game speed (faster games need shorter intervals)

### Safety Features

- F10 hotkey to emergency stop (if using keyboard fallback)
- Bot automatically stops if window becomes inactive
- All actions are logged for debugging

## Customization

### Adding New Game States

1. Capture new templates in the Configuration tab
2. The bot will automatically try to handle unknown states
3. For custom logic, modify `bot_logic.py`

### Adjusting Behavior

Edit `bot_logic.py` to customize:

- Movement patterns and timing
- Action probabilities
- Response to different game states

### Controller Mappings

Edit `xbox_controller.py` to modify:

- Button mappings for keyboard fallback
- Controller sensitivity settings
- Action durations

## File Structure

- `xbox_remote_bot.py`: Main application with GUI
- `xbox_controller.py`: Xbox controller simulation
- `image_recognition.py`: OpenCV-based template matching
- `bot_logic.py`: Game state handling and bot behavior
- `templates/`: Directory for captured template images
- `bot_config.json`: Configuration file (created automatically)

## Legal Disclaimer

This bot is for educational and personal use only. Make sure you comply with the terms of service of any games or platforms you use it with. The developers are not responsible for any consequences of using this software.

## Contributing

Feel free to submit issues and pull requests to improve the bot!

## License

MIT License - see the code files for details.
