import unittest
import time
import json
from kafka import KafkaAdminClient, KafkaProducer, KafkaConsumer
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
import multiprocessing
import threading
from producer import generate_message, KAFKA_BROKER as PRODUCER_KAFKA_BROKER, KAFKA_TOPIC as PRODUCER_TOPIC
from consumer import KAFKA_BROKER as CONSUMER_KAFKA_BROKER, KAFKA_TOPIC as CONSUMER_TOPIC, CONSUMER_GROUP_ID

# Ensure broker and topic consistency for tests
KAFKA_BROKER = PRODUCER_KAFKA_BROKER
TEST_TOPIC = PRODUCER_TOPIC # Use the same topic defined in producer/consumer
TEST_CONSUMER_GROUP_ID = f"{CONSUMER_GROUP_ID}-test"

# Number of messages for tests
NUM_TEST_MESSAGES = 3
NUM_PRODUCER_THREADS = 2
NUM_CONSUMER_PROCESSES = 2 # Should ideally match or be less than partition count for full parallelism

class TestKafkaProducerConsumer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up Kafka topic before running tests."""
        try:
            cls.admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BROKER)
        except NoBrokersAvailable:
            raise ConnectionError(f"Cannot connect to Kafka broker at {KAFKA_BROKER}. Ensure Kafka is running via docker-compose.")

        # Create the topic if it doesn't exist.
        # For tests, we want a predictable number of partitions.
        # Let's use NUM_CONSUMER_PROCESSES as the partition count for testing parallelism.
        cls.num_partitions = NUM_CONSUMER_PROCESSES
        topic = NewTopic(name=TEST_TOPIC, num_partitions=cls.num_partitions, replication_factor=1)
        try:
            cls.admin_client.create_topics(new_topics=[topic], validate_only=False)
            print(f"Test topic '{TEST_TOPIC}' created with {cls.num_partitions} partitions.")
        except TopicAlreadyExistsError:
            print(f"Test topic '{TEST_TOPIC}' already exists.")
            # If it exists, ensure it has enough partitions or consider recreating
            topic_metadata = cls.admin_client.describe_topics([TEST_TOPIC])
            current_partitions = len(topic_metadata[0]['partitions'])
            if current_partitions < cls.num_partitions:
                # This is tricky; Kafka doesn't easily allow decreasing partitions or easily increasing on the fly without broker restarts for some versions/configs.
                # For simplicity, we'll print a warning. For robust tests, ensure clean state or manage topic recreation.
                print(f"WARNING: Topic '{TEST_TOPIC}' exists with {current_partitions} partitions, but tests expect {cls.num_partitions}. Parallelism test might be affected.")
                # Attempt to create more partitions if possible (may not always work easily)
                # This is a complex operation and often disabled by default on brokers.
                # For this example, we'll proceed, but in a CI/CD, you'd want a cleaner way to manage this.

        except Exception as e:
            print(f"Error during test topic setup: {e}")
            raise

        time.sleep(2) # Give Kafka a moment to stabilize after topic creation/check

    @classmethod
    def tearDownClass(cls):
        """Clean up Kafka topic after running tests (optional)."""
        # In a real CI, you might delete the topic. For local testing, leaving it is fine.
        # try:
        #     cls.admin_client.delete_topics(topics=[TEST_TOPIC])
        #     print(f"Test topic '{TEST_TOPIC}' deleted.")
        # except Exception as e:
        #     print(f"Error deleting test topic '{TEST_TOPIC}': {e}")
        if hasattr(cls, 'admin_client') and cls.admin_client:
            cls.admin_client.close()

    def test_produce_consume_messages_multithreaded_multiprocess(self):
        """
        Test producing messages with multiple threads and consuming with multiple processes.
        Verifies that all sent messages are received.
        """
        produced_message_ids = set()
        received_message_ids = multiprocessing.Manager().list() # Process-safe list

        # --- Producer Side (Multithreaded) ---
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        producer_threads = []
        messages_per_thread = NUM_TEST_MESSAGES

        def threaded_produce(num_msg):
            for _ in range(num_msg):
                msg = generate_message()
                producer.send(TEST_TOPIC, value=msg)
                produced_message_ids.add(msg['id']) # Not thread-safe for set, but for this small test it's okay.
                                                    # Better: use a thread-safe queue and add from main thread.
                print(f"TestProducer: Sent {msg['id']}")
                time.sleep(0.05) # Small delay
            producer.flush()

        for i in range(NUM_PRODUCER_THREADS):
            thread = threading.Thread(target=threaded_produce, args=(messages_per_thread,))
            producer_threads.append(thread)
            thread.start()

        for thread in producer_threads:
            thread.join()
        producer.close()

        total_produced = NUM_PRODUCER_THREADS * messages_per_thread
        self.assertEqual(len(produced_message_ids), total_produced, "Producer did not generate unique message IDs as expected for the test.")
        print(f"Test: Total messages produced: {len(produced_message_ids)}")

        # --- Consumer Side (Multiprocess) ---
        consumer_processes = []

        # This event will be used to signal consumers to stop
        stop_event = multiprocessing.Event()

        def process_consume(process_id, num_total_processes, shared_received_ids, stop_event_ref):
            consumer = None
            try:
                consumer = KafkaConsumer(
                    TEST_TOPIC,
                    bootstrap_servers=CONSUMER_KAFKA_BROKER,
                    group_id=TEST_CONSUMER_GROUP_ID, # Use a unique group for each test run or manage offsets
                    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                    auto_offset_reset='earliest',
                    consumer_timeout_ms=3000 # Timeout to allow checking stop_event
                )

                # Optional: Manual partition assignment for testing specific distribution
                # available_partitions = consumer.partitions_for_topic(TEST_TOPIC)
                # partitions_to_assign = [p for i, p in enumerate(available_partitions) if i % num_total_processes == process_id]
                # if partitions_to_assign:
                #    consumer.assign([TopicPartition(TEST_TOPIC, p) for p in partitions_to_assign])
                # else: # Fallback to subscribe if no partitions assigned (e.g. if topic has fewer partitions than processes)
                #    consumer.subscribe(topics=[TEST_TOPIC])

                consumer.subscribe(topics=[TEST_TOPIC]) # Simpler: let Kafka handle partition assignment within the group

                print(f"TestConsumer-{process_id}: Subscribed. Waiting for messages...")

                messages_processed_by_this_process = 0
                while not stop_event_ref.is_set():
                    for message in consumer: # This will block until msg or timeout
                        msg_id = message.value.get('id')
                        print(f"TestConsumer-{process_id} (Partition {message.partition}): Received {msg_id}")
                        if msg_id not in shared_received_ids: # Avoid duplicates if somehow processed twice (should not happen with Kafka semantics)
                             shared_received_ids.append(msg_id)
                        messages_processed_by_this_process +=1
                        if len(shared_received_ids) >= total_produced:
                            stop_event_ref.set() # Signal all consumers to stop once all messages are likely received
                            break
                    if len(shared_received_ids) >= total_produced:
                        stop_event_ref.set()
                print(f"TestConsumer-{process_id}: Processed {messages_processed_by_this_process} messages. Exiting loop.")

            except Exception as e:
                print(f"TestConsumer-{process_id}: Error: {e}")
            finally:
                if consumer:
                    consumer.close()
                print(f"TestConsumer-{process_id}: Closed.")

        for i in range(NUM_CONSUMER_PROCESSES):
            process = multiprocessing.Process(target=process_consume, args=(i, NUM_CONSUMER_PROCESSES, received_message_ids, stop_event))
            consumer_processes.append(process)
            process.start()

        # Wait for consumers to finish or a timeout
        start_time = time.time()
        timeout_seconds = 30 # Max time to wait for all messages

        while len(received_message_ids) < total_produced and (time.time() - start_time) < timeout_seconds:
            time.sleep(0.5)

        stop_event.set() # Signal all consumers to stop

        for process in consumer_processes:
            process.join(timeout=10) # Wait for graceful shutdown
            if process.is_alive():
                print(f"TestConsumer: Process {process.pid} did not terminate gracefully, killing.")
                process.kill() # Force kill if stuck

        print(f"Test: Total messages received: {len(received_message_ids)}")
        self.assertSetEqual(produced_message_ids, set(received_message_ids),
                            f"Mismatch between produced and received messages. Produced: {produced_message_ids}, Received: {list(received_message_ids)}")

if __name__ == '__main__':
    # This allows running the tests directly from the script.
    # Ensure Kafka (from docker-compose) is running before executing this.
    print("Starting Kafka integration tests...")
    print(f"Connecting to Kafka Broker at: {KAFKA_BROKER}")
    print(f"Using Topic: {TEST_TOPIC}, Consumer Group: {TEST_CONSUMER_GROUP_ID}")
    print(f"Expecting {NUM_PRODUCER_THREADS * NUM_TEST_MESSAGES} messages to be produced and consumed.")
    print(f"Using {NUM_PRODUCER_THREADS} producer threads and {NUM_CONSUMER_PROCESSES} consumer processes.")

    # It's good practice to ensure the broker is available before starting tests
    try:
        KafkaAdminClient(bootstrap_servers=KAFKA_BROKER, request_timeout_ms=5000).list_topics()
    except NoBrokersAvailable:
        print(f"FATAL: Kafka broker at {KAFKA_BROKER} is not reachable. Please start Kafka using 'docker-compose up -d' in the kafka directory.")
        exit(1)

    unittest.main()
