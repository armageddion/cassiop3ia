# send a message and kill the speaker

from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers=['192.168.1.100:9092'])

producer.send("speak", b"hello world")
time.sleep(5)
#producer.send("speak", b"alfr3d-speak.exit")
#time.sleep(5)