from datetime import datetime
from zoneinfo import ZoneInfo
import spotipy
import os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
from constants import ELLIE_USERNAME, SG_FLAG, PATH_TO_LOCAL_LIBRARY, PATH_TO_DOWNLOAD_LOGS

load_dotenv()

auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)


def main():
    local_tracks = get_local_tracks(PATH_TO_LOCAL_LIBRARY)

    # Get and sort tracks from flagged Spotify playlists
    playlists = get_playlists(sp)

    need_to_download_tracks = set()
    already_downloaded_tracks = set()
    playlist_to_new_tracks: dict[str, set] = {}
    for playlist in playlists:
        playlist_name = playlist.get("name", None)

        if SG_FLAG in playlist_name:
            print(f"Looking for new tracks in playlist: {playlist_name}")
            try:
                playlist_tracks = get_playlist_tracks(sp, playlist['id'])
            except Exception as e:
                print(f"Error retrieving tracks for playlist {playlist_name}: {e}")
                continue

            for track in playlist_tracks:
                if track not in local_tracks:
                    need_to_download_tracks.add(track)

                    if not playlist_to_new_tracks.get(playlist_name, None):
                        playlist_to_new_tracks[playlist_name] = set()
                    playlist_to_new_tracks[playlist_name].add(track)
                else:
                    already_downloaded_tracks.add(track)

    # Write tracks to text file
    write_to_file(need_to_download_tracks, playlist_to_new_tracks, already_downloaded_tracks)

    print("END")


def write_to_file(
        tracks_list: set[str], 
        playlist_dict: dict[str, set] = {}, 
        already_downloaded_tracks: set[str] = set()
    ):
    # Get today's date in Eastern Time
    eastern = ZoneInfo("US/Eastern")
    today_date = datetime.now(eastern).strftime("%m-%d-%y")

    filename = f"tracks_to_download_{today_date}.txt"
    filepath = os.path.join(PATH_TO_DOWNLOAD_LOGS, filename)

    try:
        with open(filepath, 'w') as file:
            file.write(f"Total Tracks to Download: {len(tracks_list)}\n\n")
            file.write("\nAll Tracks to Download\n\n")
            for track in tracks_list:
                file.write(f"* {track}\n")

            _write_file_break(file)

            file.write(f"\nTracks Already in Library:\n\n")
            for track in already_downloaded_tracks:
                file.write(f"* {track}\n")

            _write_file_break(file)

            file.write("\nTracks to Playlists\n\n")
            for track in tracks_list:
                playlists_track_is_in = [playlist for playlist, tracks in playlist_dict.items() if track in tracks]
                formatted_playlist_bullets = "".join([f"    * {pl}\n" for pl in playlists_track_is_in])
                file.write(f"{track}: \n{formatted_playlist_bullets}\n")

            _write_file_break(file)

            file.write("\nPlaylists to Tracks\n\n")
            for playlist, tracks in playlist_dict.items():
                file.write(f"\nPlaylist: {playlist}\n")
                for track in tracks:
                    file.write(f"  * {track}\n")

        print(f"Log written to: {filepath}")
    except Exception as e:
        print(f"Error writing to file: {e}")

def _write_file_break(file):
    file.write("\n\n")
    file.write("---------------------------------------------------")
    file.write("\n\n")

def get_playlists(sp):
    playlist_resp = sp.user_playlists(ELLIE_USERNAME, limit=50)
    playlists = playlist_resp.get('items', [])

    while playlist_resp['next']:
        playlist_resp = sp.next(playlist_resp)
        playlists.extend(playlist_resp['items'])

    return playlists

def get_playlist_tracks(sp, playlist_id) -> list[str]:
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend([track['track']['name'] for track in results['items']])
    
    while results['next']:
        results = sp.next(results)
        tracks.extend([track['track']['name'] for track in results['items']])
    
    return tracks

def get_local_tracks(path) -> list[str]:
    local_tracks = []
    for _, _, files in os.walk(path):
        for file in files:
            if file.endswith(".mp3"):
                local_tracks.append(os.path.splitext(file)[0])
    
    return local_tracks

if __name__ == "__main__":
    main()





    # post playlist to spotify with need_to_download_list