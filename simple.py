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
import time, socket, sys, os, stat, select

timeout = 10
socket_addr = '/tmp/simple.sock'
target_file = '/tmp/simple.file'

class Daemon(object):
    def __init__(self):
        self.socket = None

    def write_to_file(self, filename, message):
        with open(filename, 'a') as target_file:
            target_file.write(message + '\n')

    def read_from_file(self, filename):
        with open(filename, 'r') as source_file:
            return ''.join(
                source_file.readlines()
            ).rstrip('\n')

    def is_socket(self, addr):
        try:
            is_socket = stat.S_ISSOCK(os.stat(addr).st_mode)
        except:
            return False

        if is_socket:
            return True

        raise Exception('%s exists but is not a socket' % addr)

    def is_socket_alive(self, addr):
        # ConnectionRefusedError if daemon is not listen()ing
        # BrokenPipeError if far end has shutdown
        s = socket.socket(socket.AF_UNIX)
        try:
            s.connect(addr)
        except:
            s.close() # Even though the connect() raised an Exception,
                      # a close() is required to avoid a ResourceWarning.
            return False
        s.close()
        return True

    def create_socket(self, addr):
        if self.is_socket(addr):
            if self.is_socket_alive(addr):
                raise Exception('Functioning socket already exists at %s'
                    % addr)
            os.unlink(addr)

        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.bind(addr)
        self.socket.listen(10)

    def run(self, addr):
        self.create_socket(addr)

        while True:
            c_sock, c_addr = self.socket.accept()

            # Protocol must include filename and message!

    def __del__(self):
        if type(self.socket) == socket.socket:
            self.socket.close()

class Client(object):
    def __init__(self):
        pass

if __name__ == '__main__':
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

    print('%s called with -t %.2f, -s %s, -f %s' %
        (sys.argv[0], timeout, socket_addr, target_file))
    print(message)
