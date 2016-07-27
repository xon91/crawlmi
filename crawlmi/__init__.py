version_info = (0, 1, 8)
__version__ = '0.1.8'


# Ignore noisy twisted deprecation warnings
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='twisted')
del warnings


# Apply monkey patches to fix issues in external libraries
from . import _monkeypatches
del _monkeypatches
