import random
import hashlib
from functools import reduce

class Playlist:
    def __init__(self, id, tracks):
        self.id = id
        self.old_list = tracks # Purely for when I need to push changes
        self.new_list = [] # Any modification to the playlist take place her
        self.seen_dict = {} # Whether a track has been seen in the add method
        for track in tracks:
            self.new_list.append(track)
            self.seen_dict[track['id']] = False

    def sort(self, by, reverse=False, offset=0):
        if by == 'release_date': # Also sorts by track listing, except we nullify the reversal for that
            if not reverse:
                key = lambda x: (x['album']['release_date'], x['album']['uri'], x['disc_number'], x['track_number'])
            else:
                key = lambda x: (x['album']['release_date'], x['album']['uri'], -x['disc_number'], -x['track_number'])
        elif by == 'hash': # Should appear random but remain fairly static over program runs
            # Using hashlib because the default hash() function in python is randomly salted
            key = lambda x: hashlib.md5(bytes(x['uri'], 'utf-8')).hexdigest()
        self.new_list = self.new_list[:offset] + sorted(self.new_list[offset:], key=key, reverse=reverse)

    def __has_track(self, track_id):
        for track in self.new_list:
            if track['id'] == track_id:
                return True
        return False

    def add(self, other, position=-1):
        for track in other.new_list:
            if not self.__has_track(track['id']):
                if position == -1:
                    self.new_list.append(track)
                else:
                    self.new_list.insert(position, track)
            self.seen_dict[track['id']] = True

    # Removes any tracks that haven't been seen by the add method yet
    def cleanup(self):
        i = 0
        while i < len(self.new_list):
            track_id = self.new_list[i]['id']
            if not self.seen_dict[track_id]:
                self.new_list.pop(i)
            else:
                i += 1
