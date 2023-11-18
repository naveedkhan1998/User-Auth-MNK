import requests
from dotenv import load_dotenv
import os

# Replace these values with your PythonAnywhere username, token, and host

load_dotenv()

username = os.getenv("PYTHONANYWHERE_USERNAME")
token = os.getenv("PYTHONANYWHERE_TOKEN")
host = "www.pythonanywhere.com"


# Function to execute commands in a console
def run_console_commands(commands):
    console_creation_response = requests.post(
        f"https://{host}/api/v0/user/{username}/consoles/",
        json={"executable": "bash", "arguments": "", "working_directory": "."},
        headers={"Authorization": f"Token {token}"},
    )

    if console_creation_response.status_code == 201:
        console_id = console_creation_response.json()["id"]

        # Run each command in the console
        for command in commands:
            requests.post(
                f"https://{host}/api/v0/user/{username}/consoles/{console_id}/send_input/",
                data={"input": command},
                headers={"Authorization": f"Token {token}"},
            )

        # Close the console
        requests.delete(
            f"https://{host}/api/v0/user/{username}/consoles/{console_id}/",
            headers={"Authorization": f"Token {token}"},
        )
    else:
        print(
            f"Failed to create console. Status code: {console_creation_response.status_code}"
        )


# Commands to run in the console
commands_to_run = [
    "git pull",
    "python manage.py makemigrations",
    "python manage.py migrate",
]

# Run the commands in the console
run_console_commands(commands_to_run)

# Restart the web app
webapp_domain_name = (
    "naveedkhan98.pythonanywhere.com"  # Replace with your web app's domain name
)
restart_response = requests.post(
    f"https://{host}/api/v0/user/{username}/webapps/{webapp_domain_name}/reload/",
    headers={"Authorization": f"Token {token}"},
)

if restart_response.status_code == 200:
    print("Web app restarted successfully.")
else:
    print(f"Failed to restart web app. Status code: {restart_response.status_code}")
