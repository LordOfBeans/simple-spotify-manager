import random
import hashlib
from functools import reduce

class Playlist:
    def __init__(self, id, tracks):
        self.id = id
        self.old_list = tracks # Before any changes are made
        self.new_list = [] # After changes are made
        for track in tracks:
            self.new_list.append(track)

    def sort(self, by, reverse=False, offset=0):
        if by == 'release_date': # Also sorts by track listing, except we nullify the reversal for that
            if not reverse:
                key = lambda x: (x['album']['release_date'], x['disc_number'], x['track_number'])
            else:
                key = lambda x: (x['album']['release_date'], -x['disc_number'], -x['track_number'])
        elif by == 'hash': # Should appear random but remain fairly static over program runs
            # Using hashlib because the default hash() function in python is randomly salted
            key = lambda x: hashlib.md5(bytes(x['uri'], 'utf-8')).hexdigest()
        self.new_list = self.new_list[:offset] + sorted(self.new_list[offset:], key=key, reverse=reverse)

    def __has_track(self, track_id):
        for track in self.old_list:
            if track['id'] == track_id:
                return True
        return False

    def add(self, tracks, position=-1):
        for track in tracks:
            if not self.__has_track(track['id']):
                if position == -1:
                    self.old_list.append(track)
                    self.new_list.append(track)
                else:
                    self.old_list.insert(position, track)

    # Returns params to reorder the playlist so it matches its new state
    # Uses an algorithm similar to insertion sort, but without the sorting
    def get_reorder_steps(self):
        order_dict = {}
        for i in range(0, len(self.new_list)):
            order_dict[self.new_list[i]['id']] = i
        order_list = []
        for track in self.old_list:
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


