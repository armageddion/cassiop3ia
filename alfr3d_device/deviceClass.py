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
logger = logging.getLogger("DevicesLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#handler = logging.FileHandler(os.path.join(CURRENT_PATH,"../log/devices.log"))
#handler = logging.FileHandler(os.path.join(CURRENT_PATH,"../log/total.log"))
handler = logging.FileHandler("/var/log/alfr3d/alfr3d.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

DATABASE_URL 	= os.environ.get('DATABASE_URL') or 'localhost'
DATABASE_NAME 	= os.environ.get('DATABASE_NAME') or 'cassiop3ia'
DATABASE_USER 	= os.environ.get('DATABASE_USER') or 'alfr3d'
DATABASE_PSWD 	= os.environ.get('DATABASE_PSWD') or 'alfr3d'
KAFKA_URL 		= os.environ.get('KAFKA_URL') or 'localhost:9092'

producer = None
try:
	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
except Exception as e:
	logger.error("Failed to connect to Kafka")
	sys.exit()

class Device:
	"""
		Device Class for Alfr3d Users' devices
	"""
	name = 'unknown'
	IP = '0.0.0.0'
	MAC = '00:00:00:00:00:00'
	state = 'offline'
	last_online = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
	environment = socket.gethostname()
	user = 'unknown'
	deviceType = 'guest'

	# mandatory to pass MAC for robustness
	def create(self, mac):
		"""
			Description:
				Add new device to the database with default parameters
		"""		
		logger.info("Creating a new device")
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * from device WHERE MAC = \""+mac+"\";")
		data = cursor.fetchone()

		if data:
			logger.warn("device already exists.... aborting")
			db.close()
			return False

		logger.info("Creating a new DB entry for device with MAC: "+mac)
		try:
			cursor.execute("SELECT * from states WHERE state = \""+self.state+"\";")
			data = cursor.fetchone()
			devstate = data[0]			
			cursor.execute("SELECT * from device_types WHERE type = \""+self.deviceType+"\";")
			data = cursor.fetchone()
			devtype = data[0]	
			cursor.execute("SELECT * from user WHERE username = \""+self.user+"\";")
			data = cursor.fetchone()
			usrid = data[0]
			cursor.execute("SELECT * from environment WHERE name = \""+self.environment+"\";")
			data = cursor.fetchone()
			envid = data[0]
			cursor.execute("INSERT INTO device(name, IP, MAC, last_online, state, device_type, user_id, environment_id) \
							VALUES (\""+self.name+"\", \""+self.IP+"\", \""+self.MAC+"\",  \""+self.last_online+"\",  \""+str(devstate)+"\",  \""+str(devtype)+"\",  \""+str(usrid)+"\",  \""+str(envid)+"\")")
			db.commit()
		except Exception as e:
			logger.error("Failed to create a new entry in the database")
			logger.error("Traceback: "+str(e))
			db.rollback()
			db.close()
			return False

		db.close()
		producer.send("speak", b"A new device was added to the database")
		return True

	def get(self,mac):
		"""
			Description:
				Find device from DB by MAC
		"""				
		logger.info("Looking for device with MAC: " + mac)
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * from device WHERE MAC = \""+mac+"\";")
		data = cursor.fetchone()

		if not data:
			logger.warning("Failed to find a device with MAC: " +mac+ " in the database")
			db.close()
			return False

		logger.info("Device found")
		logger.info(data)
		print(data)		#DEBUG

		self.name = data[1]
		self.IP = data[2]
		self.MAC = data[3]
		self.state = data[4]
		self.last_online = data[5]
		self.deviceType = data[6]
		self.user = data[7]
		self.environment = data[8]

		db.close()
		return True

	# update entire object in DB with latest values
	def update(self):
		"""
			Description:
				Update a Device in DB
		"""				
		logger.info("Updating device")
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * from device WHERE MAC = \""+self.MAC+"\";")
		data = cursor.fetchone()

		if not data:
			logger.warn("Failed to find a device with MAC: " +self.MAC+ " in the database")
			db.close()
			return False

		logger.info("Device found")
		logger.info(data)

		try:
			cursor.execute("UPDATE device SET name = \""+self.name+"\" WHERE MAC = \""+self.MAC+"\";")
			cursor.execute("UPDATE device SET IP = \""+self.IP+"\" WHERE MAC = \""+self.MAC+"\";")
			cursor.execute("UPDATE device SET last_online = \""+datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")+"\" WHERE MAC = \""+self.MAC+"\";")
			cursor.execute("SELECT * from states WHERE state = \"online\";")
			data = cursor.fetchone()
			stateid = data[0]
			cursor.execute("UPDATE device SET state = \""+str(stateid)+"\" WHERE MAC = \""+self.MAC+"\";")
			cursor.execute("SELECT * from environment WHERE name = \""+socket.gethostname()+"\";")
			data = cursor.fetchone()
			envid = data[0]
			cursor.execute("UPDATE device SET environment_id = \""+str(envid)+"\" WHERE MAC = \""+self.MAC+"\";")

			db.commit()
		except Exception as e:
			logger.error("Failed to update the database")
			logger.error("Traceback: "+str(e))
			db.rollback()
			db.close()
			return False

		db.close()
		logger.info("Updated device with MAC: " + self.MAC)
		return True

	# update entire object in DB with latest values
	def delete(self):
		"""
			Description:
				Delete a Device from DB
		"""				
		logger.info("Deleting device")
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * from device WHERE MAC = \""+self.MAC+"\";")
		data = cursor.fetchone()

		if not data:
			logger.warn("Failed to find a device with MAC: " +self.MAC+ " in the database")
			db.close()
			return False

		logger.info("Device found")
		#logger.info(data)

		try:
			cursor.execute("DELETE from device WHERE MAC = \""+self.MAC+"\";")
			db.commit()
		except Exception as e:
			logger.error("Failed to update the database")
			logger.error("Traceback: "+str(e))
			db.rollback()
			db.close()
			return False

		db.close()
		logger.info("Deleted device with MAC: " + self.MAC)
		return True		

