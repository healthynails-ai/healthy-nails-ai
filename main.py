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

                if booking_state["step"] is None:
                    if "book" in user_speech or "appointment" in user_speech:
                        booking_state["intent"] = "booking"

                        # Detect long sentence → slow user down
                        if any(word in user_speech for word in [
                            "tomorrow", "today", "monday", "tuesday", "wednesday",
                            "thursday", "friday", "saturday", "sunday",
                            "am", "pm", "name is", "my name", "phone", "number"
                        ]):
                            booking_state["step"] = "ask_service"
                            reply = "I heard a few details. Let’s do this one step at a time so I get everything correct. First, what service would you like to book?"
                        else:
                            booking_state["step"] = "ask_service"
                            reply = "Sure. What service would you like to book?"

                    elif any(word in user_speech for word in ["pedicure", "manicure", "eyebrow", "lip", "chin", "waxing"]):
                        booking_state["intent"] = "booking"

                        # If they gave too much info early → reset cleanly
                        if any(word in user_speech for word in [
                            "tomorrow", "today", "monday", "tuesday", "wednesday",
                            "thursday", "friday", "saturday", "sunday",
                            "am", "pm", "name is", "my name", "phone", "number"
                        ]):
                            booking_state["step"] = "ask_service"
                            reply = "I heard a few details. Let’s start with the service so I get everything correct. What service would you like to book?"
                        else:
                            booking_state["service"] = msg["voicePrompt"]
                            booking_state["step"] = "confirm_service"
                            reply = f"I heard {booking_state['service']}. Is that correct?"

                    elif "close" in user_speech or "hours" in user_speech:
                        reply = "We are open Monday through Friday from 10 A M to 7 P M, Saturday from 9 A M to 6:30 P M, and Sunday from 10 A M to 6 P M."

                    elif "late" in user_speech:
                        reply = "No problem. Please tell me your name and appointment time."

                    elif "cancel" in user_speech or "reschedule" in user_speech:
                        reply = "I can help with that. Please tell me your name and appointment time."

                    elif any(word in user_speech for word in ["price", "cost", "how much", "charge"]):
                        reply = "Prices vary by service. What service are you interested in?"

                    else:
                        reply = "I can help you book an appointment, check business hours, or assist with your visit. What would you like to do?"

                elif booking_state["step"] == "ask_service":
                    booking_state["service"] = msg["voicePrompt"]
                    booking_state["step"] = "confirm_service"
                    reply = f"I heard {booking_state['service']}. Is that correct?"

                elif booking_state["step"] == "confirm_service":
                    if "yes" in user_speech or "correct" in user_speech or "right" in user_speech:
                        booking_state["step"] = "ask_day"
                        reply = "Great. What day would you like to come in?"
                    else:
                        booking_state["step"] = "ask_service"
                        reply = "Okay. Please say the service again."

                elif booking_state["step"] == "ask_day":
                    booking_state["day"] = msg["voicePrompt"]
                    booking_state["step"] = "confirm_day"
                    reply = f"I heard {booking_state['day']}. Is that correct?"

                elif booking_state["step"] == "confirm_day":
                    if "yes" in user_speech or "correct" in user_speech or "right" in user_speech:
                        booking_state["step"] = "ask_time"
                        reply = "What time would you like?"
                    else:
                        booking_state["step"] = "ask_day"
                        reply = "Okay. Please say the day again."

                elif booking_state["step"] == "ask_time":
                    booking_state["time"] = msg["voicePrompt"]
                    booking_state["step"] = "confirm_time"
                    reply = f"I heard {booking_state['time']}. Is that correct?"

                elif booking_state["step"] == "confirm_time":
                    if "yes" in user_speech or "correct" in user_speech or "right" in user_speech:
                        booking_state["step"] = "ask_name"
                        reply = "Thank you. May I have your name?"
                    else:
                        booking_state["step"] = "ask_time"
                        reply = "Okay. Please say the time again."

                elif booking_state["step"] == "ask_name":
                    booking_state["name"] = msg["voicePrompt"]
                    booking_state["step"] = "confirm_name"
                    reply = f"I heard {booking_state['name']}. Is that correct?"

                elif booking_state["step"] == "confirm_name":
                    if "yes" in user_speech or "correct" in user_speech or "right" in user_speech:
                        booking_state["step"] = "ask_phone"
                        reply = "What is the best phone number for this appointment?"
                    else:
                        booking_state["step"] = "ask_name"
                        reply = "Okay. Please say your name again."

                elif booking_state["step"] == "ask_phone":
                    booking_state["phone"] = msg["voicePrompt"]
                    booking_state["step"] = "confirm_phone"
                    reply = f"I heard {booking_state['phone']}. Is that correct?"

                elif booking_state["step"] == "confirm_phone":
                    if "yes" in user_speech or "correct" in user_speech or "right" in user_speech:
                        booking_state["step"] = "anything_else"
                        reply = (
                            f"Perfect. I have your booking request for {booking_state['service']} "
                            f"on {booking_state['day']} at {booking_state['time']} "
                            f"under {booking_state['name']} with phone number {booking_state['phone']}. "
                            f"A team member will confirm your appointment soon. "
                            f"Is there anything else I can help you with?"
                        )
                    else:
                        booking_state["step"] = "ask_phone"
                        reply = "Okay. Please say your phone number again."

                elif booking_state["step"] == "anything_else":
                    if any(word in user_speech for word in [
                        "no", "nope", "that's it", "that is it", "that's all",
                        "that is all", "all set", "nothing else", "no thanks"
                    ]):
                        reply = "Thank you for calling Healthy Nails and Spa. Goodbye."
                        await websocket.send_text(json.dumps({
                            "type": "text",
                            "token": reply,
                            "last": True
                        }))
                        await websocket.close()
                        break
                    else:
                        booking_state["step"] = None
                        reply = "Of course. How else can I help you today?"

                else:
                    reply = "Your booking request has already been recorded. Is there anything else I can help you with?"

                await websocket.send_text(json.dumps({
                    "type": "text",
                    "token": reply,
                    "last": True
                }))

    except:
        await websocket.close()