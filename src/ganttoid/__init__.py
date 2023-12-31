import argparse
from pyclickup import ClickUp
from datetime import datetime
from requests import get, put
from . import scheduling
from .task import Task


def get_config():
    parser = argparse.ArgumentParser(
        description="Create a critical path of a ClickUp task list",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-t", "--task", help="Task ID")
    parser.add_argument("-p", "--project", help="Project name or ID")
    parser.add_argument("-l", "--list", help="List name or ID")
    parser.add_argument("-k", "--api-key", required=True, help="ClickUP API key")
    args = parser.parse_args()
    return vars(args)


# pyclickup is obsolete and doesn't support the current API, however there is no usable alternative
# except building our own client
def save(task_id, payload, api_key):
    response = put(
        f"https://api.clickup.com/api/v2/task/{task_id}",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key
        },
    )
    if response.status_code > 299:
        raise IOError(response.reason)
    
    
def get_project_by_task(task_id, api_key):
    response = get(f"https://api.clickup.com/api/v2/task/{task_id}", headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": api_key
    })
    if response.status_code > 299:
        raise IOError(response.reason)
    data = response.json()
    return data["project"]["id"], data["list"]["id"]
    


def ganttoid(api_key, **kwargs):
    clickup = ClickUp(api_key)
    
    project_name = kwargs.get("project")
    list_name = kwargs.get("list")
    
    if kwargs.get("task"):
        project_name, list_name = get_project_by_task(kwargs["task"], api_key)

    lists = []
    for team in clickup.teams:
        for space in team.spaces:
            for project in space.projects:
                if (
                    not project_name
                    or project.name == project_name
                    or project.id == project_name
                ):
                    for _list in project.lists:
                        if (
                            not list_name
                            or _list.name == list_name
                            or _list.id == list_name
                        ):
                            lists.append(_list)

    if not lists:
        if not list_name:
            raise ValueError("No lists found")
        else:
            raise ValueError(f"List or project with name or id {list_name} not found")
    elif len(lists) > 1:
        raise ValueError(
            f"List name or id {list_name} is not unique, please submit a project name"
        )

    all_tasks = lists[0].get_all_tasks(subtasks=True)

    tasks = []
    for x in all_tasks:
        tasks.append(Task(x))

    scheduling.determine_latest(datetime(2024, 6, 30, 16, 0), tasks)

    print(
        "ID;Name;Übergeordnet;Spätester Start;Sequenz;Spätestes Ende;Gewerk;Vorgänger;Nachfolger"
    )

    for t in tasks:
        predecessors = ",".join([p.name for p in t.get_predecessors()])
        successors = ",".join([p.name for p in t.get_successors()])
        print(
            f"{t.id};{t.name};{t.get_parent_name()};{t.get_latest_start()};{t.get_sequence()};{t.get_latest_end()};{t.get_trade()};{predecessors};{successors}"
        )
        save(t.id, t.create_commit(), api_key)


def main():
    config = get_config()
    ganttoid(config.get("api_key"), project=config.get("project"), list=config.get("list"), task=config.get("task"))


if __name__ == "__main__":
    main()
