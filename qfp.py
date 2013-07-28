# This script will generate Kicad modules (footprints) for QFP (TQFP, LQFP, ...) packages
# using the pad margins defined in IPC 7351. The footprint geometry is implicit from its
# IPC 7351 name, except for the terminal (lead) width that has to be specified separately.
#
# Limitations:
#   * Only square packages are implemented (there are rectangular ones in JEDEC MS-026).
#   * I haven't seen IPC-7351A or IPC-7351B.
#
# Some package examples:
#
# Atmel Atmega8 package 32A (TQFP-32, 0.8mm pitch):
#   body size 7x7 mm, conforms to JEDEC MS-026 variation ABA.
#   Terminal (lead) width is 0.45mm (max) according to JEDEC.
#   -n QFP80P900X900X100-32 -W 0.45
#
# STM32F102x8: LQFP-48 0.5mm pitch:
# TI TLK110: PT (S-PQFP-G48) package, 0.5mm pitch:
#   body size 7x7 mm, no JEDEC standard mentioned.
#   -n QFP50P900X900X100-48 -W 0.27
#
# STM32F102x8: LQFP-64 0.5mm pitch:
#   body size 10x10 mm, no JEDEC standard mentioned.
#   -n QFP50P1200X1200X100-64 -W 0.27
#
# JEDEC MS-026D variation BJC (256 pins)
#   body size 28x28 mm, pitch 0.4 mm
#   -n QFP40P3000X3000-256 -W 0.23
#

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
            self.params.termwidth = 0.1 # Ridiculous
    
    def generate(self, **kwargs):
        """Generate data using previously loaded name and parameters. Returns a list."""
        data = []
        params = self.params
    
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

        if False:
            # Draw courtyard on silkscreen
            for side in range(0, 4):    
                th = (270 + side * 90) % 360 # Coordinate system rotation for this side
                line = Line( (courtyardsize, courtyardsize), (courtyardsize, -courtyardsize) )
                line.width = params.silkwidth
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
        package = Package()
        package.data = data
        package.courtyard = ((-courtyardsize, -courtyardsize), (courtyardsize, courtyardsize))
    
        return package
    