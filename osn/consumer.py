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

from eventlet import queue


class Consumer(object):

    def __init__(self):
        self._subscribers = {}

    def subscribe(self, tenant):
        sub = queue.LightQueue()
        self._subscribers.setdefault(tenant, set()).add(sub)
        return sub

    def _get_subscriber(self, tenant):
        return self._subscribers.get(tenant, ())

    def push(self, message):
        tenant = message['payload']['tenant_id']
        for subscriber in self._get_subscriber(tenant):
            subscriber.put(message)
