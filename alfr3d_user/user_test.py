# send a message and kill the speaker

from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers=['localhost:9092'])

producer.send("user", b"scan net")
time.sleep(5)
producer.send("user", b"alfr3d-user.exit")
time.sleep(5)