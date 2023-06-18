from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from strava2.models import Login, Activity, Workout, Lap, GpsCoord, HeartRate, \
    Speed, Elevation, Distance, Split, StravaUser
from strava2.tasks import get_activities, processFit, get_workout
from django.views import generic
from django.http import JsonResponse
from stravalib import Client
from datetime import datetime, timedelta
import re
from rest_framework import viewsets, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from strava2.serializers import WorkoutSerializer, LapSerializer, ActivityItemSerializer
from strava2.stravaModel import gpsCoord
import sys, os, time
from celery.result import AsyncResult
import json, logging

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from pprint import pprint
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from django import forms
from django.views.decorators.csrf import csrf_exempt
from fitparse import FitFile

_loginId = 0
_progress = {}
log = logging.getLogger(__name__)

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()

class IndexView(generic.ListView):
    template_name = 'strava2/index.html'
    context_object_name = 'listLogin'

    def get_queryset(self):
        return Login.objects.all()

def directLogin(request):
    print ('directLogin', request)
    return redirect('/strava2/1')
    
def login(request,loginId):
    global _loginId
    login = get_object_or_404(Login, pk=loginId)
    login.userName = 'In Progress...'
    request.session['loginID'] = loginId
    _loginId=loginId
    print ("login::_loginId=",_loginId)
    client = Client()
    url = client.authorization_url(client_id=login.clientID,
                                   scope=['activity:read_all', 'activity:write'],
                                   redirect_uri=login.callbackURL)
    print ('url=',url)
    return redirect(url)

def auth(request):
    global _loginId
    print ("Auth")
    code = request.GET.get('code')
    print ("code=",code)
    scope = request.GET.get('scope')
    print ("scope=",scope)
    print ("_loginId=",_loginId)
    login = get_object_or_404(Login, pk=_loginId)
    client = Client()
    print ("client=",client)
    access_token = client.exchange_code_for_token(client_id=login.clientID,
                                                  client_secret=login.clientSecret,
                                                  code=code)
    print ("access_token=",access_token)
    user = client.get_athlete()
    strUser = StravaUser.objects.filter(uid=user.id)
    if not strUser.exists():
        print ('create user', )
        strUser = StravaUser(uid=user.id, lastname=user.lastname, firstname=user.firstname, \
            lastUpdate=(datetime.now()-timedelta(days=30)), token=access_token['access_token'])
        strUser.save()
    else:
        strUser.update(token=access_token['access_token'])
    request.session['access_token'] = access_token
    request.session['client_id'] = login.clientID
    request.session['client_secret'] = login.clientSecret

    return redirect('/strava2/activities')

def getRefreshedToken(client_id, client_secret, access_token):
    log.info('  access_token=%s',access_token)
    if access_token is not None:
        if 'expires_at' in access_token:
            if access_token['expires_at']:
                if time.time() > access_token['expires_at']:
                    log.info('  call refresh token !!!')
                    client = Client()
                    refresh_response = client.refresh_access_token(client_id, client_secret,access_token['refresh_token'])
                    log.info('  refresh_response=%s', refresh_response)
                    strUser = StravaUser(uid=client.get_athlete().id, token=refresh_response['access_token'])
                    strUser.save()
                    return refresh_response
                else:
                    return access_token
            else:
                return redirect('/strava2/')
        else:
            return redirect('/strava2/')
    else:
        return redirect('/strava2/')

@csrf_exempt
def subscribeCB (request):
    global _loginId
    log.debug ('  >>>> subscribe callback')
    challenge = ''
    if request.method == 'GET':
        log.debug ('  >>>> GET request')
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        log.debug ('  >>>> challenge=%s',challenge)
        log.debug ('  >>>> token=%s',token)
        data = {"hub.challenge":challenge}
        return JsonResponse(data)
    elif request.method == 'POST':
        log.debug ('  >>>> POST')
        log.debug("webhook event received! => request %s", request)
        # get_activities.delay (token)
        return HttpResponse(status=200)
    
def getProgress(request):
    global _progress
    if not request.session.get('access_token') in _progress:
        data = {'value': 0}
    else:
        data = {'value': _progress[request.session.get('access_token')]}
    #data = {'value': 70}
    # print ('Receive getProgress request ...')
    return JsonResponse(data)

def ping(request):
    log.info('  >>>> received ping')
    return HttpResponse(status=204)
    
