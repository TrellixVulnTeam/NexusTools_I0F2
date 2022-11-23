#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

from html.parser import HTMLParser

import argparse
import hashlib
import os
import subprocess
import sys
import tarfile
import time
import urllib.request

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
    
class Fastboot:
    
    # Original script:
    #
    # fastboot oem unlock
    # fastboot erase boot
    # fastboot erase cache
    # fastboot erase recovery
    # fastboot erase system
    # fastboot erase userdata
    # fastboot flash bootloader bootloader-grouper-4.23.img
    # fastboot reboot-bootloader
    # sleep 10
    # fastboot -w update image-nakasi-krt16o.zip
    
    def __init__(self):
        self.fastboot_path = sys.platform + '/' + 'fastboot'
        if sys.platform == 'win32':
            self.fastboot_path += '.exe'
        if not os.path.exists(self.fastboot_path):
            raise Exception('Executable not found: ' + self.fastboot_path)
        print('Found', self.fastboot_path)

    def cmd(self, *params):
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
            raise Exception('Error executing fastboot command')
        
    def flash(self, bootloader, system, wipe = False):
        self.cmd('oem', 'unlock')
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
    
class ImageParser(HTMLParser):
    
    # Contents of HTML file are like that:
    #
    # <h2 id="hammerhead">Factory Images "hammerhead" for Nexus 5 (GSM/LTE)</h2>
    # <table>
    # <tr>
    #   <th>Version
    #   <th>Download
    #   <th>MD5 Checksum
    #   <th>SHA-1 Checksum
    # <tr id="hammerheadkrt16m">
    #   <td>4.4 (KRT16M)
    #   <td><a href="https://dl.google.com/dl/android/aosp/hammerhead-krt16m-factory-bd9c39de.tgz">Link</a>
    #   <td>36aa82ab2d7d05ee144d18546565cd5f
    #   <td>bd9c39ded5dc0ac80c4e96d24db060a660266033
    # </table>
    #
    # From this information we parse the version tags and download URLs.
    
    image_url_list = []
    
    def parse(self, data, model):
        self.model = model
        self.foundModel = False
        self.foundVersion = False
        self.currVersion = '0'
        self.feed(data)
        
    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            for attr in attrs:
                if attr[0] == 'id' and attr[1] == self.model:
                    self.foundModel = True
                    self.foundVersion = False
                else:
                    self.foundModel = False
        elif self.foundModel:
            for attr in attrs:
                if attr[0] == 'id':
                    self.foundVersion = True
                if attr[0] == 'href':
                    self.image_url_list.append({'version':self.currVersion, 'url':attr[1]})

    def handle_data(self, data):
        if self.foundModel:
            data = data.strip()
            if len(data) > 0:
                if self.foundVersion:
                    self.foundVersion = False
                    self.currVersion = data

class FactoryImages:

    def __init__(self):
        f = urllib.request.urlopen('https://developers.google.com/android/nexus/images')
        self.data = f.read().decode()   
        
    def _get_version_index(self, raw_version):
        # convert into integer
        v = int(raw_version.replace('.', ''))
        if v <= 0:
            raise Exception('Invalid version string: ', raw_version)
        # make sure there's always 3 digits
        while v < 100:
            v *= 10
        return v
    
    def get_all(self, model):
        parser = ImageParser(strict=False)
        parser.parse(self.data, model)
        return parser.image_url_list
    
    def _get_any_with_op(self, model, version, op):
        device_version = self._get_version_index(version)
        factory_images = self.get_all(model)
        
        image = None
        for factory_image in factory_images:
            image_version = self._get_version_index(factory_image['version'].split(' ')[0])
            if op == '>' and image_version > device_version:
                image = factory_image
            elif op == '=' and image_version == device_version:
                image = factory_image
                
        return image

    def get_version(self, model, version):
        return self._get_any_with_op(model, version, '=')
    
    def get_latest(self, model, version):
        return self._get_any_with_op(model, version, '>')

    def download(self, image):
        url = image['url']
        path, filename = os.path.split(url)
        
        fin = urllib.request.urlopen(url)
        size = int(fin.info().get_all("Content-Length")[0])
        size_mb = (int)(size / 1024 / 1024)

        file_exists = False
        try:
            if os.path.getsize(filename) == size:
                file_exists = True
        except FileNotFoundError:
            pass
        
        if not file_exists:
            progress = 0
            with open(filename, 'wb') as fout:
                while True:
                    data = fin.read(1024*1024)
                    if not data:
                        print('')
                        break
                    fout.write(data)

                    progress += 1                
                    percent = (int)(progress * 100 / size_mb)
                    print('[' + str(percent) + '%] Downloading', progress, 'of', size_mb, 'MB', end='\r')
                    
        return filename
    
    def extract(self, filename):
        bootloader = None
        system = None
        with tarfile.open(filename) as tar:
            files = []
            for tarinfo in tar:
                ext = os.path.splitext(tarinfo.name)[1]
                if ext == ".img":
                    bootloader = tarinfo.name
                    files.append(tarinfo)
                    print(tarinfo.name)
                if ext == '.zip':
                    system = tarinfo.name
                    files.append(tarinfo)
                    print(tarinfo.name)
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, members=files)
        return bootloader, system
        
class Main:    
    
    def run(self):
        # healt check, constructors raise exception if tools are not found
        self.adb = ADB()
        self.fastboot = Fastboot()
        self.factory_images = FactoryImages()

        print('Connecting...')
        if self.adb.get_device_status() == False:
            print('Device not ready.')
        else:
            self.model, self.device_version = self.adb.get_device_info()
            print('Connected device:', '\t', self.model, '(' + self.device_version + ')')

            if self.args.list:
                self.list_images()
            elif self.args.flash:
                self.flash_image(self.args.flash)
            else:
                self.flash_image()
            
    def flash_image(self, version = None):
        if version != None:
            image = self.factory_images.get_version(self.model, version)
        else:
            image = self.factory_images.get_latest(self.model, self.device_version)

        if image == None:
            print('Device is up-to-date.')
        else:
            print('Found new image:', '\t', image['version'])
            
            filename = self.factory_images.download(image)
            
            print('Extracting files...')
            bootloader, system = self.factory_images.extract(filename)
            
            # by default the device is not wiped
            # If you're coming from a custom ROM you have to wipe it
            # Therefore set the 'wipe' parameter of fastboot.flash(..)
            
            print('Flashing images...')
            self.adb.reboot_bootloader()                
            self.fastboot.flash(bootloader, system, self.args.wipe)
                
    def list_images(self):
        print('Available versions:')
        factory_images = self.factory_images.get_all(self.model)
        for factory_image in factory_images:
            print(' ', factory_image['version'])
                
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Flashes the newest Nexus factory image.')
        parser.add_argument('-w', '--wipe', action='store_true', help='wipe the device before flashing')
        parser.add_argument('-l', '--list', action='store_true', help='list available factory images')
        parser.add_argument('-f', '--flash', action='store', type=str, metavar='VERSION', help='flash a specific factory image')
        self.args = parser.parse_args()
            
if __name__ == "__main__":
    main = Main()
    main.parse_args()
    main.run()
