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

from html.parser import HTMLParser

import hashlib
import os
import tarfile
import urllib.request

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
            tar.extractall(members=files)
        return bootloader, system
        