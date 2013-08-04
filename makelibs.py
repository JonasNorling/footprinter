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

soics = [ # lead span, pitch, length, pins, lead length
         (6.00, 1.27, 4.90, 8, 1.40, "SOIC-8"),   # JEDEC MS-012
         (6.00, 1.27, 8.65, 14, 1.40, "SOIC-14"),  # JEDEC MS-012
         (6.00, 1.27, 9.90, 16, 1.40, "SOIC-16"),  # JEDEC MS-012
         
#         (8.00, 1.27, 5.20, 8, None, "EIAJ-SOP8"),   # EIAJ EDR-7320, hard to find the right numbers...
         
         (10.30, 1.27, 10.30, 16, 1.40, "SOIC-16-W"),   # JEDEC MS-013
         (10.30, 1.27, 11.50, 18, 1.40, "SOIC-18-W"),   # JEDEC MS-013
         (10.30, 1.27, 12.80, 20, 1.40, "SOIC-20-W"),   # JEDEC MS-013
         (10.30, 1.27, 15.40, 24, 1.40, "SOIC-24-W"),   # JEDEC MS-013
         (10.30, 1.27, 17.90, 28, 1.40, "SOIC-28-W"),   # JEDEC MS-013
         (10.30, 1.27,  9.00, 14, 1.40, "SOIC-14-W"),   # JEDEC MS-013
         
         (7.80, 0.65,  3.00, 8, 1.25, "SSOP-8"),   # JEDEC MO-150
         (7.80, 0.65,  6.20, 14, 1.25, "SSOP-14"),   # JEDEC MO-150
         (7.80, 0.65,  6.20, 16, 1.25, "SSOP-16"),   # JEDEC MO-150
         (7.80, 0.65,  7.20, 18, 1.25, "SSOP-18"),   # JEDEC MO-150
         (7.80, 0.65,  7.20, 20, 1.25, "SSOP-20"),   # JEDEC MO-150
         (7.80, 0.65,  8.20, 22, 1.25, "SSOP-22"),   # JEDEC MO-150
         (7.80, 0.65,  8.20, 24, 1.25, "SSOP-24"),   # JEDEC MO-150
         (7.80, 0.65, 10.20, 28, 1.25, "SSOP-28"),   # JEDEC MO-150
         (7.80, 0.65, 10.20, 30, 1.25, "SSOP-30"),   # JEDEC MO-150
         (7.80, 0.65, 12.60, 38, 1.25, "SSOP-38"),   # JEDEC MO-150
         
         (6.40, 0.65,  3.00, 8, 1.00, "TSSOP-8"),   # JEDEC MO-153
         (6.40, 0.65,  5.00, 14, 1.00, "TSSOP-14"),   # JEDEC MO-153
         (6.40, 0.65,  5.00, 16, 1.00, "TSSOP-16"),   # JEDEC MO-153
         (6.40, 0.65,  6.50, 20, 1.00, "TSSOP-20"),   # JEDEC MO-153
         (6.40, 0.65,  7.80, 24, 1.00, "TSSOP-24"),   # JEDEC MO-153
         (6.40, 0.65,  9.70, 28, 1.00, "TSSOP-28"),   # JEDEC MO-153
         # These are defined for three pitches and three body widths...
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
    
        f = open("standard-qfp-%s.mod" % density, "w")
        
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
            if p[1] == 1.27:
                name = "SOIC"
            else:
                name = "SOP"
            packagename = "%s%dP%d-%d%s" % (name, p[1] * 100, (p[0]) * 100, p[3], density)
            index.append(packagename)
            
            generator = Soic()
            generator.parse_ipc_name(packagename)
            generator.params.termlen = p[4]
            package = generator.generate()
            body = generator.params.l - 2 * generator.params.termlen
            package.description = "%s, %.02fmm pitch, %.2fmm body" % (p[5], p[1], body)
            footprinter.make_emp(data, packagename, package, False)        
    
        f = open("standard-sop-%s.mod" % density, "w")
        
        f.write("PCBNEW-LibModule-V1  %s\n" % time.asctime())
        f.write("$INDEX\n")
        for name in index:
            f.write("%s\n" % name)
        f.write("$EndINDEX\n")
        f.write(data.getvalue())
        f.write("$EndLIBRARY\n")
        f.close()