from datetime import datetime, timedelta
from pathlib import Path
import pytz
from config import TIME_ZONE

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class Calendar:    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.token_file = Path("data/calendar/token.json")
        self.credentials_file = Path("data/calendar/credentials.json")
        self.timezone = pytz.timezone(TIME_ZONE)
        
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._authenticate()
    
    def _local_to_utc(self, dt_str: str) -> str:
        """Convert local datetime string to UTC datetime string"""
        local_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        local_dt = self.timezone.localize(local_dt)
        utc_dt = local_dt.astimezone(pytz.UTC)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    def _utc_to_local(self, dt_str: str) -> str:
        """Convert UTC datetime string to local datetime string"""
        if not dt_str:
            return dt_str
            
        try:
            utc_dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            try:
                utc_dt = datetime.strptime(dt_str.split('+')[0], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                try:
                    utc_dt = datetime.strptime(dt_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    return dt_str
        
        utc_dt = pytz.UTC.localize(utc_dt)
        local_dt = utc_dt.astimezone(self.timezone)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        if self.token_file.exists():
            self.creds = Credentials.from_authorized_user_file(str(self.token_file), self.SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not self.credentials_file.exists():
                    raise FileNotFoundError(
                        "credentials.json not found. Please download it from Google Cloud Console "
                        "and place it in data/calendar/credentials.json"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_file), self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('calendar', 'v3', credentials=self.creds)
    
    def process(self, mode: str, range_val: int = 10, event_id: str = None, 
                title: str = None, description: str = None, 
                start_time: str = None, end_time: str = None) -> str:
        """Process calendar operations based on mode"""
        try:
            if mode == 'r':
                return self._read_events(range_val)
            elif mode == 'w':
                return self._write_event(event_id, title, description, start_time, end_time)
            elif mode == 'd':
                return self._delete_event(event_id)
            else:
                return "Invalid mode. Use 'r' for read, 'w' for write, or 'd' for delete."
        except HttpError as error:
            return f"An error occurred: {error}"
    
    def _read_events(self, range_val: int = 10) -> str:
        """Read calendar events"""
        now = datetime.now(self.timezone)
        
        if range_val >= 0:
            time_min = now.astimezone(pytz.UTC).isoformat()
            time_max = (now + timedelta(days=abs(range_val))).astimezone(pytz.UTC).isoformat()
        else:
            time_min = (now + timedelta(days=range_val)).astimezone(pytz.UTC).isoformat()
            time_max = now.astimezone(pytz.UTC).isoformat()
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=abs(range_val),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return 'No events found.'
        
        result = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if start:
                start = start.replace('T', ' ').split('+')[0].split('.')[0] 
            
            end = event['end'].get('dateTime', event['end'].get('date'))
            if end:
                end = end.replace('T', ' ').split('+')[0].split('.')[0] 
                
            description = event.get('description', '')
            
            event_details = []
            event_details.append(f"Event: {event['summary']}")
            if description:
                event_details.append(f"Description: {description}")
            event_details.append(f"When: {start} to {end} {TIME_ZONE}")
            event_details.append(f"ID: {event['id']}")
            
            result.append(" | ".join(event_details))
        
        if abs(range_val) == 1:
            return result[0] if result else 'No events found.'
        
        return "\n".join(result)
    
    def _write_event(self, event_id: str = None, title: str = None, 
                     description: str = None, start_time: str = None, 
                     end_time: str = None) -> str:
        """Write or update a calendar event"""
        if not all([title, start_time, end_time]):
            return "Missing required fields: title, start_time, and end_time are required"
        
        try:
            start_utc = self._local_to_utc(start_time)
            end_utc = self._local_to_utc(end_time)
            
            event = {
                'summary': title,
                'description': description or '',
                'start': {
                    'dateTime': start_utc,
                    'timeZone': TIME_ZONE
                },
                'end': {
                    'dateTime': end_utc,
                    'timeZone': TIME_ZONE
                }
            }
            
            if event_id:
                updated_event = self.service.events().update(
                    calendarId='primary',
                    eventId=event_id,
                    body=event
                ).execute()
                return f"Event updated: {updated_event['htmlLink']}"
            else:
                created_event = self.service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()
                return f"Event created: {created_event['htmlLink']}"
        except ValueError as e:
            return f"Error: Invalid datetime format. Please use YYYY-MM-DD HH:MM:SS format. Details: {str(e)}"
        except HttpError as e:
            return f"Error: Failed to create/update event. Details: {str(e)}"
    
    def _delete_event(self, event_id: str) -> str:
        """Delete a calendar event"""
        if not event_id:
            return "Event ID is required for deletion"
        
        self.service.events().delete(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        return f"Event {event_id} deleted successfully"
    