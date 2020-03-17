import numpy as np
import pandas as pd
import seaborn as sns
import datetime
import os
import folium
import matplotlib;matplotlib.use("Agg")
import matplotlib.pyplot as plt
import genMap

class PlotDpi(object):
    
    def __init__(self,year,mon,day,hour):
        
        sns.set()

        self.dschgPath = "/dias/users/ishitsuka.y.u-tokyo/tdjpn/FF/ECMWF/out/glb050/Forecast//%04d/%02d/%02d/%02d/e%02d/cama/outflw.bin"
        self.dpiPath   = "/dias/users/ishitsuka.y.u-tokyo/tdjpn/CaMa-Flood_v3.6.2_20140909/map/global_025/DPI.bin"
        self.mapRoot   = "/dias/users/ishitsuka.y.u-tokyo/tdjpn/CaMa-Flood_v3.6.2_20140909/map/global_025"
        self.nLat      = 720
        self.nLon      = 1440
        self.nT        = 40
        self.tStep     = 3600

        self.year      = year
        self.month     = mon
        self.day       = day
        self.hour      = hour

        self.thsld     = [50,100,150,200]
        self.colors    = ["lightblue","green","orange","red"]
        self.icon      = "info-sign"
        
        self.oPath     = "/var/www/html/tdjpn/archive/"
        self.width     = 6.5
        self.height    = 2
        self.resl      = 75

        self.eMembers  = 51

        self.tickIntv  = 6


    def index(self,dschg):

        dsMax = dschg.max(axis=0) # duplicate?
        dpi   = np.fromfile(self.dpiPath,dtype="f4").reshape(-1,self.nLat,self.nLon)

        index = np.zeros((self.nLat,self.nLon))
        thsld = sorted(self.thsld)
        [ self.replaceToIndex(index,dsMax,dpi[thsld[i]-2],thsld[i]) for i in range(len(thsld)) ]

        ###deplicated?
        index[np.where(dpi[-1] < 500.)] = 0
        index[np.where(dsMax >= 1e+20)] = 0
        ###


        return index,dpi


    def getEnsMean(self):

        ENS         = np.ones((self.eMembers,self.nT,self.nLat,self.nLon))
#        for eNum in range(0, self.eMembers):
        for eNum in range(1, self.eMembers):
            print self.dschgPath%(self.year, self.month, self.day, self.hour, eNum)
            dschg     = np.fromfile(self.dschgPath%(self.year, self.month, self.day, self.hour, eNum),dtype="f4").reshape(-1,self.nLat,self.nLon)
            print dschg.shape
            ENS[eNum] = dschg

        ensMean = ENS.mean(axis=0)
        ensStd  = np.std(ENS, axis=0)

        return ensMean, ensStd


    def genHtml(self,index,ensMean,ensStd,dpi):

        chunk      = genMap.GenMap()
        self.map   = chunk.genMap()
        dRange     = []
        sDate      = datetime.datetime(self.year,self.month,self.day,self.hour)
        [dRange.append(sDate + datetime.timedelta(seconds=self.tStep*i)) for i in range(0,self.nT)]
        dRange     = np.array(dRange)

        for v in self.thsld:
            if np.where(index == v)[0].shape[0] == 0:
                continue
            lats = np.where(index == v)[0]
            lons = np.where(index == v)[1]
            [ self.plot(lats[i],lons[i],ensMean,ensStd,dpi,dRange,v) for i in range(0,lats.shape[0]) ]
        self.map.save(os.path.join(self.oPath,"gl_%04d%02d%02d%02d.html"%(self.year,self.month,self.day,self.hour)))


    def plot(self,glat,glon,ensMean,ensStd,dpi,dRange,idx):

        map = np.memmap(os.path.join(self.mapRoot,"lonlat.bin"),mode="r",dtype="f4",shape=(2,self.nLat,self.nLon))
        lat = map[1,glat,glon]
        lon = map[0,glat,glon]
        loc = [lat,lon]

        print glat,glon
        values   = ensMean[:,glat,glon]
        devs     = ensStd[:,glat,glon]
        fig,ax   = plt.subplots(figsize=(self.width,self.height))
        ax.plot(values,label="sim",color="k",linewidth=2)
        ax.plot(values+devs,color="#1A5276",linewidth=0.01)
        ax.plot(values-devs,color="#1A5276",linewidth=0.01)
        x = np.arange(0,values.shape[0])
        ax.fill_between(x,values+devs,values-devs,where=np.isfinite(values+devs),alpha=0.5,facecolor="#1A5276")
        ax.fill_between(x,values+2*devs,values+devs,where=np.isfinite(values+devs),alpha=0.25,facecolor="#1A5276")
        ax.fill_between(x,values-devs,values-2*devs,where=np.isfinite(values+devs),alpha=0.25,facecolor="#1A5276")

        cnt = 0
        for v in self.thsld:
            thsld_values = (np.ones((values.shape))*dpi[v-2,glat,glon])
            thsld_string = "1/%s flood" % v
            ax.plot(thsld_values,label=thsld_string,color=self.colors[cnt],linewidth=2)
            cnt = cnt + 1

        # arrange
        intv     = np.arange(0,self.nT,self.tickIntv)
        tickDate = []
        [ tickDate.append((dRange[0] + datetime.timedelta(seconds=self.tStep*i)).strftime("%Y/%m/%d/%H:00")) for i in intv ]
        plt.xticks(intv,tickDate,rotation=45)
        ax.set_ylabel("discharge[m3/s]")
        ax.set_xlabel("date")
        plt.xlim(0,self.nT-1)
        ax.legend(bbox_to_anchor=(1.35,1))
        plt.subplots_adjust(left=0.1, right=0.7)

        date     = dRange[0].strftime("%Y%m%d%H")
        outTitle = "gl_%s_lat%d_lon%d" % (date,glat,glon)
        imgPath  = os.path.join(self.oPath,"hydrograph")
        fig.savefig(os.path.join(imgPath,outTitle), dpi=self.resl, bbox_inches="tight")
#        plt.show()
        plt.close()

        chunk       = genMap.PlotOnFolium()
        chunk.locs  = loc
        chunk.val   = idx
        chunk.thsld = self.thsld
        chunk.color = self.colors
        chunk.icon  = self.icon
        chunk.img   = os.path.join(imgPath,outTitle+".png")
        chunk.plot(self.map)



    def replaceToIndex(self,index,dschgData,dpi,value):

        index[np.where(dschgData > dpi)] = value

        return True


    def main(self):
        
        ensMean,ensStd   = self.getEnsMean()
        index,dpi        = self.index(ensMean)
        self.genHtml(index,ensMean,ensStd,dpi)


if __name__ == "__main__":

    chunk = PlotDpi(2018,6,29,12)
    chunk.dpiPath   = "./DPI_glb.bin"
    chunk.main()
