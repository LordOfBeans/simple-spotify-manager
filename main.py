import yaml
from action_queue import ActionQueue

CONFIG_PATH = 'config.yaml'

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
    with open(CONFIG_PATH, 'r') as conf_file:
        config = yaml.safe_load(conf_file)
    queue = build_action_queue(config)

    while not queue.is_empty():
        action = queue.pop_action()
        print(action)

if __name__ == "__main__":
    main()
