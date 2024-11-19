"""
Tramopoly API
~~~~~~~~~~~~~~~~~~~

Manages multiple Tramopoly! games at once, storing them locally.

:copyright: (c) 2024 Aneurin Sterling
:license: MIT

"""

__title__ = 'tramopoly'
__author__ = 'Aneurin Sterling'
__license__ = 'MIT'
__copyright__ = 'Copyright 2024 Aneurin Sterling'
__version__ = '2.0.0'

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

from .game import *
from .stop import *
from .line import *
from .zone import *
from .team import *
from .action import *
from .special import *
from .card import *
from .map_images import drawMap