
import matplotlib as mpl
mpl.use("Agg")

import os
import datetime
import folium
import base64
import ConfigParser
import numpy as np
import pandas as pd
import seaborn as sns
import branca.colormap as bcm
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from branca.element import MacroElement
from jinja2 import Template
from folium.plugins import image_overlay
from gtool import gtopen
from matplotlib.colors import LinearSegmentedColormap
#from mpl_toolkits.basemap import Basemap


class Visualize(object):
    
    """
    wrapper of the classes below.
    """

    def __init__(self,initFile,cDate):
        
        self.initFile = ConfigParser.SafeConfigParser()
        self.initFile.read(initFile)

        self.cDate    = cDate
        self.oPath    = "/var/www/html/tdjpn/archive"


    def main(self):

        # generate map object
        gm     = GenMap()
        m      = gm.genMap()       



        # plot alerted points
        pltDpi = PlotDpi(m,self.cDate.year,self.cDate.month,self.cDate.day,self.cDate.hour)
        pltDpi.nLat = 720
        pltDpi.nLon  = 1440
        pltDpi.nT    = int(self.initFile.get("Model","FrcTime"))
        pltDpi.tStep = int(self.initFile.get("Model","dtOut"))

        rName     = self.initFile.get("Model","runName")
        outRoot   = self.initFile.get("Model","outRoot")
        print outRoot
        camaRoot  = self.initFile.get("Model","camaRoot")
        sysRoot   = self.initFile.get("Model","sysRoot")
        outSuffix = "Forecast/%04d/%02d/%02d/%02d/e%02d/cama/outflw.bin"
        pltDpi.dschgPath = os.path.join(outRoot,rName,outSuffix)

        pltDpi.dpiPath   = os.path.join(sysRoot,"src/extentions/DPI_glb.bin")
        pltDpi.mapRoot   = os.path.join(camaRoot,"map/global_025/")
        pltDpi.oPath     = self.oPath

        outfig = pltDpi.main()



        # add layers
        add = AddLayers()
        add.imgDirs   = [self.oPath]
        add.imgNames  = ["prcp_%04d%02d%02d%02d" % (self.cDate.year,self.cDate.month,self.cDate.day,self.cDate.hour)]
        add.imgTitles = ["total precipitation (39h)"]
        add.cmCaption = ["precipitation [mm/h]"]

        add.dPath     = [os.path.join(outRoot,"%s/Forecast/%04d/%02d/%02d/%02d/e00/matsiro/main/gprct"%(rName,self.cDate.year,self.cDate.month,self.cDate.day,self.cDate.hour))]
        add.nx        = [int(self.initFile.get("Forcing","nLon"))]
        add.ny        = [int(self.initFile.get("Forcing","nLat"))]
        
        add.wests     = [-180]
        add.easts     = [180]
        add.souths    = [-90]
        add.norths    = [90]
        add.res       = [0.5]
        add.nsConv    = [True]
        add.shows     = [True]
        add.varnames  = ["GPRCT"]

        add.norm      = [[10,25,50,100,150,200,250]]
        add.colors    = ['blue', 'yellow', 'red']

        add.addLayers(m)



        # save map
        outmap = os.path.join(self.oPath,"glb_%04d%02d%02d%02d.html" % (self.cDate.year,self.cDate.month,self.cDate.day,self.cDate.hour))
        gm.saveMap(m,outmap)

        return outmap



class GenMap(object):

    def __init__(self):

        self.tile  = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        self.attr  = "http://www.openstreetmap.org/copyright"
        self.cent  = [35.652832,139.839478]
        self.zoom  = 2

        self.oPath = "outPath"


    def genMap(self):

        m = folium.Map(location=self.cent,tiles=self.tile,attr=self.attr,zoom_start=self.zoom)

        return m


    def saveMap(self,m,oPath):

        m.save(oPath)


