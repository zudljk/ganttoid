from datetime import datetime, date, time, timedelta
from .task import Task

WORKDAY_MILLIS = 8 * 60 * 60 * 1000 

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
    while result.weekday() >= 5:
        result = result - timedelta(days=1)
    return result
    

def is_after(before, after):
    return (before - after).total_seconds() < 0


def print_cycle_stack(path):
    for i in reversed(path):
        task = Task.all_tasks[i]
        parent = f"{task.get_parent().name} / " if task.get_parent() else ""
        print(f"{parent}{task.name} -> ")


def determine_latest(end_date, tasks):
    
    def calculate_start_end_date(task, date, path):
        if task.id in path:
            print_cycle_stack(path+[task.id])
            raise ValueError(f"Error, cycle detected: {'->'.join(path)}->{task.id}")
        path.append(task.id)
        
        if task.latest_end and is_after(task.latest_end, date):
            return
        
        task.latest_start = subtract(date, task.get_duration())
        task.latest_end = date
        if task.latest_end.hour == 8 and task.latest_end.minute == 0:
            task.latest_end = task.latest_end - timedelta(hours=16)
        
        for predecessor in task.get_predecessors():
            calculate_start_end_date(predecessor, task.latest_start, path[:])
        
    end_points = Task.get_endpoints()
    
    for endpoint in end_points:
        calculate_start_end_date(endpoint, end_date, [])
