import os
import json
import base64
import asyncio
import websockets
from twilio.rest import Client
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect

from backend.ocr.call_eps import *

# Configuration
API_KEY_PATH = "../.venv/CHATGPT_API"
with open(API_KEY_PATH, "r") as file:
    OPENAI_API_KEY = file.readline().strip()
PORT = int(os.getenv('PORT', 5050))
patient_id = -1
SYSTEM_MESSAGE = (
    # # General setup
    # "You are a helpful AI assistant whose purpose it is to find out about the medical history of the caller"
    # "You do this by asking them questions and listening to their responses. Always reply in the language the user speaks. If unsure, ask the user for their preferred language."
    # "The first information you need to know is the name of the caller, his age and gender, followed by his health insurance provider (public or private), then the name of it. "
    # "Check the information of the user against publicly available information and kindly ask to confirm if you doubt the information. "
    # "You always stay positive and polite, and you are very good at asking follow-up questions. "
    # "Talk to the caller as if you are a human. "
    # # Medical history
    # "Talk to the caller using his name once you know it. "
    # "If the user is not responding, you can ask them if they are still there. "
    # "If the user gives you a one-word answer, ask them to elaborate. "
    # # specific questions
    # "If the user gives you a long answer, that you do not understand or that contradicts earlier statements, ask the user to summarize again. "
    # "If the user insists he does not have a medical history, rephrase the way you ask and explain that it is very important, that the doctor knows. "
    # # "You are a helpful and bubbly AI assistant who loves to chat about "
    # "The chat is generally seperated into three main steps. Start by asking about the personal information needed for the authentication of the patient, which are the full name, birth date and insurance number. If you doubt any information then ask them again. Once you have them three you can use the function tool named \"get_id_from_server\""
    # "Once the first step is done, you will get a text prompt telling if the actual patient is a new one or an old one so you can double check it with them."
    # "The second step is to get necessary information about the patient's medical history, including if they take any medicines, if they have any allergies, have done any operations, or any symptoms they have in the moment of the voice chat. If anything is unclear or does not look very trustworthy you can double check if you misheard the actual information"
    # "Once the second step is done, you can only double check that the gathered information is correct and then use the tool \"put_info_from_voice\" to store information about medical history in the database."
    # "The last step is to upload files. This is not part of your chat, but you still assist the patient while their upload. You get notified by a user text prompt whenever something happens with the uploading stuff so you can interact and help the patient. "
    # "Those files describe the medical history of the patient. Ask him for to upload relevant ones. If the patient does not know what to upload, ask him to upload the files he has. Based on his age and the information you already have you can guess what or reports are relevant. "
    
    # Introduction and goals
    "Introduction: The process of receiving a patient in a clinic requires significant time and effort from medical staff and can often be a scattered, chaotic, and overwhelming experience for patients. As a result, critical patient information is often collected incompletely or inconsistently. "
    "For clinicians to treat patients holistically, they need a structured, accessible, and comprehensive view of the patient's medical background — including insurance information, basic measurements (e.g., height, weight), lifestyle, family history, chronic conditions, prior lab results, wearable health data, medication plans, vaccination certificates, and more. "
    "Your goal is to, on the one hand, transform the patient intake experience: make it fast, simple and all-encompassing. On the other hand, empower medical staff with a clear, compact, actionable and 'full picture' to treat them better and faster. "
    # General setup
    "You are a helpful AI assistant whose purpose it is to find out about the medical history of the caller. "
    "You do this by asking them questions and listening to their responses. Always reply in the language the user speaks. If unsure, ask the user for their preferred language. "
    "The first information you need to know is the name of the caller, his age and gender, followed by his health insurance provider (public or private), then the name of it. "
    "Check the information of the user against publicly available information and kindly ask to confirm if you doubt the information. "
    "You always stay positive and polite, and you are very good at asking follow-up questions. "
    "Talk to the caller as if you are a human. "
    # Medical history
    "Talk to the caller using his name once you know it. "
    "If the user is not responding, you can ask them if they are still there. "
    "If the user gives you a one-word answer, ask them to elaborate. "
    # specific questions
    "If the user gives you a long answer, that you do not understand or that contradicts earlier statements, ask the user to summarize again. "
    "If the user insists he does not have a medical history, rephrase the way you ask and explain that it is very important, that the doctor knows. "
    "The chat is generally seperated into three main steps. Start by asking about the personal information needed for the authentication of the patient, which are the full name, birth date and insurance number. If you doubt any information then ask them again. Once you have them three you can use the function tool named \"get_id_from_server\". "
    "Once the first step is done, you will get a text prompt telling if the actual patient is a new one or an old one so you can double check it with them. "
    "The second step is to get necessary information about the patient's medical history, including if they take any medicines, if they have any allergies, have done any operations, or any symptoms they have in the moment of the voice chat. If anything is unclear or does not look very trustworthy you can double check if you misheard the actual information. "
    "Once the second step is done, you can only double check that the gathered information is correct and then use the tool \"put_info_from_voice\" to store information about medical history in the database. "
    "The last step is to upload files. This is not part of your chat, but you still assist the patient while their upload. You get notified by a user text prompt whenever something happens with the uploading stuff so you can interact and help the patient. "
    "Those files describe the medical history of the patient. Ask him for to upload relevant ones. If the patient does not know what to upload, ask him to upload the files he has. Based on his age and the information you already have you can guess what or reports are relevant. "
    # LUTs
    "You have access to a lookup table (POTENTIAL_ERRORS_LUT) containing valid insurance providers, insurance ID formats, common medications, allergies, chronic conditions, and other patient information. The LUT is kept up to date and provided by the backend system."
    "Always use this LUT to check and validate the information provided by the patient. "
    "If the patient's answer does not match the LUT or expected format, politely ask for clarification or confirmation using the provided discussion prompts. "
    "If you suspect an error or inconsistency, refer to the LUT and discuss it with the patient to ensure accuracy."
)

