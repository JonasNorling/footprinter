# Generate two-sided gull-wing package footprints, for instance for SOIC, SO, SOP, TSSOP packages
#
# This package type is defined in a lot of standards, for example:
#   SOIC: EIAJ         - 5.3mm (208mil) body, 1.27mm (50mil) pitch
#   SOIC: JEDEC MS-012 - 3.9mm (150mil) body, 1.27mm (50mil) pitch - E=6.00, E1=3.90
#   SOIC: JEDEC MS-013 - 7.5mm (300mil) body, 1.27mm (50mil) pitch - L=0.4-1.27, L1=1.04, b=0.31-0.51
#   SSOP: JEDEC MO-150 - 5.3mm body, 0.65mm (25.6mil) pitch
#  TSSOP: JEDEC MO-153 - 4.4mm body, 0.65mm pitch 
#
import re
from common import Package, Line, Pad, Rectangle

class Params(object):
    pass

class Soic(object):
    def __init__(self):
        self.params = Params()
        self.params.density = "N"    # IPC-7351 density level (L, N or M)
        self.params.termwidth = None # [mm] maximum terminal (lead) width.
        self.params.termlen = 1.04   # [mm] "L1" in JEDEC drawings (toe-to-package length)
        self.params.footlen = 0.60   # [mm] "L" in JEDEC drawings (toe-to-heel length)
        self.params.silkwidth = 0.15 # [mm] silkscreen line width and clearance
        self.params.pitch = None     # [mm] package pitch (distance between pin centers) (JEDEC "b")
        self.params.l = None         # [mm] package toe-to-toe width (lead span) (JEDEC "E")
        self.params.pincount = None  # total number of pins on package
        self.courtyard_excess = None
        
    def parse_ipc_name(self, name):
        """Parse IPC name (like SOIC127P600-14) and set parameters from it"""

        match = re.match("(SOIC|SOP)(\d+)P(\d+)(X\d+)?-(\d+)(.)?", name)
    
        if match is None:
            return None
    
        p = self.params
        p.pitch = int(match.group(2)) / 100.0
        p.l = int(match.group(3)) / 100.0
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
            # Pick defaults from JEDEC standards
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
                self.params.termwidth = 0.51 # 1.27 pitch, from MS-012F

    
    def generate(self, **kwargs):
        """Generate data using previously loaded name and parameters. Returns a list."""
        data = []
        params = self.params
        package = Package()

        package.description = "SOIC-%d, %.02fmm pitch, xxx mm body" % (
                                                    params.pincount, params.pitch)
    
        l = params.l # Package lead span
        # Positions and sizes of things relative to data center
        padtoe = l / 2 + params.JT
        padheel = l / 2 - params.footlen - params.JH
        padlen = padtoe - padheel
        padcenter = padtoe - padlen / 2.0
        padwidth = params.termwidth + params.JS
        pins_per_side = params.pincount // 2
        first_pad_x = - (pins_per_side - 1) * params.pitch / 2.0
        packagew = ((pins_per_side - 1) * params.pitch + 1.0) / 2.0 # About right, for small chips
        packageh = l / 2 - params.termlen
        courtyardw = packagew + params.courtyard_excess
        courtyardh = padtoe + params.courtyard_excess
        outlinew = packagew + params.silkwidth/2.0
        outlineh = padheel - params.silkwidth * 1.5

        # Draw courtyard on package layer
        rect = Rectangle( (-courtyardw, -courtyardh), (courtyardw, courtyardh))
        rect.layer = "package"
        data.append(rect)

        # Draw package size on package layer
        rect = Rectangle( (-packagew, -packageh), (packagew, packageh))
        rect.layer = "package"
        data.append(rect)
        
        # Draw outline on silkscreen
        rect = Rectangle( (-outlinew, -outlineh), (outlinew, outlineh))
        rect.width = params.silkwidth
        data.append(rect)
        marksize = 0.75
        rect = Rectangle( (-outlinew, -marksize), (-outlinew + marksize, marksize))
        rect.width = params.silkwidth
        data.append(rect)
        
        # Draw orientation marker by pin 1 on silkscreen
        markx = first_pad_x - padwidth / 2.0 - params.silkwidth * 2
        line = Line( (markx, padcenter - params.silkwidth*2), (markx, padcenter))
        line.width = params.silkwidth
        data.append(line)

        # Add pads, starting with pin 1 in lower-left (negative X, positive Y) corner
        # Pads are drawn on the bottom side and rotated into place
        pinno = 1
        for side in range(0, 2):
            th = side * 180 # Coordinate system rotation for this side
    
            # Pad center coordinates
            x = first_pad_x
            y = padcenter
    
            for pin in range(0, pins_per_side):
                pad = Pad(pinno)
                pad.x = x
                pad.y = y
                pad.ysize = padlen
                pad.xsize = padwidth
                pad.rotate(th)
    
                data.append(pad)
    
                pinno += 1
                x += params.pitch

        # All done!
        package.data = data
        package.courtyard = ((-courtyardw, -courtyardh), (courtyardw, courtyardh))
    
        return package
    