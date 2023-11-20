from datetime import datetime, date, time, timedelta

WORKDAY_MILLIS = 8 * 60 * 60 * 1000 
WORKDAY_START= time(8,0,0)

def get_end_points(plan):
    return [ k for k in plan if not plan[k]]


def subtract(base_date, duration):
    days = duration // WORKDAY_MILLIS
    millis_remainder = duration % WORKDAY_MILLIS
    result = base_date - timedelta(days=days, milliseconds=millis_remainder)
    if result.hour < 8:
        result = result - timedelta(hours=16)
    if result.hour == 16 and result.minute == 0:
        result = result + timedelta(hours=16)
    return result
    

def is_after(before, after):
    return (before - after).total_seconds() < 0
    

def determine_latest(end_date, predecessors, successors, durations):
    
    start_dates = {}
    end_dates = {}
    
    def calculate_dates(entry, date):
        if end_dates.get(entry) and is_after(end_dates[entry], date):
            return
        end_dates[entry] = date
        start_dates[entry] = subtract(date, durations[entry])
        for predecessor in predecessors[entry]:
            calculate_dates(predecessor, start_dates[entry])
    
    # tasks that don't have a successor
    end_points = get_end_points(successors)
    
    for endpoint in end_points:
        calculate_dates(endpoint, end_date)
        
    return start_dates, end_dates