import requests

def get_data(api):
    response = requests.get(f"{api}")
    if response.status_code == 200:
        return response.json()
    else:
        return response

