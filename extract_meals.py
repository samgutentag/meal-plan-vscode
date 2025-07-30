import os
import json
import requests
from datetime import datetime, timedelta, time
from icalendar import Calendar
from dotenv import load_dotenv

# Constants for meal times
MEAL_TIMES = {
    'breakfast': time(8, 0),
    'lunch': time(11, 0),
    'dinner': time(17, 0)
}

# Helper to get start and end of current week (Monday to Sunday)
def get_week_range():
    today = datetime.now()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start.replace(hour=0, minute=0, second=0, microsecond=0), end.replace(hour=23, minute=59, second=59, microsecond=999999)

# Classify event by start time
def classify_event(event_time):
    if event_time >= MEAL_TIMES['dinner']:
        return 'dinner'
    elif event_time >= MEAL_TIMES['lunch']:
        return 'lunch'
    elif event_time >= MEAL_TIMES['breakfast']:
        return 'breakfast'
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
    for component in cal.walk():
        if component.name == 'VEVENT':
            dtstart = component.get('dtstart').dt
            if isinstance(dtstart, datetime):
                event_date = dtstart.date()
                event_time = dtstart.time()
            else:
                event_date = dtstart
                event_time = time(0, 0)
            if not (week_start.date() <= event_date <= week_end.date()):
                continue
            meal_type = classify_event(event_time)
            if meal_type:
                day_idx = str((event_date.weekday()) % 7)
                if not meals[day_idx][meal_type]:
                    meals[day_idx][meal_type] = str(component.get('summary', ''))
    with open('meal.json', 'w') as f:
        json.dump(meals, f, indent=2)
    print('meal.json written.')

if __name__ == '__main__':
    extract_meals()
