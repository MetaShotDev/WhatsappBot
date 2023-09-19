from rest_framework.decorators import api_view
from django.http import HttpResponse
from heyoo import WhatsApp
import openai

from .models import Conversation

from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

welcome_text = '''Hello there! I'm ALL.AI, a friendly AI assistant powered by ChatGPT. 👋
I'm here to help you with a variety of questions, tasks, and engaging conversations! 💬
Before we begin, let me share a few things with you:
Terms and Conditions - https://www.helloallai.com/privacy-policy
As you've been accepted into our pilot program, you will receive 10k open AI tokens per month, all we ask is that you provide your valuable feedback weekly and report any bugs at https://forms.gle/swqKtU82uEtHaWzw9
By continuing to use this bot, you indicate your understanding and acceptance of these terms. If you agree, please continue this conversation. If you don't, you can reply with "STOP".
Thank you for choosing ALL.AI! Let's dive into some interesting conversations! 🚀🗣️'''

available_commands = {"reset", "tcount", "help"}\


@api_view(['GET', 'POST'])
def send_whatsapp_message(request):
    
    if request.method == 'GET':
        verify_token = os.getenv('VERIFY_TOKEN')
        if request.GET.get('hub.verify_token') == verify_token:
            return HttpResponse(request.GET.get('hub.challenge'))
        else:
            return HttpResponse(status=403)  # Token verification failed

    elif request.method == 'POST':
        value = request.data['entry'][0]['changes'][0]['value']
        if 'messages' in value:
            openai.api_key = os.getenv('OPENAI_API_KEY')


            messenger = WhatsApp(
                os.getenv('WHATSAPP_API_KEY'),
                phone_number_id='128744806985877'
            )

            message = value['messages'][0]
            sender_phone_number = message['from']
            
            text_body = message['text']['body']

            context = ''

            messenger.mark_as_read(message['id'])

            try:
                conversation = Conversation.objects.get(phone_number=sender_phone_number)
                if text_body == "STOP":
                    conversation.delete()
                    messenger.send_message("You have been unsubscribed from ALL.AI. Thank you for your participation!", sender_phone_number)
                    return HttpResponse({'status': 'success'})
                if text_body[0] == '/':
                    if text_body[1:] not in available_commands:
                        messenger.send_message("Sorry, that command is not available. Please try again.", sender_phone_number)
                        return HttpResponse({'status': 'success'})
                    if text_body == '/reset':
                        conversation.context = ''
                        messenger.send_message(welcome_text, sender_phone_number)
                        return HttpResponse({'status': 'success'})
                    if text_body == '/tcount':
                        token_text = "You have " + str(10000 - conversation.token_count) + " tokens remaining."
                        messenger.send_message(token_text, sender_phone_number)
                        return HttpResponse({'status': 'success'})
                    if text_body == '/help':
                        help_text = "Available commands: " + ", ".join(available_commands)
                        messenger.send_message(help_text, sender_phone_number)
                        return HttpResponse({'status': 'success'})

                if conversation.token_count > 10000:
                    text_body = "Sorry, you have exceeded the free limit allowed."
                    messenger.send_message(text_body, sender_phone_number)
                    return HttpResponse({'status': 'success'})
                if (conversation.updated_at.replace(tzinfo=None) - datetime.now()).total_seconds() > 1800:
                    context = text_body
                    conversation.context = context
                    conversation.save()
                else:
                    context = conversation.context
            except Conversation.DoesNotExist:
                context = text_body
                conversation = Conversation(phone_number=sender_phone_number, context=context)
                conversation.save()
                
                messenger.send_message(welcome_text, sender_phone_number)
                return HttpResponse({'status': 'success'})           
            try:

                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": text_body}
                    ]
                )

                response = completion['choices'][0].message
                conversation.context = str(response['content'])[:100]
                conversation.token_count += len(response['content'].split())
                conversation.save()
                messenger.send_message(response["content"], sender_phone_number)
            except:
                messenger.send_message("Sorry, I don't understand. Please try again.", sender_phone_number)

            return HttpResponse({'status': 'success'})
        
        elif 'statuses' in value:
            return HttpResponse({'status': 'success'})
        
        else:
            print("Error message received")
            return HttpResponse({'status': 'failed'}, status=400)