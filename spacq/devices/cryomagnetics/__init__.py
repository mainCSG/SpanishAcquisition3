import logging
log = logging.getLogger(__name__)


name = 'Cryomagnetics'

from . import model4g
models = [model4g]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_model4g
mock_models = [mock_model4g]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
