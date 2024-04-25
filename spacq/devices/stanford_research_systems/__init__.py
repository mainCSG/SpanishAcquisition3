import logging
log = logging.getLogger(__name__)

name = 'Stanford Research Systems'

from . import sr830dsp, sg382, sim900
models = [sr830dsp, sg382, sim900]
log.debug('Found models for "{0}": {1}'.format(name, ''.join(str(x) for x in models)))

from .mock import mock_sr830dsp, mock_sg382, mock_sim900
mock_models = [mock_sr830dsp, mock_sg382, mock_sim900]
log.debug('Found mock models for "{0}": {1}'.format(name, ''.join(str(x) for x in mock_models)))
