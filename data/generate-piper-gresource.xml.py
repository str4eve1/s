#!/usr/bin/env python3

import sys
from pathlib import Path

infile = sys.argv[1]
outfile = sys.argv[2]
svgdir = sys.argv[3]
print("Using input file: {}".format(infile))
print("Writing to output file: {}".format(outfile))
print("SVG directory: {}".format(svgdir))

with open(infile) as f_in:
    with open(outfile, "w") as f_out:
        for line in f_in:
            if "@SVG_FILES@" in line:
                for svg in sorted(Path(svgdir).glob("*.svg")):
                    f_out.write(
                        line.replace(
                            "@SVG_FILES@", "{}/{}".format(svg.parent.name, svg.name)
                        )
                    )
                continue

            f_out.write(line)
