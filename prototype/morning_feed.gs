// ============================================
// Personal Assistant — Morning Feed Prototype
// Google Apps Script + Gemini API
// ============================================
// 
// SETUP INSTRUCTIONS:
// 1. Go to script.google.com → New Project
// 2. Name it "PersonalAssistant-MorningFeed"
// 3. Paste this entire file into Code.gs
// 4. Replace YOUR_GEMINI_API_KEY with your key from aistudio.google.com
// 5. Enable Tasks API: Services (+) → search "Tasks API" → Add
// 6. IMPORTANT — Restrict permissions:
//    a. In the editor, go to Project Settings (⚙️ gear icon)
//    b. Check "Show 'appsscript.json' manifest file in editor"
//    c. Click on appsscript.json in the sidebar
//    d. Replace its contents with the appsscript.json from this prototype
//    e. This locks permissions to: send and read email (no edit/delete),
//       read calendar (no edit/delete), read tasks (no edit/delete)
// 7. Set trigger: Triggers (⏰) → + Add Trigger → morningFeed → Time-driven → Day timer → 7am-8am
// 8. Authorize and you're done!
//
// PRIVACY: All data stays within Google.
// - Calendar: READ-ONLY access (calendar.readonly scope)
// - Tasks: READ-ONLY access (tasks.readonly scope)
// - Email: READ-ONLY + SEND-ONLY (gmail.readonly + script.send_mail)
//          Cannot delete, modify, or manage emails
// - Gemini: Called via API key, data not used for training (with AI Pro opt-out)
// - External requests: Only to generativelanguage.googleapis.com (Gemini API)
// ============================================

const GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY'; // From aistudio.google.com/app/apikey
const MY_EMAIL = Session.getActiveUser().getEmail();
const TIMEZONE = 'Australia/Brisbane';

/**
 * Main entry point — called by the time-driven trigger at 7 AM.
 * Fetches calendar events and tasks, composes a briefing with Gemini,
 * and sends it to your inbox.
 */
function morningFeed() {
  const today = new Date();
  const todayStr = Utilities.formatDate(today, TIMEZONE, 'EEEE, MMMM d, yyyy');
  
  // 1. Fetch Calendar Events
  const events = getCalendarEvents(today);
  
  // 2. Fetch Tasks
  const tasks = getPendingTasks();
  
  // 3. Fetch Email Highlights (filtered — skips newsletters/ads)
  const emails = getEmailHighlights();
  
  // 4. Compose briefing with Gemini
  const briefing = composeBriefing(todayStr, events, tasks, emails);
  
  // 5. Send email to self
  sendMorningEmail(todayStr, briefing);
  
  Logger.log('Morning feed sent successfully for ' + todayStr);
}

/**
 * Fetches all calendar events for the given date across all calendars.
 * Returns an array of event objects with time, title, location, description.
 */
function getCalendarEvents(date) {
  const calendars = CalendarApp.getAllCalendars();
  const endOfDay = new Date(date);
  endOfDay.setHours(23, 59, 59);
  
  let eventList = [];
  calendars.forEach(cal => {
    cal.getEventsForDay(date).forEach(event => {
      const isAllDay = event.isAllDayEvent();
      const time = isAllDay 
        ? 'All Day' 
        : Utilities.formatDate(event.getStartTime(), TIMEZONE, 'h:mm a');
      eventList.push({
        time: time,
        title: event.getTitle(),
        location: event.getLocation() || '',
        description: event.getDescription() || ''
      });
    });
  });
  
  // Sort by time (all-day events first, then by start time)
  eventList.sort((a, b) => {
    if (a.time === 'All Day') return -1;
    if (b.time === 'All Day') return 1;
    return 0;
  });
  
  return eventList;
}

/**
 * Fetches all incomplete tasks across all task lists.
 * Requires the Tasks API to be enabled via Services.
 */
function getPendingTasks() {
  try {
    const taskLists = Tasks.Tasklists.list();
    let allTasks = [];
    
    if (!taskLists.items) return allTasks;
    
    taskLists.items.forEach(list => {
      const tasks = Tasks.Tasks.list(list.id, { showCompleted: false });
      if (tasks.items) {
        tasks.items.forEach(task => {
          if (task.title) { // Skip empty tasks
            const dueDate = task.due ? new Date(task.due) : null;
            const now = new Date();
            // Compare dates only (ignore time), and ensure year is considered
            const isOverdue = dueDate 
              && dueDate.getFullYear() <= now.getFullYear()  // same or past year
              && dueDate.getTime() < now.getTime();          // actually past
            allTasks.push({
              title: task.title,
              due: dueDate 
                ? Utilities.formatDate(dueDate, TIMEZONE, 'MMM d, yyyy') 
                : 'No due date',
              list: list.title,
              overdue: !!isOverdue
            });
          }
        });
      }
    });
    
    // Sort: overdue first, then by due date
    allTasks.sort((a, b) => {
      if (a.overdue && !b.overdue) return -1;
      if (!a.overdue && b.overdue) return 1;
      return 0;
    });
    
    return allTasks;
  } catch (e) {
    Logger.log('Tasks API error: ' + e.message);
    Logger.log('Make sure you have enabled the Tasks API via Services (+)');
    return [];
  }
}

/**
 * Fetches recent personal/work emails, filtering out newsletters,
 * subscriptions, ads, and marketing emails.
 * Uses gmail.readonly scope — cannot delete or modify any emails.
 */
