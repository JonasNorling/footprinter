#!/usr/bin/python

from qfp import Qfp
from soic import Soic
import footprinter
import time
import StringIO

# Packages specified in JEDEC MS-026D
qfps = [ # lead span x, lead span y, pitch, pins
        ( 4,  4, 0.65,  20), # Variants AKA and BKA
        ( 4,  4, 0.50,  24), # ...
        ( 4,  4, 0.40,  32),

        ( 5,  5, 0.50,  32),
        ( 5,  5, 0.40,  40),
        
        ( 7,  7, 0.80,  32),
        ( 7,  7, 0.65,  40),
        ( 7,  7, 0.50,  48),
        ( 7,  7, 0.40,  64),
        
        (10, 10, 1.00,  36),
        (10, 10, 0.80,  44),
        (10, 10, 0.65,  52),
        (10, 10, 0.50,  64),
        (10, 10, 0.40,  80),
        
        (12, 12, 1.00,  44),
        (12, 12, 0.80,  52),
        (12, 12, 0.65,  64),
        (12, 12, 0.50,  80),
        (12, 12, 0.40, 100),
        
        (14, 14, 1.00,  52),
        (14, 14, 0.80,  64),
        (14, 14, 0.65,  80),
        (14, 14, 0.50, 100),
        (14, 14, 0.40, 120),
        
        (20, 20, 0.65, 112),
        (20, 20, 0.50, 144),
        (20, 20, 0.40, 176),
        
        (24, 24, 0.50, 176),
        (24, 24, 0.40, 216),
        
#            (14, 20, 0.65, 100),
#            (14, 20, 0.50, 128),

        (28, 28, 0.65, 160),
        (28, 28, 0.50, 208),
        (28, 28, 0.40, 256),
        ]

soics = [ # lead span, pitch, length, pins
         (6, 1.27, 4.90, 8, "SOIC8"),   # JEDEC MS-012
         (6, 1.27, 8.65, 14, "SOIC14"),  # JEDEC MS-012
         (6, 1.27, 9.90, 16, "SOIC16"),  # JEDEC MS-012
         ]
if __name__ == "__main__":
    for density in "LNM":
        index = []
        data = StringIO.StringIO()
        
        for p in qfps:
            packagename = "QFP%dP%dX%d-%d%s" % (p[2] * 100, (p[0] + 2) * 100, (p[1] + 2) * 100, p[3], density)
            index.append(packagename)
            
            generator = Qfp()
            generator.parse_ipc_name(packagename)
            package = generator.generate()
            footprinter.make_emp(data, packagename, package, False)        
    
        f = open("qfp-%s.mod" % density, "w")
        
        f.write("PCBNEW-LibModule-V1  %s\n" % time.asctime())
        f.write("$INDEX\n")
        for name in index:
            f.write("%s\n" % name)
        f.write("$EndINDEX\n")
        f.write(data.getvalue())
        f.write("$EndLIBRARY\n")
        f.close()
        
    for density in "LNM":
        index = []
        data = StringIO.StringIO()
        
        for p in soics:
            packagename = "SOIC%dP%d-%d%s" % (p[1] * 100, (p[0]) * 100, p[3], density)
            index.append(packagename)
            
            generator = Soic()
            generator.parse_ipc_name(packagename)
            package = generator.generate()
            footprinter.make_emp(data, packagename, package, False)        
    
        f = open("soic-%s.mod" % density, "w")
        
        f.write("PCBNEW-LibModule-V1  %s\n" % time.asctime())
        f.write("$INDEX\n")
        for name in index:
            f.write("%s\n" % name)
        f.write("$EndINDEX\n")
        f.write(data.getvalue())
        f.write("$EndLIBRARY\n")
        f.close()