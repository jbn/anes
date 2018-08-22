import pandas as pd
import json
import numpy as np
from tabulate import tabulate
from collections import OrderedDict
import seaborn as sns
from numbers import Number
from functools import reduce
from operator import and_
from IPython.display import Markdown

__title__ = "anes"
__description__ = "ANES for Humans"
__uri__ = "https://github.com/jbn/anes"
__doc__ = __description__ + " <" + __uri__ + ">"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2018 John Bjorn Nelson"
__version__ = "0.0.1"
__author__ = "John Bjorn Nelson"
__email__ = "jbn@abreka.com"


def header(line, level=1):
    return ("#" * level) + " " + line


def var_def_to_md_str(cb, name, include_notes=True):
    var_def = cb['var_defs'].get(name)
    if not var_def:
        return 'Not Found'

    lines = [header(name)]

    module = var_def.get('module')
    if module:
        lines.append(header(module, 2))

    desc = var_def.get('desc', [])
    if module:
        lines.append(desc)

    prompt = var_def.get('prompt')
    if prompt:
        lines.append(header('Prompt', 2))
        lines.extend(prompt)

    if 'codes' in var_def:
        lines.append(header('Codes', 2))

    for k, codes in var_def.get('codes', {}).items():
        if k != 'UNIFORM':
            lines.append(header(k, 3))
        tbl = sorted(list(codes['codes'].items()))
        s = tabulate(tbl, headers=['Code', 'Desc'], tablefmt='pipe')
        lines.append(s)

    source_vars = var_def.get('source_vars')
    if source_vars:
        tbl = [[k, ", ".join(v)] for k, v in sorted(source_vars.items())]
        lines.append(header('Source Vars', 2))
        s = tabulate(tbl, headers=['Year', 'Source Vars'], tablefmt='pipe')
        lines.append(s)

    notes = var_def.get('notes')
    if notes and include_notes:
        lines.append(header('Notes', 2))
        lines.extend(prompt)

    return "\n".join(lines)


def var_names_matching(cb, q):
    q = q.lower()

    matches = set()
    for k, v in cb['var_defs'].items():

        if q in v.get('desc', '').lower():
            matches.add(k)

        if q in v.get('module', '').lower():
            matches.add(k)

    return matches


def collect_missing_codes(cb, var_name):
    missing_values = {-100}

    for k, coding in cb['var_defs'][var_name].get('codes', {}).items():
        for v in coding.get('missing', []):
            if v != 'INAP':
                missing_values.add(int(v))

    return missing_values


def remove_missings(df, cb, var_name):
    x = df[var_name]
    missing_values = collect_missing_codes(cb, var_name)
    return x[~np.in1d(x, list(missing_values))]


class ANES:

    def __init__(self, tsv_path, cb_path):
        with open(cb_path) as fp:
            self.cb = json.load(fp, object_hook=OrderedDict)

        self.df = pd.read_csv(tsv_path, sep="\t")

    def describe(self, var_name, include_notes=True):
        return Markdown(var_def_to_md_str(self.cb, var_name, include_notes))

    def plot_counts(self, var_name, ignore_missing=False):
        if var_name not in self.df.columns:
            return 'not found'

        sns.set_style('white')

        if ignore_missing:
            x = remove_missings(self.df, self.cb, var_name)
        else:
            x = self.df[var_name]

        counts = x.value_counts()
        title = "{} Counts".format(var_name)
        counts.sort_index(ascending=False).plot(kind='barh', title=title)
        sns.despine()

    def search_for(self, q):
        matches = var_names_matching(self.cb, q)
        if not matches:
            return "Not found"

        var_defs = self.cb['var_defs']
        serps = []
        for k in sorted(matches):
            var_def = var_defs[k]
            serps.append([k,
                          var_def.get('module', ''),
                          var_def.get('desc', ''),
                          " ".join(var_def.get('prompt'))])

        s = tabulate(serps, headers=['Name', 'Module', 'Desc', 'Prompt'], tablefmt='pipe')
        return Markdown(s)

    def search_for_vars(self, q):
        matches = var_names_matching(self.cb, q)
        if not matches:
            return None

        res, var_defs = OrderedDict(), self.cb['var_defs']
        for k in sorted(matches):
            var_def = var_defs[k]
            res[k] = var_def.get('desc', '')
        return res

    def select(self, k, *other_ks, years=None, strip_missings=False):
        ks = []

        if years is not None:
            ks.append('VCF0004')
            if isinstance(years, Number):
                years = [years]

        ks.append(k)
        ks.extend(list(other_ks))

        sub_df = self.df[ks].copy()

        if years is not None:
            idx = np.in1d(sub_df['VCF0004'], years)
            sub_df = sub_df[idx]

        if strip_missings:
            conds = []

            for k in sub_df.columns:
                missing_values = collect_missing_codes(self.cb, k)
                x = sub_df[k]
                conds.append(~np.in1d(x, list(missing_values)))

            sub_df = sub_df[reduce(and_, conds)]

        return sub_df
