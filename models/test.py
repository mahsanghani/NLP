import smtplib
from email.mime.text import MIMEText

def send_test_email(smtp_server, smtp_port):
    try:
        # Create a text/plain message
        msg = MIMEText("This is a test email to check if the SMTP server works without authentication.")
        msg['Subject'] = 'Test Email'
        msg['From'] = 'ags.alert@megaavaya.com'
        msg['To'] = 'mohammad.ghani@afiniti.com'

        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Enable debug output

        # Send the email without using login credentials
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
        server.quit()
        
        print(f"Email sent successfully via {smtp_server}:{smtp_port} without authentication.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Replace with your SMTP server details
send_test_email('10.23.68.138', 25)
