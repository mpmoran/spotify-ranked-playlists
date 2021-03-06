# standard libraries
import logging
from typing import List

# third-party libraries
import pandas as pd
import spotipy


logger = logging.getLogger(__name__)


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
    logger.info(f'Ranking tracks by {metric}.')
    df_ranked = df.sort_values(by=metric,
                               ascending=ascending,
                               ignore_index=True)
    tracks: List[str] = df_ranked['uri'].iloc[:num].tolist()
    logger.info('Finished ranking tracks.')

    return tracks


def spotify_create_playlist(client: spotipy.client.Spotify,
                            name: str,
                            description: str,
                            user_id: str) -> List[dict]:
    """
    Create a playlist. If a playlist of the same name exists, this function
    does nothing. Returns information about playlist that was created or None.
    """
    logger.info(f'Creating playlist {name}.')

    # get all playlist names
    api_operation_name = 'user_playlists'
    playlists: List[dict] = spotify_get_results(client,
                                                api_operation_name,
                                                user=user_id)

    # Check if playlist name exists
    for pl in playlists:
        pl_name: str = pl['name']
        pl_id: str = pl['id']
        pl_uri: str = pl['uri']

        if name == pl_name:
            logger.info('Playlist already exists. Doing nothing.')
            details = {}
            details['id'] = pl_id
            details['uri'] = pl_uri

            return details

    create_response = client.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        collaborative=False,
        description=description
    )
    details = {}
    details['id'] = create_response['id']
    details['uri'] = create_response['uri']

    logger.info('Created and filled playlist.')

    return details


def spotify_fill_playlist(client: spotipy.client.Spotify,
                          playlist_id: str,
                          track_uris: List[dict],
                          user_id: str,
                          overwrite: bool = False) -> None:
    """
    Fill a playlist with tracks. If overwrite is True, all tracks on
    playlist are truncated and the playlist is filled with new tracks.
    """
    logger.info(f'Filling playlist {playlist_id}.')

    # Is the playlist already populated?
    tracks: List[dict] = spotify_get_results(client,
                                             operation='user_playlist_tracks',
                                             limit=100,
                                             playlist_id=playlist_id,
                                             fields=None)
    num_tracks = len(tracks)
    if num_tracks > 0:
        # Is overwrite set to True?
        if overwrite is True:
            # Truncate the playlist
            track_ids: List[str] = [track['track']['id'] for track in tracks]
            client.user_playlist_remove_all_occurrences_of_tracks(
                user=user_id,
                playlist_id=playlist_id,
                tracks=track_ids,
                snapshot_id=None
            )
        else:
            logger.info(f'Playlist {playlist_id} already has tracks and '
                        f'overwrite is set to {overwrite}. Doing nothing.')
            return None

    # Fill the playlist
    client.playlist_add_items(playlist_id=playlist_id,
                              items=track_uris,
                              position=None)
    logger.info('Filled playlist.')

    return None


def spotify_get_results(client: spotipy.client.Spotify,
                        operation: str,
                        limit: int = 50,
                        offset: int = 0,
                        **kwargs) -> List[dict]:
    """
    Return results of calling operation on Spotify client
    """
    logger.info(f'Calling and collecting results for {operation} operation.')

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

    logger.info('Finished calling and collecting results.')

    return results
