import logging
log = logging.getLogger(__name__)

name = 'Physics Basel'

from . import dacsp927
models = [dacsp927]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_dacsp927
mock_models = [mock_dacsp927]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
