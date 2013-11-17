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
        if not os.path.exists(self.adb_path):
            raise Exception('adb executable not found')
        print('Found', self.adb_path)

    def getDeviceProperty(self, prop_name):
        try:
            result = subprocess.check_output([self.adb_path, '-d', 'shell', 'getprop', prop_name], universal_newlines=True)
        except FileNotFoundError:
            raise Exception('Couldn\'t find adb binary')
        except subprocess.CalledProcessError:
            raise Exception('Error executing adb command')
        return result.replace('\r', '').replace('\n', '')

    def getDeviceInfo(self):
        model = self.getDeviceProperty('ro.product.name')
        version = self.getDeviceProperty('ro.build.version.release')
        return model, version
    
    def getDeviceStatus(self):
        try:
            result = subprocess.check_output([self.adb_path, 'get-state'], universal_newlines=True)
        except FileNotFoundError:
            raise Exception('Couldn\'t find adb binary')
        except subprocess.CalledProcessError:
            raise Exception('Error executing adb command')
        status = result.replace('\r', '').replace('\n', '')
        return status.endswith('device')
    
    def rebootBootloader(self):
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
        if not os.path.exists(self.fastboot_path):
            raise Exception('fastboot executable not found')
        print('Found', self.fastboot_path)

    def cmd(self, *params):
        cmd = ['sudo', self.fastboot_path]
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
    
    def getLatest(self, model, version):
        device_version = self._get_version_index(version)
        
        parser = ImageParser(strict=False)
        parser.parse(self.data, model)
        
        latest_image = None
        for factory_image in parser.image_url_list:
            image_version = self._get_version_index(factory_image['version'].split(' ')[0])
            if image_version > device_version:
                latest_image = factory_image
                
        return latest_image

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
            tar.extractall(members=files)
        return bootloader, system
        
class Main:    
    
    def run(self):
        # healt check, constructors raise exception if tools are not found
        adb = ADB()
        fastboot = Fastboot()

        print('Connecting...')
        if adb.getDeviceStatus() == False:
            print('Device not ready.')
        else:
            model, version = adb.getDeviceInfo()
            print('Connected device:', '\t', model, '(' + version + ')')

            factory_images = FactoryImages()
            latest_image = factory_images.getLatest(model, version)

            if latest_image == None:
                print('Device is up-to-date.')
            else:
                print('Found new image:', '\t', latest_image['version'])
                
                filename = factory_images.download(latest_image)
                
                print('Extracting files...')
                bootloader, system = factory_images.extract(filename)
                
                # by default the device is not wiped
                # If you're coming from a custom ROM you have to wipe it
                # Therefore set the 'wipe' parameter of fastboot.flash(..)
                
                print('Flashing images...')
                adb.rebootBootloader()                
                fastboot.flash(bootloader, system, self.args.wipe)
                
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Flash Nexus factory images.')
        parser.add_argument('--wipe', action='store_true', help='wipe the device before flashing')
        self.args = parser.parse_args()
            
if __name__ == "__main__":
    main = Main()
    main.parse_args()
    main.run()
