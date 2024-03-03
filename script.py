import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
from constants import ELLIE_USERNAME

load_dotenv()

auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)


def main():
    playlists = get_playlists(sp)
    for playlist in playlists:
        print(f"Playlist: {playlist['name']}")

def get_playlists(sp):
    playlist_resp = sp.user_playlists(ELLIE_USERNAME, limit=50)
    playlists = playlist_resp.get('items', [])

    while playlist_resp['next']:
        playlist_resp = sp.next(playlist_resp)
        playlists.extend(playlist_resp['items'])

    return playlists


if __name__ == "__main__":
    main()




