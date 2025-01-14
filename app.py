from flask import Flask, request, send_from_directory
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from flask import jsonify
import whisper
import requests
import os
import ffmpeg
import logging
from rasa.core.agent import Agent
import asyncio


BASE_URL = 'https://b452-110-5-74-38.ngrok-free.app'

rasa_agent = None

async def load_agent():
    global rasa_agent
    rasa_agent = await Agent.load("rasa_bot/models")

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Twilio credentials (replace with your actual credentials)

account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')
client = Client(account_sid, auth_token)

# Twilio phone number
TWILIO_PHONE_NUMBER = '+1 218 757 2555'

# Smallest AI API Key for Lightning TTS
LIGHTNING_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2NzdhMzI3OWM0NDE1ODdhYjZlODJhNjUiLCJ0eXBlIjoiYXBpS2V5IiwiaWF0IjoxNzM2MDYxNTYxLCJleHAiOjQ4OTE4MjE1NjF9.zxIiI4jVl21xaqi6rOX68aO69CB1lm9eCN_6z_9nS20'

# Load Whisper model (Base model)
model = whisper.load_model("base")


# TTS Function (Lightning)
def synthesize_speech(text, voice_id='raghav', sample_rate=24000, speed=1.0):
    if not LIGHTNING_API_KEY:
        raise ValueError("Missing API Key. Set 'LIGHTNING_API_KEY' as an environment variable.")
    
    endpoint = 'https://waves-api.smallest.ai/api/v1/lightning/get_speech'
    payload = {
        "voice_id": voice_id,
        "text": text,
        "speed": speed,
        "sample_rate": sample_rate,
        "add_wav_header": True
    }
    headers = {
        'Authorization': f'Bearer {LIGHTNING_API_KEY}',
        'Content-Type': 'application/json'
    }

    try:
        logger.info(f"Sending TTS request to {endpoint}")
        response = requests.post(endpoint, json=payload, headers=headers)

        if response.status_code == 200:
            audio_path = 'static/output.wav'
            with open(audio_path, 'wb') as audio_file:
                audio_file.write(response.content)
            logger.info("Audio successfully generated!")

            # Convert WAV to MP3
            mp3_path = 'static/output.mp3'
            ffmpeg.input(audio_path).output(mp3_path).run(overwrite_output=True)
            return mp3_path
        else:
            logger.error(f"TTS API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception in TTS: {e}", exc_info=True)
        return None


# Index Route
@app.route("/")
def index():
    logger.info("Index route accessed")
    return "AI Phone Agent is Running!"


# Make Call Route
 

@app.route('/make_call', methods=['POST'])
def make_call():
    data = request.get_json()
    phone_number = data.get('phone')

    if not phone_number:
        return jsonify({"error": "Phone number is required!"}), 400

    try:
        call = client.calls.create(
            twiml='<Response><Say>Hello! This is a test call from your Twilio app.</Say></Response>',
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER
        )
        return jsonify({"message": "Call initiated", "call_sid": call.sid}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# Voice Route (TTS + Record)
@app.route("/voice", methods=['POST'])
def voice_response():
    response = VoiceResponse()
    message = "Hello! This is Sujal from AI Phone Agent. Please leave a message."

    # Generate TTS Audio
    audio_file = synthesize_speech(message)
    if audio_file:
        audio_url = f'     https://b452-110-5-74-38.ngrok-free.app/static/output.mp3'
        logger.info(f"Playing audio from: {audio_url}")
        response.play(audio_url)
    else:
        logger.warning("Falling back to Twilio TTS.")
        response.say(message)

    # Record User Response
    response.record(max_length=30, action='/transcribe', recording_format='mp3')
    return str(response)


@app.route("/transcribe", methods=['POST'])
async def transcribe_audio():
    import time
    
    # Log all incoming form data for debugging
    logger.debug(f"Received form data: {dict(request.form)}")
    
    recording_url = request.form.get('RecordingUrl')
    recording_sid = request.form.get('RecordingSid')
    
    if not recording_url:
        logger.error("No RecordingUrl provided in request")
        return "Recording URL missing!", 400
        
    logger.info(f"Processing recording SID: {recording_sid}")
    logger.info(f"Recording URL: {recording_url}")
    
    # Create unique filenames using recording SID
    audio_path = f'static/recorded_audio_{recording_sid}.mp3'
    wav_path = f'static/recorded_audio_{recording_sid}.wav'
    
    try:
        # Add delay and log the wait
        logger.info("Waiting for recording to be available...")
        time.sleep(2)
        
        # Download the audio
        logger.info("Attempting to download audio...")
        download_audio(recording_url, audio_path)
        
        # Convert to WAV
        logger.info("Converting MP3 to WAV...")
        ffmpeg.input(audio_path).output(wav_path).run(overwrite_output=True)
        
        # Transcribe
        logger.info("Starting transcription...")
        transcription = transcribe_file(wav_path)
        logger.info(f"Transcription completed: {transcription}")

        # Get Rasa response
        try:
            rasa_response = await rasa_agent.handle_text(transcription)
            bot_response = rasa_response[0]['text'] if rasa_response else "I apologize, I didn't understand that. Could you please rephrase?"
            logger.info(f"Rasa response: {bot_response}")

            # Generate TTS for bot response
            logger.info("Generating TTS for bot response...")
            response_audio = synthesize_speech(bot_response)
            response_audio_url = f"{BASE_URL}/static/{os.path.basename(response_audio)}" if response_audio else None

        except Exception as rasa_error:
            logger.error(f"Rasa processing error: {rasa_error}")
            bot_response = "I'm having trouble processing your request. Please try again."
            response_audio_url = None
        
        # Cleanup files
        try:
            os.remove(audio_path)
            os.remove(wav_path)
            logger.info("Temporary audio files cleaned up")
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup audio files: {cleanup_error}")
        
        return jsonify({
            "success": True,
            "transcription": transcription,
            "recording_sid": recording_sid,
            "bot_response": bot_response,
            "response_audio_url": response_audio_url
        })
        
    except FileNotFoundError as fnf:
        logger.error(f"File not found error: {fnf}")
        return jsonify({
            "success": False,
            "error": "Recording not found or not yet available",
            "details": str(fnf)
        }), 404
        
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to transcribe audio",
            "details": str(e)
        }), 500
    
    finally:
        # Cleanup in case of any errors
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup files in finally block: {e}")
# Download audio from Twilio (Secure)
 
def download_audio(url, save_path):
    try:
        response = requests.get(url, auth=(account_sid, auth_token))
        logger.info(f"Download attempt status: {response.status_code}")
        logger.debug(f"Response content: {response.text[:200]}")  # Log first 200 chars of response
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Audio downloaded to {save_path}")
        else:
            logger.error(f"Failed to download audio. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise FileNotFoundError(f"Recording not found or deleted. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Exception during download: {str(e)}", exc_info=True)
        raise


# Transcribe with Whisper
def transcribe_file(audio_file):
    result = model.transcribe(audio_file, fp16=False)
    return result["text"]


# Serve Static Files (for audio playback)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    print("Starting Flask app...")
    app.run(debug=True)
