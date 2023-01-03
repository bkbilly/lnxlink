from dbus.mainloop.glib import DBusGMainLoop
from mpris2 import get_players_uri
from mpris2 import Player
import alsaaudio


class Addon():
    name = 'Media Info'
    icon = 'mdi:music'
    unit = 'json'

    def __init__(self):
        self.players = []

    def exposedControls(self):
        return {
            "playpause": {
                "type": "button",
                "icon": "mdi:play-pause",
            },
            "previous": {
                "type": "button",
                "icon": "mdi:skip-previous",
            },
            "next": {
                "type": "button",
                "icon": "mdi:skip-next",
            },
            "volume_set": {
                "type": "number",
                "icon": "mdi:volume",
                "min": 0,
                "max": 100,
            }
        }

    def startControl(self, topic, data):
        if topic[1] == 'volume_set':
            mixer = alsaaudio.Mixer()
            if data < 1:
                data *= 100
            if data > 100:
                data = 100
            mixer.setvolume(int(data))
        elif topic[1] == 'playpause':
            if len(self.players) > 0:
                self.players[0]['player'].PlayPause()
        elif topic[1] == 'previous':
            if len(self.players) > 0:
                self.players[0]['player'].Previous()
        elif topic[1] == 'next':
            if len(self.players) > 0:
                self.players[0]['player'].Next()

    def getInfo(self) -> dict:
        self.__getPlayers()
        info = {
            'title': '',
            'artist': '',
            'album': '',
            'status': 'idle',
            'volume': self.__getVolume(),
            'playing': False
        }
        if len(self.players) > 0:
            player = self.players[0]
            info['playing'] = True
            info['title'] = player['title']
            info['album'] = player['album']
            info['artist'] = player['artist']
            info['status'] = player['status']

        return info

    def __getVolume(self):
        mixer = alsaaudio.Mixer()
        volume = mixer.getvolume()[0]
        if mixer.getmute()[0] == 1:
            volume = 0
        return volume

    def __getPlayers(self):
        DBusGMainLoop(set_as_default=True)
        self.players = []
        for uri in get_players_uri():
            player = Player(dbus_interface_info={'dbus_uri': uri})
            p_status = player.PlaybackStatus
            title = player.Metadata.get('xesam:title')
            artist = player.Metadata.get('xesam:artist')
            album = player.Metadata.get('xesam:album')
            if p_status != 'Stopped':
                artist_str = ''
                if artist is not None:
                    artist_str = ','.join(artist)
                self.players.append({
                    'status': p_status.lower(),
                    'title': str(title),
                    'artist': artist_str,
                    'album': '' if album is None else str(album),
                    'player': player
                })
        return self.players
