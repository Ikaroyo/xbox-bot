"""
Game Bot Logic
Implements the main bot logic with Xbox controller actions for different game states
"""

import time
import random
import math
from typing import Dict, Optional, Callable
import logging
from xbox_controller import create_controller
from image_recognition import GameStateDetector, MatchResult

logger = logging.getLogger(__name__)

class StumbleGuysBot:
    """
    Main bot logic for Stumble Guys Xbox Remote Play
    """
    
    def __init__(self, controller=None, state_detector: Optional[GameStateDetector] = None):
        """
        Initialize the bot
        
        Args:
            controller: Xbox controller instance
            state_detector: Game state detector instance
        """
        self.controller = controller or create_controller()
        self.state_detector = state_detector
        self.running = False
        self.current_state = "unknown"
        self.last_action_time = 0
        
        # Action configuration
        self.action_delay = 1.0  # Minimum delay between actions
        self.movement_duration = (1.0, 3.0)  # Min/max movement duration
        self.action_probability = 0.7  # Probability of taking action in game
        
        # State action mappings
        self.state_actions = {
            'main_menu': self.handle_main_menu,
            'game_running': self.handle_game_running,
            'game_lost': self.handle_game_lost,
            'game_results': self.handle_game_results,
            'get_reward': self.handle_get_reward,
            'unknown_state': self.handle_unknown_state,
            'no_match': self.handle_no_match,
            'error': self.handle_error
        }
        
        logger.info("Stumble Guys bot initialized")
        
    def start(self):
        """Start the bot"""
        self.running = True
        logger.info("Bot started")
        
    def stop(self):
        """Stop the bot"""
        self.running = False
        logger.info("Bot stopped")
        
    def process_game_state(self, window=None) -> str:
        """
        Process current game state and take appropriate action
        
        Args:
            window: Game window object
            
        Returns:
            Current state name
        """
        try:
            # Detect current state
            if self.state_detector:
                state, matches = self.state_detector.detect_current_state(window)
                logger.info(f"Detected game state: {state}")
                
                # Log template matches
                found_templates = [name for name, match in matches.items() if match.found]
                if found_templates:
                    logger.info(f"Found templates: {found_templates}")
                else:
                    logger.info("No templates matched")
            else:
                state = "no_detector"
                matches = {}
                logger.warning("No state detector available")
                
            self.current_state = state
            
            # Execute action for current state
            if state in self.state_actions:
                logger.info(f"Executing action for state: {state}")
                action_func = self.state_actions[state]
                action_func(matches)
            else:
                logger.warning(f"No action defined for state: {state}")
                
            return state
            
        except Exception as e:
            logger.error(f"Error processing game state: {e}")
            return "error"
            
    def can_take_action(self) -> bool:
        """Check if enough time has passed since last action"""
        current_time = time.time()
        return current_time - self.last_action_time >= self.action_delay
        
    def record_action(self):
        """Record that an action was taken"""
        self.last_action_time = time.time()
        
    # State handling methods
    
    def handle_main_menu(self, matches: Dict[str, MatchResult]):
        """Handle main menu state - start a new game"""
        if not self.can_take_action():
            logger.info("Main menu detected but action cooldown active")
            return
            
        logger.info("In main menu, attempting to start new game")
        
        # Press A button to start game (or whatever button starts the game)
        try:
            result = self.controller.press_a(0.2)
            logger.info(f"Pressed A button, result: {result}")
        except Exception as e:
            logger.error(f"Failed to press A button: {e}")
        
        # Wait a bit for the game to start loading
        logger.info("Waiting for game to start loading...")
        time.sleep(3.0)
        
        self.record_action()
        
    def handle_game_running(self, matches: Dict[str, MatchResult]):
        """Handle active gameplay - simulate player movement"""
        if not self.can_take_action():
            logger.debug("Game running but action cooldown active")
            return
            
        # Only take action with certain probability to seem more human
        if random.random() > self.action_probability:
            logger.debug(f"Skipping action (probability check: {self.action_probability})")
            return
            
        logger.info("Game running, simulating gameplay")
        
        # Choose random action
        actions = [
            self.simulate_movement,
            self.simulate_jump,
            self.simulate_grab,
            self.simulate_dive,
            self.simulate_pause_movement
        ]
        
        action = random.choice(actions)
        action_name = action.__name__
        logger.info(f"Executing action: {action_name}")
        
        try:
            action()
            logger.info(f"Action {action_name} completed")
        except Exception as e:
            logger.error(f"Action {action_name} failed: {e}")
        
        self.record_action()
        
    def handle_game_lost(self, matches: Dict[str, MatchResult]):
        """Handle game over state - restart or go back to menu"""
        if not self.can_take_action():
            return
            
        logger.info("Game lost, going back to menu")
        
        # Press B button or Start to go back (depending on the game's UI)
        if random.choice([True, False]):
            self.controller.press_b(0.2)
        else:
            self.controller.press_start(0.2)
            
        time.sleep(2.0)
        
        self.record_action()
        
    def handle_game_results(self, matches: Dict[str, MatchResult]):
        """Handle results screen - wait or continue"""
        if not self.can_take_action():
            return
            
        logger.info("On results screen, waiting or continuing")
        
        # Sometimes press A to continue, sometimes wait
        if random.random() < 0.3:
            self.controller.press_a(0.2)
            time.sleep(1.0)
            
        self.record_action()
        
    def handle_get_reward(self, matches: Dict[str, MatchResult]):
        """Handle reward collection"""
        if not self.can_take_action():
            return
            
        logger.info("Collecting reward")
        
        # Press A to collect reward
        self.controller.press_a(0.2)
        time.sleep(1.5)
        
        self.record_action()
        
    def handle_unknown_state(self, matches: Dict[str, MatchResult]):
        """Handle unknown state - try generic actions"""
        if not self.can_take_action():
            return
            
        logger.info("Unknown state, trying generic actions")
        
        # Try pressing A or B
        if random.choice([True, False]):
            self.controller.press_a(0.2)
        else:
            self.controller.press_b(0.2)
            
        time.sleep(1.0)
        self.record_action()
        
    def handle_no_match(self, matches: Dict[str, MatchResult]):
        """Handle no template matches - wait or try gentle actions"""
        logger.debug("No template matches, waiting")
        
        # Just wait - don't want to spam actions when we don't know the state
        time.sleep(1.0)
        
    def handle_error(self, matches: Dict[str, MatchResult]):
        """Handle error state"""
        logger.warning("Error state detected, waiting")
        time.sleep(2.0)
        
    # Movement simulation methods
    
    def simulate_movement(self):
        """Simulate random movement"""
        logger.info("Simulating movement")
        
        # Random movement direction
        directions = [
            (0, 1),    # Forward
            (0, -1),   # Backward  
            (-1, 0),   # Left
            (1, 0),    # Right
            (-0.7, 0.7),  # Diagonal
            (0.7, 0.7),   # Diagonal
            (-0.7, -0.7), # Diagonal
            (0.7, -0.7)   # Diagonal
        ]
        
        direction = random.choice(directions)
        duration = random.uniform(*self.movement_duration)
        
        logger.info(f"Moving in direction {direction} for {duration:.1f}s")
        
        # Set left stick movement
        if hasattr(self.controller, 'set_stick'):
            try:
                self.controller.set_stick('left', direction[0], direction[1])
                time.sleep(duration)
                self.controller.set_stick('left', 0, 0)
                logger.info("Stick movement completed")
            except Exception as e:
                logger.error(f"Stick movement failed: {e}")
        else:
            # Fallback for keyboard emulator
            logger.info("Using keyboard fallback for movement")
            try:
                if direction[0] > 0:
                    self.controller.move_stick('left', 'right', duration)
                elif direction[0] < 0:
                    self.controller.move_stick('left', 'left', duration)
                elif direction[1] > 0:
                    self.controller.move_stick('left', 'up', duration)
                elif direction[1] < 0:
                    self.controller.move_stick('left', 'down', duration)
                logger.info("Keyboard movement completed")
            except Exception as e:
                logger.error(f"Keyboard movement failed: {e}")
                
    def simulate_jump(self):
        """Simulate jumping"""
        logger.info("Simulating jump")
        
        try:
            # Press A button (jump in most games)
            result = self.controller.press_a(0.1)
            logger.info(f"Jump button pressed, result: {result}")
            
            # Sometimes double jump
            if random.random() < 0.3:
                logger.info("Attempting double jump")
                time.sleep(0.2)
                result2 = self.controller.press_a(0.1)
                logger.info(f"Double jump result: {result2}")
        except Exception as e:
            logger.error(f"Jump simulation failed: {e}")
            
    def simulate_grab(self):
        """Simulate grab action"""
        logger.debug("Simulating grab")
        
        # Press X button (usually grab in Stumble Guys)
        self.controller.press_x(random.uniform(0.1, 0.8))
        
    def simulate_dive(self):
        """Simulate dive action"""
        logger.debug("Simulating dive")
        
        # Press Y button (usually dive)
        self.controller.press_y(0.2)
        
    def simulate_pause_movement(self):
        """Simulate a brief pause in movement"""
        logger.debug("Simulating pause")
        
        # Just wait without any input
        time.sleep(random.uniform(0.5, 2.0))
        
    def simulate_random_stick_movement(self):
        """Simulate random stick movements for camera or aiming"""
        if hasattr(self.controller, 'set_stick'):
            # Random right stick movement (camera)
            x = random.uniform(-0.5, 0.5)
            y = random.uniform(-0.5, 0.5)
            duration = random.uniform(0.2, 1.0)
            
            self.controller.set_stick('right', x, y)
            time.sleep(duration)
            self.controller.set_stick('right', 0, 0)
            
    def emergency_stop(self):
        """Emergency stop - reset all controller inputs"""
        logger.info("Emergency stop activated")
        
        try:
            if hasattr(self.controller, 'reset_state'):
                self.controller.reset_state()
            else:
                # For keyboard emulator, release common keys
                import pyautogui
                pyautogui.keyUp('w')
                pyautogui.keyUp('a')
                pyautogui.keyUp('s')
                pyautogui.keyUp('d')
                
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")

