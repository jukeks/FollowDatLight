from euclid import Vector3, Point3, Ray3, Line3, Plane
from euclid import Sphere as Sphere3
from PIL import Image

import multiprocessing
import array

import time

import os

from objects import *
from tracer import Tracer

ZEROPOINT = Point3(0, 0, 0)
UP = Vector3(0,1,0)
RIGHT = Vector3(1,0,0)



class Camera:
    def __init__(self):
        self.position = Point3(0, 5, 20)
        self.look_at = Point3(0, 0, 0)
        self.up_vector = Vector3(0, 1, 0)   # Camera's up vector
        self.fov = 30                       # View angle   


class World:
    def __init__(self):
        self.camera = Camera()

        self.lights = [Point3(20, 20, 20),
                       #Point3(-20, 20, 20),
                       #Point3(0, 20, 0),
        ]

        self.objects = [#Sphere(Point3( 3,  2,    2), 2.0, Point3(1.0, 0.0, 0.0)),
                        Sphere(Point3(-2,  4,  -10), 3.0),
                        #Sphere(Point3(-5,  1.2, 10), 1.2, Point3(0.0, 0.0, 1.0)),
                        Surface(Point3(1, 0, 1), Point3(1, 0, 0), Point3(0, 0, 1)),
        ]


class Main:
    def __init__(self, width, height, jobs, recursion_depth):
        self.width = width
        self.height = height
        self.jobs = jobs
        self.canvas = Canvas(self.width, self.height)
        self.world = World()
        self.camera = Camera()
        self.recursion_depth = recursion_depth

    def render(self):
        elapsed_time = 0
        print "Starting", self.jobs, "tracer workers."
        jobs = []

        start_time = time.time()
        for i in range(self.jobs):
            t = Tracer(self.width, self.height, i,
                self.jobs, self.canvas,
                self.world, self.camera, self.recursion_depth)
            t.name = "Tracer-"+str(i)
            t.start()
            jobs.append(t)

        for j in jobs:
            j.join()

        end_time = time.time()
        elapsed_time += end_time - start_time

        print "Time usage:"
        print "Rendering\t", end_time - start_time

        start_time = time.time()
        self.canvas.write()
        end_time = time.time()
        print "Writing\t\t", end_time - start_time

        elapsed_time += end_time - start_time
        print "Total time\t", elapsed_time




class Canvas:
    def __init__(self, width, height, filename = "trace.png"):
        self.width = width
        self.height = height
        self.filename = filename
        self.data = multiprocessing.Array(typecode_or_type='i',
            size_or_initializer=self.width*self.height,
            lock=False
        )
    """
    def write(self):
        a = array.array('i', self.data)
        im = Image.fromstring('I', (self.width, self.height), a.tostring())
        im.save(self.filename, "PNG")
    """
    def write(self):
        im = Image.new("RGB", (self.width, self.height))
        pic = im.load()

        for i in range(self.width):
            offset = i * self.height
            for j in range(self.height):
                pic[i, j] = self.int_to_rgb(self.data[offset + j])

        im.save(self.filename, "PNG")

    def rgb_to_int(self, color):
        return int(color.x*255)*256*256 + int(color.y*255)*256 + int(color.z*255)

    def int_to_rgb(self, rgbint):
        return ((rgbint >> 16) % 256, (rgbint >> 8) % 256, rgbint % 256)

    def save_color(self, x, y, color):
        #self.data[y * self.width + x] = self.RGBToInt(color)
        self.data[x * self.height + y] = self.rgb_to_int(color)


def detect_cpus():
    """
    Detects the number of CPUs on a system. Cribbed from pp.
    """
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
            # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else: # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
        # Windows:
    if os.environ.has_key("NUMBER_OF_PROCESSORS"):
        ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
        if ncpus > 0:
            return ncpus
    return 1 # Default

Main(width=1024, height=768, jobs=detect_cpus(), recursion_depth=1).render()