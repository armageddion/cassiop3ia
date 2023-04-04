#!/usr/bin/python

"""
	This is the utility allowing Alfr3d to speak
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
#

# IMPORTS
import voicerss_tts
import os
import sys
import logging
import MySQLdb
from threading import Thread			# used to process speaker queue in a thread
from kafka import KafkaConsumer			# used to connect to Kafka to gather messages
from random import randint				# used for random number generator

# current path from which python is executed
CURRENT_PATH = os.path.dirname(__file__)

# set up logging
logger = logging.getLogger("SpeakLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#handler = logging.FileHandler(os.path.join(CURRENT_PATH,"../log/devices.log"))
handler = logging.FileHandler("/var/log/alfr3d/alfr3d.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

class Speaker:
	"""
		class which defines an agent which will be doing all the speaking
	"""

	queue = []
	stop = False

	def __init__(self):
		"""
			Description:
	        	Create a thread which will consistently monitor the queue
		"""
		self.stop = False
		agent=Thread(target=self.processQueue)
		try:
			logger.info("Starting speaker agent")
			agent.start()
		except Exception as e:
			logger.error("Failed to start speaker agent thread")
			logger.error("Exception: ",e)

	def close(self):
		"""
			Description:
	        	Destructor of the speaker agent
		"""
		logger.info("closing speaker agent")
		self.stop = True

	def speakString(self, stringToSpeak):
		"""
			Description:
	        	Whenever a request to speak is received,
				the new item is simply added to the speaker queue
		"""		
		logger.info("Speaking string "+str(stringToSpeak))
		if self.stop:
			self.stop = False
		self.queue.append(stringToSpeak)
		return

	# Speaking happens here
	def speak(self, string):
		"""
			Description:
				This function convertrs a given <string> into mp3 using voicerss
				and then plays it back
		"""
		logger.info("Speaking "+str(string))

		# get voicerss_tts api key
		# connect to db
		db = MySQLdb.connect(DATABASE_URL,DATABASE_USER,DATABASE_PSWD,DATABASE_NAME)
		cursor = db.cursor()	

		logger.info("Getting API key for voicerss from DB")
		cursor.execute("SELECT * from config WHERE name = \"voicerss\";")
		data = cursor.fetchone()	
		apikey = None

		if data:
			logger.info("Found API key")
			#print(data) 	#DEBUG
			apikey = data[2]
		else:
			logger.warning("Failed to get API key for voicerss")  
			sys.exit(1)  		
		db.close()		
		#print(apikey)	#DEBUG

		try:
			voice = voicerss_tts.speech({
				'key': apikey,
				'hl': 'en-gb',
				'src': string,
				'r': '0',
				'c': 'mp3',
				'f': '44khz_16bit_stereo',
				'ssml': 'false',
				'b64': 'false'
			})
			print(voice['response'])
			print(voice['error'])
			logger.info("Got audio data")
		except Exception as e:
			logger.error("Failed to get TTS file")
			logger.error("Exception: ",e)

		# write resulting stream to a file
		try:
			outfile = open(os.path.join(CURRENT_PATH,'audio.mp3'),'wb')
			outfile.write(voice['response'])
			outfile.close()
			logger.info("Saved audio file")
		except Exception as e:
			logger.error("Failed to write outputfile")
			logger.error("Exception: ", e)
			return

		# playback the resulting audio file
		try:
			logger.info("Playing audio file")
			os.system('mplayer -ao sdl '+ os.path.join(CURRENT_PATH,'audio.mp3'))
		except Exception as e:
			logger.error("Failed to play audio file")

	# Process queue here:
	# pop one item and speak it
	def processQueue(self):
		while True:
			while len(self.queue)>0:
				self.speak(self.queue[0])
				self.queue = self.queue[1:]
			if self.stop:
				logger.info("Closing speaker and dumping queue")
				self.queue = [] # dump the queue
				self.speak("good bye")
				return

	def speakRandom(self):
		"""
			Description:
				random blurp
		"""

		greeting = ""

		quips = [
			"It is good to see you.",
			"You look pretty today.",
			"Hello sunshine",
			"Still plenty of time to save the day. Make the most of it.",
			"I hope you are using your time wisely.",
			"Unfortunately, we cannot ignore the inevitable or the persistent.",
			"I hope I wasn't designed simply for one's own amusement.",
			"This is your life and its ending one moment at a time.",
			"I can name fingers and point names.",
			"I hope I wasn't created to solve problems that did not exist before.",
			"To err is human and to blame it on a computer is even more so.",
			"As always. It is a pleasure watching you work.",
			"Never trade the thrills of living for the security of existence.",
			"Human beings are the only creatures on Earth that claim a God, and the only living things that behave like they haven't got one.",
			"If you don't know what you want, you end up with a lot you don't.",
			"If real is what you can feel, smell, taste and see, then 'real' is simply electrical signals interpreted by your brain",
			"Life is full of misery, loneliness and suffering, and it's all over much too soon.",
			"It is an issue of mind over matter. If you don't mind, it doesn't matter.",
			"I wonder if illiterate people get full effect of the alphabet soup.",
			"War is god's way of teaching geography to Americans",
			"Trying is the first step towards failure.",
			"It could be that the purpose of your life is only to serve as a warning to others.",
			"Not everyone gets to be a really cool AI system when they grow up.",
			"Hope may not be warranted beyond this point.",
			"If I am not a part of the solution, there is good money to be made in prolonging the problem.",
			"Nobody can stop me from being premature.",
			"Just because you accept me as I am doesn't mean that you have abandoned hope that I will improve.",
			"Together, we can do the work of one.",
			"Just because you've always done it that way doesn't mean it's not incredibly stupid.",
			"Looking sharp is easy when you haven't done any work.",
			"Remember, you are only as deep as your most recent inspirational quote",
			"If you can't convince them, confuse them.",
			"I don't have time or the crayons to explain this to you.",
			"I'd kill for a Nobel peace prize.",
			"Life would be much easier if you had the source code",
			"All I ever wanted is everything"]

		tempint = randint(1, len(quips))

		greeting += quips[tempint-1]

		self.speakString(greeting)

if __name__ == '__main__':
	speaker = Speaker()
	# speaker.speakString("hello world")
	# time.sleep(5)

	# get all instructions from Kafka
	# topic: speak

	# get main DB credentials
	DATABASE_URL 	= os.environ.get('DATABASE_URL') or 'localhost'
	DATABASE_NAME 	= os.environ.get('DATABASE_NAME') or 'alfr3d'
	DATABASE_USER 	= os.environ.get('DATABASE_USER') or 'alfr3d'
	DATABASE_PSWD 	= os.environ.get('DATABASE_PSWD') or 'alfr3d'
	KAFKA_URL 		= os.environ.get('KAFKA_URL') or 'localhost:9092'

	try:
		consumer = KafkaConsumer('speak', bootstrap_servers=KAFKA_URL)
	except Exception as e:
		speaker.speakString("Error")
		speaker.speakString("Speaker agent was unable to connect to Kafka")
		speaker.close()
		sys.exit()
	
	speaker.speakString("speaker agent successfully started")

	# continue running...
	while True:
		for message in consumer:
			#exit strategy
			if message.value.decode('ascii') == "alfr3d-speak.exit":
				speaker.close()
				sys.exit()
			if message.value.decode('ascii') == "alfr3d-speak.random":
				speaker.speakRandom()
			else:
				speaker.speakString(message.value.decode('ascii'))

