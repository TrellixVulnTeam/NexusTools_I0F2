#!/usr/bin/python3
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from adb import ADB

import argparse

class PM(ADB):
    
    def get_disabled_packages(self):
        return self.get_packages('-d') 
        
    def get_enabled_packages(self):
        return self.get_packages('-e') 
    
    def get_system_packages(self):
        return self.get_packages('-s') 
    
    def get_user_packages(self):
        return self.get_packages('-3') 
        
    def get_packages(self, param):
        package_infos = {}
        pkgs = self.shell(['pm', 'list', 'packages', '-f', param]).split('package:')
        for pkg in pkgs:
            p = pkg.split('=')
            if len(p) == 2:
                # key=packageName, value=packagePath
                package_infos[p[1]] = p[0]
        return package_infos
        
class Main:    
    
    def run(self):
        # healt check, constructors raise exception if tools are not found
        self.pm = PM()

        package_infos = {}
        if self.args.disabled:
            package_infos = self.pm.get_disabled_packages()
        elif self.args.enabled:
            package_infos = self.pm.get_enabled_packages()
        elif self.args.system:
            package_infos = self.pm.get_system_packages()
        elif self.args.user:
            package_infos = self.pm.get_user_packages()

        for packageName, packagePath in package_infos.items():
            print(packageName, '-->', packagePath)
        
        
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
        