class PlotOnFolium(object):

    def __init__(self):

        self.locs   = [30,130] # location of plot, tuple or list [lat,lon].
        self.val    = 100
        self.thsld  = [10,50,100,200] # threshold to change marker colors
        self.color  = ["#45B39D","#2980B9","#F39C12","#C0392B"]
        self.icon   = "info-sign"

        self.img    = "/path/to/img"
        self.resl   = 75
        self.width  = 7
        self.height = 3


    def plot(self,m):
        """
        args: folium map object
        """

        # encoding image
        encoded = base64.b64encode(open(self.img,"rb").read())
        html    = '<img src="data:image/png;base64,{}">'.format
        iframe  = folium.IFrame(html(encoded), width=self.width*self.resl+20, height=self.height*self.resl+20)
        popup    = folium.Popup(iframe, max_width=2650)

        ranker = self.thsld[:]
        ranker.append(self.val)
        rank   = self.thsld.index(self.val)
        mColr  = self.color[rank]
        print mColr

        folium.Marker(location=[self.locs[0], self.locs[1]], popup=popup, icon=folium.Icon(color=mColr, icon=self.icon)).add_to(m)


class PlotDpi(object):
    
    def __init__(self,m,year,mon,day,hour):
        
        sns.set()

        self.m         = m
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

        chunk      = GenMap()
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

        return 0

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

        chunk       = PlotOnFolium()
        chunk.locs  = loc
        chunk.val   = idx
        chunk.thsld = self.thsld
        chunk.color = self.colors
        chunk.icon  = self.icon
        chunk.img   = os.path.join(imgPath,outTitle+".png")
        chunk.plot(self.m)



    def replaceToIndex(self,index,dschgData,dpi,value):

        index[np.where(dschgData > dpi)] = value

        return True


    def main(self):

        ensMean,ensStd   = self.getEnsMean()
        index,dpi        = self.index(ensMean)
        self.genHtml(index,ensMean,ensStd,dpi)


class BindColormap(MacroElement):
    """ :source from http://nbviewer.jupyter.org/gist/BibMartin/f153aa957ddc5fadc64929abdee9ff2e
    Binds a colormap to a given layer.

    Parameters
    ----------
    colormap : branca.colormap.ColorMap
        The colormap to bind.
    """

    def __init__(self, layer, colormap):
        super(BindColormap, self).__init__()
        self.layer = layer
        self.colormap = colormap
        self._template = Template(u"""
        {% macro script(this, kwargs) %}
            {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
            {{this._parent.get_name()}}.on('overlayadd', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
                }});
            {{this._parent.get_name()}}.on('overlayremove', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'none';
                }});
        {% endmacro %}
        """)  # noqa


