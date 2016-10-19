import logging

from http import HTTPStatus

from flask import Flask, send_from_directory, render_template, jsonify
from flask_cors import CORS
from flask.ext.compress import Compress
from flask_webpack import Webpack

from community_share import config, store, flask_sslify
from community_share.app_exceptions import BadRequest, Forbidden, NotFound, NotAuthorized
from community_share.routes.user_routes import register_user_routes
from community_share.routes.search_routes import register_search_routes
from community_share.routes.conversation_routes import register_conversation_routes
from community_share.routes.share_routes import register_share_routes
from community_share.routes.survey_routes import register_survey_routes
from community_share.routes.email_routes import register_email_routes
from community_share.routes.statistics_routes import register_statistics_routes

import community_share.api

YEAR_IN_SECONDS = 31536000

logger = logging.getLogger(__name__)


# Forces Flask functions to return HTTPS links
def ReverseProxied(app):

    def add_header(environ, start_response):
        environ['wsgi.url_scheme'] = 'https'
        return app(environ, start_response)

    return add_header


# Converts an exception into a JSON blob:
#
# error -> { "message": str(error) }
#
# Our client expects this format to show error messages. If we remove that dependency, we can avoid jsonifying these errors.
def jsonify_error_for_code(code):
    def jsonify_error(error):
        response = jsonify({ "message": str(error) })
        response.status_code = code
        return response
    return jsonify_error

def make_app():
    cors = CORS(origins=[
        'https://app.communityshare.us:443', # production app
        'http://communityshare.localhost:5000', # local dev angular app
        'http://communityshare.localhost:8000', # local dev elm app
        'https://dmsnell.github.io/cs-elm/', # live elm app
    ])
    compress = Compress()
    webpack = Webpack()
    app = Flask(__name__, template_folder='../static/')

    app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_CONNECTION
    app.config['WEBPACK_ASSETS_URL'] = config.WEBPACK_ASSETS_URL
    app.config['WEBPACK_MANIFEST_PATH'] = config.WEBPACK_MANIFEST_PATH

    cors.init_app(app)
    compress.init_app(app)
    webpack.init_app(app)

    if config.SSL != 'NO_SSL':
        flask_sslify.SSLify(app)
        app.wsgi_app = ReverseProxied(app.wsgi_app)

    register_user_routes(app)
    register_search_routes(app)
    register_conversation_routes(app)
    register_share_routes(app)
    register_survey_routes(app)
    register_email_routes(app)
    register_statistics_routes(app)

    community_share.api.register_routes(app)

    @app.teardown_appcontext
    def close_db_connection(exception):
        store.session.remove()

    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        return str(error), HTTPStatus.BAD_REQUEST

    app.errorhandler(Forbidden)(jsonify_error_for_code(HTTPStatus.FORBIDDEN))
    app.errorhandler(NotAuthorized)(jsonify_error_for_code(HTTPStatus.UNAUTHORIZED))
    app.errorhandler(NotFound)(jsonify_error_for_code(HTTPStatus.NOT_FOUND))

    @app.route('/static/build/<path:filename>')
    def build_static(filename):
        return send_from_directory(
            app.root_path + '/../static/build/',
            filename,
            cache_timeout=YEAR_IN_SECONDS,
        )

    @app.route('/static/js/<path:filename>')
    def js_static(filename):
        return send_from_directory(app.root_path + '/../static/js/', filename)

    @app.route('/static/fonts/<path:filename>')
    def fonts_static(filename):
        return send_from_directory(app.root_path + '/../static/fonts/', filename)

    @app.route('/static/css/<path:filename>')
    def css_static(filename):
        return send_from_directory(app.root_path + '/../static/css/', filename)

    @app.route('/static/templates/footer.html')
    def footer_template():
        return render_template('templates/footer.html', config=config)

    @app.route('/static/templates/<path:filename>')
    def templates_static(filename):
        return send_from_directory(app.root_path + '/../static/templates/', filename)

    @app.route('/')
    def index():
        logger.debug('rendering index')
        return render_template('index.html', config=config)

    return app
