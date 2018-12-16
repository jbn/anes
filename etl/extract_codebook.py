#!/usr/bin/env python
import json
import os
import re
from collections import OrderedDict
import modpipe


VERSION_RE = re.compile("^RELEASE VERSION:\s+(\d+)")
LINE_SEP = "=" * 99 + "\n"
DATA_PATH = os.path.join("data", "raw", "anes_timeseries_cdf_codebook_var.txt")
OUTPUT_PATH = os.path.join("data", "clean", "anes_cb.json")


def defn_iterator(file_path):
    version = None
    lines = []

    with open(file_path, errors='ignore') as fp:

        # for line in fp:
        #     if version is None:
        #         version = VERSION_RE.search(line).group(1)
        #         yield {'version': version}
        #     elif line == LINE_SEP:
        #         break

        for line in fp:
            if line == LINE_SEP and lines:
                yield lines
                lines = []
            else:
                lines.append(line.rstrip())

    if lines[-1] == "" and lines[-2] == "" and lines[-3] == "1":
        yield lines[:-3]


general_notes, var_defs = [], OrderedDict()

version = None
with modpipe.ModPipe("codebook_pipeline") as pipe:
    for lines in defn_iterator(DATA_PATH):
        if 'version' in lines:
            version = lines['version']
        else:
            res = pipe(lines.copy())
            if '_general_note_lines' in res:
                general_notes.append(res)
            else:
                var_defs[res['name']] = res

codebook = OrderedDict([('version', version)])
codebook['var_defs'] = var_defs
codebook['notes'] = general_notes


with open(OUTPUT_PATH, "w") as fp:
    json.dump(codebook, fp)
