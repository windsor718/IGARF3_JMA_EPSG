import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time
import json
import requests
import argparse
import sys
import re
import os

class RealTimeFloodValidator(object):
    """
        Flood validation toolkits using dartmouth flood obervatory (http://floodobservatory.colorado.edu/Version3/MasterListrev.htm).
            Notes: You need lxml, html5lib, beauttifulsoup4 to run this script. Use pip (or any other) to install them.
    """

    def __init__(self):
        
        self.url      = "http://floodobservatory.colorado.edu/Version3/MasterListrev.htm"
        self.colList  = [\
                        "Register #",\
                        "Country",\
                        "Centroid X",\
                        "Centroid Y",\
                        "Duration in Days",\
                        "Began",\
                        "Ended",\
                        "Severity *",\
                        "Affected sq km",\
                        "Main cause",\
                        "Dead",\
                        "Displaced"\
                        ]

        ### advanced setting.
        self.tableHeader = 0
        self.lastIdSrc   = "lastID_dfo.txt"


    def main(self):
        
        df = self.fetchDataFromHtml()
        flag,ids = self.checkRecentID(df)
        
        if flag == True:
            print "Validation is up-to-date. Exit with status 0."
            sys.exit(0)
        else:
            print "%d non-validated event was found. Activating validator..." % (len(ids))
            for ID in ids:
                thisDf = df.loc[ID]
                print "event-id number: %d" % ID
                print "event %d information:" % ID
                print thisDf
                self.OneEventValidator(thisDf).floodForecast()
            self.writeId(df)
            

    def fetchDataFromHtml(self):

        src = pd.read_html(self.url,header=self.tableHeader)[0]
        df  = src.loc[:,self.colList]
        
        df  = df.reset_index().dropna().set_index("Register #")
        df  = df.dropna()

        return df


    def checkRecentID(self,df):

        currentId = df.index[0]
        print "Current ID: %d" % currentId
        
        if os.path.exists(self.lastIdSrc):
            with open(self.lastIdSrc,"r") as f:
                lastId = int(f.read())
                print "Last ID: %d" % (lastId)
        else:
            sys.stderr.write("Runtime Warning: %s was not found. Validation would continue title the last ID in html.\n" % (self.lastIdSrc))
            lastId = df.index[-1]
            print "[Last ID not found] set Last ID as: %d" % lastId

        ids = np.arange(lastId,currentId+1,1)

        if currentId == lastId:
            return True,ids
        else:
            return False,ids


    def writeId(self,df):
        
        currentId = df.index[0]
        with open(self.lastIdSrc,"w") as f:
            f.write(str(currentId))

        return 0


    class OneEventValidator(object):        
        """
        Sub-class for the RealTimeFloodValidator
            No inheritance from RealTimeFloodValidator
        """
        def __init__(self,df):
            
            ### user modification may be needed.
            self.tRange   = 3600*24*10 # time range [sec] in each simulation
            self.step     = 3600*12 # execution step [sec] in each simulation

            self.buf      = 5
            self.tBuf     = 5
            self.dscthl   = 100
            
            self.srcDir   = "/directory/to/the/file"
            self.srcFile  = "file"
            self.outDir   = "/directory/to/store/outputs"

            self.useDPI   = False
            self.DPIfile  = "../../../dias/DPI.bin"
            self.DPIdtype = np.float32
            self.nx       = 1440
            self.ny       = 720

            ### from dataFrame
            self.df       = df # must contain only 1 ID.
            self.sDate    = datetime.datetime.strptime(self.df["Began"],"%d-%b-%y")
            self.eDate    = datetime.datetime.strptime(self.df["Ended"],"%d-%b-%y")
            self.durat    = self.df["Duration in Days"]
            self.centx    = self.df["Centroid X"]
            self.centy    = self.df["Centroid Y"]
            
            ### advanced setting
            self.srchIntv = 3600 # interval to serch directory. in seconds.
            self.webhookUrl  = "https://hooks.slack.com/services/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"


            ### DPI
            self.useDPI   = True
            self.minDPI   = 10

        
        def floodForecast(self):
            """
            For real time flood forecast
            """
            self.earliestDate = self.sDate - datetime.timedelta(seconds=self.tRange)
            cDate = self.earliestDate
            history=[]
            while cDate < self.eDate:
                #srcDir = self.srcDir % (cDate.year,cDate.month,cDate.day,cDate.hour)
                #path   = os.path.join(srcDir,srcFile)
                path = "../../../dias/outflw.bin"
                if os.path.exists(path):
                    data,loc  = self.CaMaFlood(path,self.centx,self.centy).readFile()
                    flag = self.judgeFloods(data,loc)
                    if flag:
                        flag = "*Success*"
                    else:
                        flag = "_Failed_"
                    history.append((cDate,flag))

                    cDate = cDate + datetime.timedelta(seconds=self.step)
                else:
                    cDate = cDate + datetime.timedelta(seconds=self.srchIntv)
            self.send(history)

        
        def judgeFloods(self,data,loc):

            iy = loc[0]
            ix = loc[1]

            flags = data.copy()
            flags[:,:,:] = 0 #initialize
            dpi   = np.fromfile(self.DPIfile,self.DPIdtype).reshape(-1,self.ny,self.nx)

            for lat in range(iy-self.buf,iy+self.buf):
                for lon in range(ix-self.buf,ix+self.buf):
                    INDEX = self.timeSeriesToDpi(data[:,lat,lon],dpi[:,lat,lon])
                    flags[:,lat,lon] = INDEX

            maximumDpi = flags.max()
            if (flags[np.where(data>self.dscthl)] > 10).any():
                ForecastFlag = True
            else:
                ForecastFlag = False


            return ForecastFlag
            

        def timeSeriesToDpi(self,discharge,dpi):

            INDEX = []
            [ INDEX.append(self.valueToDpi(d,dpi)) for d in discharge]

            return INDEX


        def valueToDpi(self,dValue,dpi):
            """
                Args: discharge (value) and dpi (list).
            """
            DPI=dpi.tolist()
            DPI.append(dValue)
            index=sorted(DPI).index(dValue)

            return index


        def send(self,history):

            url   = self.webhookUrl
            now   = datetime.datetime.now()
            posix = int(time.mktime(now.timetuple()))
            user  = "FloodValidator"

            fcst  = ""
            cnt = 0
            for his in history:
                if cnt == 10:
                    fcst = fcst + "%s:%s\n" % (his[0],"*Success*")
                else:
                    fcst = fcst + "%s:%s\n" % (his[0],his[1])
                cnt = cnt + 1
            text  = "Country:%s\nBegan:%s\nEnded:%s\nMain cause:%s\nLon:%s\nLat:%s\nSeverity:%s\nAffected Area [km2]:%s\nDead:%s\nDisplaced:%s" % \
                    (self.df["Country"],self.df["Began"],self.df["Ended"],self.df["Main cause"],self.df["Centroid X"],self.df["Centroid Y"],self.df["Severity *"],self.df["Affected sq km"],self.df["Dead"],self.df["Displaced"])


            requests.post(self.webhookUrl, data = json.dumps({
                    "attachments": [
                    {
                    "fallback": "New notification from %s" % user,
                    "pretext": "The new flood information from dartmouth flood observatory:",
                    "color": "#C70039",
                    "fields": [
                                {
                                "title": "Flood Summary",
                                "value": text,
                                "short": "false",
                                }
                              ],
                    "ts": posix,
                    },
                    {
                    "pretext": "The forecast history is below:",
                    "color": "#27AE60",
                    "fields": [
                                {
                                "title": "Flood Forecast History",
                                "value": fcst,
                                "short": "false",
                                }
                              ],
                    "ts": posix,
                    }
                    ],
                    "username": user,
                    "link_name": 1
                }))


        """
        Here you need to code for your models.
        """
        class CaMaFlood(object):
            """
            CaMa-Flood
            """
            def __init__(self,filePath,centx,centy):

                ### user modification may be needed.
                self.nx       = 1440
                self.ny       = 720
                self.res      = 0.25
                self.lat0     = 90
                self.lon0     = -180
                self.buf      = 5

                self.centx    = centx
                self.centy    = centy

                self.dPath    = filePath
                self.lonlat   = "./lonlat.bin"


            def readFile(self):
            
                data = np.fromfile(self.dPath,np.float32).reshape(-1,self.ny,self.nx)
                idy,idx = self.searchGrids()
                loc     = [idy,idx]

                return data,loc


            def searchGrids(self):
    
                loc = np.fromfile(self.lonlat,np.float32).reshape(2,self.ny,self.nx)
                
                iLat = int((self.lat0-self.centy)/self.res)
                iLon = int((self.lon0-self.centx)/self.res)
                pLat = iLat
                pLon = iLon
                err  = 1e+20
                for lat in range(iLat-self.buf,iLat+self.buf):
                    for lon in range(iLon-self.buf,iLon+self.buf):
                        cLoc = loc[:,lat,lon]
                        cErr = ((cLoc[0]-lon)**2 + (cLoc[1]-lat)**2)**0.5
                        if err > cErr:
                            pLat = lat
                            pLon = lon
                            err  = cErr
                        else:
                            continue

                return pLat,pLon


if __name__ == "__main__":

    chunk = RealTimeFloodValidator()
    chunk.main()
