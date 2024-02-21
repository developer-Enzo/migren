import time
import json

from datetime import datetime, timedelta, timezone
from collections import Counter


def get_notification_unix_date(date: str) -> int:
    # date - 19:00 / hh:mm
    
    current_time = time.time()
    msk = timezone(timedelta(hours=3))
    desired_time = datetime.strptime(date, "%H:%M")
    current_datetime_msk = datetime.fromtimestamp(current_time, timezone.utc).astimezone(msk)

    desired_datetime = datetime(
        current_datetime_msk.year, 
        current_datetime_msk.month, 
        current_datetime_msk.day,
        desired_time.hour, 
        desired_time.minute, 
        tzinfo=msk,
    )

    if current_datetime_msk > desired_datetime:
        desired_datetime += timedelta(days=1)

    time_difference = desired_datetime - current_datetime_msk

    return int(current_time + time_difference.total_seconds())


def is_today(date: int):
    timezone = 3 # MSK
    current_time = time.time()
    current_datetime_utc = datetime.utcfromtimestamp(current_time)
    date_datetime_utc = datetime.utcfromtimestamp(date)

    current_datetime_msk = current_datetime_utc + timedelta(hours=timezone)
    date_datetime_msk = date_datetime_utc + timedelta(hours=timezone)

    return current_datetime_msk.date() == date_datetime_msk.date()


def get_medicine_info(user_notes: list[list]):
    current_time = time.time()
    start_week = current_time - 604800
    start_month = current_time - 2592000
    
    # Фильтруем записи за неделю
    weekly_notes = []
    monthly_notes = []
    week_number_headaches = 0
    month_number_headaches = 0
    post_added_today = False
    
    for note in user_notes:
        if note[3] >= start_week:
            weekly_notes.append(note)
            if note[0]:
                week_number_headaches += 1
            if is_today(note[3]):
                post_added_today = True
                
        if note[3] >= start_month:
            monthly_notes.append(note)
            if note[0]:
                month_number_headaches += 1

    weekly_medicines = Counter()
    monthly_medicines = Counter()
    
    for note in weekly_notes:
        med_list = json.loads(note[2])
        for i in med_list:
            weekly_medicines.update([i["name"]])
    
    for note in weekly_notes:
        med_list = json.loads(note[2])
        for i in med_list:
            monthly_medicines.update([i["name"]]) 
    
    week_med_list_text = ""
    month_med_list_text = ""
    
    for name, amount in dict(weekly_medicines).items():
        if week_med_list_text == "":
            week_med_list_text += f"┌ Название: {name}\n└ Кол-во приемов: {amount}"
        else:
            week_med_list_text += f"\n┌ Название: {name}\n└ Кол-во приемов: {amount}"
    
    for name, amount in dict(monthly_medicines).items():
        if month_med_list_text == "":
            month_med_list_text += f"┌ Название: {name}\n└ Кол-во приемов: {amount}"
        else:
            month_med_list_text += f"\n┌ Название: {name}\n└ Кол-во приемов: {amount}"
    
    return {
        "week_number_headaches": week_number_headaches,
        "month_number_headaches": month_number_headaches,
        "post_added_today": "Да" if post_added_today else "Нет",
        "week_med_list_text": week_med_list_text,
        "month_med_list_text": month_med_list_text,
    }
    
    
async def get_user_medicine_list(db, user_id: int) -> list:
    notes = await db.get_user_notes(user_id)
    medicines = []
    
    for note in notes:
        med_list = json.loads(note[2])
        for i in med_list:
            medicines.append(i["name"])
    
    return list(set(medicines))