from flask import (
    Blueprint, current_app, flash, redirect, render_template, request, url_for
)
from flask.views import View
from markupsafe import escape
from werkzeug.exceptions import abort


BP_NAME = __name__.split('.')[-1]
bp = Blueprint(BP_NAME, __name__)


@bp.route('/create_playlists', methods=('POST',))
def create_playlists():
    if request.method == 'POST':
        current_app.logger.info('creating playlists')

        username = escape(request.form['username'])

        from spotify import Spotify
        sp = Spotify()
        sp.create_playlists(username=username)

        return 'Success!'


@bp.route('/', methods=('GET', 'POST'))
def home():
    current_app.logger.info('serving home page.')

    current_app.logger.error(f'{BP_NAME}')
    return render_template(
        f'{BP_NAME}/home.html',
    )
