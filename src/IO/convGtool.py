import numpy as np
import math
import datetime
import ConfigParser
import getpass
import argparse
import sys
import os
import matplotlib.pyplot as plt
from gtool import gtopen

#use only 24 hours data from head.
#check its collectivity

"""
SUPER CLASS
"""
class ConvGtool(object):
    """
    SUPAR CLASS: contains basic modules.
        convert binary into Gtool.
            + only z=1 is supported.
            + some conversion is included.
    """

    def __init__(self,year,mon,day,hour,eNum):
        
        ### read from args
        self.year     =  year
        self.mon      =  mon
        self.day      =  day
        self.hour     =  hour
        self.eNum     =  eNum


    def readWithUnitConv(self,var):
        C = self.unitCf[var]
        dPath = self.dataDir+var+"_%04d%02d%02d%02d_e%02d"%(self.year,self.mon,self.day,self.hour,self.eNum)+"."+str(self.cRes)
        print dPath
        if os.path.exists(dPath) == True:
            data=np.fromfile(dPath,np.float32).reshape(-1,self.dZ,self.yRes,self.xRes)
            #prd=data[0:self.nTme]*C
            prd=data*C
        else:
            raise IOError
        
        return prd

    def TensensEq(self,T2):
        T2cdeg = T2 - 273.15 # K -> Cdeg
        power  = (7.5*T2cdeg)/(237.3+T2cdeg)
        Es     = 6.11*10**(power)

        return Es


    def calcSfromD(self,D2,SP):
        Es = self.TensensEq(D2)
        q  = (0.622*Es)/(SP-0.378*Es) # g/g = kg/kg

        return q


    def calcLat2D(self):
        late=self.lats+(self.yRes*self.hRes)
        y=np.arange(self.lats,late,self.hRes)
        lat_deg=[]
        for ix in range(0,self.xRes):
            lat_deg.append(y)
        lat_deg=np.array(lat_deg).transpose()

        return lat_deg


    def calcSpecificHumidity(self,temp,rh,pres):
        E=6.11*10**(7.5*(temp-273.15)/(237.3+(temp-273.15)))
        Ep=E*rh #rh [kg/kg]
        q=622*Ep/(pres-0.378*Ep) #pres:hPa [g/kg]
        Q=q/1000 #[kg/kg]

        return Q


    def calcRadiation(self,pres,temp,d2,tcdc,lat_deg):
        #parameters
        I    =   1365 #Wm-2
        SB   =   5.67*10**(-8)
        beta =   0.1
        albd =   0.1
        print I,SB,beta,albd

        #calc. solar radiation at TOA
        DOY=30.36*(int(self.mon)-1.)+self.day
        ita=(2*math.pi/365)*DOY
        alpha=4.871+ita+0.033*np.sin(ita)
        delta=math.asin(0.398*np.sin(alpha))
        d_d=1.00011+0.034221*np.cos(ita)+0.00128*np.sin(ita)+0.000719*np.cos(2*ita)+0.000077*np.sin(2*ita)

        tStep   = 24/(self.dT/3600) #Cummlative hours in the data
        CumStep = tStep
        SSRD=[]
        SLRD=[]
        print tStep, CumStep, len(pres[:,0,0])
        while CumStep <= len(pres[:,0,0]):
            pres_mean= np.mean(pres[CumStep-tStep:CumStep],axis=0)
            temp_mean= np.mean(temp[CumStep-tStep:CumStep],axis=0)
            d2_mean  = np.mean(d2[CumStep-tStep:CumStep],axis=0)
            #rh_mean  = np.mean(rh[CumStep-tStep:CumStep],axis=0)
            #lcdc_mean= np.mean(lcdc[CumStep-tStep:CumStep],axis=0)
            tcdc_mean=np.mean(tcdc[CumStep-tStep:CumStep],axis=0)

            #E=6.11*10**(7.5*(temp_mean-273.15)/(237.3-273.15+temp_mean))
            #Ep=E*rh_mean
            Ep=self.TensensEq(d2_mean)
            Tdew=(237.3*np.log10(Ep/6.108))/(7.5-np.log10(Ep/6.108))
            logpw=0.0312*Tdew-0.0963
            logtop=0.0315*Tdew-0.1836

            lat_rad=lat_deg*(math.pi/180.)
            h=np.arccos(-np.tan(lat_rad)*np.tan(delta))
            Sd=(I/math.pi)*d_d*(h*np.sin(lat_rad)*np.sin(delta)+np.sin(h)*np.cos(lat_rad)*np.cos(delta))

            #calc. solar radiation
            latdel=lat_rad-delta
            hlfpi=math.pi/2.

            if (latdel < hlfpi).all() == True:
                mn=1/np.cos(latdel)
                kk=1.402-0.06*np.log10(beta+0.02)-0.1*((mn-0.91)**(0.5))
                md=mn*kk*(pres_mean/1013)
            else:
                ###temp
                print "==========check=========="
                print np.where([latdel > hlfpi])
                print "========================="
                latdel[np.where(latdel > hlfpi)] = hlfpi
                sys.stderr.write("any latdel >= hlfpi was detected. Using another algorithm is recommended.")
                mn=1/np.cos(latdel)
                kk=1.402-0.06*np.log10(beta+0.02)-0.1*((mn-0.91)**(0.5))
                md=mn*kk*(pres_mean/1013)

            j=(0.066+0.34*(beta)**(0.5))*(albd-0.15)
            i=0.014*(md+7+2*logpw)*logpw
            F1=0.056+0.16*(beta)**(0.5)
      
            if beta<=0.3:
                C=0.21-0.2*beta
            else:
                C=0.15

            Sdf=Sd*(C+(0.7*10**(-md*F1)))*(1-i)*(1+j)

            x=tcdc_mean-0.4*np.exp(-3*tcdc_mean)
            y=np.ones((self.dZ,int(tcdc_mean.shape[1]),int(tcdc_mean.shape[2])))

            y[np.where(tcdc_mean >= 0.3)]=1.70*np.log10((1.22-1.02*x[np.where(tcdc_mean >= 0.3)]))+0.521*x[np.where(tcdc_mean >= 0.3)]+0.846
            swd=y*Sdf

            #calc. long wave
            B=swd/Sdf

            LC=np.zeros((self.dZ,int(swd.shape[1]),int(swd.shape[2])))
            LC[np.where(B>=0.0323)]=(0.03*B[np.where(B>=0.0323)]**(3))-(0.30*B[np.where(B>=0.0323)]**(2))+1.25*B[np.where(B>=0.0323)]-0.04
      
            Ldf_sT4=0.74+0.19*logtop+0.07*(logtop**(2))
            lwd=SB*(temp_mean**(4))*(1-LC*(1-Ldf_sT4))
            if CumStep == tStep:
                print "!"*80
                print "WARNING: polar region set to 0, because of equation."
                print "!"*80
            swd[np.isnan(swd)] = 0
            swd[np.where(swd < 0)] = 0
            plt.show()

            SSRD.append(swd)
            SLRD.append(lwd)
            print "="*80
            print swd,lwd
            print "="*80
            CumStep=CumStep+tStep
   
        return np.array(SSRD),np.array(SLRD)


    def encodeGtool(self,binData,var):

        ###
        print "this is on developing code. Check how to append Z axis and endian"
        ###

        varOut  = self.varOutDict[var]
        varName = self.varNameDict[var]
        gtUnit  = self.varUnitDict[varName]

        os.environ['F_UFMTENDIAN'] = 'big' #not need?

        outPath = os.path.join(self.outDir,'%s_%04d%02d%02d%02d_e%02d.gt'%(varOut,self.year,self.mon,self.day,self.hour,self.eNum))

        DTime   = [datetime.datetime(self.year,self.mon,self.day,self.hour)+datetime.timedelta(seconds=self.dT)*i for i in range(int(binData.shape[0]))]
        TStamp  = [dtime.strftime('%Y%m%d %H%M%S ') for dtime in DTime]

        gtOut = gtopen(outPath,mode='w+')

        print "="*80
        print "encoding data..."

        [gtOut.append( d ) for d in binData]

        print "finished encoding."
        print "="*80

        gtOut = gtopen(outPath,mode='r+')

        gtVar = gtOut.vars['']

        gtVar.header['ITEM']    = varName


        gtVar.header['TITL1']   = varName
        gtVar.header['DSET']    = varName
        gtVar.header['DATE']    = TStamp
        gtVar.header['UNIT']    = gtUnit
        gtVar.header['AEND1']   = binData.shape[3]
        gtVar.header['AEND2']   = binData.shape[2]
        gtVar.header['AEND3']   = binData.shape[1]

        gtVar.header['AITM1']   = "GLON%iM"%(binData.shape[3])
        gtVar.header['AITM2']   = "GLAT%iIM"%(binData.shape[2])
        gtVar.header['AITM3']   = self.GATM
        gtVar.header['MSIGN']   = getpass.getuser()

        print "outPath: ",outPath
        print gtVar.header


