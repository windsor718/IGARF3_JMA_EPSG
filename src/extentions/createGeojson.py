import os
import datetime
import ConfigParser
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from shapely.geometry import Point
from gtool import gtopen


class CreateGeojson(object):
    
    """
    wrapper of the classes below.
    """

    def __init__(self,initFile,cDate):
        
        self.initFile = ConfigParser.SafeConfigParser()
        self.initFile.read(initFile)
        self.region = "gl"

        self.cDate    = cDate
        self.oPath    = "/var/www/html/tdjpn/archive"


    def main(self):

        # plot alerted points
        alert = Alert(self.cDate.year,self.cDate.month,self.cDate.day,self.cDate.hour,self.region)
        alert.nLat = 720
        alert.nLon  = 1440
        alert.nT    = int(self.initFile.get("Model","FrcTime"))
        alert.tStep = int(self.initFile.get("Model","dtOut"))

        rName     = self.initFile.get("Model","runName")
        outRoot   = self.initFile.get("Model","outRoot")
        camaRoot  = self.initFile.get("Model","camaRoot")
        sysRoot   = self.initFile.get("Model","sysRoot")
        outSuffix = "Forecast/%04d/%02d/%02d/%02d/e%02d/cama/rivdph.bin"
        alert.dschgPath = os.path.join(outRoot,rName,outSuffix)

        alert.dpiPath   = os.path.join(sysRoot,"src/extentions/DPI_rivdph_glb.bin")
        alert.mapRoot   = os.path.join(camaRoot,"map/global_025/")
        alert.oPath     = self.oPath

        df, dArray = alert.main()
        df.to_file(os.path.join(self.oPath,"./%04d%02d%02d%02d_%s.geojson"%(alert.year,alert.month,alert.day,alert.hour,self.region)), driver="GeoJSON")
        dArray.to_netcdf(os.path.join(self.oPath, "./%04d%02d%02d%02d_%s.nc"%(alert.year,alert.month,alert.day,alert.hour,self.region)))

    def cache(self):
        alert = Alert(self.cDate.year,self.cDate.month,self.cDate.day,self.cDate.hour,self.region)
        alert.nLat = 720
        alert.nLon  = 1440
        sysRoot   = self.initFile.get("Model","sysRoot")
        alert.dpiPath   = os.path.join(sysRoot,"src/extentions/DPI_rivdph_glb.bin")
        alert.oPath     = self.oPath

        alert.cacheDpiInfo(self.region)

