from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from celery import Celery
from django.shortcuts import get_object_or_404

from django.utils import timezone
from django.shortcuts import get_object_or_404
import requests
from strava2.models import Login, Activity, Workout, Lap, GpsCoord, HeartRate, \
    Speed, Elevation, Distance, Split, StravaUser
from strava2.serializers import WorkoutSerializer, LapSerializer, ActivityItemSerializer
from strava2.intervalTraining import getIntervalTraining

import re, time
from datetime import datetime, date, timedelta
from stravalib import Client
import logging

import sys, os, json, time
from fitparse import FitFile

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import multiprocessing

lock = multiprocessing.Lock()
log = logging.getLogger(__name__)
app = Celery('tasks', broker=os.getenv("CELERY_BROKER_URL"))
currentTime=time.time()

def getSpeed (speed):
    speed = 100/speed
    mm = int(speed/60)
    ss = int(speed-mm*60)
    ds = int((speed-mm*60-ss)*10)
    speed_100 = str(mm).zfill(2)+':'+str(ss).zfill(2)+'.'+str(ds).zfill(1)
    return speed_100

def getDate (time):
    hh = int(time/3600)
    mm = int((time-hh*3600)/60)
    ss = int(time-hh*3600-mm*60)
    date = str(hh).zfill(2)+':'+str(mm).zfill(2)+':'+str(ss).zfill(2)
    return date
    
def getTimeDelta (time):
    hh = int(time/3600)
    mm = int((time-hh*3600)/60)
    ss = int(time-hh*3600-mm*60)
    date = timedelta(hours=hh,minutes=mm,seconds=ss)
    return date

def sendMessage (type, data, channel):
    channel_layer = get_channel_layer()
    print ("Send message (task) ...", channel_layer, channel)
    async_to_sync(channel_layer.send)(
        channel,
        {
            "type": "send_message",
            "typeMessage": type,
            "message": data
        }
    )
    
def sendProgress (channel, value, activity, title=None):
    
    if activity is None:
        data = {
            'progress': value,
            'workout': []
            }
        sendMessage ('progressWorkout', data, channel)
    else:
        jsData = json.loads(activity)
        print ('activity=',jsData)
        jsData['progress'] = str(value)
        jsData['state'] = "u"
        if title is not None:
            jsData['label'] = title
        actList = []
        actList.append(jsData)
        print ('progress=',jsData['progress'])
        data = {
            'nbAct': 0,
            'currentAct': 0,
            'activities': actList
            }
        sendMessage ('actList', data, channel)
    
PROGRESS_STATE = 'PROGRESS'

