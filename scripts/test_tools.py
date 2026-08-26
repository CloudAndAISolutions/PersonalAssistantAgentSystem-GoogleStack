import os
import sys
from pprint import pprint

# Ensure the src directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.gmail_tool import GmailTool
from src.tools.calendar_tool import CalendarTool
from src.tools.tasks_tool import TasksTool
from src.tools.docs_tool import DocsTool

def main():
    print("🚀 Starting Phase 1 API Tool Tests...\n")
    
    # 1. Test Gmail
    try:
        print("Testing Gmail API...")
        gmail = GmailTool()
        unread = gmail.get_unread_emails(max_results=3)
        print(f"✅ Success! Found {len(unread)} unread personal/work emails.")
        for email in unread:
            print(f"   - From: {email['from']} | Subject: {email['subject']}")
    except Exception as e:
        print(f"❌ Gmail failed: {e}")
        
    print("-" * 40)
    
    # 2. Test Calendar
    try:
        print("Testing Calendar API...")
        calendar = CalendarTool()
        events = calendar.get_today_events()
        print(f"✅ Success! Found {len(events)} events for today.")
        for event in events[:3]:
            print(f"   - {event.get('start', 'Unknown Time')}: {event['title']}")
        if len(events) > 3:
            print("   - ...and more.")
    except Exception as e:
        print(f"❌ Calendar failed: {e}")
        
    print("-" * 40)
    
    # 3. Test Tasks
    try:
        print("Testing Tasks API...")
        tasks = TasksTool()
        pending = tasks.get_pending_tasks()
        print(f"✅ Success! Found {len(pending)} pending tasks.")
        for task in pending[:3]:
            overdue_mark = "⚠️ OVERDUE " if task['overdue'] else ""
            print(f"   - {overdue_mark}{task['title']} (Due: {task['due']})")
        if len(pending) > 3:
            print("   - ...and more.")
    except Exception as e:
        print(f"❌ Tasks failed: {e}")
        
    print("\n🎉 Tool testing complete!")
    print("Note: DocsTool (write operation) was skipped in this read-only test to avoid creating dummy files.")

if __name__ == '__main__':
    main()
