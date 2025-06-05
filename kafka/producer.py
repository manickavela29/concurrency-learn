import json
import random
import string
import threading
import time
from kafka import KafkaProducer

# Kafka broker address
KAFKA_BROKER = 'localhost:9092'
# Kafka topic to produce messages to
KAFKA_TOPIC = 'test-topic'

def generate_message():
    """Generates a random JSON message."""
    return {
        'id': ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        'timestamp': time.time(),
        'data': {
            'value': random.randint(1, 100),
            'category': random.choice(['A', 'B', 'C'])
        }
    }

def create_producer():
    """Creates a Kafka producer instance."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Kafka Producer created successfully.")
        return producer
    except Exception as e:
        print(f"Error creating Kafka producer: {e}")
        return None

def produce_messages(producer, num_messages=10, thread_id=0):
    """Produces a specified number of messages to the Kafka topic."""
    if not producer:
        print(f"Thread-{thread_id}: Producer not available. Exiting.")
        return

    for i in range(num_messages):
        message = generate_message()
        try:
            producer.send(KAFKA_TOPIC, value=message)
            print(f"Thread-{thread_id}: Sent message: {message['id']}")
        except Exception as e:
            print(f"Thread-{thread_id}: Error sending message {message.get('id', 'unknown')}: {e}")
        time.sleep(random.uniform(0.1, 0.5)) # Simulate some work/delay
    producer.flush() # Ensure all async messages are sent

if __name__ == '__main__':
    print("Starting Kafka producer demo...")
    kafka_producer = create_producer()

    if kafka_producer:
        num_threads = 3
        messages_per_thread = 5
        threads = []

        print(f"Starting {num_threads} producer threads, each sending {messages_per_thread} messages...")

        for i in range(num_threads):
            thread = threading.Thread(target=produce_messages, args=(kafka_producer, messages_per_thread, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        print(f"All {num_threads} threads finished producing messages.")

        # Close the producer connection
        kafka_producer.close()
        print("Kafka producer closed.")
    else:
        print("Failed to create Kafka producer. Exiting demo.")