@csrf_exempt
def uploadFiles(request):
    print ('Receive uploadFiles request ...')
    global _loginId
    if request.method == 'POST':
        print ('POST request')
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            #handle_uploaded_file(request.FILES['file'])
            print ('Form is Valid')
            print (request.FILES['file'])
        else:
            print (request.FILES['file'])
            f = '/tmp/'+str(request.FILES['file'])
            with open(f, 'wb+') as destination:
                for chunk in request.FILES['file'].chunks():
                    destination.write(chunk)
                extension = os.path.splitext(f)[1][1:]
                print ('file ext=',extension)
                if (extension=='fit'):
                    print ('Process Fit File ...')
                    result = processFit.delay (_loginId, request.session.get('access_token'),f)
                    print ('return do_work, tidFit=',result)
                    request.session['tidFit'] = result.task_id
                
    else:
        print ('UploadFileForm constructor')
        form = UploadFileForm()
    
    data = {'value': 0}
    return JsonResponse(data)
    
def refresh(request):
    print ('refresh', request)
    return redirect('/strava2/updateActivities')
    
def getActivitiesView(request):
    global _loginId

    #print (' >>>> getActivitiesView, get_queryset')
    client = Client(getRefreshedToken(request.session.get('client_id'), request.session.get('client_secret'),request.session.get('access_token'))['access_token'])
    
    print (' >>>> getActivitiesView, client=',client)
    act = Activity.objects.filter(uid=client.get_athlete().id).order_by('-strTime')
    #print (' >>>> getActivitiesView, acts=',act)
    tid = request.session.get('task_id')
    result = AsyncResult(tid)
    print (' >>>> getActivitiesView, state=',result.state)
    print (' >>>> getActivitiesView, meta_data=',result.info)

    actList = []
    for actItem in act:
        #print (actItem)
        serializer = ActivityItemSerializer(actItem)
        #print ('serializer.data: ',serializer.data)
        actList.append(serializer.data)
    
    if (result.info['total'] is None):
        result.info['total'] = 0
    if (result.info['current'] is None):
        result.info['current'] = 0
    data = {
        'nbAct': result.info['total'],
        'currentAct': result.info['current'],
        'activities': actList
        }

    #print ('data=',data)
    return JsonResponse(data)

class ActivitiesView(generic.ListView):
    global _loginId
    #print ('ActivitiesView')
    template_name = 'strava2/activity_list.html'
    context_object_name = 'activities_list'

    def get_queryset(self):
    
        print ('ActivitiesView, access_token=',self.request.session.get('access_token'))
        self.client = Client(getRefreshedToken(self.request.session.get('client_id'), self.request.session.get('client_secret'),self.request.session.get('access_token'))['access_token'])
        return Activity.objects.filter(uid=self.client.get_athlete().id).order_by('-strTime')
     
    def get_context_data(self, **kwargs):
        context = super(ActivitiesView, self).get_context_data(**kwargs)
        login = get_object_or_404(Login, pk=_loginId)
        user = self.client.get_athlete()
        print ("lastname=",user.lastname)
        print ('firstname=',user.firstname)
        print ('mail=',user.email)
        print ('id=',user.id)
        login.userName = user.lastname
        login.firstName = user.firstname
        context['login'] = login

        return context

class WorkoutView(generic.DetailView):
    global _loginId
    #print ('WorkoutView')

    model = Workout
    template_name = 'strava2/workout.html'

    def get_context_data(self, **kwargs):
        context = super(WorkoutView, self).get_context_data(**kwargs)
        login = get_object_or_404(Login, pk=_loginId)
        print ("Session", self.request.session)
        print ('Token=',self.request.session.get('access_token'))
        user = Client(getRefreshedToken(self.request.session.get('client_id'), self.request.session.get('client_secret'),self.request.session.get('access_token'))['access_token']).get_athlete()
        print ("Workout lastname=",user.lastname)
        login.userName = user.lastname
        context['login'] = login
        return context
      
class WorkoutDetail(APIView):
    
    def get_object(self, pk):
        try:
            print('WorkoutDetail, get_object, pk=',pk)
            w =Workout.objects.get(pk=pk)
            print('WorkoutDetail, w=',w)
            return w
        except workout.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        global _progress
        token = getRefreshedToken(self.request.session.get('client_id'), self.request.session.get('client_secret'),self.request.session.get('access_token'))['access_token']
        result = get_workout.delay (token, pk)
        print ('return do_work, tidGetWorkout=',result)
        data = {'value': 0}
        return JsonResponse(data)
        
        