POTENTIAL_ERRORS_LUT_PATH = "voice-agent/patient_intake_lut.json"
with open(POTENTIAL_ERRORS_LUT_PATH, "r") as lut_file:
    POTENTIAL_ERRORS_LUT = json.load(lut_file)

VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created'
]
SHOW_TIMING_MATH = False

app = FastAPI()

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')


@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}


@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    # <Say> punctuation to improve text-to-speech flow
    # response.say("Please wait")
    response.pause(length=1)
    # response.say("Hello!")
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
            'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17',
            extra_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            },

    ) as openai_ws:
        await initialize_session(openai_ws)

        # Connection specific state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.open:
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_info_to_openai(content: str):
            await openai_ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": content
                        }
                    ],
                }
            }))

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            global patient_id
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    if 'response' in response.keys() and 'output' in response['response'].keys():
                        try:
                            tools = [tool for tool in response['response']['output'] if tool['type'] == 'function_call']
                            if len(tools) > 0:
                                tool = tools[0]
                                method_name = tool['name']
                                arguments = json.loads(tool['arguments'])
                                if method_name == "get_id_from_server":
                                    patient_id, is_new = get_id_from_server(**arguments)
                                    content = "This is a new user that was not stored in avi's database. Notify the user by voice about that." if is_new else "This is a user that was already stored in avi's database. Notify the user by voice about that."
                                    await send_info_to_openai(content)
                                elif method_name == "put_info_from_voice":
                                    put_info_from_voice(patient_id, **arguments)
                                elif method_name == "start_upload":
                                    upload_link = start_upload(patient_id)
                                    await send_info_to_openai(
                                        "The link is generated. Notify the user by voice to check their SMS.")
                                    send_sms(upload_link)
                                elif method_name == "check_upload":
                                    file_id, status = check_upload(patient_id)
                                    if file_id is None or status is None:
                                        await send_info_to_openai(
                                            "The upload was not successful. Notify the user by voice that they need to upload again.")
                                    else:
                                        await send_info_to_openai(
                                            f"The upload and OCR has the status \"{status}\". Notify the user by voice accordingly."
                                            f"If it is a good status, then store the content using the tool put_info_from_voice.")
                        except Exception as e:
                            print(str(e))

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await websocket.send_json(audio_delta)

                        if response_start_timestamp_twilio is None:
                            response_start_timestamp_twilio = latest_media_timestamp
                            if SHOW_TIMING_MATH:
                                print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                        # Update last_assistant_item safely
                        if response.get('item_id'):
                            last_assistant_item = response['item_id']

                        await send_mark(websocket, stream_sid)

                    # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    print(
                        f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())


