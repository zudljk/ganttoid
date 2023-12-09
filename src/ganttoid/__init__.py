import argparse
from pyclickup import ClickUp
from datetime import datetime
from . import scheduling
from .task import Task

def get_config():
    parser = argparse.ArgumentParser(description="Create a critical path of a ClickUp task list",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--project", help="Project name or ID")
    parser.add_argument("-l", "--list", help="List name or ID")
    parser.add_argument("-k", "--api-key", required=True, help="ClickUP API key")
    args = parser.parse_args()
    return vars(args)
     

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

    #tasks = create_task_map(all_tasks)
    #predecessors = get_predecessors(tasks)
    #successors = get_successors(all_tasks)
    #durations = create_durations_map(all_tasks)
    #trades = get_trades(tasks)
        
    tasks = []
    for x in all_tasks:
        tasks.append(Task(x))
        
    scheduling.determine_latest2(datetime(2024, 6, 30, 16, 0), tasks)
    #start_dates, end_dates = scheduling.determine_latest(datetime(2024, 6, 30, 16, 0), predecessors, successors, durations, trades)

    print("ID;Name;Übergeordnet;Spätester Start;Sequenz;Spätestes Ende;Gewerk;Vorgänger;Nachfolger")
    
    for t in tasks:
        predecessors = ",".join([ p.name for p in t.get_predecessors()])
        successors = ",".join([ p.name for p in t.get_successors()])
        print(f"{t.id};{t.name};{t.get_parent_name()};{t.get_latest_start()};{t.get_sequence()};{t.get_latest_end()};{t.get_trade()};{predecessors};{successors}")
        
    
#    for key in tasks:
#        task = tasks[key]
#        trade = get_trade(tasks, key)
#        parent_name = tasks[task.parent].name if task.parent else None 
#        print(f"{task.id};{task.name};{parent_name};{start_dates.get(key)};{task.orderindex};{end_dates.get(key)};{trade};{predecessors[key]};{successors[key]}")
#        task.start_date = start_dates[key]
#        task.due_date = end_dates[key]
#        clickup.post(task.url, data=task)


def main():
    ganttoid()

if __name__ == '__main__':
    main()
