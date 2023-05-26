
from datetime import datetime, timedelta
import logging
import math, statistics
from strava2.models import Login, Activity, Workout, Lap

log = logging.getLogger(__name__)

class intervalTraining():
    def __init__(self):
        self.hightIntensity=0
        self.recovery=0
        self.hiAvSpeed=0
        self.hiAvDist=0
        self.liAvTime=0
        self.hiSpeed=[]
        self.hiTime=[]
        self.hiDist=[]
        self.liSpeed=[]
        self.liTime=[]
        self.series = []
        self.nbReps=0
        self.nbRecoveries=0

class itItem():
    def __init__(self, hiSpeed, hiTime, hiDist):
        self.hiSpeed=hiSpeed
        self.hiTime=hiTime
        self.hiDist=hiDist
        self.liSpeed=0
        self.liTime=0
        self.isRep=False
        self.nbReps=0

    def setRecovery (self, liSpeed, liTime):
        self.liSpeed=liSpeed
        self.liTime=liTime

class itSeries():
    def __init__(self):
        self.itList=[]
        self.title=''
        self.isRep=False
        self.nbReps=0

def convertSpeed2Pace (speed):
    pace=str(timedelta(seconds=(1000/speed)))
    x = pace.split(':')
    ss= x[2].split('.')[0]
    ms= int(round((float(x[2])-int(float(x[2])))*10,0))
    pace=x[1]+':'+ss+'.'+str(ms)
    return (pace)

def roundDistance (d):
    rd=0
    length=len(str(d))    
    fract=d/50
    if (d-int(fract)*50)>25:
        rd=int(fract+1)*50
    else:
        rd=int(fract)*50
    return rd

class Struct(object): pass

def getIntervalTraining (workoutId):

    itDescr = Struct()
    itDescr.title=''
    itDescr.description='Generated description'
    itDescr.type='REGULAR'

    laps = Lap.objects.filter(workout_id=workoutId)
    if len(laps) < 5:
        log.debug ('Regular workout')
    else:
        it = intervalTraining()
        listIt = []
        series = []
        i=1
        # warmup speed
        easySpeed=laps[0].lap_average_speed 
        for lap in laps[1:]:
            #log.debug ('     >> %s %s',lap.lap_distance, lap.lap_time)
            #log.debug ('     >> %s',lap.lap_average_speed)
            if (lap.lap_average_speed/easySpeed) > 1.2:
                if ( (i+1 <= len(laps) and laps[i+1].lap_average_speed/lap.lap_average_speed) < 0.8) or i==len(laps):
                    #log.debug('fract=%f',laps[i+1].lap_average_speed/lap.lap_average_speed)
                    it.nbReps=it.nbReps+1
                    it.hiSpeed.append(lap.lap_average_speed)
                    it.hiDist.append(lap.lap_distance)
                    it.hiTime.append(lap.lap_time)
                    rDist=roundDistance(lap.lap_distance)
                    listIt.append(itItem(lap.lap_average_speed, lap.lap_time, rDist))
                    #print ('add dist ',lap.lap_distance)
            else:
                if len(listIt)>0:
                    it.liTime.append(lap.lap_time)
                    listIt[it.nbRecoveries].setRecovery (lap.lap_average_speed,lap.lap_time)
                    it.nbRecoveries=it.nbRecoveries+1
            i=i+1
        
        i=0
        serieIndex=0
        #print ('liTime=',it.liTime)
        for revoveryTime in it.liTime:
            if i>serieIndex :
                #print ('ratio_deltatime=',it.liTime[i]/it.liTime[i-1])
                if (it.liTime[i]/it.liTime[i-1]>1.5) :
                    # print ('New serie')
                    newIt = listIt[serieIndex:i+1]
                    series.append(itSeries())
                    series[len(series)-1].itList.append(newIt)
                    serieIndex=i+1
            i=i+1

        if len(series)>0:
            it.hiAvSpeed=statistics.mean(it.hiSpeed)
            it.hiAvDist=statistics.mean(it.hiDist)
            log.debug ('Interval training')
            pace=str(timedelta(seconds=(1000/it.hiAvSpeed)))
            pace=convertSpeed2Pace (it.hiAvSpeed)
            log.debug ('hiAvPace=%s',pace)
            log.debug ('hiDist=%s',it.hiDist)
            log.debug ('hiAvDist=%d',it.hiAvDist)
            log.debug ('nbReps=%d',it.nbReps)
            log.debug ('nbSeries=%d',len(series))

            reps=1
            repIdx=-1
            for s in series:
                print("====================")
                i=0
                for l in s.itList:
                    for t in l:
                        log.debug ('  >>> %d',t.hiDist)
                        if i> 0:
                            if t.hiDist==l[i-1].hiDist:
                                t.isRep = True
                                if repIdx<0:
                                    repIdx = i-1
                                l[i-1].isRep = True
                                reps=reps+1
                            else:
                                if l[i-1].isRep:
                                    l[repIdx].nbReps = reps
                                    repIdx = -1                                
                        i=i+1
                        if i==(len(l)) and t.isRep:
                            l[repIdx].nbReps = reps

            for s in series:
                title=''
                for l in s.itList:
                    for t in l:
                        if t.isRep and t.nbReps>0:
                            if title=='':
                                sep=''
                            else:
                                sep='/'       
                            title=title+sep+str(t.nbReps)+'x'+str(t.hiDist)+'m'
                        elif not t.isRep:
                            if title=='':
                                sep=''
                            else:
                                sep='/'
                            title=title+sep+str(t.hiDist)+'m'
                s.title=title

            # get clusters
            i=0
            repIdx=-1
            for s in series:
                if i>0:
                    if s.title==series[i-1].title:
                        s.isRep = True
                        if repIdx<0:
                            repIdx = i-1
                        series[i-1].isRep = True
                        reps=reps+1
                    else:
                        if series[i-1].isRep:
                            series[repIdx].nbReps = reps
                            repIdx = -1                                
                i=i+1
                if i==(len(series)) and s.isRep:
                    series[repIdx].nbReps = reps

            title=''
            for s in series:
                if s.isRep and s.nbReps>0:
                    if title=='':
                        sep=''
                    else:
                        sep='/'
                    title=title+sep+str(s.nbReps)+'x('+s.title+')'
                elif not s.isRep:
                    if title=='':
                        sep=''
                    else:
                        sep='/'
                    title=title+sep+s.title
            log.debug('title=%s',title)
            itDescr.title = title
            itDescr.type = 'IT'
        else:
            log.debug ('Regular workout')

    return itDescr