@app.task
def get_activities (token):

    log.info ("task::get_activities")
    client = Client(token)
    user = client.get_athlete()
    log.info ("user=%s",user)
     
    # Update StavaUser
    lastUpdate=datetime.now()
    forceUpdateDateTo=datetime.now()
    login=Login.objects.filter(id=1)
    for l in login:
        forceUpdateDateTo = l.forceUpdateDateTo
    strUser = StravaUser.objects.filter(uid=user.id)
    log.info ('strUser=%s',strUser)
    log.info ('forceUpdateDateTo=%s',forceUpdateDateTo)
    for u in strUser:
        lastUpdate = u.lastUpdate
    log.info ('lastUpdate=%s',lastUpdate)
        
    limitList = 20
    initDate = datetime(2000, 1, 1)
    startDate=datetime.now()
    if forceUpdateDateTo == initDate:
        startDate = lastUpdate - timedelta(days=1)
    else:
        startDate = forceUpdateDateTo
    
    activities = client.get_activities(after=startDate,limit=limitList)
    #activities = client.get_activities(after=d,limit=limitList)
    act = None
    nbItem = 0
    nbAct = 0
    typesFilter = ["Run","Ride"]

    log.info ('activities=%s',activities)
   
    currentListSize = 0
    for activity in activities:
        if activity.type in typesFilter:
            nbAct +=1
        
    log.info ('NbAct=%d',nbAct)
    initNewActivities = False
    newUser=False
    segment=15
    begin=0
    end=begin+segment
    currentList = Activity.objects.filter(uid=client.get_athlete().id).order_by('-strTime')[begin:end]
    currentListSize = len(currentList)
    if not currentList.exists():
        newUser=True
    while (currentList.exists() or newUser) :
        log.info ('currentList=%s',currentList)
        print ('begin=',begin)
        print ('end=',end)
        actList = []
        for actItem in currentList:
            #print (actItem)
            serializer = ActivityItemSerializer(actItem)
            #print ('serializer.data: ',serializer.data)
            actList.append(serializer.data)
            
        data = {
            'nbAct': nbAct,
            'currentAct': nbItem,
            'activities': actList
            }
        sendMessage ('actList', data,strUser[0].channel_name)
        actList.clear()
        
        if not initNewActivities:
            for activity in activities:
                if activity.type in typesFilter:
                    StravaUser.objects.filter(uid=user.id).update(currentActIndex=nbItem, nbActToRetreive=nbAct)
                    act = client.get_activity(activity.id)
                    strDate = act.start_date.strftime("%Y-%m-%d %H:%M:%S")
                    #print ('uid=',user.id)
                    #print ('start_date=',strDate)
                    #print ('act.distance=',act.distance)
                    #print ('act.type=',act.type)
                    dist = re.sub(' .*$','',str(act.distance))
                    #print ('dist=',dist)
                    strDistance = format(float(dist)/1000,'.2f')
                    #print ('distance=',strDistance)
                    #print ('stravaId=',act.upload_id)
                    isDataValid = True
                    log.info ('name=%s',act.name)
                    #dump=':'.join(hex(ord(x)) for x in act.name)
                    #log.info ('dump name : %s',dump)
                    if act.name is None:
                        print ("  >>>> name is None")
                        isDataValid = False
                    if act.name == 'null':
                        print ("  >>>> name is null")
                        isDataValid = False
                    if act.name == '':
                        print ("  >>>> name is empty")
                        isDataValid = False
                    #print ('time=',act.elapsed_time)
                    #print ('splits_metric=',act.splits_metric)
                    if not Activity.objects.filter(stravaId=activity.id).exists() and isDataValid:
                        workout=Workout.objects.create(name=act.name)
                        log.info ('wid=%d',workout.id)
                        log.info ('stravaId=%d',activity.id)
                        # activity.wid=workout.id
                        stravaAct = Activity(strTime=strDate,strDist=strDistance,distance=act.distance,\
                            time=act.elapsed_time,label=act.name,stravaId=activity.id,wid=workout.id,workout_id=workout.id,\
                            resolution=strUser[0].resolution,uid=user.id,type=act.type,state="c",progress=0)
                        stravaAct.save()
                        Workout.objects.filter(id=workout.id).update(actId=stravaAct.id)
                        split = Split.objects.filter(workout__id=workout.id)
                        print ('Split first element=',split.count())
                        if not split.count():
                            if split is not None:
                                objs = [
                                    Split(split_index=i,split_distance=split.distance,split_time=split.elapsed_time,workout=workout) for i, split in enumerate(act.splits_metric)
                                ]
                                split = Split.objects.bulk_create(objs)
                        
                        # Send result list to client
                        for actItem in Activity.objects.filter(stravaId=activity.id):
                            #print (actItem)
                            serializer = ActivityItemSerializer(actItem)
                            # pre-process Json for client response to get workout
                            result = processJsonDataBackup.delay (token, workout.id, json.dumps(serializer.data),activity.id)
                            #print ('serializer.data: ',serializer.data)
                            actList.insert(0,serializer.data)

                    else:
                        Activity.objects.filter(stravaId=activity.id).update(strTime=strDate,strDist=strDistance,resolution=strUser[0].resolution)
                    
                    nbItem+=1
                    
                    data = {
                    'nbAct': nbAct,
                    'currentAct': nbItem,
                    'activities': actList
                    }
                    sendMessage ('actList', data, strUser[0].channel_name) 

        begin=end
        if currentListSize+segment > limitList:
            end=begin+limitList-currentListSize
        else:
            end=begin+segment
        currentList = Activity.objects.filter(uid=client.get_athlete().id).order_by('-strTime')[begin:end]
        currentListSize = currentListSize +  len(currentList)
        newUser=False
    
    if act is not None : 
        print ('Update user last_date')
        strUser.update(lastUpdate=datetime.now())
        
    return {'current': nbItem, 'total': nbAct}
    

