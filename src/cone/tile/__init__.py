from cone.tile._api import ITile
from cone.tile._api import register_tile
from cone.tile._api import render_template
from cone.tile._api import render_template_to_response
from cone.tile._api import render_tile
from cone.tile._api import render_to_response
from cone.tile._api import Tile
from cone.tile._api import tile
from cone.tile._api import TileRenderer
from zope.deprecation import deprecated


# B/C
registerTile = register_tile
deprecated('registerTile', """
``cone.tile.registerTile`` is deprecated as of cone.tile 1.0 and will be
removed in cone.tile 1.1. Use ``cone.tile.register_tile`` instead.""")
