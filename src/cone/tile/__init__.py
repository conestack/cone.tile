from cone.tile._api import ITile  # noqa
from cone.tile._api import register_tile
from cone.tile._api import render_template  # noqa
from cone.tile._api import render_template_to_response  # noqa
from cone.tile._api import render_tile  # noqa
from cone.tile._api import render_to_response  # noqa
from cone.tile._api import Tile  # noqa
from cone.tile._api import tile  # noqa
from cone.tile._api import TileRenderer  # noqa
from zope.deprecation import deprecated


# B/C
registerTile = register_tile
deprecated('registerTile', """
``cone.tile.registerTile`` is deprecated as of cone.tile 1.0 and will be
removed in cone.tile 1.1. Use ``cone.tile.register_tile`` instead.""")