def build_workout (token, pk, send=False, list=None, stravaActId=None):

    print ('>>> build_workout:',pk)
    client = Client(token)
    user = client.get_athlete()
    strUser = StravaUser.objects.filter(uid=user.id)
    
    sendProgress (strUser[0].channel_name, 5, list)
    
    workout = Workout.objects.get(pk=pk)
    types = ['time', 'distance', 'latlng', 'altitude', 'heartrate', 'velocity_smooth']
    print('WorkoutDetail, workout.actId=',workout.actId)
    activity = get_object_or_404(Activity, id=workout.actId)
    print('WorkoutDetail, activity.stravaId=',activity.stravaId)
    print('Resolution required=',strUser[0].resolution)
    
    distance = Distance.objects.filter(workout__id=workout.id)
    if not distance.count():
        resolution = 'medium'
        if strUser[0].resolution == 100:
            resolution = 'low'
        elif strUser[0].resolution == 1000:
            resolution = 'medium'
        elif strUser[0].resolution == 10000:
            resolution = 'high'
        print ('Get streams begin')
        streams = client.get_activity_streams(activity_id=activity.stravaId,resolution=resolution,types=types)
        print ('streams=',streams)
        sendProgress (strUser[0].channel_name, 10, list)
        
        #print('time seq size=',len(streams['time'].data))
        #print('dist seq',streams['distance'].data)
        #print('speed seq',streams['velocity_smooth'].data)
        #print('elevation seq',streams['altitude'].data)
        #print('HR seq',streams['heartrate'].data)
        #print('gps seq',streams['latlng'].data)
        gps = GpsCoord.objects.filter(workout__id=workout.id)
        print ('gps first element=',gps.count())
        if not gps.count() and 'latlng' in streams:
            print ('empty query, create SQL record')
            objs = [
                GpsCoord(gps_index=i,gps_time=streams['time'].data[i],gps_lat=gps[0],gps_long=gps[1],workout=workout) for i, gps in enumerate(streams['latlng'].data)
            ]
            #print ('GPS seq')
            #for i, gps in enumerate(streams['latlng'].data):
            #    print ('gps_index:',i,'gps_lat:',gps[0],'gps_long:',gps[1],'gps_time:',streams['time'].data[i])
            coord = GpsCoord.objects.bulk_create(objs)

        sendProgress (strUser[0].channel_name,20, list)
        hr = HeartRate.objects.filter(workout__id=workout.id)
        if not hr.count() and 'heartrate' in streams:
            objs = [
                HeartRate(hr_index=i,hr_value=hr,workout=workout) for i, hr in enumerate(streams['heartrate'].data)
            ]
            coord = HeartRate.objects.bulk_create(objs)
        
        sendProgress (strUser[0].channel_name, 25, list)
        if not distance.count() and 'distance' in streams:
            objs = [
                Distance(distance_index=i,distance_value=dist,workout=workout) for i, dist in enumerate(streams['distance'].data)
            ]
            coord = Distance.objects.bulk_create(objs)
            
        speed = Speed.objects.filter(workout__id=workout.id)
        if not speed.count() and 'velocity_smooth' in streams:
            objs = [
                Speed(speed_index=i,speed_value=speed,workout=workout) for i, speed in enumerate(streams['velocity_smooth'].data)
            ]
            coord = Speed.objects.bulk_create(objs)
        
        sendProgress (strUser[0].channel_name, 30, list)
        elevation = Elevation.objects.filter(workout__id=workout.id)
        if not elevation.count() and 'altitude' in streams:
            objs = [
                Elevation(elevation_index=i,elevation_value=elevation,workout=workout) for i, elevation in enumerate(streams['altitude'].data)
            ]
            coord = Elevation.objects.bulk_create(objs)
        
        sendProgress (strUser[0].channel_name, 35, list)
        laps = client.get_activity_laps(activity.stravaId)
        i=0
        for strLap in laps:
            i+=1
            print ('lap=',strLap)
            print ('strLap,start_index=',strLap.start_index)
            print ('strLap,end_index=',strLap.end_index)
            print ('strLap,lap_average_cadence=',strLap.average_cadence)
            print ('start_date=',strLap.start_date)
            print ('lap_time=',strLap.elapsed_time)
            print ('lap_distance=',strLap.distance)
            print ('lap_pace_zone=',strLap.pace_zone)
            if strLap.pace_zone is None:
                strLap.pace_zone = 0
            if strLap.average_cadence is None:
                strLap.average_cadence=0;
            lap = Lap.objects.filter(workout__id=workout.id, lap_index=i)
            if not lap.exists():
                lap = Lap.objects.create(lap_index=strLap.lap_index, lap_start_index=strLap.start_index, lap_end_index=strLap.end_index, lap_distance=strLap.distance, lap_time=strLap.elapsed_time, lap_start_date=strLap.start_date, lap_average_speed=strLap.average_speed, lap_average_cadence=strLap.average_cadence, lap_pace_zone=strLap.pace_zone, lap_total_elevation_gain=strLap.total_elevation_gain, workout=workout)
                print ('total_elevation_gain=',strLap.total_elevation_gain)
                print ('pace_zone=',strLap.pace_zone)
            
    sendProgress (strUser[0].channel_name, 40, list)
    #workout_sq=Workout.objects.filter(id=workout.id)
    #workout_sq = WorkoutSerializer.setup_eager_loading(workout_sq) 
    #serializer = WorkoutSerializer(workout_sq, many=True)
    serializer = WorkoutSerializer(workout)
    #print ('serializer.data size=',sys.getsizeof(serializer.data))
    sendProgress (strUser[0].channel_name, 75, list)
    #print ('jsonData=',workout.jsonData)
    data = ""
    
    if send:
        data = {
        'progress': 75,
        'workout': serializer.data
        }
        sendMessage ('workout',data,strUser[0].channel_name)

    print ('Store Json data ...')
    Workout.objects.filter(id=workout.id).update(jsonData=json.dumps(serializer.data))
    Activity.objects.filter(id=activity.id).update(progress=100)
    print ('Store Json data done')

    title = None
    if stravaActId is not None:
        print ('Get Intervall Training ...')
        it = getIntervalTraining(workout.id)
        if it.type == 'IT':
            # Update strava activity for name and description
            act = client.update_activity(stravaActId, name=it.title, description=it.description)
            print ('updated act=',act)
            # Update label to UI
            Activity.objects.filter(id=activity.id).update(label=it.title)
            title = it.title

    sendProgress (strUser[0].channel_name, 100, list, title)

