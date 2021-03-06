import os
import unittest
import numpy as np
import pytest

from geopyspark.geotrellis import (Tile,
                                   ProjectedExtent,
                                   Extent,
                                   RasterLayer,
                                   LocalLayout,
                                   TileLayout,
                                   GlobalLayout,
                                   LayoutDefinition,
                                   SpatialPartitionStrategy)
from geopyspark.tests.base_test_class import BaseTestClass
from geopyspark.geotrellis.constants import LayerType, CellType


def make_raster(x, y, v, cols=4, rows=4, ct=CellType.FLOAT32, crs=4326):
    cells = np.zeros((1, rows, cols))
    cells.fill(v)
    # extent of a single cell is 1, no fence-post here
    extent = ProjectedExtent(Extent(x, y, x + cols, y + rows), crs)
    return (extent, Tile(cells, ct, None))


class TileToLayoutTest(BaseTestClass):
    layers = [
        make_raster(0, 0, v=1),
        make_raster(3, 2, v=2),
        make_raster(6, 0, v=3)
    ]

    numpy_rdd = BaseTestClass.pysc.parallelize(layers)
    layer = RasterLayer.from_numpy_rdd(LayerType.SPATIAL, numpy_rdd)
    metadata = layer.collect_metadata(GlobalLayout(5))

    def test_to_to_layout_with_partitioner(self):
        strategy = SpatialPartitionStrategy(4)
        tiled = self.layer.tile_to_layout(LocalLayout(5), partition_strategy=strategy)

        self.assertEqual(tiled.get_partition_strategy(), strategy)

    def test_tile_to_local_layout(self):
        tiled = self.layer.tile_to_layout(LocalLayout(5))
        assert tiled.layer_metadata.extent == Extent(0,0,10,6)
        assert tiled.layer_metadata.tile_layout == TileLayout(2,2,5,5)

    def test_tile_to_global_layout(self):
        tiled = self.layer.tile_to_layout(GlobalLayout(5))
        assert tiled.layer_metadata.extent == Extent(0,0,10,6)
        assert tiled.layer_metadata.tile_layout == TileLayout(128,128,5,5)
        assert tiled.zoom_level == 7

    def test_tile_to_metadata_layout(self):
        tiled = self.layer.tile_to_layout(layout=self.metadata)

        self.assertEqual(tiled.layer_metadata.extent, Extent(0,0,10,6))
        self.assertDictEqual(tiled.layer_metadata.to_dict(), self.metadata.to_dict())

    def test_tile_to_tiled_layer_layout(self):
        extent = Extent(0., 0., 10., 6.)
        tile_layout = TileLayout(2,2,5,5)
        layout_definition = LayoutDefinition(extent, tile_layout)

        base = self.layer.tile_to_layout(layout_definition)
        tiled = self.layer.tile_to_layout(layout=base)

        self.assertDictEqual(tiled.layer_metadata.to_dict(), base.layer_metadata.to_dict())

    def test_tile_to_layout_definition(self):
        tiled = self.layer.tile_to_layout(layout=self.metadata.layout_definition)

        self.assertDictEqual(tiled.layer_metadata.to_dict(), self.metadata.to_dict())

    @pytest.fixture(scope='class', autouse=True)
    def tearDown(self):
        yield
        BaseTestClass.pysc._gateway.close()


if __name__ == "__main__":
    unittest.main()
