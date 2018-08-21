import re
from collections import OrderedDict
from modpipe import Done


VAR_NAME_RE = re.compile("^[A-Z0-9abcdexyz]+$")

STUDY_VARIABLE_RE = re.compile("^([^:]+):\s([A-Za-z0-9\- \:\(\)\/\.\,'\$\[\]\#]+)$")

RACE_SUMMARIES = {"Race summary, 3 categories",
                  "Race-ethnicity summary, 4 categories",
                  "Race-ethnicity summary, 7 categories"}

VAR_KINDS = {'AUTHORITARIANISM',
             'CANDIDATE AFFECTS',
             'CANDIDATE CONTACT',
             'CANDIDATE TRAITS',
             'CANDIDATES',
             'CANDIDATES Mention 1',
             'CANDIDATES Mention 2',
             'CANDIDATES Mention 3',
             'CANDIDATES Mention 4',
             'CANDIDATES Mention 5',
             'CONDITION/GOALS OF U.S.',
             'DEMOGRAPHICS',
             'ECONOMIC WELL-BEING',
             'ELECTION',
             'ELECTION/RACE DESCRIPTION',
             'EQUALITARIANISM',
             'GROUP THERMOMETER',
             'HOUSEHOLD COMPOSITION',
             'IDEOLOGY',
             'INTERVIEW DESCRIPTION',
             'ISSUES',
             'ISSUES Mention 1',
             'ISSUES Mention 2',
             'ISSUES Mention 3',
             'IWR DESCRIPTION',
             'IWR OBSERVATION',
             'MEDIA',
             'MOBILIZATION',
             'MORAL TRADITIONALISM',
             'PARTIES',
             'PARTIES Mention 1',
             'PARTIES Mention 2',
             'PARTIES Mention 3',
             'PARTIES Mention 4',
             'PARTIES Mention 5',
             'PARTISANSHIP',
             'PERSONAL EFFICACY',
             'POLITICAL ENGAGEMENT',
             'POLITICAL FIGURE THERMOMETER',
             'POLITICAL INTEREST',
             'POLITICAL KNOWLEDGE',
             'POLITICAL KNOWLEDGE Mention 1',
             'POLITICAL KNOWLEDGE Mention 2',
             'POLITICAL KNOWLEDGE Mention 3',
             'RACE SUMMARY',
             'RACIAL RESENTMENT',
             'RELIGIOSITY',
             'SAMPLE DESCRIPTION',
             'SOCIAL TRUST',
             'STUDY ADMIN',
             'STUDY VARIABLE',
             'SYSTEM SUPPORT',
             'VOTE VALIDATION'}

SECTION_RE = re.compile("^([A-Z\_]+):$\n^([\-]+)", re.M)

QUESTION_PREFIX = re.compile("^[^:]: .*$")

KNOWN_TYPES = {'Character-1', 'Numeric  Dec 0-1', 'Numeric  Dec 4-1'}

SIMPLE_CODE_RE = re.compile("^([0-9\-,]+|INAP)\.$")

CODE_RE = re.compile("^([0-9\-,]+|INAP)\.\s+(.*)?$")

DEGREE_RE = re.compile("^(\d{1,3}\-\d{1,3}) (Degrees)\.$")

RANGE_RE = re.compile("^(\d{1,4}\-\d{1,4})$")

SLOPPY_RANGE_RE = re.compile("^Codes (\d{1,4}\-\d{1,4})(\s* (AND|PLUS))?:$",
                             re.I)

PARTITIONED_CODE_RE = re.compile("^(\d{4}):$")

SOURCE_VAR_RE = re.compile("^(\d{4}): (.*)$")

EXTRANEOUS_WHITESPACE_RE = re.compile("\s{2,}")


LINE_PATCHES = {'3   Not sure; depends; DK; no opinion':
                '3.   Not sure; depends; DK; no opinion',
                '0 -100.   Degrees as given':
                '0-100.   Degrees as given',
                '3-Digit Number 1-182 Coded,  Except:':
                '1-182',
                '999.MD (codes 6-9 in any of: VCF0993,VCF0994,':
                '999. MD (codes 6-9 in any of: VCF0993,VCF0994,',
                "'forms'": "     'forms'",
                'Cross Section (1992)': '    Cross Section (1992)',
                '(1992)': '     (1992)',
                'worked for pay': '    worked for pay'}


def _sstrip(s):
    return EXTRANEOUS_WHITESPACE_RE.sub(s, " ")


def _assert_and_pop_blank(lines):
    line = lines.pop(0)
    assert line == ''


def setup(lines):
    return [LINE_PATCHES.get(line, line) for line in lines], OrderedDict()


def skip_general_notes(lines, var_def):
    if lines[0] == '':
        var_def['_general_note_lines'] = lines
        return Done(var_def)


def extract_variable_name(lines, var_def):
    var_def['var_name'] = lines.pop(0)
    assert VAR_NAME_RE.match(var_def['var_name']), var_def['var_name']

    _assert_and_pop_blank(lines)


