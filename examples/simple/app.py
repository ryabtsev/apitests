import requests


def main():
    response = requests.get('https://api.github.com')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    response = requests.post('https://api.nationalize.io/?name=kate')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    if response.status_code == 404:
        response = requests.get('https://ipinfo.io/161.185.160.93/geo')
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
