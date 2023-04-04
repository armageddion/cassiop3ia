 #!/usr/bin/python

"""
	This is the main Alfr3d daemon running most standard services
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
#	 and/or distribution of such software/component, that such software/
#	 component:
#	 a. be disclosed or distributed in source code form;
#	 b. be licensed for the purpose of making derivative works; and/or
#	 c. can be redistributed only free of enforceable intellectual property
#		rights (e.g. patents); and/or
# (ii) any software/component that contains, is derived in any manner (in whole
#	  or in part) from, or statically or dynamically links against any
#	  software/component specified under (i).
#

# Imports
import logging
import time
import os						# used to allow execution of system level commands
import sys
import schedule					# 3rd party lib used for alarm clock managment.
from daemon import Daemon
from random import randint		# used for random number generator
from kafka import KafkaProducer # user to write messages to Kafka
from kafka.errors import KafkaError

# current path from which python is executed
CURRENT_PATH = os.path.dirname(__file__)


# set up daemon things
os.system('sudo mkdir -p /var/run/alfr3ddaemon')
os.system('sudo chown alfr3d:alfr3d /var/run/alfr3ddaemon')

# get main DB credentials
DATABASE_URL 	= os.environ.get('DATABASE_URL') or "localhost"
DATABASE_NAME 	= os.environ.get('DATABASE_NAME') or "alfr3d"
DATABASE_USER 	= os.environ.get('DATABASE_USER') or "alfr3d"
DATABASE_PSWD 	= os.environ.get('DATABASE_PSWD') or "alfr3d"
KAFKA_URL 		= os.environ.get('KAFKA_URL') or 'localhost:9092'

# gmail unread count
UNREAD_COUNT = 0
UNREAD_COUNT_NEW = 0

# time of sunset/sunrise - defaults
# SUNSET_TIME = datetime.datetime.now().replace(hour=19, minute=0)
# SUNRISE_TIME = datetime.datetime.now().replace(hour=6, minute=30)
# BED_TIME = datetime.datetime.now().replace(hour=23, minute=00)

# various counters to be used for pacing spreadout functions
QUIP_START_TIME = time.time()
QUIP_WAIT_TIME = randint(5,10)

KAFKA_URL = os.environ.get('KAFKA_URL') or 'localhost:9092'

# set up logging
logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#handler = logging.FileHandler(os.path.join(CURRENT_PATH,"../log/total.log"))
handler = logging.FileHandler("/var/log/alfr3d/alfr3d.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

producer = None
try:
	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
	#producer.send('speak', b'starting alfr3d daemon')
except Exception as e:
	logger.error("Failed to connect to Kafka server")
	logger.error("Traceback: "+str(e))
	sys.exit(1)

class MyDaemon(Daemon):
	def run(self):
		while True:

			"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
				Check online members
			"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
			#try:
			logger.info("Time for localnet scan")
			producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
			r=producer.send("device", b"scan net")

			# Block for 'synchronous' sends
			try:
				record_metadata = r.get(timeout=10)
			except KafkaError as e:
				# Decide what to do if produce request failed...
				logger.error("Kafka error: "+str(e))
				pass

			"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
				Things to do only during waking hours and only when
				god or owner is in tha house
			"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
			logger.info("Checking if mute")
			# TODO check if mute
			mute = False	# temp
			if not mute:
				"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
					Things to do only during waking hours and only when
					god is in tha house
				"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
				# ramble quips every once in a while
				try:
					logger.info("Is it time for a smartass quip?")
					## Do a quip
					self.beSmart()
				except Exception as e:
					logger.error("Failed to complete the quip block")
					logger.error("Traceback: "+str(e))

				# check emails
				try:
					logger.info("Checking Gmail")
					# Check gmail
				except Exception as e:
					logger.error("Failed to check Gmail")
					logger.error("Traceback: "+str(e))

			# OK Take a break
			time.sleep(60)

	def checkGmail(self):
		"""
			Description:
				Checks the unread count in gMail
		"""
		logger.info("Checking email")
		global UNREAD_COUNT
		global UNREAD_COUNT_NEW

		#UNREAD_COUNT_NEW = utilities.getUnreadCount()
		producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
		producer.send("google", b"check gmail")
		UNREAD_COUNT_NEW=0

		if (UNREAD_COUNT < UNREAD_COUNT_NEW):
			logger.info("A new email has arrived...")

			logger.info("Speaking email notification")
			email_quips = [
				"Yet another email",
				"Pardon the interruption sir. Another email has arrived for you to ignore."]

			tempint = randint(1,len(email_quips))

		if (UNREAD_COUNT_NEW != 0):
			logger.info("Unread count: "+str(UNREAD_COUNT_NEW))

	def beSmart(self):
		"""
			Description:
				speak a quip
		"""
		global QUIP_START_TIME
		global QUIP_WAIT_TIME

		if time.time() - QUIP_START_TIME > QUIP_WAIT_TIME*60:
			logger.info("It is time to be a smartass")

			producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])
			producer.send("speak", b"alfr3d-speak.random")

			QUIP_START_TIME = time.time()
			QUIP_WAIT_TIME = randint(10,50)
			print("Time until next quip: ", QUIP_WAIT_TIME) 	#DEBUG

			logger.info("QUIP_START_TIME and QUIP_WAIT_TIME have been reset")
			logger.info("Next quip will be shouted in "+str(QUIP_WAIT_TIME)+" minutes.")

	def playTune(self):
		"""
			Description:
				pick a random song from current weather category and play it
		"""
		logger.info("playing a tune")

	def nightlight(self):
		"""
			Description:
				is anyone at home?
				is it after dark?
				turn the lights on or off as needed.
		"""
		logger.info("nightlight auto-check")

def sunriseRoutine():
	"""
		Description:
			sunset routine - perform this routine 30 minutes before sunrise
			giving the users time to go see sunrise
	"""
	logger.info("Pre-sunrise routine")

def morningRoutine():
	"""
		Description:
			perform morning routine - ring alarm, speak weather, check email, etc..
	"""
	logger.info("Time for morning routine")

def sunsetRoutine():
	"""
		Description:
			routine to perform at sunset - turn on ambient lights
	"""
	logger.info("Time for sunset routine")

def bedtimeRoutine():
	"""
		Description:
			routine to perform at bedtime - turn on ambient lights
	"""
	logger.info("Bedtime")

def resetRoutines():
	"""
		Description:
			refresh some things at midnight
	"""
	#utilities.resetRoutines()


def init_daemon():
	"""
		Description:
			initialize alfr3d services
	"""
	logger.info("Initializing systems check")
	producer = KafkaProducer(bootstrap_servers=[KAFKA_URL])

	producer.send("speak", b"Initializing systems checks")
	#producer.flush()

	faults = 0

	# initial geo check
	logger.info("Running a geoscan")
	producer.send("environment", b"check location")

	# set up some routine schedules
	try:
		#initSpeaker.speakString("Setting up scheduled routines")
		logger.info("Setting up scheduled routines")
		#utilities.createRoutines()
		resetRoutines()

		# "8.30" in the following function is just a placeholder
		# until i deploy a more configurable alarm clock
		schedule.every().day.at("00:05").do(resetRoutines)
		#schedule.every().day.at(str(bed_time.hour)+":"+str(bed_time.minute)).do(bedtimeRoutine)
	except Exception as e:
		logger.error("Failed to set schedules")
		logger.error("Traceback: "+str(e))
		faults+=1												# bump up fault counter

	producer.send("speak", b"Systems check is complete")
	if faults != 0:
		logger.warning("Some startup faults were detected")
		producer.send("speak", b"Some faults were detected but system started successfully")
		#producer.flush()
		#producer.send("speak", b"Total number of faults is "+str(faults))
		#producer.flush()
	else:
		logger.info("All systems are up and operational")
		producer.send("speak", b"All systems are up and operational")
		#producer.flush()

	return

if __name__ == "__main__":
	#daemon = MyDaemon('/var/run/b3nadaemon/b3nadaemon.pid',stderr='/dev/null')
	daemon = MyDaemon('/var/run/alfr3ddaemon/alfr3ddaemon.pid',stderr='/dev/stderr')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			logger.info("Alfr3d Daemon initializing")
			faults = init_daemon()
			logger.info("Alfr3d Daemon starting...")
			daemon.start()
		elif 'stop' == sys.argv[1]:
			logger.info("Alfr3d Daemon stopping...")
			daemon.stop()
			sys.exit(1)
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		else:
			print("Unknown command")
			sys.exit(2)
		sys.exit(0)
	else:
		print("usage: %s start|stop|restart" % sys.argv[0])
		sys.exit(2)
