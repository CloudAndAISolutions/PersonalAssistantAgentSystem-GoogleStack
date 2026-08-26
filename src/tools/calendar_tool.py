from googleapiclient.discovery import build
from src.services.auth import get_credentials
from datetime import datetime, timedelta
import pytz

class CalendarTool:
    def __init__(self):
        self.creds = get_credentials()
        self.service = build('calendar', 'v3', credentials=self.creds)
        self.timezone = pytz.timezone('Australia/Brisbane')

    def get_today_events(self):
        """Fetches all events for today."""
        now = datetime.now(self.timezone)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return self._fetch_events(start_of_day, end_of_day)

    def get_upcoming_events(self, days=7):
        """Fetches events for the next N days."""
        now = datetime.now(self.timezone)
        start_of_period = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_period = start_of_period + timedelta(days=days)
        
        return self._fetch_events(start_of_period, end_of_period)

    def get_reminders(self):
        """Fetches reminders for today."""
        # Note: Calendar API doesn't have a specific "reminders" endpoint in the same way 
        # it used to, but we can look for specific event keywords or colors if needed.
        # For now, it returns all events as reminders might just be regular events.
        return self.get_today_events()

    def _fetch_events(self, start_time: datetime, end_time: datetime):
        """Helper to fetch events across all calendars within a timeframe."""
        time_min = start_time.isoformat()
        time_max = end_time.isoformat()
        
        # First, get all calendar IDs
        calendar_list = self.service.calendarList().list().execute()
        
        all_events = []
        for calendar_list_entry in calendar_list.get('items', []):
            calendar_id = calendar_list_entry['id']
            events_result = self.service.events().list(
                calendarId=calendar_id, 
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                all_events.append({
                    'calendar': calendar_list_entry.get('summary', 'Unknown'),
                    'start': start,
                    'title': event.get('summary', 'No Title'),
                    'location': event.get('location', ''),
                    'description': event.get('description', '')
                })
                
        # Sort all events by start time
        all_events.sort(key=lambda x: x['start'])
        return all_events
