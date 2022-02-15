# `earth_elevation`

## Install Linux gdal
```
sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
sudo apt update
sudo apt install gdal-bin
sudo apt install libgdal-dev
```

Also for Rtree in python:
```
sudo apt install libspatialindex-dev
```

Test with
```
ogrinfo --version
```

## Install python gdal
```
su earth_elevation
```
Get Linux gdal version:
```
gdal-config --version
```

```
cd earth_elevation
python3 -m venv venv
source venv/bin/activate
python3 -m pip install pip --upgrade
python3 -m pip install wheel
python3 -m pip install -r requirements.txt
```

export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
ogrinfo --version
```
Use the version returned above in this `pip install` command
```
python -m pip install 'GDAL==2.4.2' --global-option=build_ext --global-option="-I/usr/include/gdal"
```
Check install with:
```
which gdal-config
```
