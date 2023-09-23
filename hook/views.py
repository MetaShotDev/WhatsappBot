import os
from datetime import datetime
from django.http import HttpResponse
from rest_framework.decorators import api_view
from .models import Conversation, WhiteList
import openai
from heyoo import WhatsApp
from dotenv import load_dotenv

load_dotenv()

# Constants
AVAILABLE_COMMANDS = {
    "reset", "tcount", "help",
    "feedback", "info", "image",
    "icount"
}

# Replace with your WhatsApp welcome message
WELCOME_TEXT = '''Hello there! I'm ALL.AI, a friendly AI assistant powered by ChatGPT. 👋
I'm here to help you with a variety of questions, tasks, and engaging conversations! 💬
Before we begin, let me share a few things with you:
Terms and Conditions - https://www.helloallai.com/privacy-policy
As you've been accepted into our pilot program, you will receive 10k open AI tokens per month, all we ask is that you provide your valuable feedback weekly and report any bugs at https://forms.gle/swqKtU82uEtHaWzw9
By continuing to use this bot, you indicate your understanding and acceptance of these terms. If you agree, please continue this conversation. If you don't, you can reply with "STOP".
Thank you for choosing ALL.AI! Let's dive into some interesting conversations! 🚀🗣️'''

# Replace with your help text
HELP_TEXT = '''ALL.AI help menu 🤖
Here are the available commands you can use:
1. /help - Displays this help message. 🔨
2. /info - Provides information about the bot. 📓
3. /image <prompt> - Generates an image based on the prompt provided. 🖼️
4. /tcount - Check how many tokens you have left for this month. 🔢
5. /icount - Check how many image generations token left for this month. 🖼️
6. /reset - Resets the chat to start from the welcome message. 🪫
7. /feedback - You can give feedback or report bugs using the link provided. 📖

ALL.AI works on a number of languages, so feel free to try it out.

Since the ALL.AI is in its beta testing, we will be adding more commands soon. 
We hope to introduce image generation, voice note capabilities, Real-time data and much more! 🌟'''


@api_view(['GET', 'POST'])
def send_whatsapp_message(request):
    if request.method == 'GET':
        # Handle GET request for token verification
        return process_whatsapp_get(request)
    elif request.method == 'POST':
        # Handle POST request for incoming WhatsApp messages
        return process_whatsapp_post(request)
    else:
        return HttpResponse(status=405)  # Method not allowed

def process_whatsapp_get(request):
   
    verify_token = os.getenv('VERIFY_TOKEN')
    if request.GET.get('hub.verify_token') == verify_token:
        return HttpResponse(request.GET.get('hub.challenge'))
    else:
        return HttpResponse(status=403)  # Token verification failed

def process_whatsapp_post(request):
    try:
        value = request.data['entry'][0]['changes'][0]['value']
        if 'messages' in value:
            # Handle incoming WhatsApp messages
            return handle_incoming_message(value)
        elif 'statuses' in value:
            return HttpResponse({'status': 'success'})
        else:
            return HttpResponse({'status': 'failed'}, status=400)  # Invalid message
    except Exception as e:
        # Handle exceptions and errors gracefully
        return HttpResponse({'status': 'error', 'message': str(e)}, status=500)

