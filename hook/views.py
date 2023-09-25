import os
from datetime import datetime
from django.http import HttpResponse
from rest_framework.decorators import api_view
from .models import Conversation, WhiteList, Todo
import openai
from heyoo import WhatsApp
from dotenv import load_dotenv
import speech_recognition as sr
from pydub import AudioSegment
from pytesseract import image_to_string
from PIL import Image
import time

load_dotenv()

# Constants
AVAILABLE_COMMANDS = {
    "reset", "tcount", "help",
    "feedback", "info", "image",
    "icount", "todoadd", "todoview",
    "tododelete", "todoclear"
}

HELP_TEXT = '''ALL.AI help menu 🤖
Here are the available commands you can use:
1. */help* - Displays this help message. 🔨
2. */info* - Provides information about the bot. 📓
3. */image <prompt>* - Generates an image based on the prompt provided. 🖼️
4. */tcount* - Check how many tokens you have left for this month. 🔢
5. */icount* - Check how many image generations token left for this month. 🖼️
6. */reset* - Resets the chat to start from the welcome message. 🪫
7. */todoadd <item>* - Adds an item to your Todo list. 📝
8. */todoview* - View your Todo list. 📝
9. */tododelete <todo number>*- Deletes a todo item from your todo list. 📝
10. */feedback* - You can give feedback or report bugs using the link provided. 📖

ALL.AI works on a number of languages as well as with voice notes, so feel free to try it out.

If you type *"STOP"*, you cannot use ALL.AI any further. Once this has been done, to resubscribe, you will have to get in touch with "coreteam@helloallai.com" 

Since the ALL.AI is in its beta testing, we will be adding more commands soon. 🌟'''


NOT_SUBSCRIBED_TEXT = '''Welcome to ALL.AI, a friendly AI assistant powered by ChatGPT. 👋
It looks like you haven't subscribed to ALL.AI yet. You can do so at helloallai.com, under the waitlist button.
If you have already added your name to the waitlist and have not yet been selected, please wait for at least a week and then send an email to "coreteam@helloallai.com" 
Have a good day!'''

TOKEN_LIMIT = 10000
IMAGE_LIMIT = 25
DEBUG = os.getenv('DEBUG', False)


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

def audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    ogg_audio = AudioSegment.from_ogg(audio_file)
    ogg_audio.export(f"{audio_file}.wav", format="wav")

    with sr.AudioFile(f"{audio_file}.wav") as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        # delete temporary audio file
        os.remove(f"{audio_file}.wav")
        return (text, True)
    except sr.UnknownValueError:
        return ("Could not understand audio", False)
    except sr.RequestError as e:
        return ("Could not request results from Speech Recognition service;", False)
    except Exception as e:
        return (str(e), False)

