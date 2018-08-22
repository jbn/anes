import numpy as np


BLANK_CODING = dict(zip([' ', '  ', '   ', '    '], [-101, -102, -103, -104]))

EXPECTED_OBJS = {'VERSION', 'VCF0170C', 'VCF0170D', 'VCF0900C', 'VCF0901B'}

EXPECTED_FLOATS = {'VCF0011Y', 'VCF0010Z', 'VCF0011X', 'VCF0010Y',
                   'VCF0010X', 'VCF0011Z', 'VCF0009X', 'VCF0009Y', 'VCF0009Z'}


def _attempt_numeric(x):
    try:
        return x.astype('i4')
    except ValueError:
        try:
            return x.astype('f4')
        except ValueError:
            return x


def setup(cb, df):
    return {'cb': cb}, df


def convert_all_columns_to_uppercase(env, df):
    df.columns = df.columns.str.upper()
    return env, df


def build_new_df(env, df):
    new_df = df[['VERSION']].copy()

    columns, blank_counts = [], {}
    for k in df.columns:
        if k == 'VERSION':
            continue

        x = df[k]
        counts = x.value_counts()
        blanks = counts[np.in1d(counts.index, list(BLANK_CODING))]

        if len(blanks) > 0:
            blank_counts[k] = blanks.to_dict()

        new_df[k] = _attempt_numeric(x.replace(BLANK_CODING))

    env['blank_counts'] = blank_counts
    return env, new_df


def verify_only_one_blank_in_any_column(env, df):
    blank_counts = env['blank_counts']
    assert set(len(c) for c in blank_counts.values()) == {1}


def recode_blanks(env, df):
    recoder = dict(zip(range(-104, -100), [-100] * 4))
    df.replace(recoder, inplace=True)


def verify_type_expectations(env, df):
    obj_cols = set(df.columns[df.dtypes == np.object_])
    float_cols = set(df.columns[df.dtypes == np.float32])

    assert obj_cols == EXPECTED_OBJS, obj_cols
    assert float_cols == EXPECTED_FLOATS, obj_cols


def pop_df(env, df):
    return df
