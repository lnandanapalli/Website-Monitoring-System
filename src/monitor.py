import json
import requests
import smtplib
import time
import os
import sys
from datetime import datetime
import logging
import psutil
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# logging for future use
logging.basicConfig(filename='website_monitor.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# creating a lock file in the current directory to prevent multiple processes from running at the same time
def is_already_running():
    lock_file_path = "website_monitor.lock"

    if os.path.isfile(lock_file_path):
        with open(lock_file_path, "r") as lock_file:
            pid = lock_file.read().strip()
            if pid and psutil.pid_exists(int(pid)):
                return True
            else:
                # Remove old lock file
                os.remove(lock_file_path)
    # Create a new lock file
    with open(lock_file_path, "w") as lock_file:
        lock_file.write(str(os.getpid()))
    return False

def remove_lock_file():
    lock_file_path = "website_monitor.lock"
    if os.path.isfile(lock_file_path):
        os.remove(lock_file_path)

def read_config(filename="config.json"):
    with open(filename, "r") as file:
        config = json.load(file)
    return config

# creating a systemd service so that even if the program is killed or crashed, the systemd service starts it again
def create_systemd_service():
    service_content = """
    [Unit]
    Description=Website Uptime Monitor
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /home/lokesh/website_uptime_monitor/monitor.py
    WorkingDirectory=/home/lokesh/website_uptime_monitor
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=default.target
    """

    with open("/etc/systemd/system/monitor_website.service", "w") as service_file:
        service_file.write(service_content)
    os.system("systemctl enable monitor_website")
    os.system("systemctl start monitor_website")
    os.system("systemctl daemon-reload")

def remove_systemd_service():
    os.system("systemctl stop monitor_website")
    os.system("systemctl disable monitor_website")
    os.system("rm /etc/systemd/system/monitor_website.service")
    os.system("systemctl daemon-reload")

def send_email(subject, body, to_email, from_email, password):
    msg = MIMEMultipart()
    msg.attach(MIMEText(body, 'plain'))
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.ehlo()
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)

def monitor_website(config):
    with open('/var/www/html/index.html', 'w') as html_file:
        html_file.write(f"<h1 style='color: blue;'>Website Uptime Monitor Started at {datetime.now()}</h1>\n")
    logging.info(f"Website Uptime Monitor Started at {datetime.now()}")

    while True:
        try:
            start_time = time.time()
            response = requests.get(config["website"], timeout=config["timeout"])
            end_time = time.time()

            latency = end_time - start_time

            if response.status_code != 200:
                with open('/var/www/html/index.html', 'a+') as html_file:
                    html_file.write(f"<p style='color: red;'>Alert! Website {config['website']} is down</p>")
                logging.info(f"Alert! Website {config['website']} is down")
                print(f"Alert! Website {config['website']} is down")

                send_email("Website Down Alert", f"The website {config['website']} is down.", config["alert"], config["from_email"], config["key"])
            
            else:
                with open('/var/www/html/index.html', 'a+') as html_file:
                    html_file.write("<p style='color: green;'>Website is up</p>\n")
                logging.info("Website is up")
                print("Website is up")

                with open('/var/www/html/index.html', 'a+') as html_file:
                    html_file.write(f"<p style='color: green;'>Time: {datetime.now()} | Latency: {latency} seconds</p>\n")
                logging.info(f"Time: {datetime.now()} | Latency: {latency} seconds")
                print(f"Time: {datetime.now()} | Latency: {latency} seconds")
        except requests.exceptions.RequestException as e:
            with open('/var/www/html/index.html', 'a+') as html_file:
                html_file.write(f"<p style='color: red;'>Alert! Website {config['website']} is down</p>")
            logging.info(f"Alert! Website {config['website']} is down")
            print(f"Alert! Website {config['website']} is down")

            send_email("Website Down Alert", f"The website {config['website']} is down.", config["alert"], config["from_email"], config["key"])
            
        except Exception as e:
            print(f"Error: {e}")
            logging.info(f"Error: {e}")
            send_email("Website Uptime Monitor Error Alert", f"An error occurred: {e}", config["alert"], config["from_email"], config["key"])

        time.sleep(config["poll-interval"])


if __name__ == "__main__":
    config = read_config()

    if len(sys.argv) > 1:
        action = sys.argv[1]

        if action == "stop":
            remove_systemd_service()
            remove_lock_file()
            print("Monitor service stopped.")
        else:
            print("To run: Run as root - sudo python3 monitor.py")
            print("To stop: Run as root - sudo python3 monitor.py stop")

    else:
        try:
            if is_already_running():
                print("Another instance is already running. Exiting.")
                logging.info("Another instance is already running. Exiting.")
                sys.exit(0)

            create_systemd_service()
            monitor_website(config)

        except KeyboardInterrupt:
            print("Monitoring stopped by the user.")
            logging.info("Monitoring stopped by the user.")
            remove_lock_file()

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            logging.info(f"An unexpected error occurred: {e}")
            remove_lock_file()
            sys.exit(1)
