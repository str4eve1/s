#!/usr/bin/env python3

import sys

infile = sys.argv[1]
outfile = sys.argv[2]
svgs = sys.argv[3:]
print("Using input file: {}".format(infile))
print("Writing to output file: {}".format(outfile))
print("SVG files: {}".format(",".join(svgs)))

with open(infile) as f_in:
    with open(outfile, 'w') as f_out:
        for line in f_in:
            if '@SVG_FILES@' in line:
                for svg in svgs:
                    f_out.write(line.replace('@SVG_FILES@', svg))
                continue

            f_out.write(line)
