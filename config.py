# -*- coding: utf-8 -*-
# standard libraries
import logging
import os
from pathlib import Path
from typing import Union

# third-party libraries
import yaml


logger = logging.getLogger(__name__)


class Config(object):
    """
    """
    _CONFIG_PATH = 'app.yaml'
    _config_store: Union[dict, None] = None

    @classmethod
    def get(cls, name: str) -> Union[str, list, dict]:
        """
        Return configuration value for name.
        """
        if cls._config_store is None:
            cls._load_configuration()

        val = cls._config_store.get(name)

        return val

    @classmethod
    def _load_configuration(cls):
        """
        Load configuration into store.
        """
        logger.info('Loading configurations.')

        cls._config_store = {}

        # load regular configuration
        config_text: str = Path(cls._CONFIG_PATH).read_text()
        config: dict = yaml.safe_load(config_text)
        cls._config_store['user_auth_flow'] = config['user_auth_flow']
        cls._config_store['spotify_permissions_scope'] = \
            config['spotify_permissions_scope']

        # load playlists configuration
        cls._config_store['playlist_config'] = config['playlists']

        # get authentication details for Spotify
        logger.info('Pulling secrets.')
        cls._config_store['sp_client_id'] = os.getenv('SPOTIFY_CLIENT_ID')
        cls._config_store['sp_client_secret'] = \
            os.getenv('SPOTIFY_CLIENT_SECRET')
        if cls._config_store['user_auth_flow'] == 'authorization':
            cls._config_store['sp_redirect_uri'] = \
                os.getenv('SPOTIFY_REDIRECT_URI')
        cls._config_store['sp_scope'] = \
            cls._config_store['spotify_permissions_scope']

        logger.info('Finishedd loadding configuration.')
