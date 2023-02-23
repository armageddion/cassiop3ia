# send a message and kill the speaker

from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers=['localhost:9092'])

producer.send("user", b"refresh-all")
time.sleep(5)

# create a test user
producer.send("user", value="test_user", key="create")
producer.flush()

# delete the test user
producer.send("user", value="test_user", key="delete")
producer.flush()

producer.send("user", value=b"alfr3d-user.exit")
time.sleep(5)