class AddLayers(object):

    def __init__(self):

        self.imgDirs   = ["/var/www/html/tdjpn/prcp/"]
        self.imgNames  = ["prcp"]
        self.imgTitles = ["tp"]
        self.cmCaption = ["total_precipitation (39h) [mm/h]"]

        self.dPath     = ["/data/path/"]
        self.nx        = [720]
        self.ny        = [360]

        self.wests     = [0]
        self.easts     = [360]
        self.souths    = [90]
        self.norths    = [-90]
        self.res       = [0.5]
        self.nsConv    = [True]
        self.shows     = [True]
        self.coefs     = [3600*6]
        self.varnames  = ["VARNAME"]

        self.norm      = [[2.5,5,10,15,20,25,30]]
        self.colors    = ['blue', 'yellow', 'red']


    def mkColorBar(self,name,norm):
        #linear = bcm.linear.BuPu.to_step(n=len(norm),data=norm,method="quantiles",round_method="int")
        linear = bcm.LinearColormap(self.colors,vmin=norm[0], vmax=norm[-1])
        linear = linear.to_step(n=6,data=norm, method='quantiles',round_method='int')
        linear.caption = name

        return linear


    def addLayers(self,m):

        for i in range(len(self.imgTitles)):
            imgPath  = self.drawImage(i)
            norml    = self.norm[i]
            imgTitle = self.imgTitles[i]
            west     = self.wests[i]
            east     = self.easts[i]
            south    = self.souths[i]
            north    = self.norths[i]
            res      = self.res[i]
            showb    = self.shows[i]
            caption  = self.cmCaption[i]

            #Create and add layers
            img      = image_overlay.ImageOverlay(name=imgTitle,image=imgPath+".png",bounds=[[south,west],[north,east]],opacity=0.5,interactive=True,cross_origin=True,zindex=1,show=showb).add_to(m)

            #m.add_child(imgp).add_child(imgr)
            m.add_child(img)
            m.add_child(folium.map.LayerControl())

            cmb     = self.mkColorBar(caption,norml)

            #Bind colorbars and layers
            m.add_child(cmb)
            m.add_child(BindColormap(img,cmb))


    def createCmap(self):

        values = range(len(self.colors))

        vmax   = np.ceil(np.max(values))
        color_list = []
        for v,c in zip (values,self.colors):
            color_list.append((v/vmax,c))
    
        cmap = LinearSegmentedColormap.from_list("myCmap",color_list)

        return cmap


    def drawImage(self,i,dtype="gtool",varname="VARIABLE_NAME"):
        
        sns.set_style("white")
        west     = self.wests[i]
        east     = self.easts[i]
        south    = self.souths[i]
        north    = self.norths[i]
        res      = self.res[i]
        norml    = self.norm[i]
        Norml    = colors.BoundaryNorm(norml,256)
        dPath    = self.dPath[i]
        nsConv   = self.nsConv[i]
        imgDir   = self.imgDirs[i]
        imgName  = self.imgNames[i]
        coef     = self.coefs[i]
        nx       = self.nx[i]
        ny       = self.ny[i]
        varname  = self.varnames[i]

        print dPath

        if dtype == "binary":
            print "Read as Binary"
            values = np.fromfile(dPath,dtype=np.float32).reshape(-1,ny[i],nx[i])
        elif dtype == "gtool":
            print "Read as Gtool"
            values = gtopen(dPath).vars[varname][:][:,0,:,:]
        else:
            sys.stderr.write("Unrecongizable argument for dtype: %s" % dtype)
            raise IOError

        if nsConv:
            values = values[:,::-1,:]
        val  = values.sum(axis=0)*coef
        val = self.snapLongitude(val, axis=1) # should be [-180,180]. Snap by this functiopn if not.

        mycm = self.createCmap()
        h    = float(ny)/float(nx)
        v    = 1
        plt.figure(figsize=(v*10,h*10))
        #m = Basemap(urcrnrlat=north,urcrnrlon=east,llcrnrlat=south,llcrnrlon=west,projection="merc")
        #m.imshow(np.ma.masked_less(val,norml[0]),alpha=0.5,cmap=mycm,norm=Norml)
        plt.imshow(np.ma.masked_less(val,norml[0]),alpha=0.5,cmap=mycm,norm=Norml)
        plt.tick_params(labelbottom=False,labelleft=False)
        ax = plt.gca()
        ax.spines["right"].set_color("none")
        ax.spines["left"].set_color("none")
        ax.spines["top"].set_color("none")
        ax.spines["bottom"].set_color("none")
        oName = os.path.join(os.path.join(imgDir,"prcp"),imgName)
        plt.savefig(oName,dpi=300,transparent=True,bbox_inches="tight",pad_inches=0.)
        
        return oName

    def snapLongitude(self,data,axis=1):
        lonShape = data.shape[axis]
        data_right = data[:,int(lonShape)/2::]
        data_left = data[:,0:int(lonShape)/2]
        outData = np.concatenate([data_right,data_left],axis=axis)
        return outData

if __name__ == "__main__":
    
    config = "../../config.ini"
    sDate = datetime.datetime(2018,6,29,12)
    eDate = datetime.datetime(2018,6,29,12)
    cDate = sDate
    while cDate <= eDate:
        print cDate
        chunk = Visualize(config,cDate)
        chunk.main()
        cDate = cDate + datetime.timedelta(hours=12)
