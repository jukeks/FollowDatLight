import colorsys
from euclid import Vector3, Point3, Ray3, Line3, Plane
from euclid import Sphere as Sphere3
from multiprocessing import Process

from objects import *

class Tracer(Process):
    def __init__(self, width, height, worker_id, worker_count, canvas, world, camera, recursion_depth):
        self.world = world
        self.camera = camera
        self.width = width
        self.height = height
        self.worker_count = worker_count
        self.worker_id = worker_id
        self.canvas = canvas
        self.camera_position = self.camera.position
        self.black = Point3(0, 0, 0)
        self.max_recursion_depth = recursion_depth

        self.run = self.calculate_rays_and_trace

        Process.__init__(self)

    def calculate_color(self, color, multiplier):
        h, l, s = colorsys.rgb_to_hls(color.x*255, color.y*255, color.z*255)
        r, g, b = colorsys.hls_to_rgb(h, l*multiplier, s)

        return Point3(r/255.0, g/255.0, b/255.0)

    def intersect(self, ray, cur_point = None):
        min_distance = -1
        closest_hit_object = None
        closest_is_point = None

        # finding which objects intersect
        for o in self.world.objects:
            intersection = ray.intersect(o)

            if not intersection:
                continue

            is_point = None
            if isinstance(o, Surface):
                is_point = intersection
            else:
                if ray.p.distance(intersection.p1) < ray.p.distance(intersection.p2):
                    is_point = intersection.p1
                else:
                    is_point = intersection.p2

            # if the point that intersects is the point the ray is originating
            if cur_point and is_point == cur_point:
                continue

            # if the intersection is at the camera
            if is_point == self.camera_position:
                continue

            # finding distance to intersection point
            distance = self.camera_position.distance(is_point)
            if not distance:
                continue

            # -1 is for the initial value
            if distance < min_distance or min_distance == -1:
                min_distance = distance
                closest_hit_object = o
                closest_is_point = is_point
                continue

        return (closest_hit_object, closest_is_point)

    def add_colors(self, c1, c2):
        c = Point3(c1.x + c2.x, c1.y + c2.y, c1.z + c2.z)

        # checking for overflow
        c.x, c.y, c.z = map(lambda x: 1.0 if x>1 else x, [c.x, c.y, c.z])

        return c

    def trace(self, ray, current_recursion_depth = 0):
        # color is initially black
        color = self.black

        # checking if the ray intersects with any objects
        hit_object, is_point = self.intersect(ray)
        if not hit_object:
            return color


        # checking if light hits to the point
        for light in self.world.lights:
            ray_to_light = Ray3(is_point, light)

            blocking_object, _ = self.intersect(ray_to_light, is_point)
            if not blocking_object:
                #color = self.addColors(color, hit_object.colorAt(is_point))
                color = hit_object.color_at(is_point)
                break
            else:
                #color = self.addColors(self.calculateColor(hit_object.colorAt(is_point),
                #    blocking_object.transmittivity), color)
                color = self.calculate_color(blocking_object.color_at(is_point),
                    blocking_object.transmittivity)


        # reflection
        if self.max_recursion_depth > current_recursion_depth:
            normal = hit_object.normal(is_point)
            reflected_ray = Ray3(is_point, normal)
            reflected_color = self.trace(reflected_ray, current_recursion_depth + 1)

            color = self.add_colors(self.calculate_color(reflected_color,
                hit_object.reflectivity),
                color)

        return color



    def calculate_rays_and_trace(self):
        camera_position = self.camera.position
        eye_ray = Ray3(self.camera.position, self.camera.look_at)
        right_vector = eye_ray.v.cross(self.camera.up_vector).normalize()
        up_vector = right_vector.cross(eye_ray.v).normalize() *-1 # TODO: FIND OUT WHY

        width = self.width
        height = self.height

        # progress reports
        next_report = 10

        # TODO: calculate this more intelligently
        pixel_width = 0.02/1024 * width

        for x in range(self.worker_id, width, self.worker_count):
            x_comp = right_vector.normalize() * ((x - width/2) * pixel_width)
            for y in range(height):
                y_comp = up_vector.normalize() * ((y - height/2) * pixel_width)

                cur_vec = eye_ray.v + x_comp + y_comp
                cur_ray = Ray3(camera_position, cur_vec)
                color = self.trace(cur_ray)

                self.canvas.save_color(x, y, color)

            # progress reports
            if self.worker_id == 0:
                progress = float(x) / width * 100
                if progress > next_report:
                    print int(progress), "% done"
                    next_report += 10

        if self.worker_id == 0:
            print "100 % done"