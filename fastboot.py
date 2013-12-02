# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python

import os
import subprocess
import sys
import time

class Fastboot:
    
    def __init__(self):
        self.fastboot_path = sys.platform + '/' + 'fastboot'
        if sys.platform == 'win32':
            self.fastboot_path += '.exe'
        if not os.path.exists(self.fastboot_path):
            raise Exception('Executable not found: ' + self.fastboot_path)
        print('Found', self.fastboot_path)

    def cmd(self, *params, silent=False):
        if sys.platform == 'linux':
            cmd = ['sudo', self.fastboot_path]
        else:
            cmd = [self.fastboot_path]
            
        for p in params:
            cmd.append(p)
            
        try:
            subprocess.check_output(cmd, universal_newlines=True)
        except FileNotFoundError:
            raise Exception('Couldn\'t find fastboot binary')
        except subprocess.CalledProcessError:
            if silent==False:
                raise Exception('Error executing fastboot command')
        
    def flash(self, bootloader, system, wipe = False):
        self.cmd('oem', 'unlock', silent=True)
        self.cmd('erase', 'boot')
        self.cmd('erase', 'cache')
        self.cmd('erase', 'recovery')
        self.cmd('erase', 'system')
        if wipe:
            self.cmd('erase', 'userdata')
        self.cmd('flash', 'bootloader', bootloader)
        self.cmd('reboot-bootloader')
        time.sleep(10)
        if wipe:
            self.cmd('-w', 'update', system)
        else:
            self.cmd('update', system)