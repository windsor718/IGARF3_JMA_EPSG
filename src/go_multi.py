import datetime
import subprocess
from multiprocessing import Pool
import batch
import numpy
from time import sleep


sDate = datetime.datetime(2019,5,29,12)
eDate = datetime.datetime(2019,6,19,12)

def  main():
    date  = sDate
    while date <= eDate:
        print date
        exe(date)
        date = date + datetime.timedelta(hours=12)


def exe(date):
         #packets = [numpy.arange(0,17,1).tolist(),numpy.arange(17,34,1).tolist(),numpy.arange(34,51,1).tolist()] # for parallelization.
         packets = [numpy.arange(0,3,1).tolist(),numpy.arange(17,20,1).tolist(),numpy.arange(34,37,1).tolist()]
         for packet in packets:
            years    = [date.year for i in range(len(packet))]
            months   = [date.month for i in range(len(packet))]
            days     = [date.day for i in range(len(packet))]
            hours    = [date.hour for i in range(len(packet))]
            argList = numpy.array([years,months,days,hours,packet]).T.tolist()

            # Parallel starts,
            p = Pool(3) # dont touch
            p.map(multiJob,argList)
            p.close()
            # Parallel ends.

            [ subprocess.check_call(["python","batch_m.py",str(date.year),str(date.month),str(date.day),str(date.hour),str(eNum)]) for eNum in packet ]
         #subprocess.check_call(["python","batch_v.py",str(date.year),str(date.month),str(date.day),str(date.hour),0])
 

def multiJob(aList):
    
    year = str(aList[0])
    mon  = str(aList[1])
    day  = str(aList[2])
    hour = str(aList[3])
    eNum = str(aList[4])
    print eNum

    subprocess.check_call(["python","batch_f.py",year,mon,day,hour,eNum])


if __name__ == "__main__":

    main()