def checkLAN():
	"""
		Description:
			This function checks who is on LAN
	"""
	logger.info("Checking localnet for online devices")

	# temporary file for storing results of network scan
	netclientsfile = os.path.join(os.path.join(os.getcwd(),os.path.dirname(__file__)),'netclients.tmp')	

	# find out which devices are online
	os.system("sudo arp-scan --localnet > "+ netclientsfile)

	netClients = open(netclientsfile, 'r')
	netClientsMACs = []
	netClientsIPs = []

	# parse MAC and IP addresses
	for line in netClients:
		print(line)
		if line.startswith("192.")==False and \
			line.startswith("10.")==False:
			continue
		ret = line.split('\t')
		# parse MAC addresses from arp-scan run
		netClientsMACs.append(ret[1])
		# parse IP addresses from arp-scan run
		netClientsIPs.append(ret[0])	

	# clean up and parse MAC&IP info
	netClients2 = {}
	for i in range(len(netClientsMACs)):
		netClients2[netClientsMACs[i]] = netClientsIPs[i]	

	# find who is online and
	# update DB status and last_online time
	for member in netClientsMACs:
		print(member)
		device = Device()
		exists = device.get(member)

		#if device exists in the DB update it
		if exists:
			logger.info("Updating device with MAC: "+member)
			device.IP = netClients2[member]
			device.update()

		#otherwise, create and add it.
		else:
			logger.info("Creating a new DB entry for device with MAC: "+member)
			device.IP = netClients2[member]
			device.MAC = member
			device.create(member)

	logger.info("Cleaning up temporary files")
	os.system('rm -rf '+netclientsfile)			

if __name__ == '__main__':
	# get all instructions from Kafka
	# topic: device
	try:
		consumer = KafkaConsumer('device', bootstrap_servers=KAFKA_URL)
	except Exception as e:
		logger.error("Failed to connect to Kafka device topic")
		producer.send("speak", b"Failed to connect to Kafka device topic")

	while True:
		for message in consumer:
			if message.value.decode('ascii') == "alfr3d-device.exit":
				logger.info("Received exit request. Stopping service.")
				sys.exit(1)
			if message.value.decode('ascii') == "scan net":
				checkLAN()

			time.sleep(10)
			
