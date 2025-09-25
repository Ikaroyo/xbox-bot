"""
Stumble Bot - New Modular Application

This is the new modularized version of the Stumble Bot application.
Uses the new GUI structure with separated components.
"""

from gui.main_window import StumbleBotMainWindow


def main():
    """Main entry point for the modular application."""
    app = StumbleBotMainWindow()
    app.run()


if __name__ == "__main__":
    main()