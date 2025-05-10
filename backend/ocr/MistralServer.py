import base64

from mistralai import Mistral

def encode_pdf(pdf_path):
    """Encode the pdf to base64."""
    try:
        with open(pdf_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {pdf_path} was not found.")
        return None
    except Exception as e:  # Added general exception handling
        print(f"Error: {e}")
        return None

def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:  # Added general exception handling
        print(f"Error: {e}")
        return None


API_KEY_PATH = '../../.venv/MISTRAL_API_KEY'
api_key = open(API_KEY_PATH, 'r').read()

pdf_path = "/home/mohmaed/Downloads/lab3.pdf"

# Getting the base64 string
#base64_image = encode_image(image_path)
base64_pdf = encode_pdf(pdf_path)

client = Mistral(api_key=api_key)


ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "document_url",
        "document_url": f"data:application/pdf;base64,{base64_pdf}"
    }
)


# Print the content of the response
with open('test.txt', "w") as pdf_file:
    pdf_file.write(ocr_response.pages[0].markdown)