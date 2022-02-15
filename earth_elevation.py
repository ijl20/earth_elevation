import time
import os
from osgeo import gdal, osr
from lazy import lazy
from os import listdir
from os.path import isfile, join, getsize
import json
from rtree import index

class GDALInterface(object):
    SEA_LEVEL = 0
    def __init__(self, tif_path):
        super(GDALInterface, self).__init__()
        self.tif_path = tif_path
        self.loadMetadata()

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

    def loadMetadata(self):
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


    @lazy
    def points_array(self):
        b = self.src.GetRasterBand(1)
        return b.ReadAsArray()

    #def make_points_array(self):
    #    global POINTS_ARRAY
    #    b = self.src.GetRasterBand(1)
    #    POINTS_ARRAY = b.ReadAsArray()

    def print_statistics(self):
        print(self.src.GetRasterBand(1).GetStatistics(True, True))


    def lookup(self, lat, lon):
        try:

            # get coordinate of the raster
            xgeo, ygeo, zgeo = self.coordinate_transform.TransformPoint(lon, lat, 0)

            # convert it to pixel/line on band
            u = xgeo - self.geo_transform_inv[0]
            v = ygeo - self.geo_transform_inv[3]
            # FIXME this int() is probably bad idea, there should be half cell size thing needed
            xpix = int(self.geo_transform_inv[1] * u + self.geo_transform_inv[2] * v)
            ylin = int(self.geo_transform_inv[4] * u + self.geo_transform_inv[5] * v)

            # look the value up
            v = self.points_array[ylin, xpix]

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
    GDI=None

    def load(self, path):
        global GDI
        t1 = time.perf_counter()
        GDI = GDALInterface(path)
        t2=time.perf_counter()
        print(f"load_large time {(t2-t1)*1000:.3f}")

    def lookup(self, lat, lng):
        global GDI
        tic=time.perf_counter()
        loc=GDI.lookup(lat, lng)
        toc=time.perf_counter()
        print(loc)
        print(f"lookup time {(toc-tic)*1000:.3f}")

    def load_large(self):
        self.load('/mnt/sdb1/earth_elevation/SRTM_NE_250m_TIF/SRTM_NE_250m.tif')

    def run_large(self):
        self.load_large()
        self.lookup(20,20)
