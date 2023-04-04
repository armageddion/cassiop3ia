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
from kafka import KafkaConsumer,KafkaProducer

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# current path from which python is executed
CURRENT_PATH = os.path.dirname(__file__)

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

KAFKA_URL = os.environ.get('KAFKA_URL') or 'localhost:9092'
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
	credentials = get_credentials_google()

	# Build the Gmail service from discovery
	gmail_service = build('gmail', 'v1', credentials=credentials)

	#print ("getting gmail data...")
	logger.info("Getting gmail data...")
	messages = gmail_service.users().messages().list(userId='me', q='label:inbox is:unread').execute()
	unread_msgs = messages[u'resultSizeEstimate']

	return unread_msgs

def calendarTomorrow():
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

	if not events:
		#print('No upcoming events found.')
		logger.info('No upcoming events found.')
		return False, None
	else:
		return True, events[0]

	# for event in events:
	# 	start = event['start'].get('dateTime', event['start'].get('date'))
	# 	print(start, event['summary'])

	# 	# since there is only one event, we're ok to do this
	# 	return event

def calendarToday():
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

	# for event in events:
	# 	start = event['start'].get('dateTime', event['start'].get('date'))
	# 	print(start, event['summary'])

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
			if message.value.decode('ascii') == "check calendar today":
				calendarToday()
			if message.value.decode('ascii') == "check calendar tomorrow":
				calendarTomorrow()

			time.sleep(10)