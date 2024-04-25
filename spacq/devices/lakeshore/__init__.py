import logging
log = logging.getLogger(__name__)


name = 'Lakeshore'

from . import tc335, model218
models = [tc335, model218]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_tc335, mock_model218
mock_models = [mock_tc335, mock_model218]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
