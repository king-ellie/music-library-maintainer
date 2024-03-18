from datetime import datetime
from zoneinfo import ZoneInfo
import spotipy
import os
import unicodedata
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from constants import ELLIE_USERNAME, DOWNLOAD_FLAG, PATH_TO_LOCAL_LIBRARY, PATH_TO_DOWNLOAD_LOGS, TRACKS_TO_DOWNLOAD_PLAYLIST_ID

load_dotenv()

# Set up SpotifyOAuth for authorization flow
scope = "user-library-read,user-library-modify,playlist-read-private,playlist-modify-private"
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
sp_oauth = SpotifyOAuth(scope=scope, redirect_uri=redirect_uri)
sp = spotipy.Spotify(auth_manager=sp_oauth)


def main():
    local_tracks = get_local_tracks(PATH_TO_LOCAL_LIBRARY)

    # Get and sort tracks from flagged Spotify playlists
    playlists = get_playlists(sp)

    need_to_download_track_names = set()
    need_to_download_track_ids: list[str] = []
    already_downloaded_tracks = set()
    playlist_to_new_tracks: dict[str, set] = {}
    for playlist in playlists:
        playlist_name = playlist.get("name", None)

        if DOWNLOAD_FLAG in playlist_name:
            print(f"Looking for new tracks in playlist: {playlist_name}")
            try:
                track_names_to_ids = get_playlist_tracks_and_ids(sp, playlist['id'])
            except Exception as e:
                print(f"Error retrieving tracks for playlist {playlist_name}: {e}")
                continue

            for track_name_to_id in track_names_to_ids:
                track_name = list(track_name_to_id.keys())[0]
                track_id = list(track_name_to_id.values())[0]


                if not track_is_already_downloaded(track_name, local_tracks):
                    if not playlist_to_new_tracks.get(playlist_name, None):
                        playlist_to_new_tracks[playlist_name] = set()
                    playlist_to_new_tracks[playlist_name].add(track_name)

                    if track_name not in need_to_download_track_names:
                        need_to_download_track_names.add(track_name)
                        need_to_download_track_ids.append(track_id)

                else:
                    already_downloaded_tracks.add(track_name)

    # Write tracks to text file
    write_to_file(need_to_download_track_names, playlist_to_new_tracks, already_downloaded_tracks)

    # Add tracks to download playlist
    if need_to_download_track_ids:
        print("Adding tracks to download playlist")
        track_ids_list = list(need_to_download_track_ids)
        chunk_size = 100  # Number of tracks to add at a time
        chunks = [track_ids_list[i:i + chunk_size] for i in range(0, len(track_ids_list), chunk_size)]

        for chunk in chunks:
            try:
                sp.playlist_add_items(TRACKS_TO_DOWNLOAD_PLAYLIST_ID, chunk)
                print(f"Added {len(chunk)} tracks to download playlist")
            except Exception as e:
                print(f"Error adding tracks to download playlist: {e}")

    print("END")

def track_is_already_downloaded(track_name: str, local_track_file_names: list[str]) -> bool:
    """
    Check if a track is already downloaded locally.
    Compare normalized track names for better matching.
    """
    normalized_fetched_track_name = normalize_track_name(track_name)

    for local_track_file_name in local_track_file_names:
        parts_of_file_name = local_track_file_name.split(" - ", 1)
        if len(parts_of_file_name) != 2:
            print(f"Skipping {local_track_file_name}: format does not follow expected pattern of Artist - Song")
            continue
        
        normalized_local_track_name = normalize_track_name(parts_of_file_name[1])
        if normalized_fetched_track_name == normalized_local_track_name:
            return True
    return False

def normalize_track_name(track_name: str) -> str:
    """
    Normalize track name for better comparison.
    - Convert to lowercase
    - Remove special characters and spaces
    
    O'locco - Radioland -> oloccoradioland
    O'Locco (Radioland) -> oloccoradioland
    """
    # Convert to lowercase
    normalized_name = track_name.lower()

    # Normalize Unicode characters to NFC form (Normalization Form Canonical Composition)
    normalized_name = unicodedata.normalize('NFC', normalized_name)

    # Remove special characters, spaces, and normalize accents
    normalized_name = ''.join(c for c in normalized_name if unicodedata.category(c)[0] in ['L', 'M', 'N'])

    return normalized_name

def write_to_file(
        tracks_list: set[str], 
        playlist_dict: dict[str, set] = {}, 
        already_downloaded_tracks: set[str] = set()
    ):
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

def get_playlist_tracks_and_ids(sp, playlist_id) -> list[dict[str, str]]:
    track_name_to_ids = []
    results = sp.playlist_tracks(playlist_id)
    for track in results['items']:
        track_name_to_id = {track['track']['name']: track['track']['id']}
        track_name_to_ids.append(track_name_to_id)
    
    while results['next']:
        results = sp.next(results)
        for track in results['items']:
            track_name_to_id = {track['track']['name']: track['track']['id']}
            track_name_to_ids.append(track_name_to_id)
    return track_name_to_ids

def get_local_tracks(path) -> list[str]:
    local_tracks = []
    for _, _, files in os.walk(path):
        for file in files:
            if file.endswith(".mp3"):
                local_tracks.append(os.path.splitext(file)[0])
    
    return local_tracks

if __name__ == "__main__":
    main()