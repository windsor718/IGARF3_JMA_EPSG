#!/usr/env python
#  batch-wappter script for Flood Forecasting System
#  edit config.ini for simulation settings.
#  note that the model itself should be compiled for the setting.

import ConfigParser
import subprocess
import argparse
import traceback
import datetime
import sys
import os

from retry import retry

import IO.gt2bin as gt2bin
import IO.convGtool as convGtool
import IO.decode as decode
import extentions.sendSlack as slack
import extentions.parseShape as parseShape

### edit for your environment
bash="/bin/bash"
python="/dias/users/ishitsuka.y.u-tokyo/bin/Python-2.7.14/python"
config="/dias/users/ishitsuka.y.u-tokyo/tdjpn/FF/ECMWF/config.ini" # set in absolute path.
###

### For developers
version="1.0.0_dirty"
author="Yuta Ishitsuka"
lastEdited="2018/06/01"
###

### Super class ###

class MainController(object):
    """
        SUPER CLASS: Main controller to handle the classes below;
            ForcingController
            ModelController
    """

    def __init__(self):
        """
            initial
        """
        notes = "Version: %s\nAuthor: %s\nLastEdited: %s\nImportant Notes: This wrapper should be edited in reference to your datasets/models. Currently the system is set up for ECMWF-ENS and MATSIRO/CaMa-Flood" % (version,author,lastEdited)
        print "="*80
        print notes
        print "="*80
        print "Activating MainController: ", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        args = self.parseArgs()

        # define as class variables.
        self.config = args.config
        self.cDate  = datetime.datetime(args.year,args.month,args.day,args.hour)
        self.eNum   = args.eNum
        del args.config, args.year, args.month, args.day, args.hour, args.eNum
        
        self.initFile=ConfigParser.SafeConfigParser()
        self.initFile.read(self.config)

        # for near real time run
        self.pDate, self.nT = self.checkRestart()


    def main_forcing(self):

        frcng = ForcingController()
        frcng.main()

        return 0
        

    def main_model(self):

        model = ModelController()
        model.main()

        return 0


    def parseArgs(self):

        parser = argparse.ArgumentParser(description="The controller to handle a whole Flood Forecast calculation.")
        parser.add_argument("--config",type=str,default=config,help="path to the configuration file. Default path is set in this script.")
        parser.add_argument("year",type=int,help="simulation start year")
        parser.add_argument("month",type=int,help="simulation start month")
        parser.add_argument("day",type=int,help="simulation start day")
        parser.add_argument("hour",type=int,help="simulation start hour")
        parser.add_argument("eNum",type=int,help="ensemble number")

        args = parser.parse_args()

        return args

    
    def checkRestart(self):
        
        step     = int(self.initFile.get("Model","step"))
        dt       = int(self.initFile.get("Model","dtOut"))
        step     = step*dt
        ft       = int(self.initFile.get("Model","FrcTime"))
        outRoot  = self.initFile.get("Model","outRoot")
        runName  = self.initFile.get("Model","runName")

        nDate = self.cDate - datetime.timedelta(seconds=step)
        lDate = self.cDate - datetime.timedelta(seconds=dt*ft)
        date  = nDate
        nT    = step/dt

        return nDate, nT

        while date < nDate:
            path = os.path.join(outRoot,runName,"/NRT/%04d/%02d/%02d/%02/matsiro/main/RSTA" % (date.year,date.month,date.day,date.hour))
            print path
            if os.path.exists(path):
                return date,nT
            else:
                step = step + step
                date = date - datetime.timedelta(seconds=step)
                continue
        if self.slackNotify == True:
            user = "FloodForecast"
            text = "Fatal: Cannot find restart file to reboot the system. \nDate:%s" % (self.cDate.strftime("%Y/%m/%d %H:%M"))
            slack.failed(user,text)
        sys.exit(1)


######

### Childlen class ###

class ForcingController(MainController):
    """
        CHIDLD OF MainController
        Forcing controller to handle the preprocesses (or other actions) of the datasets.
    """

    def __init__(self):
        """
            initial
        """
        print "+"*80
        print "Activating ForcingController: ", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        
        MainController.__init__(self)
        self.initFile=ConfigParser.SafeConfigParser()
        self.initFile.read(self.config)

        self.slackNotify = self.initFile.getboolean("System","SlackNotify")


    def main(self):

        #try:
        self.forecast(self.cDate.year,self.cDate.month,self.cDate.day,self.cDate.hour,self.eNum)
        #except Exception as e:
        #    err = "%s\n%s" % (str(type(e)),e.message)
        #    if self.slackNotify == True:
        #        user = "FloodForecast"
        #        text = "Error @ ForcingController\n%s" % (err)
        #        slack.failed(user,text)
        #    sys.exit(1)


    #@retry(tries=5,delay=300)
    def forecast(self,year,mon,day,hour,eNum):
        print "Creating Forecast Forcing..."
        decode.ECMWF(self.config,year,mon,day,hour,eNum).decodeECMWF()
        convGtool.ECMWF(self.config,year,mon,day,hour,eNum).ecmwfToGtool()


