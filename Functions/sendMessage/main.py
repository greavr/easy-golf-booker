import base64
import sys
import logging
import os
from google.cloud import secretmanager
from twilio.rest import Client


project_id = os.environ.get('GCP_PROJECT', '')
target_number = os.environ.get('number','14088170403')
account_sid = ""
auth_token = ""
sender_num = ""

def GetSecrets():
    global project_id, account_sid, auth_token, sender_num
    try:
        client = secretmanager.SecretManagerServiceClient()
        sid_path = f"projects/{project_id}/secrets/sid/versions/latest"
        auth_path = f"projects/{project_id}/secrets/auth/versions/latest"
        sender_path = f"projects/{project_id}/secrets/sender_num/versions/latest"

        sid_raw_response = client.access_secret_version(request={"name": sid_path})
        auth_raw_response = client.access_secret_version(request={"name": auth_path})
        sender_raw_response = client.access_secret_version(request={"name": sender_path})

        account_sid = sid_raw_response.payload.data.decode("UTF-8")
        auth_token = auth_raw_response.payload.data.decode("UTF-8")
        sender_num = sender_raw_response.payload.data.decode("UTF-8")

        logging.info("Accessed secrets for Auth_tokent and SID")
        return True
    except:
        e = sys.exc_info()[0]
        logging.error("Unable to find secrets")
        logging.error(e)
        return False

def send_sms(DataTosend):
     # Your Account Sid and Auth Token from twilio.com/console
     global target_number, account_sid, auth_token, sender_num

     if GetSecrets():
        # Create Twillio Txt
        client = Client(account_sid, auth_token)  

        ## itterate over target numbers
        for aNumber in target_number.split(','):
            message = client.messages.create(
                                    from_=sender_num,
                                    body=DataTosend,
                                    to=aNumber
                                )
        return "success"
     else:
        return "error"

def hello_pubsub(event, context):
     """Triggered from a message on a Cloud Pub/Sub topic.
     Args:
          event (dict): Event payload.
          context (google.cloud.functions.Context): Metadata for the event.
     """
     pubsub_message = base64.b64decode(event['data']).decode('utf-8')
     print(pubsub_message)
     send_sms(pubsub_message)

if __name__ == "__main__":
    send_sms("local test")