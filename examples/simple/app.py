import requests


def main():
    response = requests.get('https://api.github.com')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
