# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

def send_sms(body_text):
    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = os.environ['TWILIO_ACCOUNT_SID'] = 'ACa510e6256cd95282ba6c171c3efa416a'
    auth_token = os.environ['TWILIO_AUTH_TOKEN'] = 'e8dbcfbac1cda41e0ef81aeceb20f354'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body="Hello! This is Avi medical, please upload your documents here. Thank you! " + body_text,
        from_="+3197010274423",
        to="+491749816484",
    )

    return message.body

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid=os.environ['TWILIO_ACCOUNT_SID']='ACa510e6256cd95282ba6c171c3efa416a'
auth_token=os.environ['TWILIO_AUTH_TOKEN']='e8dbcfbac1cda41e0ef81aeceb20f354'
client = Client(account_sid, auth_token)

message = client.messages.create(
    body="Hello! This is Avi medical, please upload your documents here. Thank you!",
    from_="+3197010274423",
    to="+491749816484",
)

print(message.body)