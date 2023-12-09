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
            
    # sort the children by orderindex
    def key_extractor(x):
        return tasks[key].orderindex
                    
    for key in map:
        children = map.get(key)
        if children:
            children = sorted(children, key=key_extractor)
            map[key] = children
        
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
        durations[task.id] = task.time_estimate if task.time_estimate is not None else 0
    return durations


# FIXME: This method creates a cycle. We want to have children of a parent to have all its parent's 
# predecessors as its own predecessors. But on the other hand, we want a parent to have all its subtasks
# as predecessors. That way, subtasks will end up as their own predecessors.
# The solution would be to add all the parent's predecessors *except* the subtask itself and its siblings,
# but how do we know what the siblings are?
# Other solution: Dump all the "smart" logic and have the user set the correct dependencies by hand.
def get_predecessors(tasks):
    predecessors = {}
    hierarchy = create_top_down_hierarchy(tasks)
    parents = create_bottom_up_hierarchy(tasks)
    for key in tasks:
        task = tasks[key]
        deps = [ d["depends_on"] for d in task.dependencies if d["task_id"] == key ]
        predecessors[key] = deps
        # if a task has subtasks, make it dependent on all of them
        subtasks = (hierarchy.get(key) if hierarchy.get(key) else [])
        predecessors[key] += subtasks
    for key in tasks:
        task = tasks[key]
        deps = predecessors[key]
        # if a task has a parent, make it dependent on all of its parent's predecessors        
        siblings = [ sibling for sibling in parents if parents[sibling] == parents[key] ]
        if parents.get(key):
            deps += [ pred for pred in predecessors[parents.get(key)] if pred not in siblings ]
    return predecessors
    
    
def get_successors(tasks):
    plan = {}
    for task in tasks:
        deps = [ d["task_id"] for d in task.dependencies if d["depends_on"] == task.id ]
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
    

def get_trade(tasks, key):
    task = tasks[key]
    trade = [ f for f in task.custom_fields if f["name"] == 'Gewerk'][0]
    if trade.get('value') is not None:
        return trade['type_config']['options'][trade.get('value')]['name']
    elif task.parent:
        return get_trade(tasks, task.parent)
    else:
        return None
        
        
def get_trades(tasks):
    trades = {}
    for key in tasks:
        trades[key] = get_trade(tasks, key)
    return trades


def group_by_trade(tasks, trades):
    grouped = {}
    for key in tasks:
        trade = trades[key]
        if trade not in grouped:
            grouped[trade] = []
        grouped[trade].append(key)
    return grouped        
    

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
    predecessors = get_predecessors(tasks)
    successors = get_successors(all_tasks)
    durations = create_durations_map(all_tasks)
    trades = get_trades(tasks)
       
    start_dates, end_dates = scheduling.determine_latest(datetime(2024, 6, 30, 16, 0), predecessors, successors, durations, trades)

    print("ID;Name;Übergeordnet;Spätester Start;Sequenz;Spätestes Ende;Gewerk;Vorgänger;Nachfolger")
    for key in tasks:
        task = tasks[key]
        trade = get_trade(tasks, key)
        parent_name = tasks[task.parent].name if task.parent else None 
        print(f"{task.id};{task.name};{parent_name};{start_dates.get(key)};{task.orderindex};{end_dates.get(key)};{trade};{predecessors[key]};{successors[key]}")
#        task.start_date = start_dates[key]
#        task.due_date = end_dates[key]
#        clickup.post(task.url, data=task)


def main():
    ganttoid()

if __name__ == '__main__':
    main()
