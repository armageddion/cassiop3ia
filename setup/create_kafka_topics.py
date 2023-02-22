from kafka.admin import KafkaAdminClient, NewTopic


admin_client = KafkaAdminClient(
    bootstrap_servers="localhost:9092", 
    client_id='setup'
)

topic_list = [NewTopic(name="speak", num_partitions=1, replication_factor=1),
              NewTopic(name="environment", num_partitions=1, replication_factor=1),
              NewTopic(name="device", num_partitions=1, replication_factor=1),
              NewTopic(name="user", num_partitions=1, replication_factor=1)]
admin_client.create_topics(new_topics=topic_list, validate_only=False)