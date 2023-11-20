from collections import defaultdict

# Define the project plan with task dependencies and durations
project_plan = {
    'A': {'B', 'C'},
    'B': {'D'},
    'C': {'D'},
    'D': {'E'},
    'E': {}
}

# Define task durations in days
task_durations = {
    'A': 5,
    'B': 3,
    'C': 4,
    'D': 6,
    'E': 2
}

def calculate_early_start_end(project_plan, task_durations):
    early_start = {}
    early_end = {}

    # Initialize early start for the first task
    early_start['A'] = 0

    # Calculate early start and early end for all tasks
    for task in topological_sort(project_plan):
        early_start[task] = max(early_end[dependent] for dependent in project_plan[task]) if project_plan[task] else 0
        early_end[task] = early_start[task] + task_durations[task]

    return early_start, early_end

def calculate_late_start_end(project_plan, task_durations, project_duration):
    late_start = {}
    late_end = {}

    # Initialize late end for the last task
    late_end['E'] = project_duration

    # Calculate late start and late end for all tasks
    for task in topological_sort(project_plan, reverse=True):
        late_end[task] = min(late_start[dependent] for dependent in project_plan[task]) if project_plan[task] else project_duration
        late_start[task] = late_end[task] - task_durations[task]

    return late_start, late_end

def calculate_slack(early_start, late_start):
    slack = {}
    for task in early_start:
        slack[task] = late_start[task] - early_start[task]
    return slack

def topological_sort(graph, reverse=False):
    visited = set()
    order = []

    def visit(node):
        if node not in visited:
            visited.add(node)
            for neighbor in graph[node]:
                visit(neighbor)
            order.append(node)

    for node in graph:
        if node not in visited:
            visit(node)

    return reversed(order) if reverse else order

# Calculate early start and end times
early_start, early_end = calculate_early_start_end(project_plan, task_durations)

# Calculate project duration
project_duration = max(early_end.values())

# Calculate late start and end times
late_start, late_end = calculate_late_start_end(project_plan, task_durations, project_duration)

# Calculate slack for each task
slack = calculate_slack(early_start, late_start)

# Find the critical path by identifying tasks with zero slack
critical_path = [task for task in slack if slack[task] == 0]

# Print the results
print("Task\tEarly Start\tEarly End\tLate Start\tLate End\tSlack")
for task in project_plan:
    print(f"{task}\t{early_start[task]}\t{early_end[task]}\t{late_start[task]}\t{late_end[task]}\t{slack[task]}")

print("\nCritical Path:", " -> ".join(critical_path))
