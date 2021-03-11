# -*- coding: utf-8 -*-
# standard libraries
import logging
from typing import List, Union

# third-party libraries
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

# local libraries
from config import Config
import spotify_helpers as sh


logger = logging.getLogger(__name__)


class Spotify(object):
    """
    """
    def __init__(self):
        """
        """
        # load config values
        self._user_auth_flow: str = Config.get('user_auth_flow')
        sp_client_id: str = Config.get('sp_client_id')
        sp_client_secret: str = Config.get('sp_client_secret')
        self._sp_scope: str = Config.get('sp_scope')

        # create spotify client
        logger.info('Authenticating with Spotify API.')
        if self._user_auth_flow == 'authorization':
            self._sp_redirect_uri: str = Config.get('sp_redirect_uri')
            auth_manager = SpotifyOAuth(client_id=sp_client_id,
                                        client_secret=sp_client_secret,
                                        redirect_uri=self._sp_redirect_uri,
                                        scope=self._sp_scope)
        else:
            auth_manager = SpotifyClientCredentials(
                client_id=sp_client_id,
                client_secret=self.sp_client_secret
            )

        self._client = spotipy.Spotify(auth_manager=auth_manager)

    def get_audio_features(self, tracks: List[dict]) -> List[dict]:
        """
        """
        # get audio features of all tracks
        # audio_features is in the same order as saved_tracks
        logger.info('Getting audio features of saved tracks.')
        audio_features: List[dict] = []
        for piece in sh.chunk(tracks, 100):  # piece is List[dict]
            track_uris: List[str] = [track['track']['uri'] for track in piece]
            results: List[dict] = self._client.audio_features(track_uris)
            audio_features.extend(results)
        num_audio_features = len(audio_features)
        num_tracks = len(tracks)
        if num_tracks != num_audio_features:
            raise Exception(f'Total tracks according to Spotify '
                            f'({num_tracks}) '
                            f'does not equal total tracks extracted from API '
                            'calls ({num_audio_features}).')

        return audio_features

    def get_tracks_df(self) -> pd.DataFrame:
        """
        """
        # get all saved tracks by user
        saved_tracks: List[dict] = self.get_user_saved_tracks()
        num_saved_tracks: int = len(saved_tracks)
        logger.info(f'Number of saved tracks is {num_saved_tracks}.')

        # get audio features of all tracks
        # audio_features is in the same order as saved_tracks
        audio_features: List[dict] = self.get_audio_features(saved_tracks)
        num_audio_features = len(audio_features)
        logger.info('Number of tracks for which audio features were obtained '
                    f'is {num_audio_features}.')
        # ----------------------------------------------------------------------------

        # merge information about songs
        # ----------------------------------------------------------------------------
        logger.info('Merging info on saved tracks and their audio features.')
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
        num_tracks_stage1 = len(tracks_stage1)
        logger.info(f'Number of tracks after merge is {num_tracks_stage1}.')
        # ----------------------------------------------------------------------------

        # create pandas dataframe
        # ----------------------------------------------------------------------------
        logger.info('Creating pandas dataframe.')
        df = pd.DataFrame(tracks_stage1)

        return df

    def get_user_id(self) -> str:
        """
        """
        logger.info('Getting information of user.')

        user_details: dict = self._client.current_user()
        user_id: str = user_details['id']

        return user_id

    def get_user_saved_tracks(self) -> List[dict]:
        """
        """
        # get all saved tracks by user
        logger.info('Getting saved tracks of user.')
        saved_tracks: List[dict] = sh.spotify_get_results(
            self._client, 'current_user_saved_tracks'
        )

        return saved_tracks

    def create_playlists(self, username: str) -> None:
        """
        """
        # load config values
        playlist_config: dict = Config.get('playlist_config')

        # get details about current user
        user_id: str = username
        logger.info(f'Proceeding with user {user_id}.')

        df_raw: pd.DataFrame = self.get_tracks_df()
        df_raw_shape: tuple = df_raw.shape
        logger.info(f'Shape of raw dataframe is {df_raw_shape}.')

        # dedup tracks with same artist and song name
        logger.info('Deduping tracks with same artist and song name.')
        df_stage1_subset = ['artist', 'song_name']
        df_stage1 = df_raw.drop_duplicates(subset=df_stage1_subset,
                                           keep='first',
                                           ignore_index=True)
        df_stage1_shape: tuple = df_stage1.shape
        logger.info(f'Shape of dataframe after deduping {df_stage1_shape}.')

        # create playlists from config
        # ----------------------------------------------------------------------------
        num_config_playlists = len(playlist_config)
        logger.info(f'Creating {num_config_playlists} playlists from config.')
        for pl in playlist_config:
            name = pl['name']
            metric = pl['metric']
            num_tracks = pl['num_tracks']
            description = pl['description']

            playlist_tracks: List[dict] = sh.get_ranked_tracks(df_stage1,
                                                               metric=metric,
                                                               num=num_tracks)
            playlist_details: Union[List[dict], None] = \
                sh.spotify_create_playlist(self._client,
                                           name=name,
                                           description=description,
                                           user_id=user_id)
            playlist_id: str = playlist_details['id']

            sh.spotify_fill_playlist(
                self._client,
                playlist_id=playlist_id,
                track_uris=playlist_tracks,
                user_id=user_id,
                overwrite=True
            )
        # ----------------------------------------------------------------------------

        logger.info('Done.')
