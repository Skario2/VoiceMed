import requests

SERVER_URL = "http://localhost:5000"  # Change to your actual server URL

def get_id_from_server(name, birthday, insurance_id):
    params = {
        "name": name,
        "birthday": birthday,
        "insurance_id": insurance_id
    }
    response = requests.get(f"{SERVER_URL}/api/id", params=params)
    return response.json()["id"] if response.status_code == 200 else None

def put_info_from_voice(data_structure):
    response = requests.put(f"{SERVER_URL}/api/info", json=data_structure)
    return response.json() if response.status_code == 200 else None

def start_upload(p_id):
    response = requests.put(f"{SERVER_URL}/api/start-upload", json={"p_id": p_id})
    if response.status_code == 200:
        return response.json().get("link")
    return None

def check_upload(p_id):
    params = {"p_id": p_id}
    response = requests.get(f"{SERVER_URL}/api/upload-stats", params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("file_id"), data.get("status")
    return None, None

# Example usage:
if __name__ == "__main__":
    result = get_id_from_server("John Doe", "1980-01-01", "A123456")
    print(result)

