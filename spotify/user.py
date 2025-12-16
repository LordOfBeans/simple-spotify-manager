from spotify.auth import Auth
from spotify.playlist import Playlist
from spotify.operation_queue import build_operation_queue

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

    def __addTracks(self, playlist_id, uri_list, position=None):
        endpoint = f'/playlists/{playlist_id}/tracks'
        body = {
            'uris': uri_list
        }
        if position is not None:
            body['position'] = position
        resp = self.auth.postEndpoint(endpoint, body)

    def __moveTracks(self, playlist_id, move_params):
        endpoint = f'/playlists/{playlist_id}/tracks'
        resp = self.auth.putEndpoint(endpoint, move_params)

    def __removeTracks(self, playlist_id, uri_list):
        endpoint = f'/playlists/{playlist_id}/tracks'
        track_list = []
        for uri in uri_list:
            track_list.append({'uri':uri})
        body = {
            'tracks': track_list
        }
        resp = self.auth.deleteEndpoint(endpoint, body) 


    # Push any changes to the playlist back to Spotify
    def pushPlaylist(self, playlist):
        queue = build_operation_queue(playlist)
        while not queue.is_empty():
            op = queue.pop_operation()
            print(op)
            if op.op_type == 'REMOVE':
                uri_list = []
                for track in op.specs['tracks']:
                    uri_list.append(track['uri'])
                self.__removeTracks(playlist.id, uri_list)
            elif op.op_type == 'MOVE':
                self.__moveTracks(playlist.id, op.specs)
            elif op.op_type == 'ADD':
                uri_list = []
                for track in op.specs['tracks']:
                    uri_list.append(track['uri'])
                position = op.specs['position']
                self.__addTracks(playlist.id, uri_list, position=position)

