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

    def is_empty(self):
        return len(self.queue) == 0
