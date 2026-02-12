import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

def send_notification(slots):
    """
    Envoie une notification par email avec les créneaux disponibles.
    Si la configuration SMTP est manquante, affiche les créneaux dans la console.
    """
    subject = "Terrains de Padel Disponibles !"
    body = "Des créneaux sont disponibles :\n\n"
    for day, times in slots.items():
        body += f"{day} :\n"
        for time in times:
            body += f"  - {time}\n"
    
    body += f"\nRéservez vite sur : {config.PLANNING_URL}"

    # Fallback to console if SMTP is not configured
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        print("\n" + "="*50)
        print("NOTIFICATION (Console Mode)")
        print(f"Subject: {subject}")
        print("-" * 50)
        print(body)
        print("="*50 + "\n")
        print("To enable email notifications, please configure SMTP settings in config.py")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = config.SMTP_USER
        msg['To'] = config.NOTIFICATION_RECEIVER
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(config.SMTP_USER, config.NOTIFICATION_RECEIVER, text)
        server.quit()
        print(f"Email notification sent to {config.NOTIFICATION_RECEIVER}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Fallback print even if email fails
        print("\n[FALLBACK] Content of failed email:")
        print(body)
