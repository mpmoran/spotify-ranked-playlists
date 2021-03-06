# standard libraries
import logging
from typing import List, Union

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
    logger.info(f'Creating and filling playlist {name}.')

    # get all playlist names
    playlists: List[dict] = spotify_get_results(client,
                                                'user_playlists',
                                                user=user_id)
    playlist_names = [pl['name'] for pl in playlists]

    if name in playlist_names:
        logger.info('Playlist already exists. Doing nothing.')
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

        logger.info('Created and filled playlist.')

        return details


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
