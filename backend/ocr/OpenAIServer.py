from openai import OpenAI
import base64

# another class open ai server
# prompt model with give parameters
class OpenAIServer:
    API_KEY_PATH = ".venv/CHATGPT_API"
    SYSTEM_PROMPT = (
        "You are a medical data extraction assistant. Your task is to extract structured data from medical documents including images, PDFs, and unstructured notes. "
        "The output should be in JSON format. Extract patient identifiers, medications (name, dosage, frequency, start/end dates), appointments (date, doctor, department, status), "
        "and lab reports (test name, result, date, unit). Ensure all dates are in YYYY-MM-DD format and map ambiguous terms using standard medical terminology."
    )
    USER_PROMPT = (
        "Please extract the medication history, upcoming and past appointments, and lab test results from this patient file. "
        "The file may include scanned images and PDFs."
    )

    def __init__(self, key):
        self.client = OpenAI(api_key=key)
        self.messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": self.USER_PROMPT}
        ]

    @classmethod
    def new_server(cls):
        with open(cls.API_KEY_PATH, "r") as file:
            key = file.readline().strip()
        return cls(key)

    def extract_from_image(self, image_bytes: bytes) -> dict:
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
        )
        output = completion.choices[0].message
        self.messages.append(output)
        return {"content": output.content}