def handle_incoming_message(message_data):

    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        messenger = WhatsApp(
            os.getenv('WHATSAPP_API_KEY'),
            phone_number_id='128744806985877'
        )
        
        message = message_data['messages'][0]
        sender_phone_number = message['from']
        messenger.mark_as_read(message['id'])

        if DEBUG and sender_phone_number != os.getenv('DEBUG_PHONE_NUMBER'):
            messenger.send_message("Server maintenance in progress. Please try again later.", sender_phone_number)
            return HttpResponse({'status': 'success'})

        if message['type'] == 'text':
            text_body = message['text']['body']
        elif message['type'] == 'button':
            text_body = message['button']['text']
        elif message['type'] == 'audio':
            audio_url = messenger.query_media_url(message['audio']['id'])
            mime_type = message['audio']['mime_type']
            audio_filename = messenger.download_media(
                audio_url, mime_type,
                file_path=f"temp/audio_{sender_phone_number}"
            )
            text_body, success = audio_to_text(audio_filename)
            os.remove(audio_filename)
            if not success:
                messenger.send_message(text_body, sender_phone_number)
                return HttpResponse({'status': 'success'})
            else:
                text_body = text_body.lower()
        # elif message['type'] == 'image':
        #     image_url = messenger.query_media_url(message['image']['id'])
        #     mime_type = message['image']['mime_type']
        #     caption = ''
        #     if 'caption' in message['image']:
        #         caption = message['image']['caption']
        #     image_filename = messenger.download_media(
        #         image_url, mime_type,
        #         file_path=f"temp/image_{sender_phone_number}"
        #     )
        #     text_body = image_to_string(Image.open(image_filename), lang='eng')
        #     text_body += f" {caption}"
        #     os.remove(image_filename)
            
        else:
            messenger.send_message("Apologies, but it seems that this feature is not available yet. We are actively working on developing it and appreciate your patience. Please stay tuned for future updates!.", sender_phone_number)
            return HttpResponse({'status': 'success'})
            
           


        context = ''
        
        conversation = Conversation.objects.get(phone_number=sender_phone_number)
        
        if not conversation.is_subscribed:
            messenger.send_message(NOT_SUBSCRIBED_TEXT, sender_phone_number)
            return HttpResponse({'status': 'success'})
        
        if conversation.last_token_used.month != datetime.now().month:
            conversation.token_count = 0

        
        if (conversation.updated_at.replace(tzinfo=None) - datetime.now()).total_seconds() > 1800:
            context = text_body
            conversation.context = context
            conversation.save()
        else:
            context = conversation.context
        
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
                messenger.send_message("Your chat has been reset.", sender_phone_number)
                messenger.send_message("Hello! How can I assist you today?", sender_phone_number)
                return HttpResponse({'status': 'success'})
            elif text_body == '/tcount':
                remaining_tokens = (TOKEN_LIMIT - conversation.token_count) if (10000 - conversation.token_count) > 0 else 0
                token_text = f"You have {remaining_tokens} tokens remaining."
                messenger.send_message(token_text, sender_phone_number)
                return HttpResponse({'status': 'success'})
            elif text_body == '/icount':
                remaining_images = (IMAGE_LIMIT - conversation.image_count) if (10 - conversation.image_count) > 0 else 0
                image_text = f"You have {remaining_images} image generations remaining."
                messenger.send_message(image_text, sender_phone_number)
                return HttpResponse({'status': 'success'})
            
            elif text_body == '/help':
                messenger.send_message(HELP_TEXT, sender_phone_number)
                return HttpResponse({'status': 'success'})
            elif text_body == '/feedback':
                messenger.send_message("Please provide your feedback here: https://forms.gle/swqKtU82uEtHaWzw9", sender_phone_number)
                return HttpResponse({'status': 'success'})
            elif text_body == '/info':
                messenger.send_message("ALL.AI is a friendly AI assistant powered by Metashot LLC. It is currently in its beta testing phase. We will be adding more features soon. Stay tuned!", sender_phone_number)
                return HttpResponse({'status': 'success'})
            elif text_body[:6] == '/image':
                if conversation.image_count > IMAGE_LIMIT:
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
            
            elif text_body[:8] == '/todoadd':
                if len(text_body) < 9:
                    messenger.send_message("Please provide a todo item.", sender_phone_number)
                    return HttpResponse({'status': 'success'})

                # if items are separated by commas, add each item separately
                if ',' in text_body[9:]:
                    items = text_body[9:].split(',')
                    for item in items:
                        todo = Todo.objects.create(user=conversation, todo=item)
                        todo.save()
                    todos = Todo.objects.filter(user=conversation).order_by('-created_at')
                    todo_list = "Your todo list:\n"
                    for key, todo in enumerate(todos):
                        todo_list += f"{key+1}. {todo.todo}\n"

                    messenger.send_message(todo_list, sender_phone_number)
                    return HttpResponse({'status': 'success'})
                todo = Todo.objects.create(user=conversation, todo=text_body[9:])
                todo.save()
                # send current todo list
                todos = Todo.objects.filter(user=conversation).order_by('-created_at')
                todo_list = "Your todo list:\n"
                for key, todo in enumerate(todos):
                    todo_list += f"{key+1}. {todo.todo}\n"

                messenger.send_message(todo_list, sender_phone_number)
                return HttpResponse({'status': 'success'})
            
            elif text_body[:9] == '/todoview':
                todos = Todo.objects.filter(user=conversation).order_by('-created_at')
                if len(todos) == 0:
                    messenger.send_message("You have no todo items.", sender_phone_number)
                    return HttpResponse({'status': 'success'})
                todo_list = "Your todo list:\n"
                for key, todo in enumerate(todos):
                    todo_list += f"{key+1}. {todo.todo}\n"
                messenger.send_message(todo_list, sender_phone_number)
                return HttpResponse({'status': 'success'})
            
            elif text_body[:11] == '/tododelete':
                if len(text_body) < 12:
                    messenger.send_message("Please provide a todo item number.", sender_phone_number)
                    return HttpResponse({'status': 'success'})
                try:
                    todo_number = int(text_body[12:])
                    todos = Todo.objects.filter(user=conversation).order_by('-created_at')
                    if len(todos) == 0:
                        messenger.send_message("You have no todo items.", sender_phone_number)
                        return HttpResponse({'status': 'success'})
                    if todo_number > len(todos):
                        messenger.send_message("Invalid todo item number.", sender_phone_number)
                        return HttpResponse({'status': 'success'})
                    todos[todo_number-1].delete()
                    messenger.send_message("Todo item deleted successfully!", sender_phone_number)
                    return HttpResponse({'status': 'success'})
                except ValueError:
                    messenger.send_message("Invalid todo item number.", sender_phone_number)
                    return HttpResponse({'status': 'success'})
            
            elif text_body[:10] == '/todoclear':
                todos = Todo.objects.filter(user=conversation).order_by('-created_at')
                if len(todos) == 0:
                    messenger.send_message("You have no todo items.", sender_phone_number)
                    return HttpResponse({'status': 'success'})
                for todo in todos:
                    todo.delete()
                messenger.send_message("Todo list cleared successfully!", sender_phone_number)
                return HttpResponse({'status': 'success'})

        # if prompt is about todo list, add todo list to context
        if 'todo' in text_body.lower():
            todos = Todo.objects.filter(user=conversation).order_by('-created_at')
            if len(todos) == 0:
                messenger.send_message("You have no todo items.", sender_phone_number)
                return HttpResponse({'status': 'success'})
            
            todo_list = "Your todo list:\n"
            for key, todo in enumerate(todos):
                todo_list += f"{key+1}. {todo.todo}\n"
            text_body += todo_list
            text_body += " if time is provided sort in that time order with optimal time lose"
        
        if conversation.token_count > TOKEN_LIMIT:
            text_body = "Sorry, you have exceeded the free limit allowed for this month."
            messenger.send_message(text_body, sender_phone_number)
            return HttpResponse({'status': 'success'})
        
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
        print(e)
        messenger.send_message("Sorry, I don't understand. Please try again.", sender_phone_number)
        return HttpResponse({'status': 'error', 'message': str(e)})

@api_view(['POST'])
def on_board_numbers(request):
    try:
        phone_number = request.data['phone_number']
        if not WhiteList.objects.filter(phone_number=phone_number).exists():
            WhiteList.objects.create(phone_number=phone_number)
            messenger = WhatsApp(
                os.getenv('WHATSAPP_API_KEY'),
                phone_number_id='128744806985877'
            )
            messenger.send_template("welcome", phone_number, lang="en", components=[])
            return HttpResponse({'status': 'success'})
        else:
            return HttpResponse({'status': 'success'})
    
    except Exception as e:
        return HttpResponse({'status': 'error', 'message': str(e)})
    
    
