# -*- coding: utf-8 -*-
"""
python scheduler
"""
from crontab import CronTab
from datetime import datetime, timedelta
import logging
import math
from multiprocessing import Pool
import time
import subprocess
import sys
import numpy

# general settings
com      = "python"
exe_f    = "batch_f.py" # execution code
exe_m    = "batch_m.py" # execution code
delay    = 60 # delay of execution from initial time [hour]
logging.Formatter.converter=time.gmtime
initTimeArray = numpy.array([0,12])
###
DELAY = (numpy.ones((initTimeArray.shape[0]))*delay).astype(numpy.int32)
timeList = [ d%24 if d >= 24 else d for d in (initTimeArray + DELAY).tolist()]
timeList.sort()
sorted(timeList,reverse=True)
exeTimeList = map(str,timeList)
exeTime = ",".join(exeTimeList)

class JobConfig(object):
  """
  config
  """
 
  def __init__(self, crontab):
    """
    :type crontab: crontab.CronTab
    :param crontab: config of the schedule
    :type job: function
    :param job: the function that execute
    """
 
    self._crontab = crontab
 
 
  def schedule(self):
    """
    fetch the next schedule
    :rtype: datetime.datetime
    :return: the next schedule
    """
 
    crontab = self._crontab
    return datetime.utcnow() + timedelta(seconds=math.ceil(crontab.next(default_utc=True)))


  def next(self):
    """
    fetch the sleep time length until next schedule.
    :rtype: long
    :retuen: sleep time length (sec)
    """
 
    crontab = self._crontab
    return math.ceil(crontab.next(default_utc=True))
 
 
def job_controller(jobConfig):
  """ 
  controller
  :type crontab: crontab.CronTab
  :param crontab: config of the schedule
  """
 
  logging.info("->- start processing...")
 
  while True:
 
    try:

      # display next execution time
      execUtc = jobConfig.schedule()
      logging.info("-?- next:\texecution time [UTC]:%s" %
        execUtc.strftime("%Y-%m-%d %H:%M:%S"))
 
      # display next execution schedule.
      initUtc = jobConfig.schedule() - timedelta(hours=delay)
      logging.info("-?- next:\tinitial time [UTC]:%s" %
        initUtc.strftime("%Y-%m-%d %H:%M:%S"))

      # sleep until next schedule
      delayedSleepTime = jobConfig.next()
      time.sleep(delayedSleepTime)
 
      logging.info("-!> execute the process.")
 
###   execute the job
      try:
         packets = [numpy.arange(0,17,1).tolist(),numpy.arange(17,34,1).tolist(),numpy.arange(34,51,1).tolist()] # for parallelization.
         for packet in packets:
            years    = [initUtc.year for i in range(len(packet))]
            months   = [initUtc.month for i in range(len(packet))]
            days     = [initUtc.day for i in range(len(packet))]
            hours    = [initUtc.hour for i in range(len(packet))]
            argList = numpy.array([years,months,days,hours,packet]).T.tolist()

            # Parallel starts,
            p = Pool(3) # dont touch
            p.map(multiJob,argList)
            p.terminate()
            # Parallel ends.

            [ subprocess.check_call([com,exe_m,year,mon,day,hour,eNum]) for eNum in packet ]

      except:
         sys.stderr.write("Problem in execution")

###
      logging.info("-!< execution finished.")
 
    except KeyboardInterrupt:
      break
 
  logging.info("-<- finished processing.")
 
 
def multiJob(aList):
    
    year = aList[0]
    mon  = aList[1]
    day  = aList[2]
    hour = aList[3]
    eNum = aList[4]

    subprocess.check_call([com,exe_f,year,mon,day,hour,eNum])


def main():
  """
  """
 
  # log config
  logging.basicConfig(level=logging.DEBUG,
    format="time:%(asctime)s.%(msecs)03d\tprocess:%(process)d" +
      "\tmessage:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
 
  # execution schedule setting
  jobConfigs = JobConfig(CronTab("0 "+exeTime+" * * *"))
  
  # execute
  job_controller(jobConfigs)

 
 
if __name__ == "__main__":
 
  main()
