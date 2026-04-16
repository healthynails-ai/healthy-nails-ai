from fastapi import FastAPI, WebSocket
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Connect
import json

app = FastAPI()

WELCOME_MESSAGE = "Thank you for calling Healthy Nails and Spa. How can I help you today?"

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def incoming_call():
    response = VoiceResponse()
    
    connect = Connect()
    connect.conversation_relay(
        url="wss://healthy-nails-ai.onrender.com/ws",
        welcomeGreeting=WELCOME_MESSAGE
    )
    
    response.append(connect)
    return Response(content=str(response), media_type="application/xml")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg["type"] == "prompt":
                user_speech = msg["voicePrompt"].lower()

                # Smarter conversation flow

                elif "AI" in user_speech or "Human" in user_speech:
                    reply = "I'm AI. I can answer your question, and help you to setup your appointment nedds."

                if any(word in user_speech for word in ["build", "built", "create", "created", "develop", "made", "make"]):
                    reply = "My master, he train and treat me very well. His name is Hanh Dang, I called him is Henry"                    

                if "pedicure" in user_speech or "manicure" in user_speech:
                    reply = "Great choice. What day and time would you like to come in?"

                elif "book" in user_speech or "appointment" in user_speech:
                    reply = "Sure, what service are you looking for and what time works best for you?"

                elif "ai" in user_speech or "human" in user_speech:
                    reply = "I'm AI. I can answer your question, and help you to setup your appointment needs."

                elif "close" in user_speech or "hours" in user_speech:
                    reply = "We are open Monday through Friday from 10 AM to 7 PM, Saturday from 9 AM to 6:30 PM, and Sunday from 10 AM to 6 PM."

                elif "late" in user_speech:
                    reply = "No problem at all. May I have your name and appointment time so we can notify the team?"

                elif "cancel" in user_speech or "reschedule" in user_speech:
                    reply = "I can help with that. Can you tell me your name and your appointment time and phone number?"

                elif "price" in user_speech:
                    reply = "Prices vary by service. I can help you book or you can check full pricing on our website."

                else:
                    reply = "I can help you book an appointment, check business hours, or assist with your visit. What would you like to do?"

                await websocket.send_text(json.dumps({
                    "type": "text",
                    "token": reply,
                    "last": True
                }))

    except:
        await websocket.close()