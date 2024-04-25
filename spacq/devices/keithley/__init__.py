import logging
log = logging.getLogger(__name__)


name = 'Keithley'

from . import voltagesource230, sourceMeter2450, sourceMeter2401
models = [voltagesource230, sourceMeter2450, sourceMeter2401]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_voltagesource230, mock_sourceMeter2450, mock_sourceMeter2401
mock_models = [mock_voltagesource230, mock_sourceMeter2450, mock_sourceMeter2401]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
