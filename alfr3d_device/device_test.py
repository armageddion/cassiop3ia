# send a message and kill the speaker

from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers=['localhost:9092'])

producer.send("device", b"scan net")
time.sleep(5)
producer.send("device", b"alfr3d-device.exit")
time.sleep(5)