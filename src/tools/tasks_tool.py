from googleapiclient.discovery import build
from src.services.auth import get_credentials
from datetime import datetime
import pytz

class TasksTool:
    def __init__(self):
        self.creds = get_credentials()
        self.service = build('tasks', 'v1', credentials=self.creds)
        self.timezone = pytz.timezone('Australia/Brisbane')

    def get_pending_tasks(self):
        """Fetches all incomplete tasks across all task lists."""
        task_lists = self.service.tasklists().list().execute()
        
        all_tasks = []
        now = datetime.now(self.timezone)
        
        for task_list in task_lists.get('items', []):
            tasks_result = self.service.tasks().list(
                tasklist=task_list['id'],
                showCompleted=False,
                showHidden=False
            ).execute()
            
            for task in tasks_result.get('items', []):
                if not task.get('title'):
                    continue
                    
                due_date_str = task.get('due')
                is_overdue = False
                formatted_due = "No due date"
                
                if due_date_str:
                    # Google Tasks API returns due dates like "2023-10-27T00:00:00.000Z"
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(self.timezone)
                    formatted_due = due_date.strftime("%b %d, %Y")
                    
                    # Check if overdue (comparing dates only)
                    if due_date.date() < now.date():
                        is_overdue = True

                all_tasks.append({
                    'title': task.get('title'),
                    'due': formatted_due,
                    'list': task_list.get('title', 'Unknown List'),
                    'overdue': is_overdue
                })
                
        # Sort: overdue first, then by title
        all_tasks.sort(key=lambda x: (not x['overdue'], x['title']))
        return all_tasks

    def get_due_today(self):
        """Fetches tasks due today specifically."""
        now = datetime.now(self.timezone)
        return [t for t in self.get_pending_tasks() if t['due'] == now.strftime("%b %d, %Y")]

    def get_overdue_tasks(self):
        """Fetches only the overdue tasks requiring attention."""
        return [t for t in self.get_pending_tasks() if t['overdue']]

