import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# User Credentials
EMAIL = os.getenv("MAS_EMAIL")
PASSWORD = os.getenv("MAS_PASSWORD")

# Site URLs
LOGIN_URL = "https://lemas.gestion-sports.com/connexion.php"
PLANNING_URL = "https://lemas.gestion-sports.com/appli/Reservation"

# Notification Settings (Email)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "") # Your email address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "") # Your app password
NOTIFICATION_RECEIVER = os.getenv("NOTIFICATION_RECEIVER", EMAIL)

# Booking Preferences
# Days to check: 0=Monday, 6=Sunday
# Example: [0, 1, 2, 3, 4] for Weekdays
DAYS_TO_CHECK = [0, 1, 2, 3, 4] 

# Hours to check (Specific slots as requested)
TARGET_SLOTS = ["18:00", "19:30"]

# Deprecated ranges (kept for backward compatibility if needed)
START_HOUR = 18
END_HOUR = 22

# Headless mode (True for background, False for debug to see browser)
HEADLESS = True
