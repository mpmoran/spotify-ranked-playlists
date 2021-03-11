# -*- coding: utf-8 -*-
# standard libraries
import logging
from pathlib import Path
from typing import Union

# third-party libraries
from dotenv import load_dotenv
from flask import Flask

# local libraries


# load env vars from .env file
load_dotenv()

# configure logger
# ----------------------------------------------------------------------
log_file_path = Path('log.csv')
log_file_path.write_text('datetime|module_name|log_level|funcname|'
                         'message|filename|lineno\r\n')
logging.basicConfig(
    filename=str(log_file_path),
    filemode='a',
    # '\n' is added by logger
    format=('`{asctime}`|`{name}`|`{levelname}`|`{funcName}`|'
            '`{message}`|`{filename}`|`{lineno}`\r'),
    level=logging.INFO,
    style='{'
)
logger = logging
# ----------------------------------------------------------------------


def create_app(test_config: Union[None, dict] = None):
    """
    flask application factory
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=False)

    app.logger.info('starting application factory.')

    # # app.config.from_object('yourapplication.default_settings')
    # app.config.from_envvar('FLASK_CONFIG_PATH')
    # # load the instance config, if it exists, when not testing
    # app.config.from_pyfile('config.py', silent=True)
    #  load the test config if passed in
    # if test_config is not None:
    #     app.config.from_mapping(test_config)

    # register application blueprint
    import views
    app.register_blueprint(views.bp)
    # associate endpoint 'home' with '/' URL
    app.add_url_rule('/', endpoint='home')

    app.logger.info('finished creating application in factory.')

    return app


application = create_app()


# run the app.
if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)
