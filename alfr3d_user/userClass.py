#!/usr/bin/python

"""
	This is the utility to manage all devices that Alfr3d
	is aware of. 
"""
# Copyright (c) 2010-2022 LiTtl3.1 Industries (LiTtl3.1).
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
#	 and/or distribution of such software/component, that such software/
#	 component:
#	 a. be disclosed or distributed in source code form;
#	 b. be licensed for the purpose of making derivative works; and/or
#	 c. can be redistributed only free of enforceable intellectual property
#		rights (e.g. patents); and/or
# (ii) any software/component that contains, is derived in any manner (in whole
#	  or in part) from, or statically or dynamically links against any
#	  software/component specified under (i).

# IMPORTS
import os
import sys
import time
import logging
import socket
#import ConfigParser
import MySQLdb
from kafka import KafkaConsumer,KafkaProducer
from datetime import datetime, timedelta

# current path from which python is executed
CURRENT_PATH = os.path.dirname(__file__)

# set up logging
logger = logging.getLogger("UsersLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/var/log/alfr3d/alfr3d.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

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

class User:
	"""
		User Class for Alfr3d Users
	"""
	name = 'unknown'
	state = 'offline'
	last_online = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
	userType = 'guest'

	def create(self):
		logger.info("Creating a new user")
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * from user WHERE username = \""+self.name+"\";")
		data = cursor.fetchone()

		try:
			exists = self.get(self.name)
		except:
			exists = False
		if exists:
			logger.error("User with that name already exists")
			db.close()
			return False

		logger.info("Creating a new DB entry for user: "+self.name)
		try:
			cursor.execute("SELECT * from states WHERE state = \"offline\";")
			data = cursor.fetchone()
			usrstate = data[0]
			cursor.execute("SELECT * from user_types WHERE type = \"guest\";")
			data = cursor.fetchone()
			usrtype = data[0]
			cursor.execute("SELECT * from environment WHERE name = \""+socket.gethostname()+"\";")
			data = cursor.fetchone()
			envid = data[0]			
			cursor.execute("INSERT INTO user(username, last_online, state, type, environment_id) \
							VALUES (\""+self.name+"\", \""+self.last_online+"\",\""+str(usrstate)+"\",\""+str(usrtype)+"\",\""+str(envid)+"\");")
			db.commit()
		except Exception as  e:
			logger.error("Failed to create a new entry in the database")
			logger.error("Traceback: "+str(e))
			db.rollback()
			db.close()
			return False

		db.close()
		producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
		producer.send("speak", b"A new user has been added to the database")
		return True

	def get(self):
		"""
            Description:
                Find a user from DB by name
        """
		logger.info("Looking for user: " + self.name)
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * from user WHERE username = \""+self.name+"\";")
		data = cursor.fetchone()

		if not data:
			logger.warn("Failed to find user: " +self.name+ " in the database")
			db.close()
			return False

		#print data
		self.name = data[1]
		self.state = data[7]
		self.last_online = data[6]
		self.userType = data[8]

		db.close()
		return True

	def update(self):
		"""
            Description:
                Update a User in DB
        """
		logger.info("Updating user: " + self.name)
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * from user WHERE username = \""+self.name+"\";")
		data = cursor.fetchone()

		if not data:
			logger.warn("Failed to find user with username: " +self.name+ " in the database")
			db.close()
			return False

		logger.info("User found")
		logger.info(data)

		try:
			cursor.execute("UPDATE user SET username = \" "+self.name+"\" WHERE username = \""+self.name+"\";")
			cursor.execute("UPDATE user SET last_online = \""+datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")+"\" WHERE username = \""+self.name+"\";")
			cursor.execute("SELECT * from states WHERE state = \"online\";")
			data = cursor.fetchone()
			stateid = data[0]
			cursor.execute("UPDATE user SET state = "+str(stateid)+" WHERE username = \""+self.name+"\";")
			cursor.execute("SELECT * from environment WHERE name = \""+socket.gethostname()+"\";")
			data = cursor.fetchone()
			envid = data[0]
			cursor.execute("UPDATE user SET environment_id = \""+str(envid)+"\" WHERE username = \""+self.name+"\";")

			db.commit()
		except Exception as  e:
			logger.error("Failed to update the database")
			logger.error("Traceback: "+str(e))
			db.rollback()
			db.close()
			return False

		db.close()
		logger.info("Updated user: " + self.name)
		return True
	
	def delete(self):
		"""
            Description:
                Delete a User from DB
        """
		logger.info("Deleting a User")
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * from user WHERE username = \""+self.name+"\";")
		data = cursor.fetchone()

		if not data:
			logger.warn("Failed to find user with username: " +self.name+ " in the database")
			db.close()
			return False

		logger.info("User found")

		try:
			cursor.execute("DELETE from user WHERE username = \""+self.name+"\";")
			db.commit()
		except Exception as e:
			logger.error("Failed to update the database")
			logger.error("Traceback: "+str(e))
			db.rollback()
			db.close()
			return False

		db.close()
		logger.info("Deleted user with username: " +self.name)
		return True			