@app.task
def get_workout ( token, pk):
    client = Client(token)
    user = client.get_athlete()
    strUser = StravaUser.objects.filter(uid=user.id)
    workout = Workout.objects.get(pk=pk)
    data = ""
    if workout.jsonData == '':
        build_workout ( token, pk, True)
        print ('workout.jsonData=',workout.jsonData)
    else:
        sendProgress (strUser[0].channel_name,60, None)
        print ('Read Json data ...')
        data = {
        'progress': 75,
        'workout': json.loads(workout.jsonData)
        }
        sendMessage ('workout',data,strUser[0].channel_name)

    
@app.task
def processJsonDataBackup ( token, wid, activity, stravaActId):
    lock.acquire()
    print('workout data to save for: ', wid)
    build_workout( token, wid, False, activity, stravaActId)
    lock.release()


@app.task
def processFit ( loginId, token, file):

    client = Client(token)
    login = get_object_or_404(Login, pk=loginId)
    user = client.get_athlete()
    # Update StavaUser
    lastUpdate=datetime.now()
    strUser = StravaUser.objects.filter(uid=user.id)
    if not strUser.exists():
        print ('create user', )
        user2 = StravaUser(uid=user.id, lastname=user.lastname, firstname=user.firstname, \
            lastUpdate=datetime.now())
        user2.save()
    else:
        print ('strUser=',strUser)
        for u in strUser:
            lastUpdate = u.lastUpdate
        print ('lastUpdate=',lastUpdate)
    
    nbItem = 0
    nbAct = 0
    currentList = Activity.objects.filter(uid=client.get_athlete().id).order_by('-strTime')
    actList = []
    for actItem in currentList:
        #print (actItem)
        serializer = ActivityItemSerializer(actItem)
        #print ('serializer.data: ',serializer.data)
        actList.append(serializer.data)
        
    print ('processFit, file: ', file)
    fitfile = FitFile(file)

    act_startTime = ''
    act_totalTime = 0
    act_speed = 0
    act_distance = 0
    act_sport = ''
    for r in  fitfile.get_messages('session'):
        print (r.get_value('sport'))
        act_sport = r.get_value('sport')
        if act_sport == 'swimming':
            act_sport='Swim'
        act_startTime = r.get_value('start_time')
        print (str(r.get_value('pool_length'))+'m')
        print (str(getDate(r.get_value('total_timer_time'))))
        act_totalTime = str(getDate(r.get_value('total_timer_time')))
        print (str(getSpeed(r.get_value('avg_speed')))+'/100m')
        act_speed = getSpeed(r.get_value('avg_speed'))
        print (str(r.get_value('total_distance'))+'m')
        act_distance = r.get_value('total_distance')
        act_strDistance = format(r.get_value('total_distance')/1000,'.2f')
        print ('act_distance=',act_distance)

    numLap=0
    laps_ts = []
    laps = []
    length = []
    timeLap=0
    for record in fitfile.get_messages('lap'):
        #print ('Lap ',numLap+1)
        #print ('time:',record.get_value('start_time'))
        #print ('total_distance:',record.get_value('total_distance'))
        #print ('total_elapsed_time:',record.get_value('total_elapsed_time'))
        #print (int(record.get_value('start_time').timestamp()))
        speed = record.get_value('avg_speed')
        if (speed is None) or (speed==0):
            speed = float(0)
        else:
            speed = float (speed)
        if (record.get_value('total_strokes') is None):
            strokes = 0
        else:
            strokes = record.get_value('total_strokes')
        dict = {'start_time': record.get_value('start_time'), 'total_distance': record.get_value('total_distance'), 'total_elapsed_time': record.get_value('total_elapsed_time'), 'speed': speed, 'strokes': strokes}
        laps.append (dict)
        laps_ts.append(int(record.get_value('start_time').timestamp()))
        timeLap = record.get_value('total_elapsed_time')
        numLap+=1
    laps_ts.append(int(record.get_value('start_time').timestamp()+timeLap))
    
    curLap=0
    curTime=laps_ts[curLap+1]
    dictLength = []
    print ('>> lap ',curLap+1,laps_ts[curLap],laps[curLap]['total_distance'])
    for record in fitfile.get_messages('length'):
        ts=record.get_value('start_time').timestamp()
        #print ('ts=',ts,'curTime=',curTime)
        if ts<curTime:
            length.append(curLap)
            curTime=laps_ts[curLap+1]
        else:
            curLap+=1
            curTime=laps_ts[curLap+1]
            print ('>> lap ',curLap+1,laps_ts[curLap],laps[curLap]['total_distance'])
            length.append(curLap)

        if record.get_value('avg_speed') is None:
            speed = float(0)
        else:
            speed = float(record.get_value('avg_speed'))
        
        dictLength.append({'lap': curLap+1, 'strokes': record.get_value('total_strokes'), 'speed': speed, 'swim_stroke': record.get_value('swim_stroke')})
        laps[curLap]['length'] = dictLength

        #print (curLap+1, record.get_value('total_strokes'), speed_100, record.get_value('swim_stroke'))

    activity_id = int(act_startTime.timestamp())
    workout = None
    if not Activity.objects.filter(stravaId=activity_id).exists():
        workout=Workout.objects.create(name=act_sport+' workout')
        print ('wid=',workout.id)
        stravaAct = Activity(strTime=act_startTime,strDist=act_strDistance,distance=act_distance,\
            time=act_totalTime,label=act_sport+' workout',stravaId=activity_id,wid=workout.id,workout_id=workout.id,uid=user.id,type=act_sport)
        stravaAct.save()
        Workout.objects.filter(id=workout.id).update(actId=stravaAct.id)
        i=0
        for strLap in laps:
            i+=1
            lap = Lap.objects.filter(workout__id=workout.id, lap_index=i)
            if not lap.exists():
                lap_time=getTimeDelta(strLap['total_elapsed_time'])
                print ('lap_time=',lap_time,'lap_average_speed=',strLap['speed'])
                lap = Lap.objects.create(lap_index=i, lap_start_index=0, lap_end_index=0, lap_distance=strLap['total_distance'], lap_time=lap_time, lap_start_date=laps_ts[i], lap_average_speed=strLap['speed'], lap_average_cadence=strLap['strokes'], lap_pace_zone=0, lap_total_elevation_gain=float(0), workout=workout)
    else:
        Activity.objects.filter(stravaId=activity_id).update(strTime=act_startTime,strDist=act_strDistance)

    for actItem in Activity.objects.filter(stravaId=activity_id):
        serializer = ActivityItemSerializer(actItem)
        actList.insert(0,serializer.data)
    
    nbItem = nbItem + 1
    nbAct = nbAct + 1
    data = {
    'nbAct': nbAct,
    'currentAct': nbItem,
    'activities': actList
    }
    sendMessage ('workout', data,strUser[0].channel_name)

@app.task(name='checkCeleryAvailibility')
def checkCeleryAvailibility ():
    global currentTime
    log.info('  >>>> checkCeleryAvailibility')
    try:
        r = requests.get('https://mycelery.onrender.com')
        log.info('  >>>> body= %s',r.content)
    except RuntimeError as e:
        print ("Check celery error ",e)
    log.info('  >>>> checkCeleryAvailibility: %d', r.status_code)

    # ping django web server
    try:
        r = requests.get('https://django-srv-s9kn.onrender.com/strava2/ping')
        log.info('  >>>> status ping= %s',r.status_code)
    except RuntimeError as e:
        print ("Check celery error ",e)

    # Activities synchro each hour
    deltatime=currentTime-time.time()
    if deltatime >= 3600:
        r = requests.get('https://django-srv-s9kn.onrender.com/strava2/activities')
        log.info('  >>>> status getActivities= %s',r.status_code)
    currentTime=time.time()
    
