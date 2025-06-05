import json
import multiprocessing
import os
import signal
import time
from kafka import KafkaConsumer, TopicPartition

# Kafka broker address
KAFKA_BROKER = 'localhost:9092'
# Kafka topic to consume messages from
KAFKA_TOPIC = 'test-topic'
# Consumer group ID
CONSUMER_GROUP_ID = 'my-consumer-group'

def create_consumer(process_id, num_processes):
    """Creates a Kafka consumer instance for a specific process."""
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=KAFKA_BROKER,
            group_id=CONSUMER_GROUP_ID,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='earliest', # Start reading at the earliest message if no offset is stored
            enable_auto_commit=True, # Commit offsets automatically
            # The following parameters are important for multiprocessing:
            # Consumer timeout to prevent blocking indefinitely if no messages
            consumer_timeout_ms=5000, # milliseconds
            # Rebalance listener can be added for more fine-grained partition assignment control
        )
        print(f"Process-{process_id}: Kafka Consumer created successfully.")
        return consumer
    except Exception as e:
        print(f"Process-{process_id}: Error creating Kafka consumer: {e}")
        return None

def consume_messages(process_id, num_processes):
    """Consumes messages from the Kafka topic using a dedicated consumer for this process."""
    consumer = create_consumer(process_id, num_processes)
    if not consumer:
        print(f"Process-{process_id}: Consumer not available. Exiting.")
        return

    # Manual partition assignment (example)
    # This is one way to distribute partitions among processes.
    # Kafka's group management can also do this automatically if consumers in the same group subscribe to the topic.
    # However, for direct control with multiprocessing, manual assignment can be more predictable.

    # Wait a bit for partitions to be available (especially if topic was just created)
    time.sleep(5)

    available_partitions = consumer.partitions_for_topic(KAFKA_TOPIC)
    if not available_partitions:
        print(f"Process-{process_id}: No partitions found for topic {KAFKA_TOPIC}. Make sure the topic exists and has messages.")
        consumer.close()
        return

    partitions_to_assign = [p for i, p in enumerate(available_partitions) if i % num_processes == process_id]

    if not partitions_to_assign:
        print(f"Process-{process_id}: No partitions assigned. Available: {available_partitions}, Num Processes: {num_processes}")
        consumer.close()
        return

    consumer.assign([TopicPartition(KAFKA_TOPIC, p) for p in partitions_to_assign])
    print(f"Process-{process_id}: Assigned partitions: {partitions_to_assign}")

    try:
        print(f"Process-{process_id}: Starting to listen for messages on topic '{KAFKA_TOPIC}'...")
        while True: # Loop indefinitely or until a signal is received
            for message in consumer: # This will block until a message is available or consumer_timeout_ms
                print(f"Process-{process_id} (Partition {message.partition}): Received message: ID {message.value.get('id')}, Offset {message.offset}")
                # Simulate message processing
                time.sleep(random.uniform(0.5, 1.5))
            # If consumer_timeout_ms is reached and no messages, the loop continues.
            # This allows checking for a shutdown signal or other conditions.
            # print(f"Process-{process_id}: No new messages in the last 5 seconds...") # Optional: for debugging

    except KeyboardInterrupt:
        print(f"Process-{process_id}: KeyboardInterrupt received. Shutting down...")
    except Exception as e:
        print(f"Process-{process_id}: An error occurred: {e}")
    finally:
        print(f"Process-{process_id}: Closing consumer.")
        consumer.close()

def signal_handler(signum, frame):
    print(f"Signal {signum} received. Terminating processes.")
    # This function will be called in the main process.
    # Child processes will receive KeyboardInterrupt upon termination by the parent.
    for p in processes:
        if p.is_alive():
            p.terminate() # Send SIGTERM to child processes
            p.join(timeout=5) # Wait for them to finish
            if p.is_alive(): # If still alive, force kill
                p.kill()
    exit(0)

processes = [] # Global list to keep track of child processes

if __name__ == '__main__':
    import random # ensure random is imported for time.sleep in consume_messages

    print("Starting Kafka consumer demo with multiprocessing...")
    num_consumer_processes = 2 # Number of consumer processes to spawn

    print(f"Starting {num_consumer_processes} consumer processes...")

    # Register signal handlers for graceful shutdown in the main process
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # Handle termination signal

    for i in range(num_consumer_processes):
        process = multiprocessing.Process(target=consume_messages, args=(i, num_consumer_processes))
        processes.append(process)
        process.start()

    # Keep the main process alive until all child processes are done or a signal is received
    try:
        for process in processes:
            process.join() # Wait for each process to complete
    except KeyboardInterrupt: # This handles Ctrl+C in the main process if processes are still joining
        print("Main process: KeyboardInterrupt. Cleaning up...")
        signal_handler(signal.SIGINT, None) # Trigger cleanup
    except Exception as e:
        print(f"Main process: An error occurred: {e}")
        signal_handler(signal.SIGTERM, None) # Trigger cleanup on other errors

    print("All consumer processes have finished.")