class BotOrchestrator:
    """
    High-level bot orchestrator that manages the overall bot behavior
    """
    
    def __init__(self, bot: StumbleGuysBot, update_callback: Optional[Callable] = None):
        """
        Initialize bot orchestrator
        
        Args:
            bot: StumbleGuysBot instance
            update_callback: Callback function for status updates
        """
        self.bot = bot
        self.update_callback = update_callback
        self.stats = {
            'games_played': 0,
            'rewards_collected': 0,
            'runtime': 0,
            'state_changes': 0
        }
        self.start_time = None
        self.last_state = "unknown"
        
    def run_bot_cycle(self, window=None) -> Dict:
        """
        Run one cycle of the bot
        
        Args:
            window: Game window object
            
        Returns:
            Status dictionary
        """
        try:
            # Process current game state
            current_state = self.bot.process_game_state(window)
            
            # Update statistics
            if current_state != self.last_state:
                self.stats['state_changes'] += 1
                self.last_state = current_state
                
            if current_state == 'main_menu' and self.last_state == 'game_results':
                self.stats['games_played'] += 1
                
            if current_state == 'get_reward':
                self.stats['rewards_collected'] += 1
                
            # Calculate runtime
            if self.start_time:
                self.stats['runtime'] = time.time() - self.start_time
                
            # Prepare status update
            status = {
                'current_state': current_state,
                'running': self.bot.running,
                'stats': self.stats.copy()
            }
            
            # Call update callback if provided
            if self.update_callback:
                self.update_callback(status)
                
            return status
            
        except Exception as e:
            logger.error(f"Error in bot cycle: {e}")
            return {
                'current_state': 'error',
                'running': self.bot.running,
                'error': str(e),
                'stats': self.stats.copy()
            }
            
    def start(self):
        """Start the orchestrator"""
        self.start_time = time.time()
        self.bot.start()
        
    def stop(self):
        """Stop the orchestrator"""
        self.bot.stop()
        
    def get_stats(self) -> Dict:
        """Get current statistics"""
        stats = self.stats.copy()
        if self.start_time:
            stats['runtime'] = time.time() - self.start_time
        return stats
        
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'games_played': 0,
            'rewards_collected': 0,
            'runtime': 0,
            'state_changes': 0
        }
        self.start_time 