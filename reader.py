"""
File: reader.py
Author: Damien Riquet
Email: d.riquet@gmail.com
Description: Describe how to read a binary file
"""


import struct
import binascii

type_names = {
    'byte'   : '<b',
    'short'  : '<h',
    'ushort' : '<H',
    'int'    : '<i',
    'uint'   : '<I',
    'long'   : '<q',
    'double' : '<d',
}


class GWCReaderEOFException(Exception):
    def __str__(self):
        return 'Not enough bytes in gwc file to satisfy read request'


class GWCReader:
    def __init__(self, filename):
        self.file = open(filename, 'rb')


    def __del__(self):
        self.file.close()


    def read(self, type_name):
        if type_name == 'string':
            return self.read_string()

        type_format = type_names[type_name]
        type_size = struct.calcsize(type_format)
        print('read(%s) expected size: %d' % (type_name, type_size))
        value = self.file.read(type_size)
        if type_size != len(value):
            raise GWCReaderEOFException
        return struct.unpack(type_format, value)[0]


    def read_string(self):
        ascii_str = ""

        char = self.read_one_char()
        while char != 0:
            ascii_str += chr(char)
            char = self.read_one_char()

        return ascii_str


    def seek(self, position):
        self.file.seek(position, 0)


    def read_raw(self, size):
        return self.file.read(size)


    def read_one_char(self):
        byte = self.file.read(1)
        if len(byte) != 1:
            raise GWCReaderEOFException
        return int(binascii.hexlify(byte), 16)
