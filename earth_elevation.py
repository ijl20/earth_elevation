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

        self.get_box() # nw, se corners of tile, where each is (lon,lat)

    def get_box(self):
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

    def get_corner_coords(self):
        ulx, xres, xskew, uly, yskew, yres = self.geo_transform
        lrx = ulx + (self.src.RasterXSize * xres)
        lry = uly + (self.src.RasterYSize * yres)
        return {
            'TOP_LEFT': (ulx, uly),
            'TOP_RIGHT': (lrx, uly),
            'BOTTOM_LEFT': (ulx, lry),
            'BOTTOM_RIGHT': (lrx, lry),
        }

    def ilookup(self, lat, lon):
        #print(f"ilookup {lat}, {lon}")
        x = round((lon - self.lon_left) * self.lon_scale)
        y = round((self.lat_top - lat) * self.lat_scale)
        #print(f"ilookup using POINTS_ARRAY[{y},{x}]")
        return self.POINTS_ARRAY[y,x]

    def lookup(self, lat, lon):
        try:
            t1 = time.perf_counter()
            # get coordinate of the raster
            xgeo, ygeo, zgeo = self.coordinate_transform.TransformPoint(lon, lat, 0)
            t2 = time.perf_counter()

            # convert it to pixel/line on band
            u = xgeo - self.geo_transform_inv[0]
            v = ygeo - self.geo_transform_inv[3]

            t3 = time.perf_counter()

            # FIXME this int() is probably bad idea, there should be half cell size thing needed
            xpix = int(self.geo_transform_inv[1] * u + self.geo_transform_inv[2] * v)
            ylin = int(self.geo_transform_inv[4] * u + self.geo_transform_inv[5] * v)

            t4 = time.perf_counter()

            #print(f"lookup using POINTS_ARRAY[{ylin}, {xpix}]")
            # look the value up
            v = self.POINTS_ARRAY[ylin, xpix]

            t5 = time.perf_counter()

            #print(f"lookup times {(t2-t1)*1000} {(t3-t2)*1000} {(t4-t3)*1000} {(t5-t4)*1000}")
            return v if v != -32768 else self.SEA_LEVEL
        except Exception as e:
            print(e)
            return self.SEA_LEVEL

    def close(self):
        self.src = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

class EarthElevation():

    TILES = {}

    def load(self, name, path):
        t1 = time.perf_counter()
        self.TILES[name] = Tile(path)
        t2=time.perf_counter()
        print(f"load time {(t2-t1)*1000:.3f}")

    def lookup(self, name, lat, lng):
        tic=time.perf_counter()
        loc=self.TILES[name].lookup(lat, lng)
        toc=time.perf_counter()
        print(loc)
        print(f"lookup time {(toc-tic)*1000:.3f}")

    def ilookup(self, name, lat, lng):
        tic=time.perf_counter()
        loc=self.TILES[name].ilookup(lat, lng)
        toc=time.perf_counter()
        print(loc)
        print(f"ilookup time {(toc-tic)*1000:.3f}")

    def load_large(self):
        self.load('NE', '/mnt/sdb1/earth_elevation/SRTM_NE_250m_TIF/SRTM_NE_250m.tif')

    def load_small(self):
        self.load('/mnt/sdb1/earth_elevation/SRTM_NE_250m_TIF/SRTM_NE_250m_1_1.tif')

    def run_large(self):
        self.load_large()
        self.lookup(20,20)

    def start(self):
        tic=time.perf_counter()
        self.load('NE', '/mnt/sdb1/earth_elevation/SRTM_NE_250m_TIF/SRTM_NE_250m.tif')
        self.load('SE', '/mnt/sdb1/earth_elevation/SRTM_SE_250m_TIF/SRTM_SE_250m.tif')
        self.load('W', '/mnt/sdb1/earth_elevation/SRTM_W_250m_TIF/SRTM_W_250m.tif')
        toc=time.perf_counter()
        print(f"Tiles loaded time {(toc-tic)*1000:.3f}ms")
