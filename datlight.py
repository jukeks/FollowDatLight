from euclid import Vector3, Point3, Ray3, Plane
from euclid import Sphere as Sphere3
from PIL import Image 
import colorsys

from multiprocessing import Process, Array

import time

ZEROPOINT = Point3(0, 0, 0)
UP = Vector3(0,1,0)
RIGHT = Vector3(1,0,0)

class Cube:
    def init(self, faces):
        if len(faces) != 6:
            raise ValueError("A cube has 6 faces!")
        
        self.faces = faces
        
class Sphere(Sphere3):
    def __init__(self, point, radius):
        super(Sphere, self).__init__(point,radius)
        self.color = Point3(0.8, 0.5, 0.7)
        self.transmittivity = 0.2
        
    def colorAt(self, point):
        return self.color
        
class Surface(Plane):
    def __init__(self, point1, point2, point3):
        Plane.__init__(self, point1, point2, point3)
        self.basecolor = Point3(1.0, 1.0, 1.0)
        self.othercolor = Point3(0.0, 0.0, 0.0)
        self.transmittivity = 0.2
    
    def colorAt(self, point):
        # http://www.lshift.net/blog/2008/10/29/toy-raytracer-in-python
        if (int(abs(point.x) + 0.5) + 
            int(abs(point.y) + 0.5) + 
            int(abs(point.z) + 0.5)) % 2:
            return self.basecolor
        else:
            return self.othercolor
        
        
class Camera:
    def __init__(self):
        self.position = Point3(0, 5, 20)
        self.look_at = Point3(0, 0, 0)
        self.up_vector = Vector3(0, 1, 0)   # Camera's up vector
        self.fov = 30                       # View angle   
    

class World:
    def __init__(self):
        self.camera = Camera()
        self.lights = [Point3(20, 20, 20)]
        self.objects = [Sphere(Point3(0, 2, 0), 2.0),
                        Sphere(Point3(5, 1.2, 5), 1.2),
                        Sphere(Point3(2, 1.2, 10), 1.2),
                        Surface(Point3(1, 0, 1), Point3(1, 0, 0), Point3(0, 0, 1)),
                        ]
        

class Main:
    def __init__(self, width, height, jobs):
        self.width = width
        self.height = height
        self.jobs = jobs
        self.canvas = Canvas(self.width, self.height)
        self.world = World()
        self.camera = Camera()
    
    def multiProcess(self): 
        jobs = []
        for i in range(self.jobs):
            t = Tracer(self.width, self.height, i * self.width/self.jobs, 
                       (i+1) * self.width/self.jobs, self.canvas,
                       self.world, self.camera) 
            t.name = "Tracer-"+str(i)
            t.start()
            jobs.append(t)
        
        for j in jobs:
            j.join()
            
        t1 = time.time()
        self.canvas.write()
        t2 = time.time()
        print "Writing took\t", (t2-t1)
        
        print "Finished"

 
class Tracer(Process):
    def __init__(self, width, height, begin, end, canvas, world, camera):
        self.world = world
        self.camera = camera
        self.width = width
        self.height = height
        self.begin = begin
        self.end = end
        self.canvas = canvas
        self.camera_position = self.camera.position
        
        self.run = self.calculateRaysAndTrace
        
        Process.__init__(self)
        
    def calculateColor(self, color, multiplier):
        h, l, s = colorsys.rgb_to_hls(color.x*255, color.y*255, color.z*255)
        r, g, b = colorsys.hls_to_rgb(h, l*multiplier, s)
            
        return Point3(r/255.0, g/255.0, b/255.0)
    
    def intersect(self, ray, cur_point = None):
        min_dis = -1
        closest = None
        
        # finding which objects intersect
        for o in self.world.objects:
            intersection = ray.intersect(o)
            
            if not intersection:
                continue
            
            is_point = None
            if isinstance(o, Surface):
                is_point = intersection
            else:
                is_point = intersection.p2
            
            # if the point that intersects is the point the ray is originating
            if cur_point and is_point == cur_point:
                continue
            
            # if the intersection is at the camera 
            if is_point == self.camera_position:
                continue
            
            # finding distance to intersection point
            ls = self.camera_position.connect(is_point)
            if not ls:
                print o, ray, is_point
                continue
            
            dis = abs(ls.v)
            
            # -1 is for the initial value
            if dis < min_dis or min_dis == -1:
                min_dis = dis
                closest = o
                continue
        
        return closest            
        
    
    def trace(self, ray):
        black = Point3(0, 0, 0)
        
        # checking if the ray intersects with any objects
        closest_object = self.intersect(ray)
        if not closest_object:
            return black
            
        # finding the intersection point
        ls = ray.intersect(closest_object)
        is_point = None
        
        if isinstance(closest_object, Surface):
            is_point = ls
        else:
            is_point = ls.p2
        
        # checking if an object blocks the path to a light source
        for light in self.world.lights:
            ray_to_light = Ray3(is_point, light)
            
            if not self.intersect(ray_to_light, is_point):
                return closest_object.colorAt(is_point)
            
            return self.calculateColor(closest_object.colorAt(is_point),
                                       closest_object.transmittivity)
            
        return black
    

      
    def calculateRaysAndTrace(self):
        print self.name, "\tstarting"
        
        camera_position = self.camera.position
        eye_ray = Ray3(self.camera.position, self.camera.look_at)
        right_vector = eye_ray.v.cross(self.camera.up_vector).normalize()
        up_vector = right_vector.cross(eye_ray.v).normalize() *-1 # TODO: FIND OUT WHY
        
        width = self.width
        height = self.height

        # TODO: calculate width more intelligently
        pixel_width = 0.02
        t1 = time.time()
        for x in range(self.begin, self.end):
            x_comp = right_vector.normalize() * ((x - width/2) * pixel_width)
            for y in range(height):
                y_comp = up_vector.normalize() * ((y - height/2) * pixel_width)
                
                cur_vec = eye_ray.v + x_comp + y_comp
                cur_ray = Ray3(camera_position, cur_vec)
                color = self.trace(cur_ray)
                
                self.canvas.saveColor(x, y, color)
                
        t2 = time.time()
        print self.name, "took\t", (t2-t1)

class Canvas:
    def __init__(self, width, height, filename = "trace.png"):
        self.width = width
        self.height = height
        self.filename = filename
        self.data = Array('i', self.width*self.height)
           
    def write(self):
        im = Image.new("RGB", (self.width, self.height))
        pic = im.load()
        
        for i in range(self.width):
            offset = i * self.height
            for j in range(self.height):
                pic[i, j] =  self.intToRGB(self.data[offset + j])
                
        im.save(self.filename, "PNG")
        
    
    def RGBToInt(self, color):
        return int(color.x*255)*256*256 + int(color.y*255)*256 + int(color.z*255)
    
    def intToRGB(self, rgbint):
        return ((rgbint >> 16) % 256, (rgbint >> 8) % 256, rgbint % 256) 
    
    def saveColor(self, x, y, color):
        self.data[x * self.height + y] = self.RGBToInt(color)

Main(width=1024, height=768, jobs=4).multiProcess()