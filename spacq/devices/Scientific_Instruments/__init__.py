import logging
log = logging.getLogger(__name__)


name = 'Scientific Instruments'

from . import model9700
models = [model9700]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import model9700
mock_models = [model9700]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
