import re
from common import Package, Line, Pad, Circle

class Params(object):
    pass

class Qfp(object):
    def __init__(self):
        self.params = Params()
        self.params.density = "N"    # IPC-7351 density level (L, N or M)
        self.params.termwidth = None # [mm] default terminal (lead) width.
        self.params.termlen = 1.0    # [mm] "L1" in MSC-026 (toe-to-package length)
        self.params.footlen = 0.6    # [mm] "L" in MSC-026 (toe-to-heel length)
        self.params.silkwidth = 0.15 # [mm] silkscreen line width and clearance
        self.params.pitch = None     # [mm] package pitch (distance between pin centers)
        self.params.l1 = None        # [mm] package toe-to-toe width, X dimension
        self.params.l2 = None        # [mm] package toe-to-toe width, Y dimension
        self.params.pincount = None  # total number of pins on package
        self.courtyard_excess = None
        
    def parse_ipc_name(self, name):
        """Parse IPC name (like QFP50P900X900-48) and set parameters from it"""

        match = re.match("QFP(\d+)P(\d+)X(\d+)(X\d+)?-(\d+)(.)?", name)
    
        if match is None:
            return None
    
        p = self.params
        p.pitch = int(match.group(1)) / 100.0
        p.l1 = int(match.group(2)) / 100.0
        p.l2 = int(match.group(3)) / 100.0
        p.pincount = int(match.group(5))
        if match.group(6) is not None:
            p.density = match.group(6)
        self.recalculate_params()
    
    def set_density(self, density):
        """Set parameters for density level L, N or M"""
        self.params.density = density
        self.recalculate_params()
    
    def recalculate_params(self):
        """Recalculate pad sizes depending on the density level"""
        params = self.params
        if params.density == "0": # No protrusion at all (for debugging)
            params.JT = 0
            params.JH = 0
            params.JS = 0
            params.courtyard_excess = 0
        elif params.density == "L": # Least density level
            params.JT = 0.15
            params.JH = 0.25
            if params.pitch > 0.625:
                params.JS = 0.01
            else:
                params.JS = -0.04
            params.courtyard_excess = 0.10
        elif params.density == "N": # Nominal density level
            params.JT = 0.35
            params.JH = 0.35
            if params.pitch > 0.625:
                params.JS = 0.03
            else:
                params.JS = -0.02
            params.courtyard_excess = 0.25
        elif params.density == "M": # Most density level
            params.JT = 0.55
            params.JH = 0.45
            if params.pitch > 0.625:
                params.JS = 0.05
            else:
                params.JS = 0.01
            params.courtyard_excess = 0.50
        else:
            raise "Invalid density (need L,N or M)"

        if self.params.termwidth is None:
            # Pick defaults from JEDEC MS-026
            self.params.termwidth = 0.1 # Ridiculous
            if self.params.pitch <= 0.45:
                self.params.termwidth = 0.23
            elif self.params.pitch <= 0.55:
                self.params.termwidth = 0.27
            elif self.params.pitch <= 0.70:
                self.params.termwidth = 0.38
            elif self.params.pitch <= 0.90:
                self.params.termwidth = 0.45
            else:
                self.params.termwidth = 0.50

    
    def generate(self, **kwargs):
        """Generate data using previously loaded name and parameters. Returns a list."""
        data = []
        params = self.params
        package = Package()

        package.description = "QFP-%d, %.02fmm pitch" % (
                                                    params.pincount, params.pitch)
    
        l = params.l1 # Package length along this dimension (FIXME: non-square packages)
        # Positions of things relative to data center
        padtoe = l / 2 + params.JT
        padheel = l / 2 - params.footlen - params.JH
        padlen = padtoe - padheel
        padcenter = padtoe - padlen / 2.0
        padwidth = params.termwidth + params.JS
        pins_per_side = params.pincount // 4
        first_pad_y = (pins_per_side - 1) * params.pitch / 2.0
        courtyardsize = padtoe + params.courtyard_excess
        outlinesize = l / 2 - params.termlen + params.silkwidth

        # Draw courtyard on package layer
        for side in range(0, 4):
            th = (270 + side * 90) % 360 # Coordinate system rotation for this side
            line = Line( (courtyardsize, courtyardsize), (courtyardsize, -courtyardsize) )
            line.width = 0
            line.layer = "package"
            line.rotate(th)
            data.append(line)

        # Draw package size on package layer
        for side in range(0, 4):
            chamfer = 0.5
            packagesize = l / 2 - params.termlen
            th = (270 + side * 90) % 360 # Coordinate system rotation for this side
            line = Line( (-packagesize + chamfer, packagesize), (packagesize - chamfer, packagesize) )
            line.width = 0
            line.layer = "package"
            line.rotate(th)
            data.append(line)
            line = Line( (packagesize - chamfer, packagesize), (packagesize, packagesize - chamfer) )
            line.width = 0
            line.layer = "package"
            line.rotate(th)
            data.append(line)

            leadblockw = pins_per_side * params.pitch / 2.0
            leadblockh = l / 2
            th = (270 + side * 90) % 360 # Coordinate system rotation for this side
            line = Line( (-leadblockw, leadblockh), (leadblockw, leadblockh) )
            line.width = 0
            line.layer = "package"
            line.rotate(th)
            data.append(line)
            line = Line( (-leadblockw, leadblockh - params.footlen), (leadblockw, leadblockh - params.footlen) )
            line.width = 0
            line.layer = "package"
            line.rotate(th)
            data.append(line)
            line = Line( (-leadblockw, leadblockh), (-leadblockw, packagesize) )
            line.width = 0
            line.layer = "package"
            line.rotate(th)
            data.append(line)
            line = Line( (leadblockw, leadblockh), (leadblockw, packagesize) )
            line.width = 0
            line.layer = "package"
            line.rotate(th)
            data.append(line)
    
        # Draw outline on silkscreen
        linelen = outlinesize - first_pad_y - padwidth / 2 - params.silkwidth * 1.5
        for side in range(0, 4):
            th = (270 + side * 90) % 360 # Coordinate system rotation for this side
            line = Line( (-outlinesize, outlinesize), (-outlinesize + linelen, outlinesize) )
            line.width = params.silkwidth
            line.rotate(th)
            data.append(line)
            line = Line( (-outlinesize, outlinesize), (-outlinesize, outlinesize - linelen) )
            line.width = params.silkwidth
            line.rotate(th)
            data.append(line)

        # Draw orientation mark on silkscreen
        marklen = 1.0
        line = Line( (-outlinesize, outlinesize), (-outlinesize - marklen, outlinesize + marklen) )
        line.width = params.silkwidth
        data.append(line)
    
        # Add pads, starting with pin 1 in lower-left (negative X, positive Y) corner
        # Pads are drawn on the 0-degree (right) side and rotated into place
        pinno = 1
        for side in range(0, 4):
            th = (270 + side * 90) % 360 # Coordinate system rotation for this side
    
            # Pad center coordinates
            x = padcenter
            y = first_pad_y
    
            for pin in range(0, pins_per_side):
                pad = Pad(pinno)
                pad.x = x
                pad.y = y
                pad.ysize = padwidth
                pad.xsize = padlen
                pad.rotate(th)
    
                data.append(pad)
    
                pinno += 1
                y -= params.pitch

        # All done!
        package.data = data
        package.courtyard = ((-courtyardsize, -courtyardsize), (courtyardsize, courtyardsize))
    
        return package
    