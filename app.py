from config.main import GEMINI_API_KEY
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import speech
from google import genai
from utils.exception_handler import global_exception_handler
import asyncio
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_exception_handler(Exception, global_exception_handler)

client = genai.Client(api_key=GEMINI_API_KEY).aio

# Audio parameters
SAMPLE_RATE = 16000

# --- Helper: Summary Generation ---
async def generate_summary(transcript: str):
    output_schema = {
        'properties': {
            'history': {'type': 'array', 'items': {'type': 'string'}},
            'diagnosis': {'type': 'array', 'items': {'type': 'string'}},
            'medications': {'type': 'array', 'items': {'type': 'string'}},
            'tests': {'type': 'array', 'items': {'type': 'string'}},
            'instructions': {'type': 'array', 'items': {'type': 'string'}},
        },
        'required': ['history', 'diagnosis', 'medications', 'tests', 'instructions'],
        'type': 'object',
        'title': 'Summary'
    }
    
    prompt = "You are a medical assistant. Summarize this doctor-patient consultation transcript into structured JSON."
    
    contents = genai.types.Content(
        role='user',
        parts=[genai.types.Part.from_text(text=f"{prompt}\n\nTranscript:\n{transcript[:4000]}")]
    )
    
    try:
        response = await client.models.generate_content(
            model='gemini-2.0-flash', # Corrected model name
            contents=contents,
            config=genai.types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=output_schema
            ),
        )
        return response.text if hasattr(response, 'text') else str(response.parsed)
    except Exception as e:
        return {"error": "Summary failed", "details": str(e)}

# --- Helper: Optimized Streaming Logic ---
async def transcribe_streaming_audio(websocket: WebSocket, consultation_id: str):
    speech_client = get_speech_client('async')
    
    recognition_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="en-US",
        # model="medical_conversation", # Using medical model for better accuracy
        use_enhanced=True,
        alternative_language_codes=["kn-IN", "hi-IN"],
        enable_automatic_punctuation=True,
        diarization_config=speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=2,
            max_speaker_count=2,
        ),
    )
    
    streaming_config = speech.StreamingRecognitionConfig(
        config=recognition_config,
        interim_results=True
    )

    # This flag will help us exit the generator gracefully
    should_stop = False

    async def request_generator():
        yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
        nonlocal should_stop
        
        try:
            while not should_stop:
                # We use receive() so we can check if the client sent BYTES (audio) 
                # or TEXT (the "end" signal)
                message = await websocket.receive()
                
                if "bytes" in message:
                    yield speech.StreamingRecognizeRequest(audio_content=message["bytes"])
                
                elif "text" in message:
                    import json
                    data = json.loads(message["text"])
                    if data.get("type") == "end_session":
                        should_stop = True
                        break # Exit the generator
        except Exception as e:
            print(f"Generator error: {e}")

    full_transcript = []

    try:
        responses = await speech_client.streaming_recognize(requests=request_generator())

        async for response in responses:
            if not response.results:
                continue
            
            result = response.results[0]
            if result.is_final:
                alternative = result.alternatives[0]
                # (Speaker labeling)
                current_speaker = f"SPEAKER_{alternative.words[0].speaker_tag}" if alternative.words[0].speaker_tag else "1"
                text = alternative.transcript
                
                segment = f"[{current_speaker}]: {text}"
                full_transcript.append(segment)
                
                # Update the live transcript UI
                await websocket.send_json({
                    "type": "interim", 
                    "transcript": "\n".join(full_transcript), 
                    "is_final": True
                })

    except Exception as e:
        print(f"Streaming error: {e}")

    # --- TRIGGER SUMMARY ONLY AFTER LOOP ENDS ---
    if full_transcript:
        final_text = "\n".join(full_transcript)
        print("Generating final summary...")
        summary = await generate_summary(final_text)
        
        await websocket.send_json({
            "type": "summary",
            "summary": summary
        })
        
        await websocket.send_json({"type": "status", "message": "Complete"})
# --- WebSocket Endpoint ---
@app.websocket("/ws/transcribe/{consultation_id}")
async def websocket_endpoint(websocket: WebSocket, consultation_id: str):
    await websocket.accept()
    await websocket.send_json({"type": "connected", "message": "Listening..."})
    
    # Just call the helper function here!
    await transcribe_streaming_audio(websocket, consultation_id)
    
    await websocket.close()

# --- File Upload & Root ---
@app.post("/transcribe-file/{consultation_id}")
async def transcribe_file(consultation_id: str, file: UploadFile = File(...)):
    content = await file.read()
    speech_client = get_speech_client('sync') # Sync is fine for static files
    
    response = speech_client.recognize(
        config=speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US"
        ), 
        audio=speech.RecognitionAudio(content=content)
    )
    
    transcript = " ".join([r.alternatives[0].transcript for r in response.results])
    summary = await generate_summary(transcript)
    return {"transcript": transcript, "summary": summary}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("""
        <h1>Medical Transcription App</h1>
        <p>Please create <code>static/edit.html</code> file with the HTML client.</p>
        <p>WebSocket endpoint: <code>/ws/transcribe/{consultation_id}</code></p>
        """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)