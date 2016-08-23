from __future__ import print_function

import sys

from fontTools import agl

class GOADBParser(object):
    def __init__(self, path):
        self.order = []
        self.names = {}
        self.encodings = {}
        self._path = path
        self._parse()

    def _parseUni(self, name):
        if name.startswith("uni") and len(name) == 7:
            encoding = name[3:]
        elif name.startswith("u") and len(name) <= 7:
            encoding = name[1:]
        else:
            return None

        try:
            return int(encoding, 16)
        except ValueError:
            return None

    def _parse(self):
        with open(self._path) as fd:
            goadb = fd.read()
            for line in goadb.splitlines():
                if "#" in line:
                    line = line.split('#')[0]

                if not line:
                    continue

                split = line.split()
                if len(split) < 2:
                    print("Bad line ignored: %s" % line, file=sys.stderr)
                    continue

                final_name = split[0]
                work_name = split[1]
                self.names[work_name] = final_name
                self.order.append(work_name)

                encoding = None
                if len(split) > 2:
                    encoding = self._parseUni(split[2])
                    if encoding is None:
                        print("Bad glyph encoding ignored: %s" % split[2],
                              file=sys.stderr)
                else:
                    if final_name in agl.AGL2UV:
                        encoding = agl.AGL2UV[final_name]
                    else:
                        encoding = self._parseUni(final_name)

                if encoding is not None:
                    self.encodings[work_name] = encoding

if __name__ == "__main__":
    goadb = GOADBParser(sys.argv[1])
