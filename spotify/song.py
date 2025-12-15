class Song:
    def __init__(self, info, format):
        if format == 'spotify':
            track = info['track']
            self.id = track['id']
            self.name = track['name']
        elif format == 'postgres':
            self.id = info['song_id']
            self.name = info['name']
        self.uri = 'spotify:track:' + self.id

    def __str__(self):
        return f'{self.id}: {self.name}'

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

