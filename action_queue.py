class Action:
    def __init__(self, playlist_alias, playlist_id, action_type, action_spec):
        self.playlist_alias = playlist_alias
        self.playlist_id = playlist_id
        self.action_type = action_type
        self.action_spec = action_spec

    # TODO: Update for more specificity
    def __str__(self):
        if self.action_type == 'GET':
            return f'GET {self.playlist_alias}'
        elif self.action_type == 'ADD':
            source_list = self.action_spec['source']
            return f'ADD {source_list} TO {self.playlist_alias}'
        elif self.action_type == 'SORT':
            order = self.action_spec['by']
            return f'SORT {self.playlist_alias} BY {order}'
        elif self.action_type == 'CLEANUP':
            return f'CLEAN UP {self.playlist_alias}'
        elif self.action_type == 'PUSH':
            return f'PUSH {self.playlist_alias} CHANGES TO SPOTIFY'

class ActionQueue:
    def __init__(self):
        self.queue = []

    def add_action(self, playlist_alias, playlist_id, action_type, action_spec):
        action = Action(playlist_alias, playlist_id, action_type, action_spec)
        self.queue.append(action)

    def pop_action(self):
        return self.queue.pop(0)

    def check_get(self, playlist_alias):
        for action in self.queue:
            if action.action_type == 'GET' and action.playlist_alias == playlist_alias:
                return True
        return False

    # If there is a PUSH for that playlist, returns its position in the queue
    # Otherwise, returns -1
    def check_push(self, playlist_alias):
        for i in range(0, len(self.queue)):
            action = self.queue[i]
            if action.action_type == 'PUSH' and action.playlist_alias == playlist_alias:
                return i
        return -1

    # Remove the action at the specified index from the queue
    def remove(self, index):
        self.queue.pop(index)

    def is_empty(self):
        return len(self.queue) == 0
