import requests

SERVER_URL = "http://localhost:5000"  # Change to your actual server URL

def get_id_from_server(name : str, birthday: str, insurance_id: str) -> tuple[str, bool]:
    """
        Get the id of the patient for the given parameters.
        :param name: The patients name
        :param birthday: The patients date of birth in the format YYYY-MM-DD
        :param insurance_id: The patients health insurance number
        :return: the id of the patient.
    """
    params = {
        "name": name,
        "birthday": birthday,
        "insurance_id": insurance_id
    }
    response = requests.get(f"{SERVER_URL}/api/id", params=params)
    return response.json()['id'], response.json()['is_new'] if response.status_code == 200 else None

def put_info_from_voice(patient_id, data_structure) -> None:
    """
    create a data structure for the patient information based on the patient's voice input.
    :param patient_id: The patient's ID
    :param data_structure: the data structure to be sent to the server.
    data_structure is a dictionary with the following keys:
        - type: the type of the information (medicine/ allergy/ diagnosis/ operations/ chronic disease/ vaccination)
        - priority: the priority of how critical is the information type (0-10)
        - content: the content of the information (the description of what content to be stored)
        - date: the date of the information
    :type data_structure: [{
        "type": "str",
        "priority": "int",
        "content": "str",
        "date": "str"
        }]
    :return: None
    """
    response = requests.post(f"{SERVER_URL}/api/info", json=data_structure, params={"patient_id": patient_id})
    return response.json() if response.status_code == 200 else None

def start_upload(p_id: str) -> str | None:
    """
    Start the upload process for the patient. This includes sending the upload link per SMS
    :param p_id: The id of the patient
    :type p_id: int
    :return: link to the upload webapplication
    """    
    response = requests.put(f"{SERVER_URL}/api/start-upload", params={"patient_id": p_id})
    if response.status_code == 200:
        return response.json().get("link")
    return None

def check_upload(p_id):
    """
    checks the upload status for the given patient id. Check if the status is ok or not.
    :param p_id: The id of the patient
    :type p_id: int
    :return: f_id: The id of the file
             status: The status of the upload which can be "good", "bad" or "unclear"
    :rtype: tuple
    """    
    params = {"patient_id": p_id}
    response = requests.get(f"{SERVER_URL}/api/upload-stats", params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("file_id"), data.get("status")
    return None, None

def change_content(p_id, f_id, new_content: str):
     """
     Change the content of the file with the given id.
     :param p_id: The id of the patient
     :param f_id: The id of the file
     :param new_content: The new content of the file
     :return: None
     """
     response = requests.put(f"{SERVER_URL}/api/content", params={"patient_id": p_id, "file_id": f_id}, json=new_content)
     return response.json() if response.status_code == 200 else None



method_names = {'get_id_from_server': get_id_from_server,
                'put_info_from_voice': put_info_from_voice,
                'start_upload': start_upload,
                'check_upload': check_upload}

# Example usage:
if __name__ == "__main__":
    result = get_id_from_server("John Doe", "1980-01-01", "A123456")
    print(result)

