__all__ = ['__version__', 'version_info', 'twisted_version']


# crawlmi version
import pkgutil
__version__ = pkgutil.get_data(__package__, 'VERSION').decode('ascii').strip()
version_info = tuple(int(v) if v.isdigit() else v
                     for v in __version__.split('.'))
del pkgutil


# Ignore noisy twisted deprecation warnings
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='twisted')
del warnings


# twisted version
from twisted import version as _txv
twisted_version = (_txv.major, _txv.minor, _txv.micro)
