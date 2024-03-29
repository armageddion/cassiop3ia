#!/usr/bin/python

"""
	This file is used for all Lighting related functions.
"""
# Copyright (c) 2010-2023 LiTtl3.1 Industries (LiTtl3.1).
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

# imports
import requests
import os
import sys
import time
import logging
import MySQLdb
from kafka import KafkaConsumer, KafkaProducer

# set up logging
logger = logging.getLogger("LightingLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/var/log/alfr3d/alfr3d.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

# get main DB credentials
DATABASE_URL 	= os.environ.get('DATABASE_URL') or 'localhost'
DATABASE_NAME 	= os.environ.get('DATABASE_NAME') or 'alfr3d'
DATABASE_USER 	= os.environ.get('DATABASE_USER') or 'alfr3d'
DATABASE_PSWD 	= os.environ.get('DATABASE_PSWD') or 'alfr3d'
KAFKA_URL 		= os.environ.get('KAFKA_URL') or 'localhost:9092'

# this var will be used to handle device type ID for all lights
logger.info("Fetching Device Type ID")
db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
cursor = db.cursor()
cursor.execute("SELECT * from device_types WHERE type = \"light\"")
data = cursor.fetchone()	
LIGHTS_DEV_TYPE = data[0]

# Turn all lights on
def lights_on():
	"""
		Description:
			This function turns all available lights on
	"""
	logger.info("Turning all the lights ON")
	db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
	cursor = db.cursor()
	# SELECT * FROM DEVICE where type = Light or something like that
	cursor.execute("SELECT * from device WHERE device_type = "+str(LIGHTS_DEV_TYPE)+"")
	for light in cursor.fetchall():
		ip = light['IP']
		url=ip+"/on"
		response = requests.get(url)        
		if response.status_code != 200:
			logger.error("Failed to turn on light: "+light['name'])	# TODO make better
			print(response)     # DEBUG
		logger.info("Turned on light: "+light['name'])     
		# check response for error and log result
	return

# Turn all lights off
def lights_off():
	"""
		Description:
			This function turns all available lights off
	"""
	logger.info("Turning all the lights OFF")
	db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
	cursor = db.cursor()
	# SELECT * FROM DEVICE where type = Light or something like that
	cursor.execute("SELECT * from device WHERE device_type = "+str(LIGHTS_DEV_TYPE)+"")
	for light in cursor.fetchall():
		ip = light['IP']
		url=ip+"/off"    
		response = requests.get(url)
		if response.status_code != 200:
			logger.error("Failed to turn off light: "+light['name'])	# TODO make better
			print(response)     # DEBUG
		logger.info("Turned off light: "+light['name'])
		# check response for error and log result
	return

# Turn specific light on 
def light_on(light=None):
	"""
		Description:
			This function turns a specific light on
	"""
	if light == None:
		logger.info("Target light not specified")
		return
	
	logger.info("Turning light "+light+ " ON")
	db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
	cursor = db.cursor()
	# SELECT * FROM DEVICE where name = Light or something like that
	cursor.execute("SELECT * from device WHERE device_type = "+str(LIGHTS_DEV_TYPE)+"")
	data = cursor.fetchone()
	ip = data['IP']
	url=ip+"/on"    
	response = requests.get(url)
	if response.status_code != 200:
		logger.error("Failed to turn on light: "+light['name'])	# TODO make better
		print(response)     # DEBUG
	# check response for error and log result
	pass

# Turn specific light off
def light_off(light=None):
	"""
		Description:
			This function turns a specific light off
	"""
	if light == None:
		logger.info("Target light not specified")
		return
	
	logger.info("Turning light "+light+ " OFF")
	db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
	cursor = db.cursor()
	# SELECT * FROM DEVICE where name = Light or something like that
	cursor.execute("SELECT * from device WHERE device_type = "+str(LIGHTS_DEV_TYPE)+"")
	data = cursor.fetchone()
	ip = data['IP']
	url=ip+"/off"    
	response = requests.get(url)
	if response.status_code != 200:
		logger.error("Failed to turn off light: "+light['name'])	# TODO make better
		print(response)     # DEBUG
	# check response for error and log result
	pass

if __name__ == "__main__":
	# get all instructions from Kafka
	# topic: lighting
	logger.info("Starting Alfr3d's lighting utility")
	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])

	try:
		consumer = KafkaConsumer('lighting', bootstrap_servers='localhost:9092')
	except Exception as e:
		logger.error("Failed to connect to Kafka lighting topic")
		producer.send("speak", b"Failed to connect to Kafka lighting topic")

	while True:
		for message in consumer:
			if message.value.decode('ascii') == "alfr3d-lights.exit":
				logger.info("Received exit request. Stopping service.")
				sys.exit()
			if message.value.decode('ascii') == "lighting check":
				logger.info("Testing all lighting systems")
				lights_on()
				time.sleep(10)  # wait 10 seconds
				lights_off()
			
			if message.key.decode('ascii') == "light_on":
				msg = message.value.decode('ascii')
				light_on(msg)
			elif message.key.decode('ascii') == "light_off":
				msg = message.value.decode('ascii')
				light_off(msg)


			time.sleep(10)