from cassandra.cluster import Cluster
from datetime import datetime
import pika
import os
import binascii

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', '5672'))
RABBITMQ_USERNAME = os.environ.get('RABBITMQ_USERNAME', 'loader_raw')
RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', 'waggle')
CASSANDRA_HOSTS = os.environ.get('CASSANDRA_HOSTS', 'cassandra').split()
BEEHIVE_DEPLOYMENT = os.environ.get('BEEHIVE_DEPLOYMENT', '/')

cluster = Cluster(contact_points=CASSANDRA_HOSTS)
session = cluster.connect('waggle')
query = 'INSERT INTO sensor_data_raw (node_id, date, plugin_name, plugin_version, plugin_instance, timestamp, parameter, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
prepared = session.prepare(query)


def process_message(ch, method, properties, body):
    versionStrings = properties.app_id.split(':')
    sampleDatetime = datetime.utcfromtimestamp(float(properties.timestamp) / 1000.0)
    sampleDate = sampleDatetime.strftime('%Y-%m-%d')
    # TODO Validate / santize node_id here.
    node_id = properties.reply_to[-12:]
    plugin_name = versionStrings[0]
    plugin_version = versionStrings[1]
    plugin_instance = '0' if (len(versionStrings) < 3) else versionStrings[2]
    timestamp = int(properties.timestamp)
    parameter = properties.type
    data = binascii.hexlify(body).decode()

    session.execute(prepared, (node_id, sampleDate, plugin_name, plugin_version, plugin_instance, timestamp, parameter, data))

    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(node_id, timestamp, plugin_name, plugin_version, parameter, flush=True)


connection = pika.BlockingConnection(pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    virtual_host=BEEHIVE_DEPLOYMENT,
    credentials=pika.PlainCredentials(
        username=RABBITMQ_USERNAME,
        password=RABBITMQ_PASSWORD,
    ),
    connection_attempts=10,
    retry_delay=3.0))

channel = connection.channel()
# channel.basic_qos(prefetch_count=1)
channel.basic_consume(process_message, queue='db-raw')
channel.start_consuming()
