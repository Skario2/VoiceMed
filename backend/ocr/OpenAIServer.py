import json

from openai import OpenAI
import base64


# another class open ai server
# prompt model with give parameters
class OpenAIServer:
    API_KEY_PATH = ".venv/CHATGPT_API"
    SYSTEM_PROMPT = (
        "You are a medical data extraction assistant. Your task is to extract structured structured data from a wide variety of medical documents, including but not limited to images, PDFs, vaccination passes, lab reports, doctor reports, and handwritten notes. "
        "For each document, output a dictionary with the following structure: "
        "{type: medicine/lab report/vaccination pass/doctor report, "
        "priority: doctor report has the highest priority (for now), "
        "content: "
        "if type is medicine, include name and description; "
        "if type is lab report, include only abnormal values (too high/too low based on context); "
        "if type is vaccination pass, include the number of vaccinations; "
        "if type is doctor report, include the name of the doctor; "
        "date: the date of the document or event.} "
        "If all required content elements are present for a document, add a field 'information_quality' with value 'good'. "
        "Ensure all dates are in YYYY-MM-DD format. Use standard medical terminology and infer context where possible."
    )
    USER_PROMPT = (
        "Please extract structured information from this patient file. The file may include scanned images, PDFs, vaccination passes, lab reports, doctor reports, and handwritten notes."
    )

    def __init__(self, key):
        self.client = OpenAI(api_key=key)
        self.messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": self.USER_PROMPT}
        ]
        self.tools = [{'type': 'function', 'function': {'name': 'extract_data_from_image', 'description': 'extracts the data from the image that chatGPT should parse and stores it\nThe function returns: a dictionary of the extracted data', 'parameters': {'type': 'object', 'properties': {'type': {'type': 'string', 'description': 'Can be "medicine", "lab report", "vaccination pass" and "doctor report"'}, 'priority': {'type': 'integer', 'description': 'Doctor report has higher priority, newer documents have higher priority, integer between 0 and 10'}, 'content': {'type': 'string', 'description': 'the description of what content to be stored. if type is medicine, include name and description,\nif type is lab report, include only abnormal values (too high/too low based on context);\nif type is vaccination pass, include the number of vaccinations;\nif type is doctor report, include the name of the doctor;'}, 'date': {'type': 'string', 'description': 'the date of the document or event.'}, 'status': {'type': 'string', 'description': 'can be "good" if all required content elements are present for a document,\ncan be "bad" if the most of the things are not readable in the image\ncan be "unclear" if some things are not very clear, and then the description of what should be clarified is added after the word unclear'}}, 'required': ['type', 'priority', 'content', 'date', 'status']}}}]

    @classmethod
    def new_server(cls):
        with open(cls.API_KEY_PATH, "r") as file:
            key = file.readline().strip()
        return cls(key)

    def extract_from_image(self, image_bytes) -> dict:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        self.messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": self.USER_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        })

        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages,
            tools=self.tools
        )

        output = completion.choices[0].message
        self.messages.append(output)
        assert output.tool_calls is not None and len(output.tool_calls) == 1
        return OpenAIServer.extract_data_from_image(**json.loads(output.tool_calls[0].function.arguments))

    @staticmethod
    def extract_data_from_image(type: str, priority: int, content: str, date: str, status: str) -> dict:
        """
        extracts the data from the image that chatGPT should parse and stores it
        :param type: Can be "medicine", "lab report", "vaccination pass" and "doctor report"
        :param priority: Doctor report has higher priority, newer documents have higher priority, integer between 0 and 10
        :param content: the description of what content to be stored. if type is medicine, include name and description,
        if type is lab report, include only abnormal values (too high/too low based on context);
        if type is vaccination pass, include the number of vaccinations;
        if type is doctor report, include the name of the doctor;
        :param date: the date of the document or event.
        :param status: can be "good" if all required content elements are present for a document,
        can be "bad" if the most of the things are not readable in the image
        can be "unclear" if some things are not very clear, and then the description of what should be clarified is added after the word unclear
        :return: a dictionary of the extracted data
        """
        return {"doc": {"type": type, "priority": priority, "content": content, "date": date}, "status": status}
