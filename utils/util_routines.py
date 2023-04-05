#!/usr/bin/python

"""
	This is a utility for Routines for Alfr3d:
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

import os
import logging
import socket
import MySQLdb
from kafka import KafkaProducer
from datetime import datetime, timedelta

# set up logging
logger = logging.getLogger("RoutinesLog")
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

def checkRoutines():
	"""
		Description:
			Check if it is time to execute any routines and take action
			if needed...
	"""
	logger.info("Checking routines")	

	# fetch available Routines
	db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
	cursor = db.cursor()

	# get environemnt id of current environment
	cursor.execute("SELECT * from environment WHERE name = \""+socket.gethostname()+"\";")
	data = cursor.fetchone()
	env_id = data[0]

	cursor.execute("SELECT * from routines WHERE \
					environment_id = "+str(env_id)+"\
					and enabled = 1;")
	routines = cursor.fetchall()

	for routine in routines:
		logger.info("Checking "+routine[1]+" routine with time "+str(routine[2])+" and flag "+str(routine[4]))
		# get routine trigger time and flag
		routine_time = routine[2]
		routine_time = datetime.now().replace(hour=int(routine_time.seconds/3600), minute=int((routine_time.seconds//60)%60))
		routine_trigger = routine[4]
		cur_time = datetime.now()

		# does routine need to be triggered??
		if cur_time > routine_time and not routine_trigger:
			logger.info(routine[1] + " routine is being triggered")
			# set triggered flag = True
			try:
				logger.info("Resetting 'triggered' flag for "+routine[1]+" routine")
				cursor.execute("UPDATE routines SET triggered = 1 WHERE id = \""+str(routine[0])+"\";")
				db.commit()
			except Exception as  e:
				logger.error("Failed to update the database")
				logger.error("Traceback: "+str(e))
				db.rollback()
				db.close()
				return False

			logger.info("Sending routine to speaker")
			producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
			producer.send("speak", key = b'routine', value = bytes(routine[1],'utf-8'))

	db.close()
	return True	

def resetRoutines():
	"""
		Description:
			reset Triggerd flag for every Enabled routine
	"""
	logger.info("Resetting routine flags")
	db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
	cursor = db.cursor()

	# get environemnt id of current environment
	cursor.execute("SELECT * from environment WHERE name = \""+socket.gethostname()+"\";")
	data = cursor.fetchone()
	env_id = data[0]

	cursor.execute("SELECT * from routines WHERE \
					environment_id = "+str(env_id)+"\
					and enabled = True;")
	routines = cursor.fetchall()

	for routine in routines:
		# set Triggered flag to false
		try:
			logger.info("Resetting 'triggered' flag for "+routine[1]+" routine")
			cursor.execute("UPDATE routines SET triggered = 0 WHERE id = \""+str(routine[0])+"\";")
			db.commit()
		except Exception as  e:
			logger.error("Failed to update the database")
			logger.error("Traceback: "+str(e))
			db.rollback()
			db.close()
			return False

	return True

def checkMute():
	"""
		Description:
			checks what time it is and decides if B3na should be quiet
	"""
	logger.info("Checking if B3na should be mute")
	result = False

	db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
	cursor = db.cursor()

	# get environemnt id of current environment
	cursor.execute("SELECT * from environment WHERE name = \""+socket.gethostname()+"\";")
	data = cursor.fetchone()
	if data:
		env_id = data[0]

	cursor.execute("SELECT * from routines WHERE \
					environment_id = "+str(env_id)+"\
					and name = \"Morning\";")
	morning = cursor.fetchone()
	morning_time = morning[2]

	cursor.execute("SELECT * from routines WHERE \
					environment_id = "+str(env_id)+"\
					and name = \"Bedtime\";")
	bed = cursor.fetchone()
	bed_time = bed[2]

	cur_time = datetime.now()
	mor_time = datetime.now().replace(hour=int(morning_time.seconds/3600), minute=int((morning_time.seconds//60)%60))
	end_time = datetime.now().replace(hour=int(bed_time.seconds/3600), minute=int((bed_time.seconds//60)%60))

	# only speak between morning alarm and bedtime alarm...
	if cur_time > mor_time and cur_time < end_time:
		logger.info("Alfr3d is free to speak during this time of day")
	else:
		logger.info("Alfr3d should be quiet while we're sleeping")
		result = True

	# get state id of status "online"
	cursor.execute("SELECT * from states WHERE state = \"online\";")
	data = cursor.fetchone()
	if data:
		state_id = data[0]

	# get all user types which are god or owner type
	cursor.execute("SELECT * from user_types WHERE type = \"owner\" or \
												   type = \"technoking\" or \
												   type = \"resident\";")
	data = cursor.fetchall()
	types = []
	for item in data:
		types.append(item[0])

	# see if any users worth speaking to are online
	cursor.execute("SELECT * from user WHERE state = \""+str(state_id)+"\" and \
											  (type = \""+str(types[0])+"\" or \
											   type = \""+str(types[1])+"\" or \
											   type = \""+str(types[2])+"\");")
	data = cursor.fetchall()

	if not data:
		logger.info("Alfr3d should be quiet when no worthy ears are around")
		result = True
	else:
		logger.info("Alfr3d has worthy listeners:")
		for user in data:
			logger.info("    - "+user[1])

	if result:
		logger.info("Alfr3d is to be quiet")
	else:
		logger.info("Alfr3d is free to speak")

	return result
