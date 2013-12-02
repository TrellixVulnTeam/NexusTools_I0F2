#!/usr/bin/python3
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from adb import ADB

import argparse

class PackageInfo:
    
    path = None
    packageName = None
    
    def __init__(self, pkg):
        p = pkg.split('=')
        if len(p) == 2:
            self.path = p[0]
            self.packageName = p[1]
            
    def valid(self):
        return self.path is not None and self.packageName is not None
        
    def __str__(self):
        return self.path + ' --> ' + self.packageName
        
class PM(ADB):
    
    def list_disabled_packages(self):
        self.list_packages('-d') 
        
    def list_enabled_packages(self):
        self.list_packages('-e') 
    
    def list_system_packages(self):
        self.list_packages('-s') 
    
    def list_user_packages(self):
        self.list_packages('-3') 
        
    def list_packages(self, param):
        package_infos = self.get_packages(param)
        for pi in package_infos:
            print(str(pi))
        
    def get_packages(self, param):
        package_infos = []
        pkgs = self.shell(['pm', 'list', 'packages', '-f', param]).split('package:')
        for p in pkgs:
            pinf = PackageInfo(p)
            if pinf.valid():
                package_infos.append(pinf)
        return package_infos
        
class Main:    
    
    def run(self):
        # healt check, constructors raise exception if tools are not found
        self.pm = PM()

        if self.args.disabled:
            self.pm.list_disabled_packages()
        elif self.args.enabled:
            self.pm.list_enabled_packages()
        elif self.args.system:
            self.pm.list_system_packages()
        elif self.args.user:
            self.pm.list_user_packages()
        
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Interface to Package Manager.')
        parser.add_argument('-d', '--disabled', action='store_true', help='list all disabled packages')
        parser.add_argument('-e', '--enabled', action='store_true', help='list all enabled packages')
        parser.add_argument('-s', '--system', action='store_true', help='list all system packages')
        parser.add_argument('-u', '--user', action='store_true', help='list all user packages')
        self.args = parser.parse_args()
        
if __name__ == "__main__":
    main = Main()
    main.parse_args()
    main.run()
        