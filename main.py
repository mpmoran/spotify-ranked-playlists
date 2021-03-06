# standard libraries
import os
from typing import List, Union

# third-party libraries
from dotenv import load_dotenv
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# local libraries
import spotify_helpers as sh


# load env vars from .env file
load_dotenv()

# get authentication details for Spotify
# ----------------------------------------------------------------------------
sp_client_id: str = os.getenv('SPOTIFY_CLIENT_ID')
sp_client_secret: str = os.getenv('SPOTIFY_CLIENT_SECRET')
sp_redirect_uri: str = os.getenv('SPOTIFY_REDIRECT_URI')
sp_scope = 'user-library-read playlist-modify-private playlist-read-private'
# ----------------------------------------------------------------------------

# create spotify client
# ----------------------------------------------------------------------------
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(client_id=sp_client_id,
                              client_secret=sp_client_secret,
                              redirect_uri=sp_redirect_uri,
                              scope=sp_scope)
)
# ----------------------------------------------------------------------------

# get details about current user
# ----------------------------------------------------------------------------
user_details: dict = sp.current_user()
user_id: str = user_details['id']
user_uri: str = user_details['uri']

# get all saved tracks by user
# ----------------------------------------------------------------------------
saved_tracks: List[dict] = sh.spotify_get_results(sp,
                                                  'current_user_saved_tracks')
num_saved_tracks: int = len(saved_tracks)
# ----------------------------------------------------------------------------

# get audio features of all tracks
# ----------------------------------------------------------------------------
# audio_features is in the same order as saved_tracks
audio_features: List[dict] = []
for piece in sh.chunk(saved_tracks, 100):  # piece is List[dict]
    track_uris: List[str] = [track['track']['uri'] for track in piece]
    results: List[dict] = sp.audio_features(track_uris)
    audio_features.extend(results)
num_audio_features = len(audio_features)
if num_saved_tracks != num_audio_features:
    raise Exception(f'Total tracks according to Spotify ({num_saved_tracks}) '
                    f'does not equal total tracks extracted from API calls '
                    f'({num_audio_features}).')
# ----------------------------------------------------------------------------

# merge information about songs
# ----------------------------------------------------------------------------
saved_tracks_stage1: List[dict] = []
for track in saved_tracks:
    info = track['track']
    rec = {}
    rec['artist'] = info['artists'][0]['name']
    rec['album'] = info['album']['name']
    rec['song_name'] = info['name']
    rec['date'] = info['album']['release_date']
    rec['popularity'] = info['popularity']
    rec['uri'] = info['uri']
    saved_tracks_stage1.append(rec)

audio_features_stage1: List[dict] = []
for track in audio_features:
    rec = {}
    rec['danceability'] = track['danceability']
    rec['tempo'] = track['tempo']
    rec['energy'] = track['energy']
    rec['key'] = track['key']
    rec['speechiness'] = track['speechiness']
    rec['acousticness'] = track['acousticness']
    rec['instrumentalness'] = track['instrumentalness']
    rec['liveness'] = track['liveness']
    rec['valence'] = track['valence']
    rec['time_signature'] = track['time_signature']
    audio_features_stage1.append(rec)

tracks_stage1: List[dict] = []
for str, afr in zip(saved_tracks_stage1, audio_features_stage1):
    rec = {}
    rec.update(str)
    rec.update(afr)
    tracks_stage1.append(rec)
# ----------------------------------------------------------------------------

# create pandas dataframe
# ----------------------------------------------------------------------------
df = pd.DataFrame(tracks_stage1)
df.to_csv('./saved_tracks.csv',
          sep='\t',
          header=True,
          index=True,
          mode='w',
          encoding='utf-8')
# ----------------------------------------------------------------------------

# config storage for creating playlists
# ----------------------------------------------------------------------------
playlist_config = [
    {
        'name': 'most danceable',
        'metric': 'danceability',
        'num_tracks': 50,
        'description': '50 most danceable tracks from my liked songs.'
    },
    {
        'name': 'highest tempo',
        'metric': 'tempo',
        'num_tracks': 50,
        'description': '50 highest tempo songs from my liked songs.'
    },
    {
        'name': 'highest energy',
        'metric': 'energy',
        'num_tracks': 50,
        'description': '50 highest energy songs from my liked songs.'
    },
    {
        'name': 'most live',
        'metric': 'liveness',
        'num_tracks': 50,
        'description': '50 most live songs from my liked songs.'
    }

]
# ----------------------------------------------------------------------------

# create playlists from config
# ----------------------------------------------------------------------------
for pl in playlist_config:
    name = pl['name']
    metric = pl['metric']
    num_tracks = pl['num_tracks']
    description = pl['description']

    playlist_tracks: List[dict] = sh.get_ranked_tracks(df,
                                                       metric=metric,
                                                       num=num_tracks)
    playlist_details: Union[List[dict], None] = \
        sh.spotify_create_and_fill_playlist(
            sp,
            name=name,
            track_uris=playlist_tracks,
            description=description,
            user_id=user_id
        )
# ----------------------------------------------------------------------------
