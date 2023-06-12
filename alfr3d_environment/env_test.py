# send a message and kill the speaker

from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers=['192.168.1.100:9092'])

producer.send("environment", b"check location")
time.sleep(10)
# producer.send("environment", b"alfr3d-env.exit")
# time.sleep(5)