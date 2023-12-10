from datetime import datetime

class Task:
    
    all_tasks = {}
    
    def __init__(self, clickup_task):
        self.clickup_task = clickup_task
        self.id = clickup_task.id
        self.name = clickup_task.name
        self.latest_start = None
        self.latest_end = None
        Task.all_tasks[self.id] = self
        
        
    def get_parent(self):
        return Task.all_tasks.get(self.clickup_task.parent)
        
        
    def get_parent_name(self):
        if self.get_parent():
            return self.get_parent().name
        return None
        
        
    def get_duration(self):
        if not self.get_children():
            return self.clickup_task.time_estimate if self.clickup_task.time_estimate is not None else 0
        return 0
        
    
    def get_children(self):
        return [ child for child in Task.all_tasks.values() if child.get_parent() and child.get_parent().id == self.id]


    def get_hierarchy_bottom(self):
        bottom = []
        stack = [self]
        while stack:
            item = stack.pop()
            children = item.get_children()
            if children:
                for child in children:
                    stack.append(child)
            else:
                bottom.append(item)
        return bottom
    

    def get_trade(self):
        trade = [ f for f in self.clickup_task.custom_fields if f["name"] == 'Gewerk'][0]
        if trade.get('value') is not None:
            return trade['type_config']['options'][trade.get('value')]['name']
        elif self.get_parent():
            return self.get_parent().get_trade()
        else:
            return None
                
                
    def get_sequence(self):
        return float(self.clickup_task.orderindex)
    
    
    def get_siblings(self):
        if not self.get_parent():
            return sorted([ sibling for sibling in Task.all_tasks.values() if sibling.get_parent() is None ], key=lambda x: x.get_sequence())
        return sorted([ sibling for sibling in self.get_parent().get_children() if sibling.id != self.id ], key=lambda x: x.get_sequence())
    
    
    def get_latest_start(self):       
        children = self.get_children()
        if children:
            return min([ t.get_latest_start() for t in children ])
        return self.latest_start
    
    
    def get_latest_end(self):
        children = self.get_children()
        if children:
            return max([ t.get_latest_end() for t in children ])
        return self.latest_end
    
    
    def get_successors(self):
        return [ t for t in Task.all_tasks.values() if self in t.get_predecessors() ]
    
    
    def get_predecessors(self):
        predecessors = []
        # add all defined predecessors
        deps = [ Task.all_tasks[d["depends_on"]] for d in self.clickup_task.dependencies if d["task_id"] == self.id ]
        # if one predecessor has subtasks, replace it with its subtasks
        for d in deps:
            for t in d.get_hierarchy_bottom():
                predecessors.append(t)
        # add our parent's predecessors as our predecessors
        if self.get_parent():
            for t in self.get_parent().get_predecessors():
                predecessors.append(t)
        pred = None
        # find or next-oldest sibling with the same trade and add it as predecessor
        # make sure that siblings of the same trade can't be parallelized
        for t in self.get_siblings():
            if t.get_sequence() < self.get_sequence() and t.get_trade() == self.get_trade():
                pred = t
        if pred:
            predecessors.append(pred)
        # ensure unique items in list
        return sorted(list(dict.fromkeys(predecessors)), key=lambda x: x.get_sequence())
    
    
    def create_commit(self):
        return {
            "start_date_time": True,                                         
            "due_date_time": True,                 
            "start_date": datetime.timestamp(self.get_latest_start()) * 1000,
            "due_date": datetime.timestamp(self.get_latest_end()) * 1000
        }
    
    def get_endpoints():
        return [ task for task in Task.all_tasks.values() if not task.get_successors() ]

