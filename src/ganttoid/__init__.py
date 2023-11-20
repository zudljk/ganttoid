import argparse
from pyclickup import ClickUp
from datetime import datetime
from . import scheduling

def get_config():
    parser = argparse.ArgumentParser(description="Create a critical path of a ClickUp task list",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--project", help="Project name or ID")
    parser.add_argument("-l", "--list", help="List name or ID")
    parser.add_argument("-k", "--api-key", required=True, help="ClickUP API key")
    args = parser.parse_args()
    return vars(args)


def create_task_map(tasks):
    map = {}
    for task in tasks:
        map[task.id] = task
    return map


def create_top_down_hierarchy(tasks):
    map = {}
    for key in tasks:
        task = tasks[key]
        if task.parent:
            children = map.get(task.parent)
            if not children:
                children = []
                map[task.parent] = children
            children.append(task.id)
    return map


def create_bottom_up_hierarchy(tasks):
    map = {}
    for key in tasks:
        task = tasks[key]
        map[task.id] = task.parent
    return map


# Get tasks that don't have subtasks
def get_leaves(hierarchy, tasks):
    return [ t for t in tasks if not hierarchy.get(t) ]


def create_durations_map(tasks):
    durations = {}
    for task in tasks:
        durations[task.id] = task.time_estimate
    return durations


def get_predecessors(tasks):
    plan = {}
    for task in tasks:
        deps = [ d["depends_on"] for d in task.dependencies if d["task_id"] == task.id ]
        plan[task.id] = deps
    return plan
    
    
def get_successors(tasks):
    plan = {}
    for task in tasks:
        deps = [ d["task_id"] for d in task.dependencies if d["depends_on"] == task.id ]
        plan[task.id] = deps
    return plan
   
   
def validate_durations(durations, tasks):
    for d in durations:
        if durations[d] is None:
            raise ValueError(f"Task '{tasks[d].name}' has no time estimate.")


def calculate_durations(durations, tasks):
    hierarchy = create_top_down_hierarchy(tasks)
    parents = create_bottom_up_hierarchy(tasks)
    leaves = get_leaves(hierarchy, tasks)
    calculated_durations = {}
    for leaf in leaves:
        calculated_durations[leaf] = durations[leaf]
    while leaves:
        leaf = leaves.pop(0)
        d = calculated_durations.get(leaf)
        if not d:
            raise ValueError(f"Task '{tasks[d].name}' has no time estimate.")
        parent = parents[leaf]
        if parent:
            pd = calculated_durations.get(parent) if calculated_durations.get(parent) else 0
            pd += d
            calculated_durations[parent] = pd
            leaves.append(parent)
    return calculated_durations    


def get_trade(tasks, key):
    task = tasks[key]
    trade = [ f for f in task.custom_fields if f["name"] == 'Gewerk'][0]
    if trade.get('value') is not None:
        return trade['type_config']['options'][trade.get('value')]['name']
    elif task.parent:
        return get_trade(tasks, task.parent)
    else:
        return None
        

def ganttoid():
    config = get_config()
    project_name = config.get("project")
    list_name = config.get("list")
    
    #pk_54476427_49HZ2J531X46BZTH0ANDKKBCMDYVR2DO
    clickup = ClickUp(config["api_key"])

    lists = []    
    for team in clickup.teams:
        for space in team.spaces:
            for project in space.projects:
                if not project_name or project.name == project_name or project.id == project_name:
                    for _list in project.lists:
                       if not list_name or _list.name == list_name or _list.id == list_name:
                           lists.append(_list)
    
    if not lists:
        if not list_name:
            raise ValueError("No lists found")
        else:
            raise ValueError(f"List or project with name or id {list_name} not found")
    elif len(lists) > 1:
        raise ValueError(f"List name or id {list_name} is not unique, please submit a project name")

    all_tasks = lists[0].get_all_tasks(subtasks=True)

    tasks = create_task_map(all_tasks)
    predecessors = get_predecessors(all_tasks)
    successors = get_successors(all_tasks)
    durations = create_durations_map(all_tasks)
    
    durations = calculate_durations(durations, tasks)
    
    start_dates, end_dates = scheduling.determine_latest(datetime(2024, 6, 30, 16, 0), predecessors, successors, durations)

    for key in tasks:
        task = tasks[key]
        trade = get_trade(tasks, key)
        parent_name = tasks[task.parent].name if task.parent else None 
        print(f"{task.id};{task.name};{parent_name};{start_dates.get(key)};{end_dates.get(key)};{trade};{predecessors[key]};{successors[key]}")
#        task.start_date = start_dates[key]
#        task.due_date = end_dates[key]
#        clickup.post(task.url, data=task)


def main():
    ganttoid()

if __name__ == '__main__':
    main()
