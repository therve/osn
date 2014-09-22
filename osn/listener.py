#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo.config import cfg
import oslo.messaging

from osn.openstack.common import service


opts = [
    cfg.StrOpt('topic',
               default='notifications2',
               help='Topic on which to listen notifications.'),
    cfg.StrOpt('default_exchange',
               default='nova',
               help='Exchange on which to listen notifications.')
]

cfg.CONF.register_opts(opts)


class NotificationService(service.Service):

    def __init__(self, consumer):
        super(NotificationService, self).__init__()
        self._consumer = consumer

    def start(self):
        super(NotificationService, self).start()
        self._listener = get_listener(self._consumer)
        self._listener.start()

    def stop(self):
        self._listener.stop()
        super(NotificationService, self).stop()


class NotificationHandler(object):

    def __init__(self, consumer):
        self._consumer = consumer

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        message = {
            'event_type': event_type,
            'payload': payload,
            'metadata': metadata
        }
        self._consumer.push(message)


def get_listener(consumer):
    oslo.messaging.set_transport_defaults('osn')

    transport = oslo.messaging.get_transport(cfg.CONF)
    targets = [
        oslo.messaging.Target(
            topic=cfg.CONF.topic, exchange=cfg.CONF.default_exchange)
    ]

    endpoints = [
        NotificationHandler(consumer)
    ]

    return oslo.messaging.get_notification_listener(
        transport, targets, endpoints, executor='eventlet')
