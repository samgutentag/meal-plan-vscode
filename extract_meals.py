import os
import json
import requests
from datetime import datetime, timedelta, time
import pytz
from icalendar import Calendar
from dotenv import load_dotenv


# Constants for meal intervals in PST
BREAKFAST_START = time(8, 0)
LUNCH_START = time(11, 0)
DINNER_START = time(17, 0)

# Helper to get start and end of current week (Monday to Sunday)
def get_week_range():
    today = datetime.now()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start.replace(hour=0, minute=0, second=0, microsecond=0), end.replace(hour=23, minute=59, second=59, microsecond=999999)


# Classify event by start time (in PST)
def classify_event(event_time):
    if BREAKFAST_START <= event_time < LUNCH_START:
        return 'breakfast'
    elif LUNCH_START <= event_time < DINNER_START:
        return 'lunch'
    elif event_time >= DINNER_START:
        return 'dinner'
    return None


# Main extraction function
def extract_meals():
    load_dotenv()
    feed_url = os.environ.get('GOOGLE_CALENDAR_FEED')
    if not feed_url:
        raise ValueError('GOOGLE_CALENDAR_FEED environment variable not set')
    resp = requests.get(feed_url)
    resp.raise_for_status()
    cal = Calendar.from_ical(resp.content)
    week_start, week_end = get_week_range()
    # Prepare output structure
    meals = {str(i): {'breakfast': '', 'lunch': '', 'dinner': ''} for i in range(7)}
    pst = pytz.timezone('America/Los_Angeles')
    for component in cal.walk():
        if component.name == 'VEVENT':
            dtstart = component.get('dtstart').dt
            # Convert to datetime if date only
            if isinstance(dtstart, datetime):
                # If dtstart is naive, assume UTC
                if dtstart.tzinfo is None:
                    dtstart = pytz.utc.localize(dtstart)
                dtstart_pst = dtstart.astimezone(pst)
            else:
                # All-day event, treat as 00:00 UTC
                dtstart = datetime.combine(dtstart, time(0, 0))
                dtstart = pytz.utc.localize(dtstart)
                dtstart_pst = dtstart.astimezone(pst)
            event_date = dtstart_pst.date()
            event_time = dtstart_pst.time()
            if not (week_start.date() <= event_date <= week_end.date()):
                continue
            meal_type = classify_event(event_time)
            if meal_type:
                day_idx = str((event_date.weekday()) % 7)
                if not meals[day_idx][meal_type]:
                    meals[day_idx][meal_type] = str(component.get('summary', ''))
    # Add 'today' entry
    today_idx = str(datetime.now().weekday())
    today_meals = meals[today_idx].copy()
    today_meals['Date'] = datetime.now().strftime('%B, %d, %Y')
    meals['today'] = today_meals
    with open('meal.json', 'w') as f:
        json.dump(meals, f, indent=2)
    print('meal.json written.')

if __name__ == '__main__':
    extract_meals()
