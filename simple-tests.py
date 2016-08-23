#!/bin/python3
# -*- coding: utf-8 -*-

import unittest, os, tempfile, socket, stat
from simple import Client, Daemon, is_socket, is_socket_alive

class ClientTests(unittest.TestCase):
    pass

class DaemonSocketTests(unittest.TestCase):
    def setUp(self):
        self.d = Daemon()
        self.tempsocket = tempfile.mktemp(dir='/tmp')
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.bind(self.tempsocket)
        self.socket.listen(1)

    def testSocketAlreadyExists(self):
        self.assertTrue(is_socket(self.tempsocket))
        self.assertFalse(is_socket('/tmp/this_file_does_not_exist'))
        self.assertRaises(Exception, is_socket, arge=(('/tmp/',)))

    def testSocketAlive(self):
        self.assertTrue(is_socket_alive(self.tempsocket))

        self.socket.shutdown(socket.SHUT_RDWR)
        self.assertFalse(is_socket_alive(self.tempsocket))

    def testCreateSocket(self):
        self.assertRaises(Exception, self.d.create_socket,
            args=(self.tempsocket,))

        self.socket.shutdown(socket.SHUT_RDWR)
        self.d.create_socket(self.tempsocket)
        self.assertTrue(stat.S_ISSOCK(os.stat(self.tempsocket).st_mode))

    def tearDown(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        os.path.exists(self.tempsocket) and os.unlink(self.tempsocket)

class DaemonFileTests(unittest.TestCase):
    def setUp(self):
        self.d = Daemon()
        self.tempfile = tempfile.NamedTemporaryFile(dir='/tmp', delete=False)
        self.tempfile.close()

    def testWriteToFile(self):
        message = 'abc, easy as 123'
        target_file = self.tempfile.name
        self.d.write_to_file(target_file, message)
        with open(target_file, 'r') as test_file:
            lines = test_file.readlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], message + '\n')

    def testReadFile(self):
        message = 'abc, easy as 123'
        target_file = self.tempfile.name
        with open(target_file, 'a') as test_file:
            test_file.write(message + '\n')
        test_message = self.d.read_from_file(target_file)
        self.assertEqual(test_message, message)

    def tearDown(self):
        os.unlink(self.tempfile.name)

if __name__ == '__main__':
    unittest.main()
