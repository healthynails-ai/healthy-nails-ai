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

    booking_state = {
        "intent": None,
        "service": None,
        "time": None,
        "name": None,
        "phone": None,
        "step": None
    }

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg["type"] == "prompt":
                user_speech = msg["voicePrompt"].lower()

                # Start booking flow
                if booking_state["step"] is None:
                    if "book" in user_speech or "appointment" in user_speech:
                        booking_state["intent"] = "booking"
                        booking_state["step"] = "ask_service"
                        reply = "Sure. What service would you like to book?"

                    elif any(word in user_speech for word in ["pedicure", "manicure", "eyebrow", "lip", "chin", "waxing"]):
                        booking_state["intent"] = "booking"
                        booking_state["service"] = user_speech
                        booking_state["step"] = "ask_time"
                        reply = "Great. What day and time would you like to come in?"

                    elif "close" in user_speech or "hours" in user_speech:
                        reply = "We are open Monday through Friday from 10 AM to 7 PM, Saturday from 9 AM to 6:30 PM, and Sunday from 10 AM to 6 PM."

                    elif "late" in user_speech:
                        reply = "No problem at all. May I have your name and appointment time so we can notify the team?"

                    elif "cancel" in user_speech or "reschedule" in user_speech:
                        reply = "I can help with that. Can you tell me your name and your appointment time and phone number?"

                    elif any(word in user_speech for word in ["price", "cost", "how much", "charge"]):
                        reply = "Prices vary by service. What service are you interested in?"

                    else:
                        reply = "I can help you book an appointment, check business hours, or assist with your visit. What would you like to do?"

                elif booking_state["step"] == "ask_service":
                    booking_state["service"] = user_speech
                    booking_state["step"] = "ask_time"
                    reply = "Great. What day and time would you like to come in?"

                elif booking_state["step"] == "ask_time":
                    booking_state["time"] = user_speech
                    booking_state["step"] = "ask_name"
                    reply = "Thank you. May I have your name?"

                elif booking_state["step"] == "ask_name":
                    booking_state["name"] = msg["voicePrompt"]
                    booking_state["step"] = "ask_phone"
                    reply = "Thanks. What is the best phone number for this appointment?"

                elif booking_state["step"] == "ask_phone":
                    booking_state["phone"] = msg["voicePrompt"]
                    booking_state["step"] = "complete"
                    reply = (
                        f"Perfect. I have your booking request for {booking_state['service']} "
                        f"at {booking_state['time']} under {booking_state['name']} "
                        f"with phone number {booking_state['phone']}. "
                        f"A team member will confirm your appointment soon."
                    )

                else:
                    reply = "Your booking request has already been recorded. Is there anything else I can help you with?"

                await websocket.send_text(json.dumps({
                    "type": "text",
                    "token": reply,
                    "last": True
                }))

    except:
        await websocket.close()