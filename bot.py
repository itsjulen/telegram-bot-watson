import requests, json, logging 
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from emoji import emojize
import os
import cloudinary.uploader
import telegram
import keys

cloudinary.config(
  cloud_name = keys.cloud_name,  
  api_key = keys.api_key,  
  api_secret = keys.api_secret  
)

'''
requests, json, logging Suelen venir instalados
telegram.ext https://github.com/python-telegram-bot/python-telegram-bot
emoji https://github.com/carpedm20/emoji
bs4 pip install beautifulsoup4
selenium pip install selenium

'''
URL_WATSON = "https://bot-cs.eu-gb.mybluemix.net/"
URL = "https://api.telegram.org/bot{}/".format(keys.TOKEN)

updater = Updater(token=keys.TOKEN)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(bot, update):
	mensaje = "¡Me alegro de conocerte! Soy CatSon, un bot que utiliza la tecnología de Watson para ayudarte :smile: \n\n ¿Qué puedo hacer?\n - Utiliza /tiempo seguido de un lugar para obtener el tiempo actual\n - Utiliza /traducir y una frase en castellano e intentaré traducírtela a inglés\n - Escríbeme algo y lo responderé (puedo contar chistes)\n - Utiliza /decir y una frase en castellano y te mandaré un audio diciéndolo\n - Utiliza /tono seguido de una frase e intentaré adivinar el tono en el que la dices\n - Mándame una foto y hare un reconocimiento visual (facial o de objetos)"
	bot.send_message(chat_id=update.message.chat_id, text=emojize(mensaje, use_aliases=True))
	
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def assistant(bot, update):
	mensaje = update.message.text
	r = requests.post(url = URL_WATSON + "assistant", data = json.dumps({'body':mensaje}))
	bot.send_message(chat_id=update.message.chat_id, text=r.text)
	
assistant_handler = MessageHandler(Filters.text, assistant)
dispatcher.add_handler(assistant_handler)

def translator(bot, update):
	update.message.text = update.message.text.split(' ', 1)[1]
	mensaje = update.message.text
	r = requests.post(url = URL_WATSON+"translator", data = json.dumps({'body':mensaje}))
	bot.send_message(chat_id=update.message.chat_id, text=r.text)
	
translator_handler = CommandHandler('traducir', translator)
dispatcher.add_handler(translator_handler)

def transformar(tone):
	if tone=="Anger":
		return "Enfado"
	elif tone=="Fear":
		return "Miedo"
	elif tone=="Joy":
		return "Alegría"
	elif tone=="Sadness":
		return "Tristeza"
	elif tone=="Analytical":
		return "Analítico"
	elif tone=="Confident":
		return "Seguro"
	elif tone=="Tentative":
		return "Tentativo"
	else:
		return tone
	
def tone(bot, update):
	update.message.text = update.message.text.split(' ', 1)[1]
	mensaje = update.message.text
	r = requests.post(url = URL_WATSON+"tone", data = json.dumps({'body':mensaje}))
	r = json.loads(r.text)
	tones = r['document_tone']['tones']
	mensaje = ""
	for tone in tones:
		mensaje = mensaje + "Creo que el tono es " + transformar(tone['tone_name']) + " (" + str(int(100*tone['score'])) + "%)\n"
	if mensaje=="":
		mensaje = "El tono de la frase es neutro"
	bot.send_message(chat_id=update.message.chat_id, text=mensaje)
	
tone_handler = CommandHandler('tono', tone)
dispatcher.add_handler(tone_handler)

def tiempo(bot, update):
	update.message.text = update.message.text.split(' ', 1)[1]
	bot.send_message(chat_id=update.message.chat_id, text="Voy a buscar, un momento")
	location_api_url = "https://www.mapquestapi.com/geocoding/v1/batch?key="+keys.location_key+"&location=" + update.message.text
	location_r  = requests.get(url = location_api_url)
	location_r = json.loads(location_r.text)
	location = str(location_r['results'][0]['locations'][0]['latLng']['lat']) + "," + str(location_r['results'][0]['locations'][0]['latLng']['lng'])
	r = requests.post(url = URL_WATSON+"weather", data = json.dumps({'body':location}))
	weather_data = json.loads(r.text)
	mensaje = "Tiempo actual en " + weather_data['obs_name'] + ":\n" + " - Temperatura: " + str(weather_data['temp']) + "ºC\n - Estado: " + weather_data['wx_phrase'] + "\n - Índice UV: " + str(weather_data['uv_index'])
	bot.send_message(chat_id=update.message.chat_id, text=mensaje)

	
