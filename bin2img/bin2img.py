from threading import Thread
from queue import Queue
import os
import math
from PIL import Image
import numpy as np
from utils.utils import log
#? for python < 3.9
from typing import Tuple as tuple


class Binary2Image:

    _sequence_length = None

    def __init__(self, config) -> None:
        if 'sequence_length' in config:
            self._sequence_length = config['sequence_length']
        else:
            log(f'[!] No `sequence_length` found in config. Generating byte_code might be affected.')
        pass


    def getBinaryData(self, filepath) -> list:
        """
        Extract byte values from binary executable file and store them into list
        :param filepath: executable file name
        :return: byte value list
        """

        binary_values = []

        if not filepath:
            return None

        with open(filepath, 'rb') as fileobject:

            # read file byte by byte
            data = fileobject.read(1)

            while data != b'':
                binary_values.append(ord(data))
                data = fileobject.read(1)

        return binary_values


    def getHexData(self, filepath) -> list:
        """
        Extract byte values from binary executable file and store them into list
        :param filepath: executable file name
        :return: byte value list
        """
        hex_values = []

        with open(filepath, 'rb') as fileobject:

            # read file byte by byte
            data = fileobject.read(1)

            while data != b'':
                hex_values.append(data.hex())
                data = fileobject.read(1)

        return hex_values


    def createGreyScaleImage(self, filepath, width=None, outdir=None) -> str:
        """
        Create greyscale image from binary data. Use given with if defined or create square size image from binary data.
        :param filepath: image filepath
        """
        if not os.path.isfile(filepath):
            return None

        greyscale_data = self.getBinaryData(filepath)
        if greyscale_data is None:
            return None
        size = self.get_size(len(greyscale_data), width)
        image = Image.new('RGB', size)
        image.putdata(greyscale_data)
        if width > 0:
            image = image.resize((width, width))
        if outdir is not None:
            self.save_file(filepath, image, size, 'L', width, outdir)
        
        # return np.array(image)/255.0
        return filepath


    def createRGBImage(self, filepath, width=None, outdir=None) -> str:
        """
        Create RGB image from 24 bit binary data 8bit Red, 8 bit Green, 8bit Blue
        :param filepath: image filepath
        """
        print('[Binary2Image][createRGBImage] filepath, outdir', filepath, outdir)

        if not os.path.isfile(filepath):
            return None

        index = 0
        rgb_data = []

        #? Read binary file
        binary_data = self.getBinaryData(filepath)
        if binary_data is None:
            return None

        #? Create R,G,B pixels
        while (index + 3) < len(binary_data):
            R = binary_data[index]
            G = binary_data[index+1]
            B = binary_data[index+2]
            index += 3
            rgb_data.append((R, G, B))

        size = self.get_size(len(rgb_data), width)
        image = Image.new('RGB', size)
        image.putdata(rgb_data)
        if width > 0:
            image = image.resize((width, width))
        outpath = None
        if outdir is not None:
            outpath = os.path.join(outdir, os.path.basename(filepath) + '_RGB.png')
            print(f'[Binary2Image][createRGBImage] outpath : {outpath}')
            self.save_file(outpath, image, size, 'RGB', width, outdir)
        # print('np.array(image)', np.array(image).shape)
        
        # return np.array(image)/255.0
        return outpath


    def save_file(self, outpath, image, size, image_type, width, outdir='image') -> None:
        try:
            # setup output filepath
            # dirname = os.path.dirname(filepath)
            # name, _ = os.path.splitext(filepath)
            # name = os.path.basename(name)
            # # imagename   = dirname + os.sep + image_type + os.sep + name + '_'+image_type+ '.png'
            # imagename = outdir+'/'+name + '_'+image_type + '.png'
            imagename = outpath
            os.makedirs(os.path.dirname(imagename), exist_ok=True)

            print(f'[Binary2Image][save_file] imagename = {imagename}')
            print(f'[Binary2Image][save_file] size', size, (width, width), imagename)

            image.save(imagename)
            print('[Binary2Image][save_file] The file', imagename, 'saved.')
        except Exception as err:
            print(err)


    def get_size(self, data_length, width=None) -> tuple[int, int]:
        # source Malware images: visualization and automatic classification by L. Nataraj
        # url : http://dl.acm.org/citation.cfm?id=2016908

        if width is None:  # with don't specified any with value

            size = data_length

            if (size < 10240):
                width = 32
            elif (10240 <= size <= 10240 * 3):
                width = 64
            elif (10240 * 3 <= size <= 10240 * 6):
                width = 128
            elif (10240 * 6 <= size <= 10240 * 10):
                width = 256
            elif (10240 * 10 <= size <= 10240 * 20):
                width = 384
            elif (10240 * 20 <= size <= 10240 * 50):
                width = 512
            elif (10240 * 50 <= size <= 10240 * 100):
                width = 768
            else:
                width = 1024

            height = int(size / width) + 1

        else:
            width = int(math.sqrt(data_length)) + 1
            height = width

        return (width, height)


    def createSeq(self, filepath, config=None, outdir=None) -> str:
        print('[createSeq] config', config, ' | self._sequence_length', self._sequence_length)

        # if config is None or 'sequence_length' not in config:
        #     return ''

        # sequence_length = int(config['sequence_length'])
        sequence_length = self._sequence_length
        
        hex_seq_data = self.getHexData(filepath)
        print('[createSeq] hex_seq_data', hex_seq_data)

        data = ' '.join(str(byte) for byte in hex_seq_data)[:sequence_length*3]
        # print(data)
        if outdir is not None:
            # dirname = os.path.dirname(filepath)
            name, _ = os.path.splitext(os.path.basename(filepath))
            outpath = os.path.join(outdir, name + '.txt')
            with open(outpath, 'w') as f:
                f.write(data)
            print('[createSeq] File', outpath, 'saved.')
            return outpath
        # return data
        return None


    def run(self, file_queue, outdir_seq, outdir_img, width, config, out_types, q_rgb, q_seq) -> None:
        while not file_queue.empty():
            filepath = file_queue.get()

            # createGreyScaleImage(filepath, width, outdir)
            print(f'[Binary2Image][run] out_types = {out_types}')
            if out_types is not None and 'img' in out_types:
                rgb_path = self.createRGBImage(filepath, width, outdir_img)
                #? return the path to the image
                if rgb_path is not None:
                    q_rgb.put(rgb_path)
            if out_types is not None and 'bytecode' in out_types:
                seq_path = self.createSeq(filepath, config, outdir=outdir_seq)
                if seq_path is not None:
                    q_seq.put(seq_path)

            file_queue.task_done()


    def from_files(self, filepaths, outdir_seq, outdir_img, width=None, config=None, out_types=['img', 'bytecode'], thread_number=7) -> tuple[list, list]:
        file_queue = Queue()
        for file_path in filepaths:
            print('[Binary2Image][from_files] in queue', file_path)
            file_queue.put(file_path)

        #? Start thread
        q_rgb = Queue()
        q_seq = Queue()
        # rgb_datas = []
        # seq_datas = []
        rgb_paths = []
        seq_paths = []

        print(f'[Binary2Image][from_files] outdir_img : {outdir_img}')
        for index in range(thread_number):
            thread = Thread(target=self.run, args=(file_queue, outdir_seq, outdir_img, width, config, out_types, q_rgb, q_seq))
            thread.daemon = True
            thread.start()
        file_queue.join()

        while not q_rgb.empty() or not q_seq.empty():
            if not q_rgb.empty():
                rgb_paths.append(q_rgb.get())
            if not q_seq.empty():
                seq_paths.append(q_seq.get())
        
        return (rgb_paths, seq_paths)