"""
CHILD CLASS: dataset-wide modules.
"""

class ECMWF(ConvGtool):
    """
    For ECMWF.
    """
    def __init__(self,config,year,mon,day,hour,eNum):
        ConvGtool.__init__(self,year,mon,day,hour,eNum)

        ###Configuration
        self.initFile = ConfigParser.SafeConfigParser()
        self.initFile.read(config)

        ###
        self.xRes     =  int(self.initFile.get("Forcing","nlon")) #lon
        self.yRes     =  int(self.initFile.get("Forcing","nlat")) #lat
        self.nTme     =  int(self.initFile.get("Forcing","nTme")) #time
        self.dT       =  int(self.initFile.get("Forcing","tRes"))
        self.dZ       =  int(self.initFile.get("Forcing","dZ"))
        self.GATM     =  str(self.initFile.get("Forcing","GATM"))

        self.hRes     =  float(self.initFile.get("Forcing","nRes")) #degree
        self.cRes     =  str(self.initFile.get("Forcing","cRes")) #suffix
        self.lats     =  float(self.initFile.get("Forcing","lat0"))

        self.dataRoot =  str(self.initFile.get("Forcing","gtRoot"))
        self.outRoot  =  str(self.initFile.get("Forcing","gtRoot"))
        
        ###Edit if you need.
        self.dataDir      =  self.dataRoot
        self.outDir       =  self.outRoot+self.cRes+"/%04d/%02d/%02d/%02d" % (self.year,self.mon,self.day,self.hour)

        self.varOutDict   =  {"tp":"PRCP","tcdc":"CCOVER","sp":"PS","t2":"T","ugrd":"U","vgrd":"V","SSRD":"SSRD","SLRD":"SLRD","Q":"Q"}
        self.varNameDict  =  {"tp":"PRCP","tcdc":"CCOVER","sp":"PS","t2":"T","ugrd":"U","vgrd":"V","SSRD":"SSRD","SLRD":"SLRD","Q":"Q"}
        self.varUnitDict  =  {"PRCP":"kg/m2/s","CCOVER":"kg/kg","PS":"hPa","T":"K","U":"m/s","V":"m/s","SSRD":"W/m2","SLRD":"W/m2","Q":"kg/kg"}

        self.unitCf       =  {"tp":1./21600.,"tcdc":1./100.,"sp":1./100.,"t2":1.,"d2":1.,"ugrd":1.,"vgrd":1.,"tcdc":1./100.} #unit conversion coefficient

    
    def ecmwfToGtool(self):
        
        if os.path.exists(self.outDir) == False:
            os.makedirs(self.outDir)

        prcp = self.TP2PRCP(self.readWithUnitConv("tp"))
        tcdc = self.readWithUnitConv("tcdc")
        sp   = self.readWithUnitConv("sp")
        t2   = self.readWithUnitConv("t2")
        d2   = self.readWithUnitConv("d2")
        ugrd = self.readWithUnitConv("ugrd")
        vgrd = self.readWithUnitConv("vgrd")
        q    = self.calcSfromD(d2,sp)


        lat_deg = self.calcLat2D()
        ssrd,slrd = self.calcRadiation(sp,t2,d2,tcdc,lat_deg)

        self.encodeGtool(prcp,"tp")
        self.encodeGtool(tcdc,"tcdc")
        self.encodeGtool(sp,"sp")
        self.encodeGtool(t2,"t2")
        self.encodeGtool(ugrd,"ugrd")
        self.encodeGtool(vgrd,"vgrd")
        self.encodeGtool(ssrd,"SSRD")
        self.encodeGtool(slrd,"SLRD")
        self.encodeGtool(q,"Q")

        return 0

        
    def TP2PRCP(self,TP):
        tRes = TP.shape[0]
        t = 0
        PRCP = np.zeros((TP.shape[0]-1,TP.shape[1],TP.shape[2],TP.shape[3]))
        while t < TP.shape[0]-1:
            crntData = TP[t]
            nextData = TP[t+1]
            product  = nextData - crntData
            PRCP[t]  = product
            t = t+1
        return PRCP


if __name__ == "__main__":

    config = "/dias/users/ishitsuka.y.u-tokyo/tdjpn/FF/ECMWF/config.ini"

    parser = argparse.ArgumentParser(description="The script to convert raw binary into gtool format.")
    parser.add_argument("--config",type=str,default=config,help="path to the configuration file. Default path is set in this script.")
    parser.add_argument("year",type=int,help="simulation start year")
    parser.add_argument("month",type=int,help="simulation start month")
    parser.add_argument("day",type=int,help="simulation start day")
    parser.add_argument("hour",type=int,help="simulation start hour")
    parser.add_argument("eNum",type=int,help="ensemble member")
    args = parser.parse_args()

    conf = args.config
    year = args.year
    mon  = args.month
    day  = args.day
    hour = args.hour
    eNum = args.eNum

    chunk = ECMWF(conf,year,mon,day,hour,eNum)
    chunk.ecmwfToGtool()
