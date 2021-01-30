import mpris2
from dbus.mainloop.glib import DBusGMainLoop
from mpris2 import get_players_uri
from mpris2 import Player
import json

class Addon():
    service = 'media'
    name = 'Media Info'
    icon = 'mdi:media'
    unit = 'json'

    def getInfo(self):
        DBusGMainLoop(set_as_default=True)
        players = []
        for uri in get_players_uri():
            player = Player(dbus_interface_info={'dbus_uri': uri})
            p_status = player.PlaybackStatus
            title = player.Metadata.get('xesam:title')
            artist = player.Metadata.get('xesam:artist')
            album = player.Metadata.get('xesam:album')
            if title is not None:
                artist_str = ''
                if artist is not None:
                    artist_str = ','.join(artist)
                players.append({
                    'status': p_status,
                    'title': str(title),
                    'artist': artist_str,
                    'album': '' if album is None else str(album)
                })
        return json.dumps(players)
