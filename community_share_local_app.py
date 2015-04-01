import logging

from community_share import config, app

logger = logging.getLogger(__name__)

logger.info('Loading settings from file')
config.load_from_file()
logger.info('Making application')
app = app.make_app()
app.debug = True
logger.info('Debug={0}'.format(app.debug))
app.run()
