# main.py
import customtkinter as ctk
import config
from app.ui.main_window import RouteApp

if __name__ == "__main__":
    # Apply global configurations
    ctk.set_appearance_mode(config.APPEARANCE_MODE)
    ctk.set_default_color_theme(config.COLOR_THEME)

    # Initialize and run the application
    app = RouteApp()
    app.mainloop()