from OpenAIServer import OpenAIServer
import os

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "../../resources/lab3.jpg")
    image_path = os.path.normpath(image_path)  # Normalize the path

    server = OpenAIServer.new_server()
    response = server.extract_from_image(image_path)
    print(response)