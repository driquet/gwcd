"""
File: gwcd.py
Author: Damien Riquet
Email: d.riquet@gmail.com
Description: Decompile a .gwc file and extract data from it (compiled lua file, media files and so on)
    How is formatted a gwc file: https://github.com/WFoundation/WF.Compiler
"""


import os
import argparse
from reader import GWCReader


object_types = {
    1 : 'bmp',
    2 : 'png',
    3 : 'jpg',
    4 : 'gif',
    17: 'wav',
    18: 'mp3',
    19: 'fdl',
    20: 'snd',
    21: 'ogg',
    33: 'swf',
    49: 'txt',
}


class GWCCorruptedFile(Exception):
    def __str__(self):
        return 'GWC file is corrupted or not valid'


class GWCDecompiler:
    def __init__(self, filename):
        self.reader = GWCReader(filename)
        self.cartridge_data = {}
        self.output = "."


    def decompile(self):
        self.read_file_header()
        self.read_cartridge_objects()
        self.read_cartridge_header()


    def set_output(self, output):
        self.output = output


    def read_file_header(self):
        # Read signature value and identifier
        if self.reader.read('short') != int('0a02', 16) or \
                self.reader.read('string') != 'CART':
            raise GWCCorruptedFile


    def read_cartridge_objects(self):
        nb_objects = self.reader.read('ushort')
        objects = []

        for i in range(nb_objects):
            obj_id = self.reader.read('ushort')
            obj_addr = self.reader.read('int')
            objects.append((obj_id, obj_addr))

        self.cartridge_data['objects'] = objects


    def read_cartridge_header(self):
        header = {}

        # Read length
        header['length'] = self.reader.read('int')

        # Cartridge location data
        header['latitude'] = self.reader.read('double')
        header['longitude'] = self.reader.read('double')
        header['altitude'] = self.reader.read('double')

        # Date of creation
        header['date'] = self.reader.read('long')

        # Media ID
        header['id_splash'] = self.reader.read('short')
        header['id_icon'] = self.reader.read('short')

        # Cartridge data
        header['type'] = self.reader.read('string')
        header['player'] = self.reader.read('string')
        header['player_id'] = self.reader.read('long')
        header['cartridge_name'] = self.reader.read('string')
        header['cartridge_guid'] = self.reader.read('string')
        header['cartridge_desc'] = self.reader.read('string')
        header['starting_location_description'] = self.reader.read('string')
        header['version'] = self.reader.read('string')
        header['author'] = self.reader.read('string')
        header['company'] = self.reader.read('string')
        header['recommanded_device'] = self.reader.read('string')

        # Completion code
        header['completion_length'] = self.reader.read('int')
        header['completion_code'] = self.reader.read('string')

        self.cartridge_data['header'] = header




    def write_lua_bytecode(self, filename='cartridge.luac'):
        # Go to the correct position
        self.reader.seek(self.cartridge_data['objects'][0][1])

        # Read and write the lua bytecode
        lua_length = self.reader.read('int')
        filepath = os.path.join(self.output, filename)
        with open(filepath, 'wb') as f:
            f.write(self.reader.read_raw(lua_length))

        return filename


    def write_media_files(self):
        medias = []

        for obj_id, obj_addr in self.cartridge_data['objects'][1:]:
            # Go to the correct position
            self.reader.seek(obj_addr)

            # Read valid object byte
            valid = self.reader.read('byte')
            if valid != 0:
                object_type = self.reader.read('int')
                object_length = self.reader.read('int')

                if object_type in object_types:
                    object_path = os.path.join(self.output, "media_%s.%s" % (obj_id, object_types[object_type]))
                    with open(object_path, 'wb') as f:
                        f.write(self.reader.read_raw(object_length))
                        medias.append(object_path)
        return medias



def decompile(filename):
    d = GWCDecompiler(filename)
    d.decompile()
    d.write_lua_bytecode()
    d.write_media_files()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Wherigo input file")
    parser.add_argument("--output", help="Output directory where gwcd will store extracted data")
    parser.add_argument("--lua", action='store_true', help="Extract compiled lua file")
    parser.add_argument("--completion", action='store_true', help="Show the completion code")
    parser.add_argument("--media", action='store_true', help="Extract media files")
    parser.add_argument("--verbose", "-v", action='store_true', help="Show all data related to the cartridge")
    parser.add_argument("--all", action='store_true', help="Do everything")
    args = parser.parse_args()

    dobj = GWCDecompiler(args.input)
    dobj.decompile()

    if args.output:
        dobj.set_output(args.output)
        if not os.path.isdir(args.output):
            print("creating directory %s" % args.output)
            os.makedirs(args.output)

    if args.lua or args.all:
        print("luac file extracted: %s" % dobj.write_lua_bytecode())

    if args.completion or args.all:
        print("completion code: %s (full: %s)" % (
            dobj.cartridge_data['header']['completion_code'][:15],
            dobj.cartridge_data['header']['completion_code']
        ))

    if args.media or args.all:
        print("extracting media from %s" % args.input)
        for media in dobj.write_media_files():
            print(" - extracted: %s" % media)

    if args.verbose or args.all:
        print("relative data about the cartridge")
        for key, value in dobj.cartridge_data['header'].items():
            print(" - %s: %s" % (key, value))
