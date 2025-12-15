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
            queue.add_action(alias, data['id'], 'SORT', {
                'by': data['sort']['by'],
                'reverse': data['sort']['reverse']
            })

    for alias, data in conglomerates.items():
        for source_alias in data['sources']:
            if not queue.check_get(source_alias):
                source = sources[source_alias]
                queue.add_action(source_alias, source['id'], 'GET', {})
            queue.add_action(alias, data['id'], 'ADD', {
                'source': source_alias
            })
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
            playlist.sort(
                action.action_spec['by'],
                action.action_spec['reverse']
            )
            playlist.get_reorder_steps()
        elif action.action_type == 'ADD':
            pass

    for alias, playlist in playlist_dict.items():
        me.pushPlaylist(playlist)


if __name__ == "__main__":
    main()
