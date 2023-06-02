#!/bin/bash

gdal_translate -of GTiff $1 /tmp/output.tif

gdaldem color-relief -of GTiff -alpha /tmp/output.tif ./color.txt /tmp/output_contour.tif

gdalwarp \
-s_srs \
"+proj=lcc +units=m +a=6370000.0 +b=6370000.0 +lat_1=30.0 \
 +lat_2=60.0 +lat_0=40.0 +lon_0=-97.0 +x_0=0 +y_0=0 +k_0=1.0 \
 +nadgrids=@null +wktext  +no_defs"\
  -t_srs EPSG:3857 \
  /tmp/output_contour.tif \
  /tmp/output_contour.png

echo "Projection successfully generated"
exit 0