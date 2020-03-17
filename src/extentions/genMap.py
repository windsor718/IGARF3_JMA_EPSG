import numpy as np
import pandas as pd
import folium
import matplotlib.pyplot as plt
import base64
import os

class GenMap(object):

    def __init__(self):
        
        self.tile = "https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png"
        self.attr = "http://www.openstreetmap.org/copyright"
        self.cent = [35.652832,139.839478]
        self.zoom = 5


    def genMap(self):

        map = folium.Map(location=self.cent,tiles=self.tile,attr=self.attr,zoom_start=self.zoom)

        return map


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
    

    def plot(self,map):
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
        
        folium.Marker(location=[self.locs[0], self.locs[1]], popup=popup, icon=folium.Icon(color=mColr, icon=self.icon)).add_to(map)
