# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

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