class Alert(object):
    
    def __init__(self,year,mon,day,hour,region):
        
        self.dschgPath = "/dias/users/ishitsuka.y.u-tokyo/tdjpn/FF/ECMWF/out/glb050/Forecast//%04d/%02d/%02d/%02d/e%02d/cama/rivdph.bin"
        self.dpiPath   = "./DPI.bin"
        self.mapRoot   = "/dias/users/ishitsuka.y.u-tokyo/tdjpn/CaMa-Flood_v3.6.2_20140909/map/global_025"
        self.nLat      = 720
        self.nLon      = 1440
        self.nT        = 40
        self.tStep     = 3600

        self.year      = year
        self.month     = mon
        self.day       = day
        self.hour      = hour
        self.region    = region

        self.thsld     = [50,100,150,200]
        self.colors    = ["lightblue","green","orange","red"]
        self.icon      = "info-sign"
        
        self.oPath     = "/var/www/html/tdjpn/archive/"
        self.width     = 6.5
        self.height    = 2
        self.resl      = 75

        self.eMembers  = 51

        self.tickIntv  = 6

    def main(self):
        ensMean, ensStd = self.getEnsMean()
        index, dpi = self.index(ensMean)
        df, dArray = self.extractAlertedPoints(index, ensMean, ensStd, dpi)
    
        return df, dArray

    def cacheDpiInfo(self,region):
        dpi = np.fromfile(self.dpiPath,dtype="f4").reshape(-1,self.nLat,self.nLon)*2
        DPIs = []
        for v in self.thsld:
            dpisForThsld = []
            IDs = []
            for lat in range(0,self.nLat):
                for lon in range(0,self.nLon):
                    ID = "%d_%d_%s"%(lat,lon,self.region)
                    dpiDschg = dpi[v-2,lat,lon]
                    IDs.append(ID)
                    dpisForThsld.append(dpiDschg)
            DPIs.append(dpisForThsld)
        DPIs = np.array(DPIs)
        print DPIs.shape
        dArray = xr.DataArray(DPIs, dims=("rYear","ID"), coords=(self.thsld,IDs))
        dArray.to_netcdf(os.path.join(self.oPath,"dpiDischarge_%s.nc"%(region)))

    def index(self,dschg):

        dsMax = dschg.max(axis=0) # duplicate?
        dpi   = np.fromfile(self.dpiPath,dtype="f4").reshape(-1,self.nLat,self.nLon)*2

        index = np.zeros((self.nLat,self.nLon))
        thsld = sorted(self.thsld)
        [ self.replaceToIndex(index,dsMax,dpi[thsld[i]-2],thsld[i]) for i in range(len(thsld)) ]

        ###deplicated?
        index[np.where(dpi[-1] < 1)] = 0
        index[np.where(dsMax >= 1e+20)] = 0
        ###


        return index,dpi


    def getEnsMean(self):

        ENS = np.ones((self.eMembers,self.nT,self.nLat,self.nLon))
        ENS[ENS==1] = np.nan
        for eNum in range(0, self.eMembers):
            print self.dschgPath%(self.year, self.month, self.day, self.hour, eNum)
            if os.path.exists(self.dschgPath%(self.year, self.month, self.day, self.hour, eNum)):
                dschg  = np.fromfile(self.dschgPath%(self.year, self.month, self.day, self.hour, eNum),dtype="f4").reshape(-1,self.nLat,self.nLon)
                ENS[eNum] = dschg
            else:
                print(self.dschgPath%(self.year, self.month, self.day, self.hour, eNum),"not found.")
                continue

        ensMean = np.nanmean(ENS, axis=0)
        ensStd  = np.nanstd(ENS, axis=0)

        return ensMean, ensStd


    def extractAlertedPoints(self,index,ensMean,ensStd,dpi):

        dRange     = []
        sDate      = datetime.datetime(self.year,self.month,self.day,self.hour)
        [dRange.append(sDate + datetime.timedelta(seconds=self.tStep*i)) for i in range(0,self.nT)]

        Map = np.memmap(os.path.join(self.mapRoot,"lonlat.bin"),mode="r",dtype="f4",shape=(2,self.nLat,self.nLon))
        IDs = []
        dsList = []
        stdList = []
        geoElements = []
        for v in self.thsld:
            if np.where(index == v)[0].shape[0] == 0:
                continue
            lats = np.where(index == v)[0]
            lons = np.where(index == v)[1]
            for i in range(0,lats.shape[0]):
                ID, point, dsSeries, stdSeries = self.makeProperties(Map,lats[i],lons[i],ensMean,ensStd)
                IDs.append(ID)
                dsList.append(dsSeries)
                stdList.append(stdSeries)
                geoElements.append([ID, v, point])
        df = pd.DataFrame(geoElements)
        df.columns = ["ID", "DPI", "geometry"]
        print df
        df = gpd.GeoDataFrame(df, geometry="geometry")

        dsArray = np.concatenate(dsList, axis=0).reshape(1,len(IDs),len(dRange))
        stdArray = np.concatenate(stdList, axis=0).reshape(1,len(IDs),len(dRange))
        outArray = np.concatenate([dsArray,stdArray],axis=0)
        outArray = xr.DataArray(outArray, dims=("kind", "ID", "datetime"), coords=(["mean","std"],IDs,dRange))
        print outArray
        return df, outArray

    def makeProperties(self,Map,glat,glon,ensMean,ensStd):

        ID = "%d_%d_%s"%(glat,glon,self.region)
        lat = Map[1,glat,glon]
        lon = Map[0,glat,glon]
        point = Point(lon, lat)
        values = ensMean[:,glat,glon].reshape(1,-1)
        stds = ensStd[:,glat,glon].reshape(1,-1)*10

        return ID, point, values, stds

    def replaceToIndex(self,index,dschgData,dpi,value):

        index[np.where(dschgData > dpi)] = value

        return True

if __name__ == "__main__":
    
    config = "../../config.ini"
    sDate = datetime.datetime(2019,5,19,0)
    eDate = datetime.datetime(2019,5,29,12)
    cDate = sDate
    while cDate <= eDate:
        print cDate
        chunk = CreateGeojson(config,cDate)
        #chunk.cache()
        chunk.main()
        cDate = cDate + datetime.timedelta(hours=12)