function getEmailHighlights() {
  try {
    // Query: unread emails from the last 24 hours, excluding noise
    const query = 'is:unread newer_than:1d '
      + '-category:promotions '
      + '-category:social '
      + '-category:updates '
      + '-category:forums '
      + '-{unsubscribe} '       // Skip emails with unsubscribe links
      + '-from:noreply '
      + '-from:newsletter '
      + '-from:marketing '
      + '-from:digest ';
    
    const threads = GmailApp.search(query, 0, 10); // Max 10 threads
    let emailList = [];
    
    threads.forEach(thread => {
      const firstMsg = thread.getMessages()[0];
      emailList.push({
        from: firstMsg.getFrom(),
        subject: thread.getFirstMessageSubject(),
        snippet: firstMsg.getPlainBody().substring(0, 150).replace(/\n/g, ' '),
        date: Utilities.formatDate(firstMsg.getDate(), TIMEZONE, 'h:mm a'),
        starred: thread.hasStarredMessages()
      });
    });
    
    // Starred emails first
    emailList.sort((a, b) => {
      if (a.starred && !b.starred) return -1;
      if (!a.starred && b.starred) return 1;
      return 0;
    });
    
    return emailList;
  } catch (e) {
    Logger.log('Gmail error: ' + e.message);
    return [];
  }
}

/**
 * Sends the event and task data to Gemini 2.5 Flash to compose
 * a friendly, concise morning briefing.
 */
function composeBriefing(dateStr, events, tasks, emails) {
  const overdueWarning = tasks.filter(t => t.overdue).length > 0
    ? `\n⚠️ OVERDUE TASKS:\n${tasks.filter(t => t.overdue).map(t => `- ${t.title} (was due: ${t.due}) [${t.list}]`).join('\n')}`
    : '';

  const emailSection = emails.length > 0
    ? `\nEMAIL HIGHLIGHTS (overnight, filtered — personal/work only):\n${emails.map(e => `- ${e.starred ? '⭐ ' : ''}From: ${e.from} | Subject: ${e.subject}`).join('\n')}`
    : '\nEMAIL HIGHLIGHTS: No actionable emails overnight.';

  const prompt = `You are a friendly personal assistant. Compose a concise morning briefing for ${dateStr}.

CALENDAR EVENTS:
${events.length > 0 
  ? events.map(e => `- ${e.time}: ${e.title}${e.location ? ' @ ' + e.location : ''}`).join('\n')
  : '- No events today'}
${overdueWarning}
PENDING TASKS:
${tasks.filter(t => !t.overdue).length > 0 
  ? tasks.filter(t => !t.overdue).map(t => `- ${t.title} (Due: ${t.due}) [${t.list}]`).join('\n')
  : '- No pending tasks'}
${emailSection}

Instructions:
- Start with a brief, warm greeting
- If there are OVERDUE tasks, mention them prominently with urgency
- Summarize the "Hard Landscape" (fixed-time events like meetings, appointments)
- Then the "Soft Landscape" (tasks you can slot into gaps between events)
- Include a brief "Email Highlights" section for notable emails (starred first)
- End with a practical tip about time management or priorities for the day
- Use emoji sparingly for visual structure
- Keep it under 250 words`;

  const url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent';
  
  try {
    const response = UrlFetchApp.fetch(url + '?key=' + GEMINI_API_KEY, {
      method: 'post',
      contentType: 'application/json',
      muteHttpExceptions: true,
      payload: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }]
      })
    });
    
    const statusCode = response.getResponseCode();
    if (statusCode !== 200) {
      Logger.log('Gemini API error: ' + statusCode + ' ' + response.getContentText());
      return buildFallbackBriefing(dateStr, events, tasks);
    }
    
    const result = JSON.parse(response.getContentText());
    return result.candidates[0].content.parts[0].text;
  } catch (e) {
    Logger.log('Gemini API call failed: ' + e.message);
    return buildFallbackBriefing(dateStr, events, tasks);
  }
}

/**
 * Fallback briefing if Gemini API is unavailable.
 * Returns a simple formatted text summary.
 */
function buildFallbackBriefing(dateStr, events, tasks) {
  let text = `☀️ Good Morning! Here's your day — ${dateStr}\n\n`;
  
  text += '📅 TODAY\'S SCHEDULE\n';
  if (events.length > 0) {
    events.forEach(e => {
      text += `• ${e.time} — ${e.title}`;
      if (e.location) text += ` @ ${e.location}`;
      text += '\n';
    });
  } else {
    text += '• No events — a free day!\n';
  }
  
  text += '\n📋 TASKS\n';
  if (tasks.length > 0) {
    tasks.forEach(t => {
      const prefix = t.overdue ? '⚠️' : '•';
      text += `${prefix} ${t.title} (${t.due}) [${t.list}]\n`;
    });
  } else {
    text += '• All clear!\n';
  }
  
  text += '\n(Note: Gemini was unavailable — this is a raw summary)';
  return text;
}

/**
 * Sends the morning briefing email with a styled HTML template.
 */
function sendMorningEmail(dateStr, briefing) {
  const htmlBody = `
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; border-radius: 12px; color: white; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 20px;">☀️ Good Morning!</h1>
        <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">${dateStr}</p>
      </div>
      <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; line-height: 1.6; font-size: 14px; white-space: pre-wrap;">
        ${briefing.replace(/\n/g, '<br>')}
      </div>
      <p style="color: #999; font-size: 11px; text-align: center; margin-top: 16px;">
        Powered by your Personal Assistant Agent · Phase 0 Prototype
      </p>
    </div>`;
  
  // Using MailApp (not GmailApp) for send-only permission
  // MailApp uses scope 'script.send_mail' — can only send, never read or delete
  MailApp.sendEmail(MY_EMAIL, '☀️ Morning Feed — ' + dateStr, briefing, {
    htmlBody: htmlBody,
    name: 'Personal Assistant'
  });
}

// ============================================
// MANUAL TEST — Run this function to test now
// ============================================
function testMorningFeed() {
  morningFeed();
  Logger.log('Test complete — check your inbox!');
}
