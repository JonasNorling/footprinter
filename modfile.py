# Code for parsing Kicad module files and generating preview
# images of modules

import sys
import os
import re
from common import Package, Line, Pad
import footprinter

def decimil2mm(dmil):
    """Convert kicad's old 1/10 mil format to mm"""
    return dmil * 0.00256

class Mod(object):
    def __init__(self, filename):
        self.f = open(filename)
        self.name = os.path.split(filename)[1]
        self.index = []
        self.mods = []
        self.unit_is_mm = False
        
    def read_index(self):
        for line in self.f:
            if line == "$INDEX\n":
                for line in self.f:
                    if line == "$EndINDEX\n":
                        #break
                        return
                    self.index.append(line.strip())

    def parse(self):
        self.f.seek(0)
        modulere = re.compile("^\$MODULE (.*)\n$")
        endmodulere = re.compile("^\$EndMODULE (.*)\n$")
        
        for line in self.f:
            match = modulere.match(line)
            if match:
                #print("Module %s" % match.group(1))
                package = Package()
                self.mods.append(package)
                
                for line in self.f:
                    if endmodulere.match(line):
                        break
                    self.parse_line(package, line)
            elif line.startswith("Units"):
                if line == "Units mm\n":
                    self.unit_is_mm = True

    def dim(self, dmilstring):
        if self.unit_is_mm:
            return float(dmilstring)
        else:
            return decimil2mm(float(dmilstring))
    
    def parse_line(self, package, line):
        t = line.split()
        if t[0] == "Po":
            return
        elif t[0] == "Li":
            return
        elif t[0] == "Cd":
            return
        elif t[0] == "Sc":
            return
        elif t[0] == "AR":
            return
        elif t[0] == "Op":
            return
        elif t[0][:1] == "T":
            return
        elif t[0] == "DS":
            t = line.split()
            start = (self.dim(t[1]), self.dim(t[2]))
            end = (self.dim(t[3]), self.dim(t[4]))
            package.data.append(Line( start, end, self.dim(t[5]) ))
            package.expand_bbox(start)
            package.expand_bbox(end)
            #line.layer = t[6]
        elif t[0] == "$PAD":
            pad = Pad()
            package.data.append(pad)
            
            for line in self.f:
                t = line.split()
                if t[0] == "Sh":
                    pad.xsize = self.dim(t[3])
                    pad.ysize = self.dim(t[4])
                    pad.rotation = float(t[7]) / 10.0
                elif t[0] == "Dr":
                    pass
                elif t[0] == "At":
                    pass
                elif t[0] == "Ne":
                    pass
                elif t[0] == "Po":
                    pad.x = self.dim(t[1])
                    pad.y = self.dim(t[2])
                elif t[0] == "$EndPAD":
                    maxdim = max(pad.xsize, pad.ysize) / 2.0
                    package.expand_bbox((pad.x - maxdim, pad.y - maxdim))
                    package.expand_bbox((pad.x + maxdim, pad.y + maxdim))
                    return
        else:
            return

        
if __name__ == "__main__":
    mod = Mod(sys.argv[1])
    mod.read_index()
    mod.parse()
    
    package = mod.mods[0]
    package.courtyard = package.bbox
    f = open("out.png", "w")
    footprinter.make_pil_png(f, 50, package)
    f.close()
