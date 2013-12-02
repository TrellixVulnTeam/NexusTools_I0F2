# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

# Nexus Tools by ramdroid
# Copyright (C) 2013 Ronald Ammann (ramdroid)
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

import os
import subprocess
import sys

class ADB:
    
    def __init__(self):
        self.adb_path = sys.platform + '/' + 'adb'
        if sys.platform == 'win32':
            self.adb_path += '.exe'
        if not os.path.exists(self.adb_path):
            raise Exception('Executable not found: ' + self.adb_path)
        print('Found', self.adb_path)

    def get_device_property(self, prop_name):
        try:
            result = subprocess.check_output([self.adb_path, '-d', 'shell', 'getprop', prop_name], universal_newlines=True)
        except FileNotFoundError:
            raise Exception('Couldn\'t find adb binary')
        except subprocess.CalledProcessError:
            raise Exception('Error executing adb command')
        return result.replace('\r', '').replace('\n', '')

    def get_device_info(self):
        model = self.get_device_property('ro.product.name')
        version = self.get_device_property('ro.build.version.release')
        return model, version
    
    def get_device_status(self):
        try:
            result = subprocess.check_output([self.adb_path, 'get-state'], universal_newlines=True)
        except FileNotFoundError:
            raise Exception('Couldn\'t find adb binary')
        except subprocess.CalledProcessError:
            raise Exception('Error executing adb command')
        status = result.replace('\r', '').replace('\n', '')
        return status.endswith('device')
    
    def reboot_bootloader(self):
        try:
            subprocess.check_output([self.adb_path, 'reboot-bootloader'], universal_newlines=True)
        except FileNotFoundError:
            raise Exception('Couldn\'t find adb binary')
        except subprocess.CalledProcessError:
            raise Exception('Error executing adb command')