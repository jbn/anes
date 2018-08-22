#!/usr/bin/env python
import pandas as pd
import os
import json
import modpipe

OUTPUT_PATH = os.path.join("data", "clean", "anes.tsv")
INPUT_PATH = os.path.join("data", "raw", "anes_timeseries_cdf_rawdata.txt")
CODEBOOK_PATH = os.path.join("data", "clean", "anes_cb.json")

with open(CODEBOOK_PATH) as fp:
    cb = json.load(fp)

df = pd.read_csv(INPUT_PATH, sep="|", low_memory=False, dtype=str)

with modpipe.ModPipe("df_pipeline") as pipe:
    new_df = pipe(cb, df)

new_df.to_csv(OUTPUT_PATH, sep="\t")
