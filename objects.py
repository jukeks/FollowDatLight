from euclid import Vector3, Point3, Ray3, Line3, Plane
from euclid import Sphere as Sphere3

class Cube:
    def init(self, faces):
        if len(faces) != 6:
            raise ValueError("A cube has 6 faces!")

        self.faces = faces

class Sphere(Sphere3):
    def __init__(self, point, radius, color = Point3(0.8, 0.5, 0.7)):
        super(Sphere, self).__init__(point,radius)
        self.color = color
        self.transmittivity = 0.1
        self.reflectivity = 0.1

    def colorAt(self, point):
        return self.color

    def normal(self, point):
        assert isinstance(point, Point3)
        return Line3(self.c, point).v

class Surface(Plane):
    def __init__(self, point1, point2, point3):
        Plane.__init__(self, point1, point2, point3)
        self.basecolor = Point3(1.0, 1.0, 1.0)
        self.othercolor = Point3(0.0, 0.0, 0.0)
        self.transmittivity = 0.2
        self.reflectivity = 0.2

    def normal(self, point):
        return self.n

    def colorAt(self, point):
        # http://www.lshift.net/blog/2008/10/29/toy-raytracer-in-python
        if (int(abs(point.x) + 0.5) +
            int(abs(point.y) + 0.5) +
            int(abs(point.z) + 0.5)) % 2:
            return self.basecolor
        else:
            return self.othercolor