def handle_incoming_message(message_data):

    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        messenger = WhatsApp(
            os.getenv('WHATSAPP_API_KEY'),
            phone_number_id='128744806985877'
        )
        
        message = message_data['messages'][0]
        sender_phone_number = message['from']
        if message['type'] == 'text':
            text_body = message['text']['body']
        elif message['type'] == 'button':
            
            text_body = message['button']['text']
        context = ''
        
        messenger.mark_as_read(message['id'])
       
        
        conversation = Conversation.objects.get(phone_number=sender_phone_number)
        
        if not conversation.is_subscribed:
            messenger.send_message("You are unsubscribed from ALL.AI. Contact team ALL.AI at coreteam@helloallai.com", sender_phone_number)
            return HttpResponse({'status': 'success'})
        
        if text_body == "START":
            messenger.send_message("Hello! How can I assist you today?", sender_phone_number)
            return HttpResponse({'status': 'success'})

        if text_body == "STOP":
            conversation.is_subscribed = False
            conversation.save()
            messenger.send_message("You are unsubscribed from ALL.AI. Thank you for your participation!", sender_phone_number)
            return HttpResponse({'status': 'success'})
        if text_body[0] == '/':
            if text_body.split()[0][1:] not in AVAILABLE_COMMANDS:
                messenger.send_message("Sorry, that command is not available. Please try again.", sender_phone_number)
                return HttpResponse({'status': 'success'})
            if text_body == '/reset':
                conversation.context = ''
                conversation.save()
                messenger.send_message(WELCOME_TEXT, sender_phone_number)
                return HttpResponse({'status': 'success'})
            if text_body == '/tcount':
                remaining_tokens = (10000 - conversation.token_count) if (10000 - conversation.token_count) > 0 else 0
                token_text = f"You have {remaining_tokens} tokens remaining."
                messenger.send_message(token_text, sender_phone_number)
                return HttpResponse({'status': 'success'})
            if text_body == '/icount':
                remaining_images = (10 - conversation.image_count) if (10 - conversation.image_count) > 0 else 0
                image_text = f"You have {remaining_images} image generations remaining."
                messenger.send_message(image_text, sender_phone_number)
                return HttpResponse({'status': 'success'})
            
            if text_body == '/help':
                messenger.send_message(HELP_TEXT, sender_phone_number)
                return HttpResponse({'status': 'success'})
            if text_body == '/feedback':
                messenger.send_message("Please provide your feedback here: https://forms.gle/swqKtU82uEtHaWzw9", sender_phone_number)
                return HttpResponse({'status': 'success'})
            if text_body == '/info':
                messenger.send_message("ALL.AI is a friendly AI assistant powered by Metashot LLC. It is currently in its beta testing phase. We will be adding more features soon. Stay tuned!", sender_phone_number)
                return HttpResponse({'status': 'success'})
            if text_body[:6] == '/image':
                if conversation.image_count > 10:
                    messenger.send_message("Sorry, you have exceeded the free limit allowed for this month.", sender_phone_number)
                    return HttpResponse({'status': 'success'})

                if conversation.last_image_used.month != datetime.now().month:
                    conversation.image_count = 0

                if len(text_body) < 7:
                    messenger.send_message("Please provide a prompt for the image generation.", sender_phone_number)
                    return HttpResponse({'status': 'success'})

                response = openai.Image.create(
                    prompt=text_body[6:],
                    n=1,
                    size="1024x1024"
                )
                image_url = response['data'][0]['url']
                conversation.image_count += 1
                conversation.last_image_used = datetime.now()
                conversation.save()
                messenger.send_image(
                    image_url, 
                    sender_phone_number,
                    caption="Image generated by ALL.AI"
                )
                return HttpResponse({'status': 'success'})


        if conversation.last_token_used.month != datetime.now().month:
            conversation.token_count = 0

        if conversation.token_count > 10000:
            text_body = "Sorry, you have exceeded the free limit allowed for this month."
            messenger.send_message(text_body, sender_phone_number)
            return HttpResponse({'status': 'success'})
        if (conversation.updated_at.replace(tzinfo=None) - datetime.now()).total_seconds() > 1800:
            context = text_body
            conversation.context = context
            conversation.save()
        else:
            context = conversation.context

       
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": text_body}
            ]
        )

        response = completion['choices'][0].message
        conversation.context = str(response['content'])[:500]
        conversation.token_count += len(response['content'].split())
        conversation.last_token_used = datetime.now()
        conversation.save()
        messenger.send_message(response["content"], sender_phone_number)
        
        return HttpResponse({'status': 'success'})

    except Conversation.DoesNotExist:
        context = text_body
        conversation = Conversation(phone_number=sender_phone_number, context=context)
        conversation.last_token_used = datetime.now()
        conversation.last_image_used = datetime.now()
    
        if WhiteList.objects.filter(phone_number=sender_phone_number).exists():
            conversation.is_subscribed = True
        else:
            conversation.is_subscribed = False

        conversation.save()
        messenger.send_template("welcome", sender_phone_number, lang="en", components=[])
        return HttpResponse({'status': 'success'})
    except Exception as e:
        messenger.send_message("Sorry, I don't understand. Please try again.", sender_phone_number)
        return HttpResponse({'status': 'error', 'message': str(e)})