class ModelController(MainController):
    """
        CHILD of MainController
        Model cintroller to handler the model actions.
    """
    def __init__(self):
        """
            initial
        """
        print "+"*80
        print "Activating ModelController: ", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        MainController.__init__(self)
        self.initFile=ConfigParser.SafeConfigParser()
        self.initFile.read(self.config)


    def main(self):

        self.info = self.makeInfo()
        flag = self.forecast()

        return 0


    def forecast(self):
        
        print "Forecast mode:"
        
        MATSIRO = self.initFile.get("Model","matExe")
        try:
            print "-"*80
            print "Activating MATSIRO: ", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            subprocess.check_call([bash, MATSIRO, self.info, "rest", str(self.eNum)])
        except Exception as e:
            err = "%s\n%s" % (str(type(e)),e.message)
            self.sendError("matsiro",err)
            sys.exit(1)
        
        
        converter = gt2bin.Gt2Bin("Forecast")
        try:
            print "-"*80
            print "Activating gt2bin: ", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            converter.config = self.config
            converter.year   = self.cDate.year
            converter.mon    = self.cDate.month
            converter.day    = self.cDate.day
            converter.hour   = self.cDate.hour
            converter.eNum   = self.eNum
            converter.main()
        except Exception as e:
            err = "%s\n%s" % (str(type(e)),e.message)
            self.sendError("gt2bin",err)
            sys.exit(1)
        
        
        CaMa    = self.initFile.get("Model","camaExe")
        try:
            print "-"*80
            print "Activating CaMa-Flood: ", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            subprocess.check_call([bash, CaMa, self.info, str(self.eNum)])
        except Exception as e:
            err = "%s\n%s" % (str(type(e)),e.message)
            self.sendError("CaMa-Flood",err)
            sys.exit(1)

        return 0


    def sendError(self,code,err):

       if self.initFile.getboolean("System","slackNotify") == True:
            user = "FloodForecast"
            text = "Error @ %s\n%s" % (code,err)
            slack.failed(user,text) 
       else:
            text = "Error @ %s" % code
            sys.stderr.write(text)

       return 0


    def makeInfo(self):
    
        runName  = self.initFile.get("Model","runName")
        gtRoot   = self.initFile.get("Forcing","gtRoot")
        cRes     = self.initFile.get("Forcing","cRes")
        dtInRad  = self.initFile.get("Model","dtInRad")
        dtIn     = self.initFile.get("Model","dtIn")
        dtOut    = self.initFile.get("Model","dtOut")
        outRoot  = self.initFile.get("Model","outRoot")
        matRoot  = self.initFile.get("Model","matRoot")
        camaRoot = self.initFile.get("Model","camaRoot")
        matExe   = self.initFile.get("Model","matExe")
        camaRes  = self.initFile.get("Model","camaRes")
        step     = self.initFile.get("Model","step")
        FT       = str(int(self.initFile.get("Model","FrcTime")) * int(dtIn) / 3600 )
        nT       = self.nT

        if self.initFile.getboolean("Model","flexibleTime"):
            FT  = parseShape.main(self.config,self.cDate.year,self.cDate.month,self.cDate.day,self.cDate.hour)

        infoFile = "Modelinfo_%04d%02d%02d%02d.txt" % (self.cDate.year,self.cDate.month,self.cDate.day,self.cDate.hour)
        infoPath = os.path.join(os.getcwd(),infoFile)
        if os.path.exists(infoPath):
            subprocess.call(["rm",infoPath])
            print "initialize %s" % infoPath

        varList = ["year","mon","day","hour","FT","pYear","pMon","pDay","pHour","nT","runName","gtRoot","cRes","dtInRad","dtIn","dtOut","outRoot","matRoot","camaRoot","matExe","camaRes","step"]
        varDict = {"year":self.cDate.year,"mon":self.cDate.month,"day":self.cDate.day,"hour":self.cDate.hour,"FT":FT,"pYear":self.pDate.year,"pMon":self.pDate.month,"pDay":self.pDate.day,"pHour":self.pDate.hour,"nT":nT,"runName":runName,"gtRoot":gtRoot,"cRes":cRes,"dtInRad":dtInRad,"dtIn":dtIn,"dtOut":dtOut,"outRoot":outRoot,"matRoot":matRoot,"camaRoot":camaRoot,"matExe":matExe,"camaRes":camaRes,"step":step}

        for var in varList:
            string = "echo %s=%s >> %s\n" % (var,varDict[var],infoPath)
            subprocess.call(string,shell=True)


        return infoPath



if __name__ == "__main__":

    ex = MainController()
    f  = ex.main_forcing()

