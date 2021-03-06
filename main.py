# standard libraries
import os
from typing import List, Union

# third-party libraries
from dotenv import load_dotenv
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth


# functions
# ----------------------------------------------------------------------------
def chunk(iterable, n):
    """
    Yield successive n-sized chunks from iterable.
    """
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]


def get_ranked_tracks(df: pd.DataFrame,
                      metric: str,
                      num: int,
                      ascending: bool = False) -> List[dict]:
    """
    Return num tracks ranked by metric.
    """
    df_ranked = df.sort_values(by=metric,
                               ascending=ascending,
                               ignore_index=True)
    tracks: List[str] = df_ranked['uri'].iloc[:num].tolist()

    return tracks


def spotify_create_and_fill_playlist(client: spotipy.client.Spotify,
                                     name: str,
                                     track_uris: List[dict],
                                     description: str,
                                     user_id: str) -> Union[List[dict], None]:
    """
    Create a playlist and fill it with tracks. If a playlist of the same name
    exists, this function does nothing. Returns information about playlist
    that was created or None.
    """
    # get all playlist names
    playlists: List[dict] = spotify_get_results(client,
                                                'user_playlists',
                                                user=user_id)
    playlist_names = [pl['name'] for pl in playlists]

    if name in playlist_names:
        return None
    else:
        create_response = client.user_playlist_create(
            user=user_id,
            name=name,
            public=False,
            collaborative=False,
            description=description
        )
        playlist_id: str = create_response['id']
        client.playlist_add_items(playlist_id=playlist_id,
                                  items=track_uris,
                                  position=None)

        details = {}
        details['id'] = create_response['id']
        details['uri'] = create_response['uri']

        return details


def spotify_get_results(client: spotipy.client.Spotify,
                        operation: str,
                        limit: int = 50,
                        offset: int = 0,
                        **kwargs) -> List[dict]:
    """
    Return results of calling operation on Spotify client
    """
    # get client operation method
    method = getattr(client, operation)

    # keep making API calls and collecting results
    results: List[dict] = []
    while True:
        response: dict = method(**kwargs,
                                limit=limit,
                                offset=offset)
        items: list = response['items']
        results.extend(items)
        whats_left = response['next']
        if whats_left is None:
            break
        offset += limit

    # ensure the number of expected items matches the number of actuals
    num_expected: int = response['total']
    num_actual: int = len(results)
    if num_expected != num_actual:
        raise Exception(f'Total tracks according to Spotify ({num_expected}) '
                        f'does not equal total tracks extracted from API '
                        f'calls ({num_actual}).')

    return results
# ----------------------------------------------------------------------------


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
saved_tracks: List[dict] = spotify_get_results(sp,
                                               'current_user_saved_tracks')
num_saved_tracks: int = len(saved_tracks)
# ----------------------------------------------------------------------------

# get audio features of all tracks
# ----------------------------------------------------------------------------
# audio_features is in the same order as saved_tracks
audio_features: List[dict] = []
for piece in chunk(saved_tracks, 100):  # piece is List[dict]
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

    playlist_tracks: List[dict] = get_ranked_tracks(df,
                                                    metric=metric,
                                                    num=num_tracks)
    playlist_details: Union[List[dict], None] = \
        spotify_create_and_fill_playlist(
            sp,
            name=name,
            track_uris=playlist_tracks,
            description=description,
            user_id=user_id
        )
# ----------------------------------------------------------------------------
