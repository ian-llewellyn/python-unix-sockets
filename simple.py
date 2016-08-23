#!/bin/python3
# -*- coding: utf-8 -*-
"""
simple.py -t <timeout> -s <path_to_socket> -f <path_to_file> <message>
Options:
  -t secs   Period of inactivity before daemon shuts down
  -s path   Location of socket for send/receive
  -f path   Location of file into which message is placed

If this is the only instance of simple.py, spawn a daemon to
handle requests. If another daemon is running, connect to it.
"""
import time, socket, sys, os, stat, pickle, logging

timeout = 10
socket_addr = '/tmp/simple.sock'
target_file = '/tmp/simple.file'

logger = logging.getLogger(__name__)

def is_socket(addr):
    try:
        is_socket = stat.S_ISSOCK(os.stat(addr).st_mode)
    except:
        logger.debug('%s does not exist' % addr)
        return False

    if is_socket:
        logger.debug('%s exists and is a socket' % addr)
        return True

    logger.debug('%s exists but is not a socket' % addr)
    raise Exception('%s exists but is not a socket' % addr)

def is_socket_alive(addr):
    # ConnectionRefusedError if daemon is not listen()ing
    # BrokenPipeError if far end has shutdown
    s = socket.socket(socket.AF_UNIX)
    try:
        s.connect(addr)

    except:
        logger.debug('%s is a stale socket' % addr)
        return False

    finally:
        s.close()

    logger.debug('%s is a functioning socket' % addr)
    return True


class Daemon(object):
    def __init__(self):
        logger.debug('Initialising Daemon()')
        self.socket = None
        self.socket_addr = None

    def write_to_file(self, filename, message):
        with open(filename, 'a') as target_file:
            if not message.endswith('\n'):
                message += '\n'
            target_file.write(message)

    def read_from_file(self, filename):
        with open(filename, 'r') as source_file:
            return ''.join(
                source_file.readlines()
            ).rstrip('\n')

    def create_socket(self, addr):
        if is_socket(addr):
            if is_socket_alive(addr):
                raise Exception('Functioning socket already exists at %s'
                    % addr)
            os.unlink(addr)

        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.bind(addr)
        self.socket_addr = addr
        self.socket.listen(10)

    def run(self, addr):
        self.create_socket(addr)

        while True:
            c_sock, c_addr = self.socket.accept()
            logger.info('accept()ed connection from: %s' % c_addr)

            c_sock.settimeout(timeout)

            # Protocol must include filename and message!
            request = pickle.loads(c_sock.recv(1024))
            logger.debug('Received request: %s' % request)

            filename = request['filename']
            message = request['message']

            if not message.endswith('\n'):
                message += '\n'

            self.write_to_file(filename, message)

            response_text = self.read_from_file(filename)

            response = {
                'length': len(response_text),
                'message': response_text
            }

            logger.debug('Responding with: %s' % response)
            c_sock.send(pickle.dumps(response))

            c_sock.close()

    def __del__(self):
        if type(self.socket) == socket.socket:
            self.socket.close()
        if self.socket_addr is not None:
            os.unlink(self.socket_addr)

class Client(object):
    def __init__(self, filename):
        self.filename = filename

    def __del__(self):
        self._disconnect()

    def _connect_to(self, addr):
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.connect(addr)

    def _disconnect(self):
        self.socket.close()

    def send_to(self, socket_addr, message):
        self._connect_to(socket_addr)

        request = pickle.dumps({
            'filename': self.filename,
            'message': message
        })

        self.socket.send(request)

    def receive(self):
        self.socket.settimeout(timeout)

        return pickle.loads(self.socket.recv(1024))['message']

if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    i = 0
    while True:
        if i == len(sys.argv):
            break

        arg = sys.argv[i]

        if arg == '-t':
            try:
                i += 1
                timeout = float(sys.argv[i])
            except ValueError:
                sys.stderr.write('Timeout must be a number.\n')
                sys.exit(os.EX_USAGE)
            i += 1
            continue

        if arg == '-s':
            i += 1
            socket_addr = sys.argv[i]
            i += 1
            continue

        if arg == '-f':
            i += 1
            target_file = sys.argv[i]
            i += 1
            continue

        if i > 1:
            break

        i += 1

    message = ' '.join(sys.argv[i:])

    logger.debug('%s: timeout: %.2f, socket_addr: %s, filename: %s' %
        (sys.argv[0], timeout, socket_addr, target_file))
    logger.debug(message)

    if not is_socket(socket_addr) or not is_socket_alive(socket_addr):
        pid = os.fork()
        if pid == 0:
            logger.debug('This is the child process')
            d = Daemon()
            d.run(socket_addr)
        logger.debug('This is the parent process')
        time.sleep(0.25) # Give the kid a chance to plug hisself in!
    c = Client(filename=target_file)
    c.send_to(socket_addr, message)
    print(c.receive())
