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
