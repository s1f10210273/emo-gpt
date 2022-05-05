from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_exempt
import urllib
import json

from .models import Reply

WEBHOOK_URL = 'YOUR_WEBHOOK_URL'
VERIFICATION_TOKEN = 'YOUR_VERIFICATION_TOKEN'
ACTION_HOW_ARE_YOU = 'HOW_ARE_YOU'

def index(request):
    positive_replies = Reply.objects.filter(response=Reply.POSITIVE)
    neutral_replies = Reply.objects.filter(response=Reply.NEUTRAL)
    negative_replies = Reply.objects.filter(response=Reply.NEGATIVE)

    context = {
        'positive_replies': positive_replies,
        'neutral_replies': neutral_replies,
        'negative_replies': negative_replies,

    }
    return render(request, 'index.html', context)

def clear(request):
    Reply.objects.all().delete()
    return redirect(index)

def announce(request):
    if request.method == 'POST':
        data = {
            'text': request.POST['message']
        }
        post_message(WEBHOOK_URL, data)

    return redirect(index)

@csrf_exempt
def echo(request):
    if request.method != 'POST':
        return JsonResponse({})
    
    if request.POST.get('token') != VERIFICATION_TOKEN:
        raise SuspiciousOperation('Invalid request.')
    
    user_name = request.POST['user_name']
    user_id = request.POST['user_id']
    content = request.POST['text']

    result = {
        'text': '<@{}> {}'.format(user_id, content.upper()),
        'response_type': 'in_channel'
    }

    return JsonResponse(result)

@csrf_exempt
def hello(request):
    if request.method != 'POST':
        return JsonResponse({})
    
    if request.POST.get('token') != VERIFICATION_TOKEN:
        raise SuspiciousOperation('Invalid request.')
    
    user_name = request.POST['user_name']
    user_id = request.POST['user_id']
    content = request.POST['text']

    result = {
        'blocks': [
            {
                'type' : 'section',
                'text' : {
                    'type': 'mrkdwn',
                    'text': '<@{}> How are you?'.format(user_id)
                },
                'accessory': {
                    'type': 'static_select',
                    'placeholder': {
                        'type': 'plain_text',
                        'text': 'I am:',
                        'emoji': True
                    },
                    'options': [
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': 'Fine.',
                                'emoji': True
                            },
                            'value': 'positive'
                        },
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': 'So so.',
                                'emoji': True
                            },
                            'value': 'neutral'
                        },
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': 'Terrible.',
                                'emoji': True
                            },
                            'value': 'negative'
                        }
                    ],
                    'action_id': ACTION_HOW_ARE_YOU
                }
            }
        ],
        'response_type': 'in_channel'
    }

    return JsonResponse(result)

@csrf_exempt
def reply(request):
    if request.method != 'POST':
        return JsonResponse({})
    
    payload = json.loads(request.POST.get('payload'))
    print(payload)
    if payload.get('token') != VERIFICATION_TOKEN:
        raise SuspiciousOperation('Invalid request.')
    
    if payload['actions'][0]['action_id'] != ACTION_HOW_ARE_YOU:
        raise SuspiciousOperation('Invalid request.')
    
    user = payload['user']
    selected_value = payload['actions'][0]['selected_option']['value']
    response_url = payload['response_url']

    if selected_value == 'positive':
        reply = Reply(user_name=user['name'], user_id=user['id'], response=Reply.POSITIVE)
        reply.save()
        response = {
            'text': '<@{}> Great! :smile:'.format(user['id'])
        }
    elif selected_value == 'neutral':
        reply = Reply(user_name=user['name'], user_id=user['id'], response=Reply.NEUTRAL)
        reply.save()
        response = {
            'text': '<@{}> Ok, thank you! :sweat_smile:'.format(user['id'])
        }
    else:
        reply = Reply(user_name=user['name'], user_id=user['id'], response=Reply.NEGATIVE)
        reply.save()
        response = {
            'text': '<@{}> Good luck! :innocent:'.format(user['id'])
        }
    
    post_message(response_url, response)
    return JsonResponse({})

def post_message(url, data):
    headers = {
        'Content-Type': 'application/json',
    }
    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(req) as res:
        body = res.read()