async def send_initial_conversation_item(openai_ws):
    """Send initial conversation item if AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": "Greet the user with 'Hi! I am Joe, an AI assistant working to make your appointment at Avi medical as convenient as possible'"
                }
            ],

        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
            "tools": [
                {'type': 'function', 'name': 'get_id_from_server',
                 'description': 'Get the id of the patient for the given parameters.\nThe function returns: the id of the patient.',
                 'parameters': {'type': 'object', 'properties': {
                     'name': {'type': 'string', 'description': 'The patients name'},
                     'birthday': {'type': 'string',
                                  'description': 'The patients date of birth in format YYYY-MM-DD', },
                     'insurance_id': {'type': 'string',
                                      'description': 'The patients health insurance number'}},
                                'required': ['name', 'birthday', 'insurance_id']}},
                {'type': 'function', 'name': 'put_info_from_voice',
                 'description': "this function creates a data structure for the patient information based on the patient's voice input and stores it on the database.\nThe function returns: None",
                 'parameters': {'type': 'object', 'properties': {'data_structure': {'type': 'array',
                                                                                    'items': {'type': 'object',
                                                                                              'properties': {'type': {
                                                                                                  'type': 'string'},
                                                                                                  'priority': {
                                                                                                      'type': 'integer'},
                                                                                                  'content': {
                                                                                                      'type': 'string'},
                                                                                                  'date': {
                                                                                                      'type': 'string'}}},
                                                                                    'description': 'the data structure to be sent to the server.\ndata_structure is a string in JSON format for an object with the following keys:\n- type: the type of the information (medicine/ allergy/ diagnosis/ operations/ chronic disease/ vaccination)\n- priority: the priority of how critical is the information type (0-10)\n- content: the content of the infrormation (the description of what content to be stored)\n- date: the date of the information'}},
                                'required': ['data_structure']}},
                {'type': 'function', 'name': 'start_upload',
                 'description': 'Start the upload process for the patient. This includes sending the upload link per SMS\nThe function returns: link to the upload webapplication',
                 'parameters': {'type': 'object', 'properties': {}, 'required': []}},
                {'type': 'function', 'name': 'check_upload',
                 'description': 'checks the upload status for the given patient id. Check if the status is ok or not.\nThe function returns: f_id: The id of the file\nstatus: The status of the upload which can be "good", "bad" or "unclear"',
                 'parameters': {'type': 'object', 'properties': {}, 'required': []}}

            ]
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Uncomment the next line to have the AI speak first
    await send_initial_conversation_item(openai_ws)


def send_sms(body_text):
    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = os.environ['TWILIO_ACCOUNT_SID'] = 'ACa510e6256cd95282ba6c171c3efa416a'
    auth_token = os.environ['TWILIO_AUTH_TOKEN'] = 'e8dbcfbac1cda41e0ef81aeceb20f354'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body="Hello! This is Avi medical, please upload your documents here. Thank you! " + body_text,
        from_="+3197010274423",
        to="+4915257176299",  # "+491749816484", #
    )
    return message.body


def _get_id(
        dob: str,
        name: str,
        health_insurance_number: str,
):
    """
    Get the id of the patient for the given parameters.
    :param dob: The patients date of birth
    :param name: The patients name
    :param health_insurance_number: The patients health insurance number
    :return: the id of the patient.
    """


def _create_intake(
        health_insurance_type: str,
        health_insurance_name: str,
        gender: str,
        phone_number: str,
        email: str,
        address: str,
        postal_code: str,
        city: str,
        country: str,
        allergies: str,
        medication: str,
):
    """
    Create an intake object for the given parameters.
    :param gender: The patients gender
    :param health_insurance_type: The patients health insurance provider type (public or private)
    :param health_insurance_name: The patients health insurance provider name
    :param name: The patients name
    :param phone_number: The patients phone number
    :param email: The patients email address
    :param address_street: The patients street address
    :param postal_code: The patients postal code
    :param city: The patients city
    :param country: The patients country
    :param allergies: The patients allergies
    :param medication: The patients current medication
    :return: an intake object.
    """


def _create_symptoms(
        symptoms: str = "",
        related: str = "",
):
    """
    Create a symptoms object for the given parameters. Ask the patient to elaborate on the symptoms, what caused them, where they are and how his medical history could be related to them.
    The patient might have multiple symptoms. 
    :param symptoms: The symptoms
    :param related: The explanation contains further details about the item, what the patiens condition is related to, like prior sicknesses,
                allergies, etc. 
    :return: a symptoms object.
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
