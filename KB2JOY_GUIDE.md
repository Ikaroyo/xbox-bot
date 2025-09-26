# KB2JOY - Keyboard/Mouse to Xbox Controller

## 🎮 Overview

The **KB2JOY** (Keyboard to Joystick) feature allows you to capture keyboard and mouse inputs in real-time and convert them to Xbox controller button presses. This enables you to play controller-based games using your keyboard and mouse with complete customization.

## ✨ Features

### 🔧 **Full Input Mapping**
- Map **any keyboard key** to any Xbox controller button
- Map **mouse buttons** (left, right, middle) to controller buttons  
- Map **mouse scroll** (up/down) to controller buttons
- Support for **all Xbox controller buttons**:
  - Face buttons: A, B, X, Y
  - Shoulder buttons: LB, RB
  - D-Pad: Up, Down, Left, Right
  - System buttons: START, BACK
  - Thumbsticks: LEFT_THUMB, RIGHT_THUMB
  - Left stick directions: UP, DOWN, LEFT, RIGHT, UP_LEFT, UP_RIGHT, DOWN_LEFT, DOWN_RIGHT, CENTER

### 🎛️ **Easy Configuration**
- **Visual mapping interface** with organized button categories
- **One-click capture** - click "Capture" and press the key you want to map
- **Real-time feedback** - see your mappings update instantly
- **Clear individual mappings** or clear all at once
- **Enable/Disable toggle** - easily turn KB2JOY on/off

### 💾 **Configuration Management**
- **Auto-save** mappings between sessions
- **Export/Import** configurations to share with others
- **JSON-based** configuration files for easy editing
- **Backup and restore** your custom mappings

### ⚡ **Real-Time Performance**
- **Low latency** input conversion
- **Background operation** - works while you use other applications
- **No game modification** required - works with any controller-compatible game
- **Thread-safe** operation with the main application

## 🚀 Getting Started

### 1. **Install Requirements**
The KB2JOY feature requires the `pynput` library:

```bash
pip install pynput
```

Or use the built-in installer:
- Go to the KB2JOY tab
- Click "Install pynput" if prompted
- Restart the application

### 2. **Basic Setup**
1. **Open the KB2JOY tab** in the application
2. **Enable KB2JOY** using the toggle switch
3. **Map your inputs**:
   - Click "Capture" next to any Xbox button
   - Press the keyboard key or mouse button you want to map
   - See the mapping appear instantly

### 3. **Example Mappings**
Common gaming setups:

**FPS Games:**
- `W` → `STICK_UP` (move forward)
- `A` → `STICK_LEFT` (move left)  
- `S` → `STICK_DOWN` (move backward)
- `D` → `STICK_RIGHT` (move right)
- `Space` → `A` (jump)
- `Left Mouse` → `RB` (shoot)
- `Right Mouse` → `LB` (aim)

**Platformer Games:**
- `Arrow Up` → `DPAD_UP`
- `Arrow Down` → `DPAD_DOWN`
- `Arrow Left` → `DPAD_LEFT`
- `Arrow Right` → `DPAD_RIGHT`
- `Z` → `A` (jump)
- `X` → `B` (run)

## 🛠️ Advanced Usage

### **Input Types Supported**

1. **Keyboard Keys**
   - All letter keys (a-z)
   - Number keys (0-9)  
   - Special keys (space, enter, shift, ctrl, alt, etc.)
   - Function keys (f1-f12)
   - Arrow keys, home, end, page up/down

2. **Mouse Inputs**
   - Left mouse button: `mouse_left`
   - Right mouse button: `mouse_right`
   - Middle mouse button: `mouse_middle`
   - Scroll up: `scroll_up`
   - Scroll down: `scroll_down`

### **Configuration Files**

KB2JOY saves configurations in `kb2joy_config.json`:

```json
{
  "mappings": {
    "A": "space",
    "B": "mouse_right", 
    "STICK_UP": "w",
    "STICK_LEFT": "a",
    "STICK_DOWN": "s", 
    "STICK_RIGHT": "d"
  },
  "enabled": false
}
```

### **Performance Tips**

1. **Minimize Mapped Keys** - Only map the keys you actually need
2. **Test Mappings** - Use the Joystick tab to verify controller output
3. **Game Compatibility** - Ensure your target game supports Xbox controllers
4. **Background Operation** - KB2JOY works even when the app is not focused

## 🎮 Usage Scenarios

### **Gaming Applications**
- **Retro Gaming** - Play old games that only support keyboards with controller comfort
- **Emulation** - Use modern keyboard controls with emulated console games
- **Steam Gaming** - Convert keyboard games to controller-compatible
- **Accessibility** - Custom input schemes for users with mobility needs

### **Productivity Uses**
- **Media Control** - Map keyboard shortcuts to controller buttons for media apps
- **Presentation Control** - Use a controller as a wireless presenter remote
- **Application Navigation** - Create custom controller schemes for any application

## 🔧 Troubleshooting

### **KB2JOY Not Starting**
- Ensure `pynput` is installed: `pip install pynput`
- Check for permission issues (run as administrator if needed)
- Verify no other keyboard capture software is interfering

### **Mappings Not Working**
- Ensure KB2JOY is enabled (toggle switch on)
- Check that virtual controller is connected (green status in other tabs)
- Verify target application recognizes Xbox controller input
- Test individual mappings using the capture interface

### **Performance Issues**
- Reduce number of mapped keys
- Close unnecessary background applications
- Check for conflicts with other input software
- Monitor CPU usage in task manager

### **Input Not Captured**
- Some special keys may not be capturable due to system restrictions
- Anti-virus software may block input monitoring
- Gaming keyboards with macro software may interfere
- Try running the application as administrator

## 📁 Files Created

KB2JOY creates these files:
- `kb2joy_config.json` - Your saved mappings and settings
- Log entries in the main application log

## 🔐 Security & Privacy

- KB2JOY only monitors inputs when explicitly enabled
- No data is sent over the network
- All configuration is stored locally
- Input monitoring stops when the application closes
- Source code is fully transparent and auditable

## 🎯 Tips & Best Practices

1. **Start Simple** - Map just a few essential keys first
2. **Test Thoroughly** - Use the Joystick tab to verify each mapping works
3. **Save Configs** - Export your mappings before making major changes  
4. **Game-Specific Setups** - Create different mapping files for different games
5. **Document Mappings** - Keep notes on what each mapping does for complex setups

## 🚀 Future Enhancements

Planned features for future versions:
- **Analog stick mapping** for mouse movement
- **Trigger pressure simulation** for variable input
- **Key combinations** support (Ctrl+C, etc.)
- **Timing controls** for held vs pressed inputs
- **Profile switching** for different games
- **Macro recording** and playback
- **Visual controller display** showing active inputs

---

## 🎮 **Ready to Game!**

With KB2JOY, you can now enjoy controller-based games using your preferred keyboard and mouse setup. The possibilities are endless - from classic gaming to modern accessibility solutions!

**Happy Gaming! 🎯**