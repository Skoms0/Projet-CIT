apiVersion: v1
kind: Pod
metadata:
  name: amqp-worker
  namespace: default
spec:
  restartPolicy: OnFailure
  containers:
  - name: amqp-worker
    image: python:3.9-slim
    command: ["/bin/sh", "-c"]
    args:
      - |
        # Install the AMQP library (pika) instead of MQTT
        pip install pika && \
        python3 -c "
        import pika
        import sys
        import os

        # --- CONFIG ---
        # The K8s Service Name (Internal DNS)
        BROKER = 'rabbitmq-mqtt'
        USERNAME = 'davidra'
        PASSWORD = 'davidra'
        
        QUEUE_NAME = 'video_processing_queue'
        BINDING_KEY = 'cam.h264.#'

        print(f'[Worker] Connecting to {BROKER} on port 5672...')

        try:
            credentials = pika.PlainCredentials(USERNAME, PASSWORD)
            parameters = pika.ConnectionParameters(host=BROKER, port=5672, credentials=credentials)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            # Declare and Bind
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.queue_bind(exchange='amq.topic', queue=QUEUE_NAME, routing_key=BINDING_KEY)
            
            # Fair dispatch
            channel.basic_qos(prefetch_count=1)

            print(f'[Worker] Connected. Waiting for messages on {QUEUE_NAME}...')

            def callback(ch, method, properties, body):
                message_text = body.decode()
                print(f'[Worker] Received: {message_text}')
                
                # Logic removed as requested (sleep and finished print)
                
                # Acknowledge completion
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
            channel.start_consuming()

        except Exception as e:
            print(f'[Error] Connection failed: {e}')
            sys.exit(1)
        "