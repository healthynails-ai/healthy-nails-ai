import os
from datetime import datetime, timedelta
from dateutil import parser
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

SCOPES = ["https://www.googleapis.com/auth/calendar"]

BUSINESS_TIMEZONE = "America/Los_Angeles"


def get_calendar_service():
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)
    return service


def convert_booking_to_datetime(date_text, time_text):
    now = datetime.now()

    date_text_lower = str(date_text).lower().strip()
    time_text_lower = str(time_text).lower().strip()

    if date_text_lower == "today":
        base_date = now.date()
    elif date_text_lower == "tomorrow":
        base_date = (now + timedelta(days=1)).date()
    else:
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        if date_text_lower in weekdays:
            target_weekday = weekdays[date_text_lower]
            days_ahead = target_weekday - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            base_date = (now + timedelta(days=days_ahead)).date()
        else:
            parsed_date = parser.parse(date_text)
            base_date = parsed_date.date()

    if time_text_lower == "morning":
        hour = 10
        minute = 0
    elif time_text_lower == "afternoon":
        hour = 14
        minute = 0
    elif time_text_lower == "evening":
        hour = 17
        minute = 0
    else:
        parsed_time = parser.parse(time_text)
        hour = parsed_time.hour
        minute = parsed_time.minute

    start_dt = datetime.combine(base_date, datetime.min.time()).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    end_dt = start_dt + timedelta(hours=1)

    return start_dt, end_dt


def create_booking_event(service_name, customer_name, customer_phone, date_text, time_text):
    service = get_calendar_service()

    start_dt, end_dt = convert_booking_to_datetime(date_text, time_text)

    event = {
        "summary": f"{service_name.title()} Appointment - {customer_name}",
        "description": (
            f"Customer Name: {customer_name}\n"
            f"Phone: {customer_phone}\n"
            f"Service: {service_name}\n"
            f"Booked by AI receptionist"
        ),
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": BUSINESS_TIMEZONE,
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": BUSINESS_TIMEZONE,
        },
    }

    created_event = service.events().insert(calendarId="primary", body=event).execute()
    return created_event.get("id"), created_event.get("htmlLink")