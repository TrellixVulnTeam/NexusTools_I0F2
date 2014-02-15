#!/usr/bin/python3
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python

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
        
    def flash(self, bootloader, system, wipe = False, skip_bootloader = False, skip_recovery = False):
        self.cmd('oem', 'unlock', silent=True)
        self.cmd('erase', 'boot')
        self.cmd('erase', 'cache')
        self.cmd('erase', 'system')
        
        if not skip_recovery:
            self.cmd('erase', 'recovery')
        
        if wipe:
            self.cmd('erase', 'userdata')
            
        if not skip_bootloader:
            self.cmd('flash', 'bootloader', bootloader)
            self.cmd('reboot-bootloader')
            time.sleep(10)
            
        if wipe:
            self.cmd('-w', 'update', system)
        else:
            self.cmd('update', system)