# refreshes state and last_online for all users
def refreshAll():
	logger.info("Refreshing users")

	db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
	cursor = db.cursor()
	cursor.execute("SELECT * from user;")
	data = cursor.fetchall()

	# figure out device types
	dev_types = {}
	cursor.execute("SELECT * FROM device_types;")
	types = cursor.fetchall()
	for type in types:
		dev_types[type[1]]=type[0]

	# figure out states
	stat = {}
	cursor.execute("SELECT * FROM states;")
	states = cursor.fetchall()
	for state in states:
		stat[state[1]]=state[0]

	# figure out environments
	cursor.execute("SELECT * FROM environment WHERE name = \""+socket.gethostname()+"\";")
	env_data = cursor.fetchone()
	if env_data:
		env = env_data[1]
		env_id = env_data[0]

	# get all devices for that user
	for user in data:
		print(data) 	# DEBUG
		logger.info("refreshing user "+user[1])
		last_online=user[3]

		# get all devices for that user
		try:
			logger.info("Fetching user devices")
			cursor.execute("SELECT * FROM device WHERE user_id = "+str(user[0])+" and device_type != "+str(dev_types['HW'])+";")
			devices = cursor.fetchall()
			for device in devices:
				# update last_online time for that user
				if device[5] > user[6]:
					logger.info("Updating user "+user[1])
					cursor.execute("UPDATE user SET last_online = \""+str(device[5])+"\" WHERE username = \""+user[1]+"\";")
					cursor.execute("UPDATE user set environment_id = \""+str(env_id)+"\" WHERE username = \""+user[1]+"\";")
					db.commit()
					last_online = device[5]
		except Exception as  e:
			logger.error("Failed to update the database")
			logger.error("Traceback: "+str(e))
			db.rollback()
			continue

		# this time only needs to account for one cycle of alfr3d's standard loop
		# or a few... in case one of them misses it :)
		try:
			time_now = datetime.utcnow()
			delta = time_now-last_online
		except Exception as  e:
			logger.error("Failed to figure out the timedelta")
			delta = timedelta(minutes=60)

		if delta < timedelta(minutes=30):	# 30 minutes
			logger.info("User is online")	#DEBUG
			if user[5] == stat["offline"]:
				logger.info(user[1]+" just came online")
				producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
				producer.send("speak", bytes(user[1]+" just came online",'utf-8')) ## temp until greeting
				# welcome the user
				cursor.execute("UPDATE user SET state = "+str(stat['online'])+" WHERE username = \""+user[1]+"\";")
				#nighttime_auto()	# turn on the lights
				# speak welcome
		else:
			logger.info("User is offline")	#DEBUG
			if user[5] == stat["online"]:
				logger.info(user[1]+" went offline")
				cursor.execute("UPDATE user SET state = "+str(stat['offline'])+" WHERE username = \""+user[1]+"\";")
				#nighttime_auto()			# this is only useful when alfr3d is left all alone

		try:
			db.commit()
		except Exception as  e:
			logger.error("Failed to update the database")
			logger.error("Traceback: "+str(e))
			db.rollback()
			db.close()
			continue

	db.close()
	return True
	
if __name__ == '__main__':
	# get all instructions from Kafka
	# topic: user
	try:
		consumer = KafkaConsumer('user', bootstrap_servers=KAFKA_URL)
	except Exception as e:
		logger.error("Failed to connect to Kafka user topic")
		producer.send("speak", b"Failed to connect to Kafka user topic")

	while True:
		for message in consumer:
			if message.value.decode('ascii') == "alfr3d-user.exit":
				logger.info("Received exit request. Stopping service.")
				sys.exit(1)
			if message.value.decode('ascii') == "refresh-all":
				refreshAll()
			if message.key.decode('ascii') == "create":
				usr = User()
				usr.name = message.value.decode('ascii')
				usr.create()
			if message.key.decode('ascii') == "delete":
				usr = User()
				usr.name = message.value.decode('ascii')
				usr.delete()	

			time.sleep(10)
			

