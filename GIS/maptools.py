# -*- coding: utf-8 -*-
"""
    Various useful tools for mapping.
	
	Mainly calls the GDAL library
	
	Uses include:
		Coordinate conversion
		Reading various raster formats
		Reading shapefiles
		...
"""
from osgeo import osr
import ogr
import gdal
from gdalconst import * 
import numpy as np
import matplotlib.pyplot as plt

import pdb

def ll2utm(LL,zone,CS='WGS84',north=True):
    """ Convert from lat/long coordinates to utm"""
    
    srs = osr.SpatialReference()
    if north:
        proj = "UTM %d (%s) in northern hemisphere."%(zone,CS)
    else:
        proj = "UTM %d (%s) in southern hemisphere."%(zone,CS)
        
    srs.SetProjCS( proj );
    srs.SetWellKnownGeogCS( CS );
    srs.SetUTM( zone, True );
    
    srsLatLong = srs.CloneGeogCS()
    ct = osr.CoordinateTransformation(srsLatLong,srs )
    
    npt=np.size(LL,0)
    if npt > 2:
        XY=np.zeros((npt,2))
        for ii in range(0,npt):
            X,Y,z =  ct.TransformPoint(LL[ii,0],LL[ii,1])
            XY[ii,0]=X
            XY[ii,1]=Y
    else:
        XY=np.zeros((1,2))
        X,Y,z = ct.TransformPoint(LL[0],LL[1])
        XY[0,0]=X
        XY[0,1]=Y
    
    return XY
    
def readDEM(bathyfile,returnvec=False):
    """ Loads the data from a DEM file"""
    # register all of the drivers
    gdal.AllRegister()
    # open the image
    ds = gdal.Open(bathyfile, GA_ReadOnly)
    
    # Read the x and y coordinates
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bands = ds.RasterCount
    
    geotransform = ds.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    
    x = originX + np.linspace(0,cols-1,cols)*pixelWidth
    y = originY + np.linspace(0,rows-1,rows)*pixelHeight
    X,Y=np.meshgrid(x,y)
    
    # Read the actual data
    data = ds.ReadAsArray(0,0,cols,rows)
    
    # Remove missing points
    data[data==-32767]=np.nan

    if returnvec:
        x=np.ravel(X)
        y=np.ravel(Y)
        z=np.ravel(data)
        ind = z != np.nan
        nc = np.sum(ind)
        XY = np.concatenate((np.reshape(x[ind],(nc,1)),np.reshape(y[ind],(nc,1))),axis=1)
        data = z[ind]
        return XY,data
    else:
        return X, Y, data     
    
def readShpBathy(shpfile,FIELDNAME = 'CONTOUR'):
    """ Reads a shapefile with line or point geometry and returns x,y,z
    
    See this tutorial:
        http://www.gis.usu.edu/~chrisg/python/2009/lectures/ospy_slides1.pdf
    """
    # Open the shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    
    shp = driver.Open(shpfile, 0)
    
    lyr = shp.GetLayer()
    
    lyr.ResetReading()
    X=[]
    Y=[]
    Z=[]
    for feat in lyr:
        feat_defn = lyr.GetLayerDefn()
        for i in range(feat_defn.GetFieldCount()):
            field_defn = feat_defn.GetFieldDefn(i)
            if field_defn.GetName() == FIELDNAME:
                geom = feat.GetGeometryRef()
                ztmp = float(feat.GetField(i))
                if geom.GetGeometryType() == ogr.wkbPoint: # point
                    X.append(geom.getX())
                    Y.append(geom.getY())
                    Z.append(ztmp)
                elif geom.GetGeometryType() == 2:  # line
                    xyall=geom.GetPoints()
                    for xy in xyall:
                        X.append(xy[0])
                        Y.append(xy[1])
                        Z.append(ztmp)
                        
                elif geom.GetGeometryType() == 5:  # multiline
#                    pdb.set_trace()
                    for ii in range(0,geom.GetGeometryCount()):
                        geom2 = geom.GetGeometryRef(ii)
                        xyall=geom2.GetPoints()
                        for xy in xyall:
                            X.append(xy[0])
                            Y.append(xy[1])
                            Z.append(ztmp)
#                    print geom.GetGeometryName()
#                    print geom.GetGeometryType()
    shp=None
    nc = len(X)
    XY = np.concatenate((np.reshape(np.array(X),(nc,1)),(np.reshape(np.array(Y),(nc,1)))),axis=1)
    del X
    del Y
    return XY,np.array(Z)

def readraster(infile):
    """ Loads the data from any raster-type file
        eg. *.dem, *.grd,...    
    """
    # register all of the drivers
    gdal.AllRegister()
    # open the image
    ds = gdal.Open(infile, GA_ReadOnly)
    
    # Read the x and y coordinates
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bands = ds.RasterCount
    
    geotransform = ds.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    
    x = originX + np.linspace(0,cols-1,cols)*pixelWidth
    y = originY + np.linspace(0,rows-1,rows)*pixelHeight
    
    # Read the actual data
    data = ds.ReadAsArray(0,0,cols,rows)
    
    # Remove missing points
    data[data==-32767]=np.nan

###Testing###
#LL=[-94.2,27.0]
#zone=15
#ll2utm(LL,zone,CS='WGS84',north=True)

#shpfile = 'C:/Projects/GOMGalveston/DATA/Bathymetry/TNRIS/BathyTopoTXCoast_V0.2/Shapefiles/Bathymetry.shp'
#XY,Z = readShpBathy(shpfile)
#
#fig= plt.figure(figsize=(8,9))
##h.imshow(np.flipud(self.Z),extent=[bbox[0],bbox[1],bbox[3],bbox[2]])
#plt.plot(XY[:,0],XY[:,1],'.')
#plt.axis('equal')
#plt.show()