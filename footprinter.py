#!/usr/bin/python
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

import optparse
import qfp
import soic
import time
import sys
import common
import re

description="""Generate a QFP footprint (land pattern) from an IPC name.
The name is given on the form QFP<pitch>P<L1>X<L2>[X<height>]-<pincount>, where
pitch is the distance between the centre of the pins; L1 and L2 is the nominal
width in the X and Y dimensions of the package measured between opposite pin toes;
height is optionally the thickness of the package (ignored); pincount is the number
of pins (leads) on the package. The unit for all measurements is mm, represented in
1/100ths. For example: QFP50P900X900-48 is a square QFP package with 48 pins where
the distance between the pin ends is 9.00 mm, pin pitch 0.50 mm (this is a standard
7x7 mm LQFP package).
"""

def make_kicad_mod(f, name, package):
    f.write("(module %s (layer F.Cu) (tedit %X)\n" % (name, time.time()))
    f.write("  (at 0 0)\n")
    f.write("  (descr \"%s\")\n" % package.description)
    f.write("  (tags qfp, lqfp, tqfp)\n")
    f.write("  (model smd/tqfp32.wrl (at (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n")
    f.write("  (fp_text reference %s (at 0 -1) (layer F.SilkS)\n" % name)
    f.write("    (effects (font (size 1.5 1.5) (thickness 0.15))))\n")
    f.write("  (fp_text value VAL** (at 0 1) (layer F.SilkS) hide\n")
    f.write("    (effects (font (size 1.5 1.5) (thickness 0.15))))\n")
    for d in package.data:
        f.write(d.kicad_sexp())
    f.write(")\n") # close module

def make_emp(f, name, package, write_lib_header=True):
    m = common.decimil
    if write_lib_header:
        f.write("PCBNEW-LibModule-V1  %s\n" % time.asctime())
        f.write("$INDEX\n")
        f.write("%s\n" % name)
        f.write("$EndINDEX\n")

    f.write("$MODULE %s\n" % name)
    f.write("Po 0 0 0 15 %X 00000000 ~~\n" % time.time())
    f.write("Li %s\n" % name)
    f.write("Cd %s\n" % package.description)
    f.write("Sc 0\n")
    f.write("AR \n")
    f.write("Op 0 0 0\n")

    f.write("T0 %d %d %d %d %d %d N V 21 N \"%s\"\n" % (m(0), m(-1), m(1.5), m(1.5), m(0), m(0.15), name))
    f.write("T1 %d %d %d %d %d %d N I 21 N \"%s\"\n" % (m(0), m(1), m(1.5), m(1.5), m(0), m(0.15), "VAL**"))
    
    for d in package.data:
        f.write(d.kicad_mod())

    f.write("$EndMODULE %s\n" % name)
    
    if write_lib_header:
        f.write("$EndLIBRARY\n")

def make_cairo_png(filename, scale, package):
    import cairo
    
    margin = 0.1 # mm
    size = package.courtyard
    w = int((size[1][0] - size[0][0] + 2 * margin) * scale)
    h = int((size[1][1] - size[0][1] + 2 * margin) * scale)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surface)

    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    # Move origin to center of image, scale to mm
    ctx.translate(w/2, h/2)
    ctx.scale(scale, scale)

    for d in package.data:
        d.draw(ctx)

    surface.write_to_png(filename)
    return (w, h)

def make_pil_png(f, scale, package):
    from PIL import Image, ImageDraw
    
    scale = float(scale)
    margin = 0.1 # mm
    size = package.courtyard
    size = ( (size[0][0] - margin, size[0][1] - margin),
             (size[1][0] + margin, size[1][1] + margin) )
    w = int((size[1][0] - size[0][0]) * scale)
    h = int((size[1][1] - size[0][1]) * scale)

    im = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(im)
    ctx = common.PilContext(draw)

    ctx.scale(scale, scale)
    ctx.translate(-size[0][0], -size[0][1])

    for d in package.data:
        d.draw(ctx)

    im.save(f, "png")
    return (w, h)


if __name__ == "__main__":
    # Parse command line
    parser = optparse.OptionParser(usage="Usage: %prog [options]", description=description)
    parser.add_option("-n", "--name", dest="name",
                      help="IPC device name and description string. For example QFP50P900X900-48", metavar="IPCNAME")
    parser.add_option("--footlen", dest="footlen", type="float",
                      help="L - Terminal (lead) length (nominal, heel-to-toe) [mm]", metavar="N")
    parser.add_option("--termlen", dest="termlen", type="float",
                      help="L1 - Terminal (lead) length (package-to-toe) [mm]", metavar="N")
    parser.add_option("--termwidth", dest="termwidth", type="float",
                      help="b - Terminal (lead) width (maximum) [mm]", metavar="N")
    parser.add_option("--density", "--density", dest="density",
                      help="IPC-7351 density level: L (least), N (nominal), M (most)")
    parser.add_option("--toe-protrusion", dest="jt", type="float",
                      help="Override toe protrusion (outside pad length) [mm]", metavar="N")

    group = optparse.OptionGroup(parser, "Output format options")
    group.add_option("--format", dest="format", default="kicad_mod",
                      help="Output file format: kicad_mod (new s-record file format), "
                     "emp (exported legacy format module), "
                     "cairo-png (high quality image), png (image)", metavar="FORMAT")
    group.add_option("--outfile", dest="outfile", default="out",
                      help="Output file name", metavar="FILE")
    group.add_option("--scale", dest="pngscale", type="int", default="8",
                     help="Image scale in number of pixels per mm", metavar="N")
    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    if not options.name:
        parser.error("-n argument is mandatory")

    generator = None
    if re.match("^QFP", options.name):
        generator = qfp.Qfp()
    if re.match("^SOIC", options.name):
        generator = soic.Soic()
    if re.match("^SOP", options.name):
        generator = soic.Soic()

    generator.parse_ipc_name(options.name)
    if options.density:
        generator.set_density(options.density)
    if options.footlen: # "L" in MSC-026: 0.6mm
        generator.params.footlen = options.footlen
    if options.termlen: # "L1" in MSC-026: 1.0mm
        generator.params.termlen = options.termlen
    if options.termwidth: # "b" in MSC-026, varies with pitch
        generator.params.termwidth = options.termwidth
    if options.jt:
        generator.params.JT = options.jt

    package = generator.generate()

    if options.format == "kicad_mod":
        f = open(options.outfile, "w")
        make_kicad_mod(f, options.name, package)
        f.close()

    elif options.format == "emp":
        f = open(options.outfile, "w")
        make_emp(f, options.name, package)
        f.close()

    elif options.format == "cairo-png":
        make_cairo_png(options.outfile, options.pngscale, package)

    elif options.format == "png":
        f = open(options.outfile, "w")
        make_pil_png(f, options.pngscale, package)
        f.close()

    else:
        parser.error("Unsupported output format")
