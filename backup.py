#!/usr/bin/python3
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

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
                