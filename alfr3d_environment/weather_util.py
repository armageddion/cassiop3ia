#!/usr/bin/python

"""
	This file is used for all weather related functions.
"""
# Copyright (c) 2010-2018 LiTtl3.1 Industries (LiTtl3.1).
# All rights reserved.
# This source code and any compilation or derivative thereof is the
# proprietary information of LiTtl3.1 Industries and is
# confidential in nature.
# Use of this source code is subject to the terms of the applicable
# LiTtl3.1 Industries license agreement.
#
# Under no circumstances is this component (or portion thereof) to be in any
# way affected or brought under the terms of any Open Source License without
# the prior express written permission of LiTtl3.1 Industries.
#
# For the purpose of this clause, the term Open Source Software/Component
# includes:
#
# (i) any software/component that requires as a condition of use, modification
#     and/or distribution of such software/component, that such software/
#     component:
#     a. be disclosed or distributed in source code form;
#     b. be licensed for the purpose of making derivative works; and/or
#     c. can be redistributed only free of enforceable intellectual property
#        rights (e.g. patents); and/or
# (ii) any software/component that contains, is derived in any manner (in whole
#      or in part) from, or statically or dynamically links against any
#      software/component specified under (i).
#

import json											# used to handle jsons returned from www
import os											# used to allow execution of system level commands
import math											# used to round numbers
import logging										# needed for useful logs
import socket
import MySQLdb
import sys
from datetime import datetime
from kafka import KafkaConsumer,KafkaProducer
from time import gmtime, strftime, localtime		# needed to obtain time
from urllib.request import urlopen					# used to make calls to www
from random import randint

# current path from which python is executed
CURRENT_PATH = os.path.dirname(__file__)

