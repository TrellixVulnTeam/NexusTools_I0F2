#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

# Nexus Tools by ramdroid
# Copyright (C) 2013-2014 Ronald Ammann (ramdroid)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from adb import ADB
from fastboot import Fastboot
from factoryimages import ImageParser, FactoryImages

import argparse
    
class Main:    
    
    def run(self):
        # healt check, constructors raise exception if tools are not found
        self.fastboot = Fastboot()
        self.factory_images = FactoryImages()

        self.flash_image(self.args.flash_model, self.args.flash_version)
            
    def flash_image(self, model, version):
        image = self.factory_images.get_version(model, version)

        if image == None:
            print('Image not found.')
        else:
            print('Found new image:', '\t', image['version'])
            
            filename = self.factory_images.download(image)
            
            print('Extracting files...')
            bootloader, system = self.factory_images.extract(filename)
            
            print('Flashing images...')           
            self.fastboot.flash(bootloader, system, self.args.wipe, self.args.skip_bootloader, self.args.skip_recovery)
                
    def list_images(self):
        print('Available versions:')
        factory_images = self.factory_images.get_all(self.model)
        for factory_image in factory_images:
            print(' ', factory_image['version'])
                
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Flashes the newest Nexus factory image.')
        parser.add_argument('-w', '--wipe', action='store_true', help='wipe the device before flashing')
        parser.add_argument('-fm', '--flash_model', action='store', type=str, metavar='MODEL', help='specify the model name')
        parser.add_argument('-fv', '--flash_version', action='store', type=str, metavar='VERSION', help='specify the Android version')
        parser.add_argument('-sb', '--skip_bootloader', action='store_true', help='skip flashing the bootloader')
        parser.add_argument('-sr', '--skip_recovery', action='store_true', help='skip flashing the recovery')
        self.args = parser.parse_args()
            
if __name__ == "__main__":
    main = Main()
    main.parse_args()
    main.run()
