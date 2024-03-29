#!/usr/bin/python

"""
	This is a utility for all Google APIs - gmail, calendar..
"""
# Copyright (c) 2010-2020 LiTtl3.1 Industries (LiTtl3.1).
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

from __future__ import print_function
import pickle
import os
import sys
import time
import datetime
import logging
import MySQLdb
from random import randint		# used for random number generator
from kafka import KafkaConsumer,KafkaProducer

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# current path from which python is executed
CURRENT_PATH = os.path.dirname(__file__)

# gmail unread count
UNREAD_COUNT = 0
UNREAD_COUNT_NEW = 0

# set up logging
logger = logging.getLogger("GoogleLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/var/log/alfr3d/alfr3d.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
		  'https://www.googleapis.com/auth/calendar.readonly']

CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__),'../conf/client_secret_google.json')
APPLICATION_NAME = 'Alfr3d'

DATABASE_URL 	= os.environ.get('DATABASE_URL') or 'localhost'
DATABASE_NAME 	= os.environ.get('DATABASE_NAME') or 'alfr3d'
DATABASE_USER 	= os.environ.get('DATABASE_USER') or 'alfr3d'
DATABASE_PSWD 	= os.environ.get('DATABASE_PSWD') or 'alfr3d'
KAFKA_URL 		= os.environ.get('KAFKA_URL') or 'localhost:9092'
try:
	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
except Exception as e:
	logger.error("Failed to connect to Kafka")
	sys.exit()

# calculate offset to UTC
#timezone_offset = "-04:00"
timezone_offset = "Z"
tz_off = datetime.datetime.now().hour-datetime.datetime.utcnow().hour
if tz_off < 0:
	timezone_offset = str(tz_off).zfill(3)+":00"
else:
	timezone_offset = "+"+str(tz_off).zfill(2)+":00"

