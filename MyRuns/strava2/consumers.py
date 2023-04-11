import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.auth import login
from strava2.models import StravaUser
from strava2.tasks import get_activities, get_workout, processJsonDataBackup

log = logging.getLogger(__name__)

class Consumers(AsyncWebsocketConsumer):

    async def connect(self):
        # Accept the connection
        log.info ("Connect socket, self=%s",self.channel_name)
        log.info ("scope=%s",self.scope)
        log.info ("session=%s",self.scope["session"])
        log.info ("user=%s",self.scope["user"])
        
        await self.accept()
        await self.send(text_data=json.dumps(
            {
                "type": "accept",
                "firstname": "xxx",
                "lastname": "yyy",
                "message": "accept",
            },
        ))
        
    async def receive(self, text_data):
        # login the user to this session.
        log.info ("receive message: %s",text_data)
        data = json.loads(text_data)
        strUser = StravaUser.objects.filter(firstname=data['firstname'],lastname=data['lastname'])
        strUser.update(channel_name=self.channel_name)
        token = ''
        for u in strUser:
            token = u.token
        log.info ('receive, token=%s',token)
        if data['type'] == 'Authentication':
            self.result = get_activities.delay (token)
            log.info ('get_activities task result=%s',self.result)
        elif data['type'] == 'workout':
            log.info ('get Workout message')
            self.result = get_workout.delay (token, data['message'])
        log.info ('return do_work, tid=%s',self.result)
        
    async def send_message(self, event):
        # Send a message down to the client
        #print ("Send message, event=",event)
        await self.send(text_data=json.dumps(
            {
                "type": event["typeMessage"],
                "firstname": "xxx",
                "lastname": "yyy",
                "message": event["message"],
            },
        ))
        log.info ("Send message OK")
        
    async def receive_json(self, content):
        log.info ("receive_json")
        command = content.get("command", None)
        try:
            print (command)
        except ClientError as e:
            log.debug("ws message isn't json text")
            return
        
    async def disconnect(self, close_code):
        log.info ('Socket closed!')
