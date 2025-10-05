# New Features Added

## 1. Process Focus Control

This feature allows the bot to only work when a specific process (application) is focused.

### How to Use:

1. Go to the **KB2JOY tab**
2. Find the **"Process Focus Control"** section at the top
3. Check **"Only work when target process is focused"**
4. Enter the process name (e.g., `xbox.exe`, `game.exe`)
5. The status will show whether the target process is currently focused

### Benefits:

- Bot only runs when the target game/app is active
- Prevents accidental inputs when working in other applications
- Saves system resources when target isn't focused
- Perfect for games that require focus to receive inputs

### Status Indicators:

- **Status: Disabled** - Process monitoring is off
- **Status: Monitoring {process}** - Watching for the process
- **Status: ✓ {process} FOCUSED** - Target process is active
- **Status: ⚠️ {process} NOT focused** - Target process not active

---

## 2. KB2JOY Hotkey Toggle

This feature allows you to enable/disable KB2JOY (keyboard to controller conversion) with a customizable hotkey.

### How to Use:

1. Go to the **KB2JOY tab**
2. Find the **"KB2JOY Control"** section
3. Check **"Enable hotkey toggle"**
4. Set your desired hotkey combination (default: `ctrl+shift+f1`)
5. The hotkey will now toggle KB2JOY on/off globally

### Hotkey Format Examples:

- `ctrl+shift+f1` - Control + Shift + F1
- `alt+f2` - Alt + F2
- `ctrl+alt+x` - Control + Alt + X
- `shift+f10` - Shift + F10

### Benefits:

- Quick toggle without switching windows
- Emergency disable if KB2JOY interferes
- Easy to turn on/off during gameplay
- Works from any application

### Status Indicators:

- **Hotkey: Disabled** - No hotkey listener active
- **Hotkey: {combo} (Active)** - Hotkey is working and listening

---

## Installation Requirements

To use these new features, you may need additional packages:

```bash
# For process focus monitoring
pip install psutil

# For Windows API features (should already be installed)
pip install pywin32

# For keyboard input monitoring (should already be installed)
pip install pynput
```

---

## Example Usage Scenarios

### Scenario 1: Xbox Remote Play Bot

```
Process Focus: ✓ Enabled
Process Name: xbox.exe
Hotkey: ctrl+shift+f1
```

- Bot only works when Xbox app is focused
- Use Ctrl+Shift+F1 to quickly toggle KB2JOY on/off
- Safe to work in other apps without interference

### Scenario 2: Steam Game Bot

```
Process Focus: ✓ Enabled
Process Name: steamgame.exe
Hotkey: alt+f9
```

- Bot only active when Steam game is running and focused
- Alt+F9 to toggle controller simulation
- Perfect for games requiring focus for input

### Scenario 3: Multi-Application Setup

```
Process Focus: ✗ Disabled
Hotkey: shift+f12
```

- Bot works regardless of focused application
- Shift+F12 for manual control when needed
- Good for testing or multi-app workflows

---

## Troubleshooting

### Process Focus Not Working:

1. Make sure `psutil` is installed: `pip install psutil`
2. Check the exact process name in Task Manager
3. Try with and without `.exe` extension
4. Check logs for error messages

### Hotkey Not Working:

1. Make sure `pynput` is installed: `pip install pynput`
2. Try different hotkey combinations
3. Avoid conflicts with system hotkeys
4. Check if other apps are using the same hotkey

### KB2JOY Pausing/Resuming Issues:

1. Check process focus status indicator
2. Look for pause/resume messages in logs
3. Try disabling process focus if causing issues
4. Use hotkey toggle as alternative control method

---

## Technical Details

- **Process monitoring frequency**: Every 500ms (configurable)
- **Hotkey detection**: Global system-wide listener
- **Focus detection**: Uses Windows API to get foreground window
- **Process matching**: Case-insensitive, supports partial names
- **Integration**: Works seamlessly with existing KB2JOY system

Both features are designed to work together and enhance the existing bot functionality without breaking compatibility.
