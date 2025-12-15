import random

class Playlist:
    def __init__(self, id, tracks):
        self.id = id
        self.tracks = tracks

        # The following are important for when I want to push changes
        self.new_tracks = []
        self.new_order = []
        for track in tracks:
            self.new_order.append(track)

    def sort(self, by, reverse=False, offset=0):
        if by == 'release_date': # Also sorts by track listing, except we nullify the reversal for that
            if not reverse:
                key = lambda x: (x['album']['release_date'], x['disc_number'], x['track_number'])
            else:
                key = lambda x: (x['album']['release_date'], -x['disc_number'], -x['track_number'])
        elif by == 'random':
            key = lambda x: random.random()
        self.new_order = self.new_order[:offset] + sorted(self.new_order[offset:], key=key, reverse=reverse)

    def __has_track(self, track_id):
        for track in self.tracks:
            if track['id'] == track_id:
                return True
        return False

    def add(self, tracks):
        for track in tracks:
            if not self.__has_track(track['id']):
                self.tracks.append(track)
                self.new_tracks.append(track)
                self.new_order.append(track)

    # Returns params to reorder the playlist so it matches its new state
    # Uses an algorithm similar to insertion sort, but without the sorting
    def get_reorder_steps(self):
        order_dict = {}
        for i in range(0, len(self.new_order)):
            order_dict[self.new_order[i]['id']] = i
        order_list = []
        for track in self.tracks:
            order_list.append(track['id'])

        steps_list = []
        curr_num = 0
        while curr_num < len(order_list):
            # Find the curr num in order_list
            for i in range(curr_num + 1, len(order_list)):
                if order_dict[order_list[i]] == curr_num: # Found where we need to start moving
                    range_length = 1
                    while i + range_length < len(order_list) and order_dict[order_list[i + range_length]] == curr_num + range_length:
                        range_length += 1
                    # Check if we can also move subsequent tracks to limit number of requets
                    move = {
                        'range_start': i,
                        'range_length': range_length,
                        'insert_before': curr_num
                    }
                    steps_list.append(move)
                    for j in range(0, range_length):
                        track_id = order_list.pop(i + j)
                        order_list.insert(curr_num + j, track_id)
                    curr_num = curr_num + range_length
                    break
            else: # The current track is correctly placed
                curr_num += 1
        return steps_list


