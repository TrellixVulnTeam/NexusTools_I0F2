#!/usr/bin/python3
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

import argparse
import os
import subprocess
import time

class Backup(ADB):
    
    def __init__(self):
        ADB.__init__(self)
        self.outputPath = 'archives'
        if not os.path.isdir(self.outputPath):
            os.makedirs(self.outputPath)
    
    def create(self, packages, include_apk=False):
        for packageName in packages:
            archive = os.path.join(self.outputPath, packageName.replace('.', '_') + '.ab')
            apk = '-apk' if include_apk else '-noapk'
                
            try:
                result = subprocess.check_output([self.adb_path, 'backup', '-f', archive, packageName], universal_newlines=True)
            except FileNotFoundError:
                raise Exception('Couldn\'t find adb binary')
            except subprocess.CalledProcessError:
                raise Exception('Error executing adb command')
            
            time.sleep(1)
            
    def restore(self, packages):
        for packageName in packages:
            archive = os.path.join(self.outputPath, packageName.replace('.', '_') + '.ab')
                
            try:
                result = subprocess.check_output([self.adb_path, 'restore', archive], universal_newlines=True)
            except FileNotFoundError:
                raise Exception('Couldn\'t find adb binary')
            except subprocess.CalledProcessError:
                raise Exception('Error executing adb command')
            
class Main:    
    
    def run(self):
        # healt check, constructors raise exception if tools are not found
        self.backup = Backup()
        
        if self.args.create:
            self.backup.create(self.args.packages)
        elif self.args.restore:
            self.backup.restore(self.args.packages)
        
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Interface to Android Backup.')
        parser.add_argument('packages', metavar='PACKAGES', type=str, nargs='+', help='list of packages')
        parser.add_argument('-c', '--create', action='store_true', help='create a backup')
        parser.add_argument('-r', '--restore', action='store_true', help='restore a backup')
        self.args = parser.parse_args()
        
if __name__ == "__main__":
    main = Main()
    main.parse_args()
    main.run()
                