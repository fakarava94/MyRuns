import json, logging, time
from stravalib import Client
from strava2.models import Login, StravaUser
from django.shortcuts import get_object_or_404, render, redirect

log = logging.getLogger(__name__)

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
                    strUser = StravaUser(uid=client.get_athlete().id)
                    strUser.update(token=refresh_response['access_token'], refresh_token=refresh_response['refresh_token'],token_expires_at=refresh_response['expires_at'])
                    return refresh_response
                else:
                    return access_token
            else:
                return redirect('/strava2/')
        else:
            return redirect('/strava2/')
    else:
        return redirect('/strava2/')