def extract_variable_desc(lines, var_def):
    line = lines.pop(0)
    m = STUDY_VARIABLE_RE.match(line)
    if not m:
        assert line in RACE_SUMMARIES, line
        var_def['desc_kind'] = 'RACE SUMMARY'
        var_def['desc'] = "Race-ethnicity summary, 7 categories"
    else:
        var_def['desc_kind'] = m.group(1)
        var_def['desc'] = m.group(2)

    assert var_def['desc_kind'] in VAR_KINDS, var_def['desc_kind']

    _assert_and_pop_blank(lines)


def extract_sections(lines, var_def):
    sections, section = OrderedDict(), None

    while lines:
        if section is None:
            two_lines = "\n".join(lines[:2])
            m = SECTION_RE.match(two_lines)
            if m:
                section = {'name': m.group(1), 'lines': []}
                lines.pop(0)
                lines.pop(0)
                continue

        line = lines.pop(0)

        if section:
            if line == '':
                if section['name'] != 'SOURCE_VARS':
                    sections[section['name']] = section['lines']
                    section = None
            else:
                section['lines'].append(line)

    if section:
        sections[section['name']] = section['lines']

    return sections, var_def


def parse_type(sections, var_def):
    type_list = sections.pop('TYPE')

    assert len(type_list) == 1, type_list
    type_spec = type_list[0]

    assert type_spec in KNOWN_TYPES
    var_def['var_type'] = type_spec


def parse_question(sections, var_def):
    assert 'QUESTION' in sections, sections

    questions, parts = [], []

    for line in sections.pop('QUESTION'):
        if QUESTION_PREFIX.match(line):
            if parts:
                questions.append(_sstrip(" ".join(parts)))
            parts = [line]
        else:
            parts.append(line)

    if parts:
        questions.append(_sstrip(" ".join(parts)))

    var_def['question'] = questions


def _extract_code_groups(lines):
    groups, sub_lines, group = OrderedDict(), [], None,

    for line in lines:
        m = PARTITIONED_CODE_RE.match(line)
        if m:
            if group:
                groups[group] = sub_lines

            group, sub_lines = m.group(1), []
        else:
            if group:
                assert line.startswith(' '), line
                sub_lines.append(line[1:])
            else:
                sub_lines.append(line)

    if group:
        groups[group] = sub_lines
    elif sub_lines:
        groups['UNIFORM'] = sub_lines

    return groups


def _extract_code_line(line):
    m = SIMPLE_CODE_RE.match(line)
    if m:
        return m.group(1), ''

    m = CODE_RE.match(line)
    if m:
        return m.group(1), m.group(2)

    m = DEGREE_RE.match(line)
    if m:
        return m.group(1), 'DEGREES'

    m = RANGE_RE.match(line)
    if m:
        return m.group(1), 'RANGE'

    m = SLOPPY_RANGE_RE.match(line)
    if m:
        return m.group(1), 'RANGE'

    if line == 'Exact number of days is coded, except:':
        return '0-365', 'RANGE'


def _parse_codes(var_type, code_lines):
    coding = OrderedDict()

    k, parts = None, []

    for line in code_lines:
        pair = _extract_code_line(line)
        if pair is not None:
            if k is not None and parts:
                coding[k] = _sstrip(" ".join(parts))

            k = pair[0]
            parts = [pair[1]]
        else:
            if line.strip() == '.':
                continue  # ... continuation

            if line.startswith(' '):
                parts.append(line.strip())
            else:
                assert False, (line, code_lines)

    if k not in coding:
        coding[k] = _sstrip(" ".join(parts))

    return coding


def temp(sections, var_def):
    if var_def['var_name'] in {'VCF0735', 'VCF0735', 'VCF0976', 'VCF9067'}:
        return Done(var_def)


def parse_valid_codes(sections, var_def):
    var_type = var_def['var_type']
    valid_codes = sections.pop('VALID_CODES', None)

    if valid_codes is not None:
        codes = OrderedDict()
        for group, lines in _extract_code_groups(valid_codes).items():
            codes[group] = _parse_codes(var_type, lines)
        var_def['valid_codes'] = codes


def parse_missing_codes(sections, var_def):
    var_type = var_def['var_type']
    missing_codes = sections.pop('MISSING_CODES', None)

    if missing_codes is not None:
        codes = OrderedDict()
        for group, lines in _extract_code_groups(missing_codes).items():
            codes[group] = _parse_codes(var_type, lines)
        var_def['missing_codes'] = codes


def parse_source_vars(sections, var_def):
    lines = sections.pop('SOURCE_VARS', None)
    if lines is None:
        return

    k, source_vars = None, OrderedDict()
    for line in lines:
        m = SOURCE_VAR_RE.match(line)
        if not m:
            if k is not None:
                assert ',' not in line, line
                source_vars[k].append(line.strip())
        else:
            assert m, line
            k = m.group(1)
            source_vars[k] = [s.strip() for s in m.group(2).split(",")]

    var_def['source_vars'] = source_vars


def parse_weights(sections, var_def):
    weights = sections.pop('WEIGHT', None)
    if weights is not None:
        assert len(weights) == 1
        var_def['weights'] = weights[0].split("/")


def parse_notes(sections, var_def):
    notes = sections.pop('NOTES', None)
    if notes is not None:
        var_def['notes'] = "\n".join(notes)


def pop_res(sections, var_def):
    assert not sections, sections
    return var_def
