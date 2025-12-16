class Operation:
    def __init__(self, playlist_id, op_type, specs):
        self.playlist_id = playlist_id
        self.op_type = op_type
        self.specs = specs

    def __str__(self):
        if self.op_type == 'REMOVE':
            num = len(self.specs['tracks'])
            ret_str = f'{self.playlist_id}: REMOVE {num} TRACKS'
        elif self.op_type == 'MOVE':
            range_start = self.specs['range_start']
            range_end = range_start + self.specs['range_length'] - 1
            insert_before = self.specs['insert_before']
            return f'{self.playlist_id}: MOVE TRACKS {range_start}-{range_end} TO {insert_before}'
        elif self.op_type == 'ADD':
            position = self.specs['position']
            num = len(self.specs['tracks'])
            ret_str = f'{self.playlist_id}: ADD {num} TRACKS AT POSITION {position}'
            return ret_str

class OperationQueue:
    def __init__(self):
        self.queue = []

    def add_operation(self, playlist_id, op_type, specs):
        self.queue.append(Operation(playlist_id, op_type, specs))

    def pop_operation(self):
        return self.queue.pop(0)

    def is_empty(self):
        return len(self.queue) == 0


def __get_reorder_steps(old_order_list, new_order_dict):
    steps_list = []
    curr_num = 0
    while curr_num < len(old_order_list):
        # Find the curr num in order_list
        for i in range(curr_num + 1, len(old_order_list)):
            if new_order_dict[old_order_list[i]] == curr_num: # Found where we need to start moving
                range_length = 1
                while i + range_length < len(old_order_list) and new_order_dict[old_order_list[i + range_length]] == curr_num + range_length:
                    range_length += 1
                # Check if we can also move subsequent tracks to limit number of requets
                move = {
                    'range_start': i,
                    'range_length': range_length,
                    'insert_before': curr_num
                }
                steps_list.append(move)
                for j in range(0, range_length):
                    track_id = old_order_list.pop(i + j)
                    old_order_list.insert(curr_num + j, track_id)
                curr_num = curr_num + range_length
                break
        else: # The current track is correctly placed
            curr_num += 1
    return steps_list

def list_chunks(full_list, chunk_size):
    for i in range(0, len(full_list), chunk_size):
        yield full_list[i:i+n]

# Creates an operation queue from the changes made to a playlist
# Operations read from the queue can be used with Spotify API to edit playlist
def build_operation_queue(playlist):
    track_uri_dict = {}
    old_track_uris = []
    for track in playlist.old_list:
        uri = track['uri']
        old_track_uris.append(uri)
        if uri not in track_uri_dict:
            track_uri_dict[uri] = track
    new_track_uris = []
    for track in playlist.new_list:
        uri = track['uri']
        new_track_uris.append(uri)
        if uri not in track_uri_dict:
            track_uri_dict[uri] = track

    old_order_list = []
    remove_list = []
    for uri in old_track_uris:
        if uri in new_track_uris:
            old_order_list.append(uri)
        else:
            remove_list.append(uri)
    new_order_dict = {}
    move_place = 0
    add_list = [] # Contains tuples
    for i in range(0, len(new_track_uris)):
        uri = new_track_uris[i]
        if uri in old_track_uris:
            new_order_dict[uri] = move_place
            move_place += 1
        else:
            add_list.append((i, uri))

    queue = OperationQueue()

    # Track removal comes first
    for chunk in list_chunks(remove_list, 100):
        items = []
        for uri in chunk:
            items.append({
                'uri': uri,
                'name': track_uri_dict[uri]['name']
            })
        queue.add_operation(playlist.id, 'REMOVE', {
            'tracks': items
        })

    # Now comes track reordering, which employs a helper function
    steps = __get_reorder_steps(old_order_list, new_order_dict)
    for step in steps:
        queue.add_operation(playlist.id, 'MOVE', step)

    # And finally we add tracks
    i = 0
    while i < len(add_list):
        items = []
        expected = add_list[i][0]
        position = expected
        while len(items) < 100 and add_list[i][0] == expected:
            uri = add_list[i][1]
            name = track_uri_dict[uri]['name']
            items.append({
                'uri': uri,
                'name': name
            })
            i += 1
            expected += 1
        queue.add_operation(playlist.id, 'ADD', {
            'position': position,
            'tracks': items
        })
    return queue
