# Kafka Producer/Consumer Demonstration with Python

This project demonstrates a basic Kafka setup using Docker Compose, along with a Python producer that sends messages with multithreading and a Python consumer that processes messages with multiprocessing.

## Prerequisites

- Docker and Docker Compose: [Install Docker](https://docs.docker.com/get-docker/)
- Python 3.7+: [Install Python](https://www.python.org/downloads/)
- Python `kafka-python` library:
  ```bash
  pip install kafka-python
  ```

## Overview

The demonstration consists of:

1.  **`docker-compose.yml`**: Sets up a single-node Kafka broker and a Zookeeper instance. It automatically creates a topic named `test-topic`.
2.  **`producer.py`**: A Python script that produces JSON messages to the `test-topic`. It uses multiple threads to simulate concurrent message production.
3.  **`consumer.py`**: A Python script that consumes messages from `test-topic`. It uses multiple processes to simulate scalable message processing. Each consumer process can handle a subset of topic partitions.

## Setup and Running the Demonstration

### 1. Start Kafka Services

Navigate to the `kafka` directory in your terminal and run Docker Compose:

```bash
cd kafka
docker-compose up -d
```

This command will start Zookeeper and Kafka in detached mode. You can view logs using `docker-compose logs -f kafka zookeeper`.

To ensure the topic `test-topic` is created, you can check the Kafka logs or wait a few moments. The `docker-compose.yml` is configured to create it with 1 partition by default (`KAFKA_CREATE_TOPICS: "test-topic:1:1"`). For better demonstration of multiprocessing consumers, consider increasing the number of partitions (e.g., `test-topic:3:1` for 3 partitions) in `docker-compose.yml` before starting the services. If you change it, you'll need to stop and remove existing containers and volumes: `docker-compose down -v` and then `docker-compose up -d`.

### 2. Run the Kafka Producer

Open a new terminal window/tab, navigate to the `kafka` directory, and run the producer script:

```bash
python producer.py
```

The producer will start sending messages using multiple threads. You will see log output indicating messages being sent. It will send a predefined number of messages and then exit.

### 3. Run the Kafka Consumer

Open another new terminal window/tab, navigate to the `kafka` directory, and run the consumer script:

```bash
python consumer.py
```

The consumer script will start multiple processes. Each process will attempt to consume messages from the `test-topic`.
- If you are using the default 1 partition, only one consumer process will actively fetch messages, as a partition can only be consumed by one consumer in a group at a time.
- To see multiple consumer processes working in parallel, you need to have more partitions than consumer processes (or an equal number). For example, if `test-topic` has 3 partitions, and you run `consumer.py` (which starts 2 processes by default), both processes will be assigned partitions and consume messages.

You will see log output from each consumer process indicating received messages. The consumers will run indefinitely until you stop them (e.g., with `Ctrl+C`). The script includes signal handling for graceful shutdown.

### Observing Multithreading (Producer)

The `producer.py` script uses Python's `threading` module. Multiple threads are spawned, each calling the `produce_messages` function. This simulates multiple sources generating and sending data to Kafka simultaneously.

### Observing Multiprocessing (Consumer)

The `consumer.py` script uses Python's `multiprocessing` module. It spawns multiple independent processes.
- **Partition Assignment**: The script demonstrates a basic manual partition assignment strategy where partitions of the `test-topic` are distributed among the available consumer processes.
- **Scalability**: By running multiple consumer processes, you can process messages from different partitions in parallel, which is a key aspect of Kafka's scalability for consumers. If one process handles messages from partition 0, another can handle messages from partition 1 concurrently.

### 4. Stopping the Demonstration

- **Stop Consumers**: Press `Ctrl+C` in the terminal(s) where the `consumer.py` script(s) are running.
- **Stop Kafka Services**: Navigate to the `kafka` directory and run:
  ```bash
  docker-compose down
  ```
  If you also want to remove the data volumes (e.g., Kafka logs, Zookeeper snapshots), use:
  ```bash
  docker-compose down -v
  ```

## Customization

- **Number of Messages/Threads (Producer)**: Modify `num_threads` and `messages_per_thread` in `producer.py`.
- **Number of Consumer Processes**: Modify `num_consumer_processes` in `consumer.py`.
- **Kafka Topic and Partitions**:
    - Change `KAFKA_TOPIC` in `producer.py` and `consumer.py`.
    - Change the topic name and partition count in `docker-compose.yml` (e.g., `KAFKA_CREATE_TOPICS: "your-topic:6:1"` for 6 partitions). Remember to restart Docker Compose services if you change this.
- **Message Content**: Modify the `generate_message()` function in `producer.py`.
- **Message Processing Logic**: Modify the `consume_messages()` function in `consumer.py` to implement your desired processing logic.

This setup provides a foundational example. For production systems, consider aspects like error handling, monitoring, security, and more robust configuration.
