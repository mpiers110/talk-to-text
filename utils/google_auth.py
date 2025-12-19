import os
import json
from google.oauth2 import service_account
from google.cloud import speech
from google.cloud.speech_v1 import SpeechAsyncClient # Correct Async Client

def get_speech_client(type: str):
    """Get authenticated Speech client for both local and Render"""
    
    # Check if running on Render with service account JSON in env var
    google_creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    
    if google_creds_json:
        # Render: Use JSON from environment variable
        credentials_info = json.loads(google_creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info
        )
        if type == "sync":
            return speech.SpeechClient(credentials=credentials)
        else:
            return SpeechAsyncClient(credentials=credentials)
    else:
        # Local: Use application default credentials
        if type == "sync":
            return speech.SpeechClient()
        else:
            return SpeechAsyncClient()
