# `earth_elevation`

## Install Linux gdal
```
sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
sudo apt update
sudo apt install gdal-bin
sudo apt install libgdal-dev
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
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
pip install GDAL
ogrinfo --version
```
Use the version returned above in this `pip install` command
python -m pip install 'GDAL==2.4.2'
```
Check install with:
```
which gdal-config
```
