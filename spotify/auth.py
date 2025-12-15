from urllib.parse import urlencode
import webbrowser # Opens application authorization window
import socket # Handles callback
from base64 import b64encode
import requests
import json
from datetime import datetime, timedelta
import os

# Listens for callback on localhost port 8888
def listenCallback(port):
    sock = socket.socket()
    sock.bind(('', port))
    sock.listen(1)
    conn, address = sock.accept()
    data = conn.recv(1024).decode()
    
    # TODO: Clean up and minimize positional dependencies
    lines = data.splitlines()
    query = lines[0][14:-9]
    if query[:5] != 'code=':
        conn.send('Authorization stage failed. You may close this window.'.encode())
        conn.close()
        sock.close()
        raise Exception('Authorization was not granted')
    conn.send('Authorization stage completed. You may close this window.'.encode())
    conn.close()
    sock.close()
    return query[5:]

# User gives app permission to access playlists
def requestAuthCode(client_id, port):
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': f'http://localhost:{port}/callback',
        # TODO: Learn about using 'state' to protect against XSRF
        'scope': 'playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public' # Every playlist-related scope
    }

    auth_url = 'https://accounts.spotify.com/authorize?' + urlencode(params)
    webbrowser.open(auth_url)
    return listenCallback(port)

def requestAccessToken(b64_auth_string, auth_code, port):
    headers = {
        'Authorization': f'Basic {b64_auth_string}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': f'http://localhost:{port}/callback' # Used only for validation on Spotify backend
    }

    resp = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers)
    if resp.status_code != 200:
        raise Exception(f'Failed to get new access token with status code {resp.status_code}')
    return json.loads(resp.text)

# Handles everything to do with authorization
# Makes singular get and post requests
# Not responsible for looping through pages and whatnot
class Auth:
    def __init__(self, client_id, client_secret, callback_port, token_path):
        self.client_id = client_id
        self.b64_auth_string = str(b64encode(f'{client_id}:{client_secret}'.encode('utf-8')), 'utf-8')
        self.callback_port = callback_port
        self.token_path = token_path

        if not os.path.exists(token_path): # Get fresh access token and save
            auth_code = requestAuthCode(self.client_id, self.callback_port)
            self.token_info = requestAccessToken(self.b64_auth_string, auth_code, self.callback_port)
            with open(self.token_path, 'w') as f:
                json.dump(self.token_info, f)
                self.expiration = datetime.now() + timedelta(seconds=self.token_info['expires_in'])
        else: # Read access token from file
            last_modified = os.path.getmtime(self.token_path)
            with open(self.token_path, 'r') as f:
                self.token_info = json.load(f)
                self.expiration = datetime.fromtimestamp(last_modified) + timedelta(seconds=self.token_info['expires_in'])
        self.headers = {
            'Authorization': 'Bearer ' + self.token_info['access_token'],
            'Content-Type': 'application/json'
        }
        if datetime.now() > self.expiration:
            self.refreshToken()

    # TODO: Have this return a value?
    def refreshToken(self):
        headers = {
            'Authorization': f'Basic {self.b64_auth_string}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.token_info['refresh_token']
        }

        resp = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers)
        if resp.status_code != 200:
            raise Exception(f'Failed to refresh access token with status code {resp.status_code}')

        new_token = json.loads(resp.text)
        if 'refresh_token' not in new_token: # A new refresh token is not always included in the response
            refresh_token = self.token_info['refresh_token']
            new_token['refresh_token'] = refresh_token
        self.expiration = datetime.now() + timedelta(seconds=new_token['expires_in'])
        with open(self.token_path, 'w') as f:
            json.dump(new_token, f)
        self.token_info = new_token
        self.headers['Authorization'] = 'Bearer ' + self.token_info['access_token']

    # For ease-of-use
    def getEndpoint(self, endpoint, params=None):
        if endpoint[0] != '/':
            endpoint = '/' + endpoint
        url = 'https://api.spotify.com/v1' + endpoint
        return self.getUrl(url, params=params)

    def getUrl(self, url, params=None):
        if datetime.now() > self.expiration:
            self.refreshToken()
        resp = requests.get(url, params=params, headers=self.headers)
        if resp.status_code == 200:
            return(json.loads(resp.text))
        if resp.status_code == 401:
            self.refreshToken() # Gets new token and updates headers
            resp = requests.get(url, params=params, headers=self.headers)
            if resp.status_code == 200:
                return json.loads(resp.text)
        # TODO: Change exception type to something more meaningful
        raise Exception(f'Failed to GET {resp.request.url} with status code {resp.status_code}')

    def postEndpoint(self, endpoint, body):
        if endpoint[0] != '/':
            endpoint = '/' + endpoint
        url = 'https://api.spotify.com/v1' + endpoint
        return self.postUrl(url, body)

    # TODO: Improve exceptions
    def postUrl(self, url, body):
        if datetime.now() > self.expiration:
            self.refreshToken()
        resp = requests.post(url, json=body, headers=self.headers)
        if resp.status_code != 201:
            if resp.status_code == 401:
                self.refreshToken()
                resp = requests.post(url, json=body, headers=self.headers)
                if resp.status_code != 201:
                    raise Exception(f'Failed to POST to {resp.request.url} after token refresh with status code {resp.status_code}')
            else:
                raise Exception(f'Failed to POST to {resp.request.url} with status code {resp.status_code}')
        return json.loads(resp.text)

    def putEndpoint(self, endpoint, body):
        if endpoint[0] != '/':
            endpoint = '/' + endpoint
        url = 'https://api.spotify.com/v1' + endpoint
        return self.putUrl(url, body)

    # TODO: Improve exceptions
    def putUrl(self, url, body):
        if datetime.now() > self.expiration:
            self.refreshToken()
        resp = requests.put(url, json=body, headers=self.headers)
        if resp.status_code != 200:
            if resp.status_code == 401:
                self.refreshToken()
                resp = requests.put(url, json=body, headers=self.headers)
                if resp.status_code != 200:
                    raise Exception(f'Failed to PUT to {resp.request.url} after token refresh with status code {resp.status_code}')
            else:
                raise Exception(f'Failed to PUT to {resp.request.url} with status code {resp.status_code}')
        return json.loads(resp.text)
