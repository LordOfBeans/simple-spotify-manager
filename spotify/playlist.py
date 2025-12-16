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
                    self.new_list.append(track)
                else:
                    self.new_list.insert(position, track)


