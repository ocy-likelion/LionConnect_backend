import requests

def send_slack_message(webhook_url: str, message: str) -> bool:
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    return response.status_code == 200 