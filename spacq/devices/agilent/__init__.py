import logging
log = logging.getLogger(__name__)


name = 'Agilent'

from . import dm34410a, dm34401a, nwa8753et
models = [dm34410a, dm34401a, nwa8753et]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_dm34410a, mock_dm34401a, mock_nwa8753et
mock_models = [mock_dm34410a, mock_dm34401a, mock_nwa8753et]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