def get_credentials_google():
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
		Credentials, the obtained credential.
	"""
	logger.info("Getting google credentials")
	credential_dir = os.path.join(os.path.dirname(__file__),'../conf')
	credentials = None
	# The file token.pickle stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.

	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	token_file = os.path.join(os.path.join(credential_dir,'token.pickle'))
	if os.path.exists(token_file):
		with open(token_file, 'rb') as token:
			credentials = pickle.load(token)

	# if there are no (valid) credentials available, let the user log in
	if not credentials or not credentials.valid:
		if credentials and credentials.expired and credentials.refresh_token:
			credentials.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
					CLIENT_SECRET_FILE, SCOPES)
			credentials = flow.run_local_server(port=0)
		# save credentials for the next run
		with open(token_file, 'wb') as token:
			pickle.dump(credentials, token)

	logger.info("Got google credentials")
	return credentials

def getUnreadCount():
	"""
		Description:
			This function provides the count of unread messages in my gmail inbox
		Returns:
			Intiger value of under emails
	"""
	logger.info("Checking gmail's unread count")
	global UNREAD_COUNT
	credentials = get_credentials_google()

	# Build the Gmail service from discovery
	gmail_service = build('gmail', 'v1', credentials=credentials)

	#print ("getting gmail data...")
	logger.info("Getting gmail data...")
	messages = gmail_service.users().messages().list(userId='me', q='label:inbox is:unread').execute()
	unread_msgs = messages[u'resultSizeEstimate']

	logger.info("Unread count - "+str(unread_msgs))

	if (unread_msgs > UNREAD_COUNT):
		logger.info("A new email has arrived...")

		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * FROM quips WHERE type = 'email';")
		quip_data = cursor.fetchall()

		quip = quip_data[randint(0,len(quip_data)-1)][2]

		producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
		producer.send("speak", bytes(quip,'utf-8'))
		# update ESL
		producer.send("danavation",key=b"emails",value=bytes(str(unread_msgs),'utf-8'))		

		UNREAD_COUNT = unread_msgs

	logger.info("Done checking email")
	return 

def morningMailCheck():
	"""
		Description:
			This function provides the count of unread messages to the morning routine
	"""	
	if UNREAD_COUNT > 0:
		producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
		producer.send('speak',bytes("while you were sleeping "+str(UNREAD_COUNT)+" emails flooded your inbox",'utf-8'))

def daytimeMailCheck():
	"""
		Description:
			This function provides the count of unread messages to user upon return home
	"""	
	if UNREAD_COUNT > 0:
		producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
		producer.send('speak',bytes("while you were away "+str(UNREAD_COUNT)+" emails flooded your inbox",'utf-8'))

def calendarTomorrow():
	logger.info("Getting tomorrow's events")
	credentials = get_credentials_google()

	calendar_service = build('calendar', 'v3', credentials = credentials)

	tomorrow = datetime.datetime.now().replace(hour=0,minute=0) + datetime.timedelta(days=1)
	tomorrow_night = tomorrow + datetime.timedelta(hours=23, minutes=59)
	tomorrow = tomorrow.isoformat()+timezone_offset
	tomorrow_night = tomorrow_night.isoformat()+timezone_offset

	#print('Getting the first event of tomorrow')
	logger.info('Getting the first event of tomorrow')
	eventsResult = calendar_service.events().list(
		calendarId='primary', timeMin=tomorrow, maxResults=1, timeMax=tomorrow_night, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])

	logger.info("Done getting tomorrow's calendar info")
	if not events:
		#print('No upcoming events found.')
		logger.info('No upcoming events found.')
		return False, None
	else:
		for event in events:
			start = event['start'].get('dateTime', event['start'].get('date'))
			#print(start, event['summary'])
			logger.info(str(start)+" : "+event['summary'])

			# since there is only one event, we're ok to do this
			#return True, event

			producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
			# send msg to the speaker
			greeting = "Tomorrow at "
			greeting += datetime.datetime.fromisoformat(start).hour
			greeting += " hours "
			if datetime.datetime.fromisoformat(start).minute != 0:
				greeting += "and "
				greeting += datetime.datetime.fromisoformat(start).minute
				greeting += " minutes "
			greeting += "you have "
			greeting += event['summary']
			producer.send("speak", greeting.encode('utf-8'))

		return True, events[0]

def calendarToday():
	logger.info("Getting today's calendar info")
	credentials = get_credentials_google()

	calendar_service = build('calendar', 'v3', credentials = credentials)

	today = datetime.datetime.now()
	tonight = datetime.datetime.now().replace(hour=23,minute=59)
	today = today.isoformat()+timezone_offset
	tonight = tonight.isoformat()+timezone_offset

	#print('Getting todays events')
	logger.info('Getting todays events')
	eventsResult = calendar_service.events().list(
		calendarId='primary', timeMin=today, maxResults=10, timeMax=tonight, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])

	if not events:
		logger.info('No upcoming events found.')
		return False, None

	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
	for event in events:
		start = event['start'].get('dateTime', event['start'].get('date'))
		logger.info(str(start)+" : "+event['summary'])

		# send msg to the speaker
		greeting = "at "
		greeting += datetime.datetime.fromisoformat(start).hour
		greeting += " hours "
		if datetime.datetime.fromisoformat(start).minute != 0:
			greeting += "and "
			greeting += datetime.datetime.fromisoformat(start).minute
			greeting += " minutes "
		greeting += "you have "
		greeting += event['summary']
		producer.send("speak", greeting.encode('utf-8'))

	logger.info("Done checking calendar")
	return True, events

# Main
if __name__ == '__main__':
	# get all instructions from Kafka
	# topic: google
	logger.info("Starting Alfr3d's google service")
	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])

	try:
		consumer = KafkaConsumer('google', bootstrap_servers=KAFKA_URL)
	except Exception as e:
		logger.error("Failed to connect to Kafka device topic")
		producer.send("speak", b"Failed to connect to Kafka device topic")

	while True:
		for message in consumer:
			if message.value.decode('ascii') == "alfr3d-google.exit":
				logger.info("Received exit request. Stopping service.")
				sys.exit(1)
			if message.value.decode('ascii') == "check gmail":
				getUnreadCount()
			if message.value.decode('ascii') == "morning mail":
				morningMailCheck()
			if message.value.decode('ascii') == "daytime mail":
				daytimeMailCheck()
			if message.value.decode('ascii') == "check calendar today":
				calendarToday()
			if message.value.decode('ascii') == "check calendar tomorrow":
				calendarTomorrow()

			time.sleep(10)