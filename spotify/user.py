from spotify.auth import Auth
from spotify.playlist import Playlist

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

    # Returns a Playlist object
    # TODO: Modify so this uses the Get Playlist endpoint instead of the Get Playlist Items endpoint
    def getPlaylist(self, playlist_id):
        endpoint = f'/playlists/{playlist_id}/tracks'
        tracks = self.__getListItems(endpoint, lambda x: x['track'])
        playlist = Playlist(playlist_id, tracks)
        return playlist

    def __reorderPlaylist(self, playlist_id, reorder_steps):
        endpoint = f'/playlists/{playlist_id}/tracks'
        snapshot_id = None
        for step in reorder_steps:
            if snapshot_id is not None:
                step['snapshot_id'] = snapshot_id
            resp = self.auth.putEndpoint(endpoint, step)
            snapshot_id = resp['snapshot_id']

    # Push any changes to the playlist back to Spotify
    def pushPlaylist(self, playlist):
        reorder_steps = playlist.get_reorder_steps()
        self.__reorderPlaylist(playlist.id, reorder_steps)
