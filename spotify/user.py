from spotify.auth import Auth
from spotify.entity import Song

import requests
import json
import os
import yaml

class User:
    def __init__(self, CONFIG_FILE):
        if not os.path.exists(CONFIG_FILE):
            raise FileNotFoundError(f'Spotify configuration file {CONFIG_FILE} does not exist')
        with open(CONFIG_FILE, 'r') as f:
            self.config = yaml.safe_load(f)
        self.auth = Auth (
            self.config['client_id'],
            self.config['client_secret'],
            self.config['callback_port'],
            self.config['token_path']
        )

    def __getListItems(self, endpoint, func, params=None, initial_key=None):
        return_list = []
        info = self.auth.getEndpoint(endpoint, params=params)
        while True:
            if initial_key is not None:
                info = info[initial_key]
            for item in info['items']:
                return_list.append(func(item))
            next = info['next']
            if next is None:
                break
            info = self.auth.getUrl(next)
        return return_list

    def getPlaylistSongs(self, playlist_id):
        endpoint = f'/playlists/{playlist_id}/tracks'
        songs = self.__getListItems(endpoint, lambda x: Song(x, 'spotify'))
        return songs

    def addPlaylistSongs(self, playlist_id, songs, position=None):
        if len(songs) == 0: #TODO: Is there a more user-friendly behavior here?
            return
        endpoint = f'/playlists/{playlist_id}/tracks'
        groups = [songs[i * 100: (i+1) * 100] for i in range(0, int(len(songs)/100)+1)] # Split into groups of 100 songs
        for i in range(0, len(groups)):
            uri_list = []
            for song in groups[i]:
                uri_list.append(song.uri)
            body = {
                'uris': uri_list
            }
            if position is not None:
                body['position'] = i * 100 + position
            self.auth.postEndpoint(endpoint, body)