tiempo_handler = CommandHandler('tiempo', tiempo)
dispatcher.add_handler(tiempo_handler)

def tts(bot, update):
	update.message.text = update.message.text.split(' ', 1)[1]
	mensaje = update.message.text	
	mensaje = mensaje.lower().replace('julen','yulen')
	tmp_f = open('tmp.ogg', 'wb+')
	
	r = requests.post(url = URL_WATSON+"tts", data = json.dumps({'body':mensaje}))
	tmp_f.write(r.content)
	tmp_f.close()
	bot.sendAudio(update.message.chat_id, audio=open('tmp.ogg', 'rb'))
	os.remove('tmp.ogg')
	
tts_handler = CommandHandler('decir', tts)
dispatcher.add_handler(tts_handler)
tts_handler2 = CommandHandler('d', tts)
dispatcher.add_handler(tts_handler2)

def unknown(bot, update):
	mensaje = emojize("No conozco ese comando  :sweat_smile:", use_aliases=True)
	bot.send_message(chat_id=update.message.chat_id, text=mensaje)
	
unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

def faceRecognition(bot, update):
	name = str(update.message.chat_id) + ".jpg"
	url_photo = cloudinary.uploader.upload(name)
	mensaje = url_photo['url']
	r = requests.post(url = URL_WATSON+"visual", data = json.dumps({'body':mensaje}))
	cloudinary.api.delete_resources([url_photo['public_id']])
	respuesta = json.loads(r.text)
	faces = respuesta['images'][0]['faces']
	i = 1
	for face in faces:
		mensaje = "Cara "+str(i)+":\n"
		i+=1
		mensaje = mensaje+" - Edad aproximada entre "+str(face['age']['min'])+" y "+str(face['age']['max'])+" años con una tasa de acierto del "+str(int(100*face['age']['score']))+"%\n"
		genero = face['gender']['gender']
		if genero == "MALE":
			mensaje = mensaje+" - Género masculino con una tasa de acierto del "+str(int(100*face['gender']['score']))+"%"
		else:
			mensaje = mensaje+" - Género femenino con una tasa de acierto del "+str(int(100*face['gender']['score']))+"%"
		bot.send_message(chat_id=update.message.chat_id, text=mensaje)
	os.remove(name)
	
def objectRecognition(bot, update):
	name = str(update.message.chat_id) + ".jpg"
	url_photo = cloudinary.uploader.upload(name)
	mensaje = url_photo['url']
	r = requests.post(url = URL_WATSON+"object", data = json.dumps({'body':mensaje}))
	cloudinary.api.delete_resources([url_photo['public_id']])
	respuesta = json.loads(r.text)
	objetos = respuesta['images'][0]['classifiers'][0]['classes']
	mensaje = "He encontrado esto en la imagen:"
	for objeto in objetos:
		mensaje = mensaje + "\n - " + objeto['class'].capitalize() + " (" + str(int(100*objeto['score'])) + "% de acierto)"
	bot.send_message(chat_id=update.message.chat_id, text=mensaje)
	os.remove(name)
	
def visualRecognition(bot, update):
	user = update.message.from_user
	photo_file = bot.get_file(update.message.photo[-1].file_id)
	name = str(update.message.chat_id) + ".jpg"
	photo_file.download(name)
	keyboard = [[telegram.InlineKeyboardButton("Reconocimiento facial", callback_data='1')], [telegram.InlineKeyboardButton("Reconocimiento de objetos", callback_data='2')]]
	reply_markup = telegram.InlineKeyboardMarkup(keyboard)
	update.message.reply_text('Elige el tipo de reconocimiento que quieres aplicar a la imagen', reply_markup=reply_markup)
	
def button(bot, update):
	query = update.callback_query
	if query.data == "1":
		bot.edit_message_text(text="Haré un reconocimiento facial, dame un momento...", chat_id=query.message.chat_id, message_id=query.message.message_id)
		faceRecognition(bot, query)
	else:
		bot.edit_message_text(text="Haré un reconocimiento de objetos, a ver qué veo...", chat_id=query.message.chat_id, message_id=query.message.message_id)
		objectRecognition(bot, query)


photo_handler = MessageHandler(Filters.photo, visualRecognition)
dispatcher.add_handler(photo_handler)
dispatcher.add_handler(CallbackQueryHandler(button))

print("Añadidos todos los handler")
updater.start_polling()
print("Bot inicializado")
updater.idle()