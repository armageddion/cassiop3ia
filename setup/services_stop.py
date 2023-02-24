# send a message and kill the speaker

from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers=['localhost:9092'])

producer.send("device", b"alfr3d-device.exit")
time.sleep(5)

producer.send("user", value=b"alfr3d-user.exit")
time.sleep(5)

producer.send("environment", b"alfr3d-env.exit")
time.sleep(5)

producer.send("speak", b"alfr3d-speak.exit")
time.sleep(5)