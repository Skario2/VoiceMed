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

    @classmethod
    def new_server(cls):
        with open(cls.API_KEY_PATH, "r") as file:
            key = file.readline().strip()
        return cls(key)

    def extract_from_image(self, image_path: str) -> dict:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
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
