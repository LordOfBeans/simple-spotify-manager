import yaml
from action_queue import ActionQueue
from spotify.user import User

APP_CONFIG_PATH = 'config.yaml'
SPOTIFY_CONFIG_PATH = 'credentials/spotify-config.yaml'

def build_action_queue(config):
    sources = config['sources']
    conglomerates = config['conglomerates']

    queue = ActionQueue()

    for alias, data in sources.items():
        if 'sort' in data:
            queue.add_action(alias, data['id'], 'GET', {})
            queue.add_action(alias, data['id'], 'SORT', data['sort'])
            queue.add_action(alias, data['id'], 'PUSH', {})

    for alias, data in conglomerates.items():
        if not queue.check_get(alias):
            queue.add_action(alias, data['id'], 'GET', {})
        position = -1
        if 'position' in data:
            position = data['position']
        for source_alias in data['sources']:
            if not queue.check_get(source_alias):
                source = sources[source_alias]
                queue.add_action(source_alias, source['id'], 'GET', {})
            queue.add_action(alias, data['id'], 'ADD', {
                'source': source_alias,
                'position': position
            })
        if 'cleanup' in data and data['cleanup']:
            queue.add_action(alias, data['id'], 'CLEANUP', {})
        if 'sort' in data:
            queue.add_action(alias, data['id'], 'SORT', data['sort'])
        queue.add_action(alias, data['id'], 'PUSH', {})
    return queue

def main():
    me = User(SPOTIFY_CONFIG_PATH)

    with open(APP_CONFIG_PATH, 'r') as conf_file:
        config = yaml.safe_load(conf_file)
    queue = build_action_queue(config)

    # Key is alias, value is Playlist object
    playlist_dict = {}

    while not queue.is_empty():
        action = queue.pop_action()
        print(action)
        if action.action_type == 'GET':
            playlist = me.getPlaylist(action.playlist_id)
            playlist_dict[action.playlist_alias] = playlist
        elif action.action_type == 'SORT':
            playlist = playlist_dict[action.playlist_alias]
            kwargs = {}
            for key, value in action.action_spec.items():
                if key == 'by': 
                    by = value
                else:
                    kwargs[key] = value
            playlist.sort(by, **kwargs)
        elif action.action_type == 'ADD':
            conglomerate = playlist_dict[action.playlist_alias]
            source = playlist_dict[action.action_spec['source']]
            position = action.action_spec['position']
            conglomerate.add(source, position=position)
        elif action.action_type == 'CLEANUP':
            conglomerate = playlist_dict[action.playlist_alias]
            conglomerate.cleanup()
        elif action.action_type == 'PUSH':
            playlist = playlist_dict[action.playlist_alias]
            me.pushPlaylist(playlist) 

if __name__ == "__main__":
    main()
