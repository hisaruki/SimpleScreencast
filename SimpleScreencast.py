#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import time
import argparse
import datetime
from pathlib import Path


parser = argparse.ArgumentParser(prog='Simple ffmpeg-screencast wrapper')
parser.add_argument('command', choices=['start', 'stop', 'toggle', 'daemon'])
parser.add_argument('--framerate', type=int, default=30)
parser.add_argument('--path', type=str, default=os.path.expanduser('~'))
args = parser.parse_args()
args.path = os.path.expanduser(args.path)


class SimpleScreencast:

    def __init__(self, framerate, path):
        self.recording = False
        self.ffmpeg = None
        self.framerate = str(framerate)
        self.path = path

    def xwininfo(self):
        ls = subprocess.Popen(
            ["xwininfo", "-frame"],
            stdout=subprocess.PIPE
        ).communicate()[0].decode("utf-8").splitlines()

        ls += subprocess.Popen(
            ["xdpyinfo"],
            stdout=subprocess.PIPE
        ).communicate()[0].decode("utf-8").splitlines()

        ls = map(lambda x: x.split(":"), ls)
        ls = filter(lambda x: len(x) == 2, ls)
        ls = map(lambda x: (x[0].lstrip().rstrip(),
                            x[1].lstrip().rstrip()), ls)
        self.info = {}
        for k, v in ls:
            self.info[k] = v

        dim = self.info["dimensions"]
        dim = dim.split()[0]
        dim = (int(dim.split("x")[0]), int(dim.split("x")[1]))

        width = int(self.info["Width"])
        height = int(self.info["Height"])
        ulx = self.info["Absolute upper-left X"]
        ulx = max(0, int(ulx))
        uly = self.info["Absolute upper-left Y"]
        uly = max(0, int(uly))

        overx = (ulx + width) - dim[0]
        overy = (uly + height) - dim[1]

        if overx > 0:
            width -= overx
        if overy > 0:
            height -= overy

        self.size = str(width) + "x" + str(height)
        self.input = ":0.0+" + str(ulx) + "," + str(uly)

    def start(self):
        filename = str(datetime.datetime.now()) + '.mkv'
        ps = [
            "ffmpeg",
            "-y",
            "-video_size",
            self.size,
            "-framerate",
            self.framerate,
            "-f",
            "x11grab",
            "-i",
            self.input,
            "-f",
            "pulse",
            "-ac",
            "2",
            "-i",
            "default",
            "-vcodec",
            "prores",
            "-acodec",
            "pcm_s16le",
            str(Path(self.path) / Path(filename))
        ]
        print(ps)
        self.ffmpeg = subprocess.Popen(ps, stdin=subprocess.PIPE)

    def stop(self):
        self.ffmpeg.communicate(b"q")
        self.ffmpeg = None

    def operation(self):
        while 1:
            time.sleep(0.1)
            try:
                if Path("/tmp/SimpleScreencast").read_text().find("1") == 0:
                    self.recording = True
                else:
                    self.recording = False
            except:
                self.recording = False
            if self.recording is True:
                if self.ffmpeg is None:
                    self.xwininfo()
                    self.start()
            if self.recording is False:
                if self.ffmpeg is not None:
                    self.stop()


s = SimpleScreencast(args.framerate, args.path)

if args.command == "daemon":
    s.operation()
if args.command == "start":
    Path("/tmp/SimpleScreencast").write_text("1")
if args.command == "stop":
    Path("/tmp/SimpleScreencast").write_text("0")
if args.command == "toggle":
    if Path("/tmp/SimpleScreencast").read_text().find("1") == 0:
        Path("/tmp/SimpleScreencast").write_text("0")
    else:
        Path("/tmp/SimpleScreencast").write_text("1")
