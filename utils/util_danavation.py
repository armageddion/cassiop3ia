#!/usr/bin/python

"""
	This is the utility to manage all ESLs from Danavation
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
# IMPORTS
import os
import socket
import sys
import time
import rsa
import json
import base64
import logging
import requests
import MySQLdb
from kafka import KafkaConsumer,KafkaProducer
from datetime import datetime, timedelta

# set up logging
logger = logging.getLogger("DanavationLog")
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

class DanavationServer:
	def __init__ (self, server_addr, server_acc, server_paswd, stores,server_agent,server_merch):
		self.server_address = "http://"+server_addr+":9999"
		self.server_agent = server_agent
		self.server_merch = server_merch
		self.server_account = server_acc
		self.server_password = server_paswd
		self.server_encpass = ""
		self.stores = stores
		self.creds = None

		self.server_encpass = self.encrypt()

	def get_pub_key(self):
		"""
			get server public key
		"""
		logger.info("Getting public key")
		url = self.server_address+"/user/getErpPublicKey?="
		r = requests.get(url=url)
		response = r.json()
		key = response["data"]
		return key        

	def encrypt(self):
		"""
			encrypt sunparl password
		"""
		key=self.get_pub_key()
		logger.info("Encrypting password")
		msg = self.server_password
		#print("message: "+msg)
		#print("key: "+key)

		pubkey = base64.b64decode(key)
		publicKey = rsa.PublicKey.load_pkcs1_openssl_der(pubkey)

		#print(publicKey)
		emsg = rsa.encrypt(msg.encode(), publicKey)
		ret = base64.b64encode(emsg)
		#print(ret)
		#print(ret.decode())
		return ret.decode()

	def login(self):
		logger.info("Logging in:")
		logger.info("Server: "+self.server_address+" , account: "+self.server_account)
		req_login = {
			"account":self.server_account,
			"loginType":3,
			"password":self.server_encpass
		}
		headers = {'content-type':'application/json', 'Language':'en'}
		url = self.server_address + '/user/login'
		r = requests.post(url = url, data = json.dumps(req_login), headers = headers)

		response = r.json()
		if response['code'] == 14014:
			print('got token')
			logger.info("Got token")
		else:
			print(response)
			logger.error("Failed to log into server")
			logger.error(response)
			return False

		self.creds = response['data']['token']
		logger.info("All logged in...")

		return True
	
	def update_esls(self):
		"""
			Description:
				Get all the info that needs to be displayed
				and push it to ESLs
		"""
		# connect to DB
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()
		cursor.execute("SELECT * from environment WHERE name = \""+socket.gethostname()+"\";")
		data = cursor.fetchone()
		# get today's low
		today_low = data[8]
		# get today's high
		today_high = data[9]
		# get today's DOW
		dow = datetime.today().weekday()
		if dow == 0:
			dow = "Ponedeljak"
		elif dow == 1:
			dow = "Utorak"
		elif dow == 2:
			dow = "Sreda"
		elif dow == 3:
			dow = "Cetvrtak"
		elif dow == 4:
			dow = "Petak"
		elif dow == 5:
			dow = "Subota"
		elif dow == 6:
			dow = "Nedelja"

		# get today's sunrise
		sunrise = data[11]
		# get today's sunset
		sunset = data[12]
		# get today's pressure
		pressure = data[13]
		# get today's humidity
		humidity = data[14]

		if self.login():
			# actually update data
			headers = headers = {'content-type':'application/json', 'Language':'en','Authorization':self.creds}
			url = self.server_address+'/item/batchImportItem'
			payload = {
				"agencyId": self.server_agent,
				"merchantId": self.server_merch,
				"storeId": self.stores[0],
				"itemList": [
				{
					"attrCategory": "default",
					"attrName": "default",
					"barCode": "133701",
					"stock1": today_low,
					"stock3": today_high,
					"productArea": dow,
					"custFeature1": str(sunrise),
					"custFeature2": str(sunset),
					"custFeature3": pressure,
					"custFeature4": humidity
				}]
			}
			r = requests.post(url = url, data=json.dumps(payload), headers = headers)
			#print(r.json())     # DEBUG
			res = r.json()	
			if res['success']:
				return True
			else:
				return False			

	def update_emails(self,msg):
		if self.login():
			# actually update data
			headers = headers = {'content-type':'application/json', 'Language':'en','Authorization':self.creds}
			url = self.server_address+'/item/batchImportItem'
			payload = {
				"agencyId": self.server_agent,
				"merchantId": self.server_merch,
				"storeId": self.stores[0],
				"itemList": [
				{
					"attrCategory": "default",
					"attrName": "tech_test",
					"barCode": "133702",
					"stock1": str(msg)
				}]
			}
			r = requests.post(url = url, data=json.dumps(payload), headers = headers)
			#print(r.json())     # DEBUG
			res = r.json()	
			if res['success']:
				return True
			else:
				return False	

	def update_temp(self,msg):
		if self.login():
			# actually update data
			headers = headers = {'content-type':'application/json', 'Language':'en','Authorization':self.creds}
			url = self.server_address+'/item/batchImportItem'
			payload = {
				"agencyId": self.server_agent,
				"merchantId": self.server_merch,
				"storeId": self.stores[0],
				"itemList": [
				{
					"attrCategory": "default",
					"attrName": "default",
					"barCode": "133701",
					"stock2": str(msg)
				}]
			}
			r = requests.post(url = url, data=json.dumps(payload), headers = headers)
			#print(r.json())     # DEBUG
			res = r.json()	
			if res['success']:
				return True
			else:
				return False				

# Main
if __name__ == '__main__':
	# get all instructions from Kafka
	# topic: google
	logger.info("Starting Alfr3d's danavation service")
	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])

	try:
		consumer = KafkaConsumer('danavation', bootstrap_servers=KAFKA_URL)
	except Exception as e:
		logger.error("Failed to connect to Kafka device topic")
		producer.send("speak", b"Failed to connect to Kafka device topic")
		
	# get server information from db
	pass 

	# create Danavation Server
	ser_server="seriesz.danavation.com"
	ser_user="danavationserbia"
	ser_pwd="k8mGaJT7O1p8"
	ser_store=['1683791237194']
	ser_agency="1613571631378"
	ser_merch="1613571004929"
	ser = DanavationServer(server_addr=ser_server,server_acc=ser_user,server_paswd=ser_pwd,stores=ser_store,server_agent=ser_agency,server_merch=ser_merch)

	while True:
		for message in consumer:
			if message.value.decode('ascii') == "alfr3d-dana.exit":
				logger.info("Received exit request. Stopping service.")
				sys.exit(1)
			if message.value.decode('ascii') == "update-esls":
				ser.update_esls()
			if message.key:
				if message.key.decode('ascii') == "emails":				
					msg = message.value.decode('ascii')
					# update emails (msg)
					ser.update_emails(msg)
				if message.key.decode('ascii') == "curr-temp":
					msg = message.value.decode('ascii')
					# update current temp
					ser.update_temp(msg)

			time.sleep(10)    