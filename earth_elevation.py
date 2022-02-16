import time
import os
from osgeo import gdal, osr
from lazy import lazy
from os import listdir
from os.path import isfile, join, getsize
import json
from rtree import index

class Tile(object):
    # Globals
    SEA_LEVEL = 0
    POINTS_ARRAY = None

    def __init__(self, tif_path):
        super(Tile, self).__init__()
        self.tif_path = tif_path

        # open the raster and its spatial reference
        self.src = gdal.Open(self.tif_path)

        if self.src is None:
            raise Exception('Could not load GDAL file "%s"' % self.tif_path)
        spatial_reference_raster = osr.SpatialReference(self.src.GetProjection())

        # get the WGS84 spatial reference
        spatial_reference = osr.SpatialReference()
        spatial_reference.ImportFromEPSG(4326)  # WGS84

        # coordinate transformation
        self.coordinate_transform = osr.CoordinateTransformation(spatial_reference, spatial_reference_raster)
        gt = self.geo_transform = self.src.GetGeoTransform()
        dev = (gt[1] * gt[5] - gt[2] * gt[4])
        self.geo_transform_inv = (gt[0], gt[5] / dev, -gt[2] / dev,
                                  gt[3], -gt[4] / dev, gt[1] / dev)

        b = self.src.GetRasterBand(1)
        self.POINTS_ARRAY = b.ReadAsArray()

        ulx, xres, _, uly, _, yres = self.src.GetGeoTransform()
        self.lat_top = uly
        self.lon_left = ulx
        lon_right = ulx + self.src.RasterXSize * xres
        lat_bottom = uly + self.src.RasterYSize * yres
        lon_width = lon_right - self.lon_left
        lat_height = self.lat_top - lat_bottom
        lon_points = self.POINTS_ARRAY.shape[1]
        lat_points = self.POINTS_ARRAY.shape[0]
        self.lon_scale = lon_points / lon_width
        self.lat_scale = lat_points / lat_height

    def lookup(self, lat, lon):
        #print(f"lookup {lat}, {lon}")
        try:
            x = round((lon - self.lon_left) * self.lon_scale)
            y = round((self.lat_top - lat) * self.lat_scale)
            #print(f"ilookup using POINTS_ARRAY[{y},{x}]")

            elevation = self.POINTS_ARRAY[y,x]

            return elevation if elevation != -32768 else self.SEA_LEVEL
        except Exception as e:
            print(e)
            return self.SEA_LEVEL

class EarthElevation():

    TILES = {}

    def load(self, name, path):
        t1 = time.perf_counter()
        self.TILES[name] = Tile(path)
        t2=time.perf_counter()
        print(f"load time {(t2-t1)*1000:.3f}")

    def lookup(self, lat, lon):
        #tic=time.perf_counter()
        # We can hard-code the Tile selection
        name = 'NE'
        if lon < -30.010416772249997:
            name = 'W'
        elif lat < -0.00208333333:
            name = 'SE'
        elevation = self.TILES[name].lookup(lat, lon)
        #toc=time.perf_counter()
        #print(f"lookup time {(toc-tic)*1000:.3f}")
        return int(elevation)

    def start(self):
        tic=time.perf_counter()
        self.load('NE', '/mnt/sdb1/earth_elevation/SRTM_NE_250m_TIF/SRTM_NE_250m.tif')
        self.load('SE', '/mnt/sdb1/earth_elevation/SRTM_SE_250m_TIF/SRTM_SE_250m.tif')
        self.load('W', '/mnt/sdb1/earth_elevation/SRTM_W_250m_TIF/SRTM_W_250m.tif')
        toc=time.perf_counter()
        print(f"Tiles loaded time {(toc-tic)*1000:.3f}ms")

    def test(self):
        print(f"Mifflin lookup {self.lookup(40.6778,-77.6263)} should be 251")
        print(f"Germany lookup {self.lookup(50.56323,10.62979)} should be 601")
        print(f"South Africa lookup {self.lookup(-32.67897,24.20700)} should be 744")
        print(f"Australia lookup {self.lookup(-32.28488,150.87893)} should be 144")
        print(f"Equador lookup {self.lookup(-0.11823,-78.35878)} should be 2372")
