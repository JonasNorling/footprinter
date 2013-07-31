import numpy
import math

def rotate(p, angle):
    """Rotate vector, compensating for the Y axis being upside down"""
    th = math.radians(angle)
    return (math.cos(th)*p[0] + math.sin(th)*p[1], -(math.sin(th)*p[0] - math.cos(th)*p[1]))

def decimil(mm):
    """Convert mm to kicad's old 1/10 mil format"""
    return int(round(mm / 0.00256))
    
class PilContext:
    """Keep context for drawing with PIL, emulating Cairo to some extent"""
    def __init__(self, draw):
        self.draw = draw
        self.pos = (0, 0)
        self.matrixstack = []
        self.matrix = numpy.matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    def devicecoord(self, c):
        v = numpy.matrix([ [c[0]], [c[1]], [1] ])
        d = self.matrix * v
        return (int(round(d.item(0))), int(round(d.item(1))))

    def save(self):
        self.matrixstack.append(numpy.matrix(self.matrix))

    def restore(self):
        self.matrix = self.matrixstack.pop()

    def set_source_rgb(self, r, g, b):
        self.color = "rgb(%d, %d, %d)" % (r*255, g*255, b*255)

    def set_line_width(self, w):
        self.linewidth = int(round(w * self.matrix.item(0)))

    def scale(self, x, y):
        self.matrix *= numpy.matrix([[x, 0, 0],
                                     [0, y, 0],
                                     [0, 0, 1]])

    def translate(self, x, y):
        self.matrix *= numpy.matrix([[1, 0, x],
                                     [0, 1, y],
                                     [0, 0, 1]])

    def rotate(self, a):
        self.matrix *= numpy.matrix([[math.cos(a), -math.sin(a), 0],
                                     [math.sin(a), math.cos(a), 0],
                                     [0, 0, 1]])

    def move_to(self, x, y):
        self.pos = self.devicecoord((x, y))

    def line_to(self, x, y):
        self.draw.line((self.pos, self.devicecoord((x, y))), fill=self.color, width=self.linewidth)
        self.pos = self.devicecoord((x, y))

    def rectangle(self, x, y, w, h):
        self.draw.polygon((self.devicecoord((x, y)),
                           self.devicecoord((x+w, y)),
                           self.devicecoord((x+w, y+h)),
                           self.devicecoord((x, y+h))),
                          fill=self.color)

    def arc(self, x, y, size, start, end):
        s = size
        self.draw.arc(self.devicecoord((x-s, y-s)) + self.devicecoord((x+s, y+s)),
                      0, 360, fill=self.color)

    def stroke(self):
        pass

    def fill(self):
        pass

    
class Package:
    pass


class Line:
    def __init__(self, start, end):
        self.layer = "F.SilkS"
        self.start = start
        self.end = end

    def rotate(self, th):
        self.start = rotate(self.start, th)
        self.end = rotate(self.end, th)

    def kicad_sexp(self):
        if self.layer == "package":
            return ""
        return "  (fp_line (start %.3f %.3f) (end %.3f %.3f) (layer %s) (width %.2f))\n" % (
            self.start[0], self.start[1],
            self.end[0], self.end[1],
            self.layer, self.width)

    def kicad_mod(self):
        if self.layer == "package":
            return ""
        return "DS %d %d %d %d %d 21\n" % (
            decimil(self.start[0]), decimil(self.start[1]),
            decimil(self.end[0]), decimil(self.end[1]),
            decimil(self.width))

    def draw(self, ctx):
        if self.layer == "package":
            ctx.set_source_rgb(0.7, 0.7, 0.7)
        else:
            ctx.set_source_rgb(0, 0.52, 0.52)
        ctx.set_line_width(self.width)
        ctx.move_to(*self.start)
        ctx.line_to(*self.end)
        ctx.stroke()


class Circle:
    def __init__(self, pos, size):
        self.layer = "F.SilkS"
        self.pos = pos
        self.size = size

    def kicad_sexp(self):
        return "  (fp_circle (center %.2f %.2f) (end %.2f %.2f) (layer %s) (width %.2f))\n" % (
            self.pos[0], self.pos[1],
            self.pos[0] + self.size, self.pos[1],
            self.layer, self.width)

    def kicad_mod(self, scale):
        return "\n"

    def draw(self, ctx):
        ctx.set_source_rgb(0, 0.52, 0.52)
        ctx.set_line_width(self.width)
        ctx.arc(self.pos[0], self.pos[1], self.size, 0, 2*math.pi)
        ctx.stroke()


class Pad:
    def __init__(self, number):
        self.number = number
        self.rotation = 0

    def rotate(self, th):
        self.rotation += th
        (self.x, self.y) = rotate((self.x, self.y), th)

    def kicad_sexp(self):
        return "  (pad %d smd rect (at %.2f %.2f %.0f) (size %.2f %.2f) (layers F.Cu F.Paste F.Mask))\n" % (
            self.number,
            self.x, self.y,
            self.rotation,
            self.xsize,
            self.ysize)

    def kicad_mod(self):
        return """$PAD
Sh "%d" R %d %d 0 0 %d
Dr 0 0 0
At SMD N 00888000
Ne 0 ""
Po %d %d
$EndPAD
""" % (self.number, decimil(self.xsize), decimil(self.ysize), self.rotation * 10, decimil(self.x), decimil(self.y))

    def draw(self, ctx):
        ctx.save()
        ctx.set_source_rgb(0.52, 0, 0)
        ctx.translate(self.x, self.y)
        ctx.rotate(math.radians(self.rotation))
        ctx.rectangle(-self.xsize/2, -self.ysize/2, self.xsize, self.ysize)
        ctx.fill()
        ctx.restore()
