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

from eventlet import websocket
from keystonemiddleware.auth_token import AuthProtocol
from oslo.config import cfg


from osn.openstack.common import jsonutils


opts = [
    cfg.StrOpt('host',
               default='0.0.0.0',
               help='Address on which the server listens.'),
    cfg.StrOpt('port',
               default=7000,
               help='Port on which the server listens.')
]

cfg.CONF.register_opts(opts)


class Handler(object):

    def __init__(self, consumer, env):
        self._consumer = consumer
        self._env = env
        self.handle = websocket.WebSocketWSGI(self.handle)

    def _header_to_env_var(self, key):
        return 'HTTP_%s' % key.replace('-', '_').upper()

    def handle(self, ws):

        def ws_error(status, message):
            ws.send(status)

        def ws_response(env, start_response):
            consumer = self._consumer.subscribe(env['HTTP_X_PROJECT_ID'])
            while True:
                msg = consumer.get()
                ws.send(jsonutils.dumps(msg).decode('utf-8'))

        auth_protocol = AuthProtocol(
            ws_response, dict(cfg.CONF.keystone_authtoken))

        auth = jsonutils.loads(ws.wait())
        self._env.update(
            (self._header_to_env_var(key), value)
            for key, value in auth.iteritems())
        auth_protocol(self._env, ws_error)


class Dispatcher(object):

    def __init__(self, consumer):
        self._consumer = consumer

    def dispatch(self, environ, start_response):
        if environ['PATH_INFO'] == '/data':
            handler = Handler(self._consumer, environ)
            return handler.handle(environ, start_response)
        else:
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return ['Not Found\r\n']