# set up logging
logger = logging.getLogger("WeatherLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#handler = logging.FileHandler(os.path.join(CURRENT_PATH,"../log/total.log"))
handler = logging.FileHandler("/var/log/alfr3d/alfr3d.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

# get main DB credentials
DATABASE_URL 	= os.environ.get('DATABASE_URL') or 'localhost'
DATABASE_NAME 	= os.environ.get('DATABASE_NAME') or 'alfr3d'
DATABASE_USER 	= os.environ.get('DATABASE_USER') or 'alfr3d'
DATABASE_PSWD 	= os.environ.get('DATABASE_PSWD') or 'alfr3d'
KAFKA_URL 		= os.environ.get('KAFKA_URL') or 'localhost:9092'

producer = None
try:
	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
except Exception as e:
	logger.error("Failed to connect to Kafka")
	sys.exit()

def getWeather(lat,lon):
	"""
		Description:
			This function gets weather data and parses it.
		Return:
			Boolean; True if successful, False if not.
	"""
	# connect to db
	db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
	cursor = db.cursor()

	logger.info("getting API key for openWeather from DB")
	cursor.execute("SELECT * from config WHERE name = \"openWeather\";")
	data = cursor.fetchone()	

	if data:
		logger.info("Found API key")
		#print(data) 	#DEBUG
		apikey = data[2]
	else:
		logger.warning("Failed to get API key for openWeather")  
		sys.exit(1)  

	weatherData = None

	url = "https://api.openweathermap.org/data/2.5/weather?lat="+str(lat)+"&lon="+str(lon)+'&units=metric&appid='+apikey
	try:
		weatherData = json.loads(urlopen(url).read().decode('utf-8'))
	except Exception as e:
		logger.error("Failed to get weather data\n")
		logger.error("URL: "+url)
		logger.error("Traceback "+str(e))
		return False, weatherData

	logger.info("got weather data")
	logger.info(weatherData)		# DEBUG

	#log current conditions
	logger.info("City:                           "+str(weatherData['name']))
	logger.info("Wind Speed:                     "+str(weatherData['wind']['speed']))
	logger.info("Atmospheric Pressure            "+str(weatherData['main']['pressure']))
	logger.info("Humidity                        "+str(weatherData['main']['humidity']))
	logger.info("Today's Low:                    "+str(weatherData['main']['temp_min']))
	logger.info("Today's High:                   "+str(weatherData['main']['temp_max']))
	logger.info("Description:                    "+str(weatherData['weather'][0]['description']))
	logger.info("Current Temperature:            "+str(weatherData['main']['temp']))
	logger.info("Sunrise:                        "+datetime.fromtimestamp(weatherData['sys']['sunrise']).strftime("%Y-%m-%d %H:%M:%S"))
	logger.info("Sunset:                         "+datetime.fromtimestamp(weatherData['sys']['sunset']).strftime("%Y-%m-%d %H:%M:%S"))

	logger.info("Parsed weather data\n")

	# Initialize the database
	logger.info("Updating weather data in DB")

	try:
		cursor.execute("UPDATE environment SET description = \""+str(weatherData['weather'][0]['description'])+"\" WHERE name = \""+socket.gethostname()+"\";")
		cursor.execute("UPDATE environment SET low = \""+str(int(weatherData['main']['temp_min']))+"\" WHERE name = \""+socket.gethostname()+"\";")
		cursor.execute("UPDATE environment SET high = \""+str(int(weatherData['main']['temp_max']))+"\" WHERE name = \""+socket.gethostname()+"\";")
		cursor.execute("UPDATE environment SET sunrise = \""+datetime.fromtimestamp(weatherData['sys']['sunrise']).strftime("%Y-%m-%d %H:%M:%S")+"\" WHERE name = \""+socket.gethostname()+"\";")
		cursor.execute("UPDATE environment SET sunset = \""+datetime.fromtimestamp(weatherData['sys']['sunset']).strftime("%Y-%m-%d %H:%M:%S")+"\" WHERE name = \""+socket.gethostname()+"\";")
		cursor.execute("UPDATE environment SET pressure = \""+str(int(weatherData['main']['pressure']))+"\" WHERE name = \""+socket.gethostname()+"\";")
		cursor.execute("UPDATE environment SET humidity = \""+str(int(weatherData['main']['humidity']))+"\" WHERE name = \""+socket.gethostname()+"\";")
		db.commit()
		logger.info("Environment weather info updated")
	except Exception as e:
		logger.error("Failed to update Environment database with weather info")
		logger.error("Traceback "+str(e))
		db.rollback()
		db.close()
		return False

	# update times for sunrise and sunset routines
	try:
		logger.info("Updating routines")
		cursor.execute("SELECT * FROM environment WHERE name = \""+socket.gethostname()+"\";")
		env_data = cursor.fetchone()
		env_id = env_data[0]
		cursor.execute("UPDATE routines SET time = \""+datetime.fromtimestamp(weatherData['sys']['sunrise']).strftime("%H:%M:%S")+"\" \
						WHERE name = \"Sunrise\" \
						and environment_id = \""+str(env_id)+"\";")
		cursor.execute("UPDATE routines SET time = \""+datetime.fromtimestamp(weatherData['sys']['sunset']).strftime("%H:%M:%S")+"\" \
						WHERE name = \"Sunset\" \
						and environment_id = \""+str(env_id)+"\";")
		cursor.execute("UPDATE routines SET triggered = 0 \
						WHERE name = \"Sunrise\" \
						and environment_id = \""+str(env_id)+"\";")
		cursor.execute("UPDATE routines SET triggered = 0 \
						WHERE name = \"Sunset\" \
						and environment_id = \""+str(env_id)+"\";")
		db.commit()
	except Exception as e:
		logger.error("Failed to update Routines database with daytime info")
		logger.error("Traceback "+str(e))
		db.rollback()
		db.close()
		return False

	db.close()

	# update ESL
	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
	producer.send("danavation",key=b"curr-temp",value=bytes(str(weatherData['main']['temp']),'utf-8'))

	# Subjective weather
	badDay = []
	badDay_data = []
	badDay.append(False)
	badDay.append(badDay_data)

	# if weather is bad...
	if weatherData['weather'][0]['main'] in ['Thunderstorm','Drizzle','Rain','Snow','Atmosphere','Exreeme']:
		badDay[0] = True
		badDay[1].append(weatherData['weather'][0]['description'])
	elif weatherData['main']['humidity'] > 80:
		badDay[0] = True
		badDay[1].append(weatherData['main']['humidity'])
	if weatherData['main']['temp_max'] > 27:
		badDay[0] = True
		badDay[1].append(weatherData['main']['temp_max'])
	elif weatherData['main']['temp_min'] < -5:
		badDay[0] = True
		badDay[1].append(weatherData['main']['temp_min'])
	if weatherData['wind']['speed'] > 10:
		badDay[0] = True
		badDay[1].append(weatherData['wind']['speed'])

	logger.info("Speaking weather data:\n")
	# Speak the weather data
	greeting = ''
	random = ["Weather patterns ", "My scans "]
	greeting += random[randint(0,len(random)-1)]

	# Time variables
	hour=strftime("%I", localtime())
	minute=strftime("%M", localtime())
	ampm=strftime("%p",localtime())

	if badDay[0]:
		producer.send("speak", b"I am afraid I don't have good news.")
		greeting+="indicate "

		for i in range(len(badDay[1])):
			if badDay[1][i] == weatherData['weather'][0]['description']:
				greeting += badDay[1][i]
			elif badDay[1][i] == weatherData['main']['humidity']:
				greeting += "humidity of a steam bath"
			elif badDay[1][i] == weatherData['main']['temp_max']:
				greeting += "it is too hot for my gentle circuits"
			elif badDay[1][i] == weatherData['main']['temp_min']:
				greeting += "it is catalysmically cold"
			elif badDay[1][i] == weatherData['wind']['speed']:
				greeting += "the wind will seriously ruin your hair"

			if len(badDay[1])>=2 and i < (len(badDay[1])-1):
				add = [' , also, ',' , and if that isn\'t enough, ', ' , and to make matters worse, ']
				greeting += add[randint(0,len(add)-1)]
			elif len(badDay[1])>2 and i == (len(badDay[1])-1):
				greeting += " , and on top of everything, "
			else:
				logger.info(greeting+"\n")
		producer.send("speak", greeting.encode('utf-8'))
	else:
		producer.send("speak", b"Weather today is just gorgeous!")
		greeting += "indicate "+weatherData['weather'][0]['description']
		producer.send("speak", greeting.encode('utf-8'))
		logger.info(greeting+"\n")

	producer.send("speak", ("Current temperature in "+weatherData['name']+" is "+str(int(weatherData['main']['temp']))+" degrees").encode('utf-8'))
	if (ampm=="AM" and int(hour)<10):
		producer.send("speak", ("Today\'s high is expected to be "+str(int(weatherData['main']['temp_max']))+" degrees").encode('utf-8'))

	logger.info("Spoke weather\n")
	return True

def KtoC(tempK):
	"""
		converts temperature in kelvin to celsius
	"""
	return math.trunc(int(tempK)-273.15)

# purely for testing purposes
if __name__ == "__main__":
	getWeather()
