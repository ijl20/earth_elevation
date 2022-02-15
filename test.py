import time
from gdal_interfaces import GDALInterface

class Test():
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
