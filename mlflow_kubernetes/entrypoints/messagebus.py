import abc
import json
import logging
import os
import time
from collections import defaultdict
from typing import Tuple, Any

import redis


class MessageBus:
    """
    message bus used to send and receive topics's message from other systems。
    it will be used as Receiver_ or Sender_.


    .. _Receiver:

    commonly, pass :py:cls:`TopicHandler`s in its constructor, when topics message
    arrival, it will dispatch corresponding message to all handlers that owner this
    topic.

    call :py:meth:`register` if another eventhandlers you want attached to this
    messagebus, then call :py:meth:`run` to listen.

    .. Sender:

    call :py:meth:`dispatch_event` to dispatch message out if you want

    """

    def __init__(self, *handlers):
        self._handlers = defaultdict(set)

        for handler in handlers:
            self.register(handler)

        self._run = True
        # graceful stop
        # signal.signal(signal.SIGINT, self.signal_stop)
        # signal.signal(signal.SIGTERM, self.signal_stop)

    def register(self, handler):
        """
        register new handler
        """
        for topic in handler.topics:

            if topic not in self._handlers:
                self._subsribe(topic)
            self._handlers[topic].add(handler)

    def run(self):
        """
        run forever for dispatch future incoming events.

        should distinct different topics
        """
        while self._run:
            topic, message = self.get_message()
            if message:
                try:
                    self.handle_event(topic, message)
                except Exception as e:
                    logging.exception(e)

    def dispatch_event(self, topic, event):
        """
        outgoing event handle
        """
        self._publish(topic, event)

    def handle_event(self, topic, event):
        """
        incoming event handle
        """
        for handler in self._handlers[topic]:
            logging.info('handle [] handle %s with message:\n%s', handler, topic, event)
            messages = handler.handle(topic, event)

            if messages:
                for topic, message in messages:
                    self.dispatch_event(topic, message)

    @abc.abstractmethod
    def get_message(self) -> Tuple[str, Any]:
        """
        get next message for topic, blocked if no available event occurred
        """

    @abc.abstractmethod
    def _subsribe(self, topic):
        pass

    @abc.abstractmethod
    def _publish(self, topic, event):
        pass

    def stop(self):
        self._run = False

    def signal_stop(self, signum, frame):
        pass


class RedisMessageBus(MessageBus):

    def __init__(self, host='localhost', port=6379, *handlers):
        # register handle use these information
        self._redis = redis.StrictRedis(
            host=host, port=port, encoding='utf-8',
            decode_responses=True
        )
        self._pub_sub = self._redis.pubsub(ignore_subscribe_messages=True)
        self._message_generator = self._pub_sub.listen()
        super(RedisMessageBus, self).__init__(*handlers)

    def _subsribe(self, topic):
        self._pub_sub.subscribe(topic)

    def _publish(self, topic, event):
        self._redis.publish(topic, json.dumps(event))

    def get_message(self):
        while True:
            response = next(self._message_generator)
            topic = response['channel']
            if topic:
                return topic, json.loads(response['data'])
