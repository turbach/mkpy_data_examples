"""demonstrate programmatic codemap generation"""

import re
import pandas as pd
from make_zenodo_files import MDE_HOME

# stim info scraped from .scn scenario files
PM_ITEM_ID_BY_SCN_F = MDE_HOME / "mkpy/pm_item_id_by_scn.tsv"

# study phase codemap
PM_STUDY_CODEMAP_F = MDE_HOME / "mkpy/pm_study_codemap.tsv"

# test phase codemap
PM_TEST_CODEMAP_F = MDE_HOME / "mkpy/pm_test_codemap.tsv"


def make_pm_item_id_by_scn():
    """scrape stimuli out of the presentation files and extract code information"""

    stim_split_re = re.compile(
        r"(?P<soa>\d+)\s+(?P<dur>\d+)\s+(?P<evcode>\d+)\s+"
        r"(?P<type>....)=(?P<stim>.+)[\.]"
    )
    scn_paths = sorted(MDE_HOME.glob("mkstim/pictmem/*.scn"))

    header_str = "".join(
        [
            f"{col:>16}"
            for col in ["ccode", "phase", "condition_id", "item_id", "jpg", "scn"]
        ]
    )
    items = [header_str]
    for scn_path in scn_paths:
        with open(scn_path, "r") as _fh:
            scn = scn_path.stem
            phase = None
            ccode = None
            for phase, ccode in [("study", 2), ("test", 1)]:
                if phase in str(scn_path):
                    break
            assert phase is not None and ccode is not None
            for line in _fh.readlines():
                fields = stim_split_re.match(line)
                if fields is None:
                    continue
                evcode = int(fields["evcode"])

                if evcode > 0 and evcode <= 4:
                    assert fields["type"] == "jpeg"
                    stim = fields["stim"]
                    cond = evcode

                if evcode > 100:
                    item = evcode
                    items.append(
                        "".join(
                            [
                                f"{val:>16}"
                                for val in [ccode, phase, cond, item, stim, scn]
                            ]
                        )
                    )

    with open(PM_ITEM_ID_BY_SCN_F, "w") as _fh:
        _fh.write("\n".join(items))
        _fh.write("\n")


def make_pm_study_phase_codemap():
    """ Study phase """

    # read the item information table
    pm_items = pd.read_csv(PM_ITEM_ID_BY_SCN_F, delim_whitespace=True).query(
        "scn in ['studyp1', 'testp1']"
    )

    # code map
    pm_study_codemap_cols = [
        "regexp",
        "study_bin_id",
        "animacy",
        "study_response",
    ] + list(pm_items.columns)

    # stimulus-response tag template as a Python dictionary
    # The key:val pair says "this code sequence gets these tags"
    # The ITEM_ID string will be replaced by the actual 3-digit item number

    study_code_tags = {
        "(#[12]) 8 (ITEM_ID) 1040": (2000, "like"),
        "(#[12]) 8 1040 (ITEM_ID)": (2001, "like"),
        "(#[12]) 1040 8 (ITEM_ID)": (2002, "like"),
        "(#[12]) 8 (ITEM_ID) 2064": (2100, "dislike"),
        "(#[12]) 8 2064 (ITEM_ID)": (2101, "dislike"),
        "(#[12]) 2064 8 (ITEM_ID)": (2102, "dislike"),
        "(#[12]) 8 (ITEM_ID) (?!(1040|2064))": (2003, "no_response"),
    }

    # the new 4-digit "study_bin_id" tag re-codes the match event 1 or
    # 2 with more information
    #
    #  phase animacy response response_timing
    #    phase: study=2
    #    animacy: 1=animate, 2=inanimate
    #    response(0=like, 1=dislike)
    #    response timing: 0=prompted,1,2 anticipation, 3=no response)
    #
    study_code_tags = {
        # animate
        "(#[1]) 8 (ITEM_ID) 1040": (2100, "animate", "like"),
        "(#[1]) 8 1040 (ITEM_ID)": (2101, "animate", "like"),
        "(#[1]) 1040 8 (ITEM_ID)": (2102, "animate", "like"),
        "(#[1]) 8 (ITEM_ID) 2064": (2110, "animate", "dislike"),
        "(#[1]) 8 2064 (ITEM_ID)": (2111, "animate", "dislike"),
        "(#[1]) 2064 8 (ITEM_ID)": (2112, "animate", "dislike"),
        "(#[1]) 8 (ITEM_ID) (?!(1040|2064))": (2103, "animate", "no_response"),
        # inanimate
        "(#[2]) 8 (ITEM_ID) 1040": (2200, "inanimate", "like"),
        "(#[2]) 8 1040 (ITEM_ID)": (2201, "inanimate", "like"),
        "(#[2]) 1040 8 (ITEM_ID)": (2202, "inanimate", "like"),
        "(#[2]) 8 (ITEM_ID) 2064": (2210, "inanimate", "dislike"),
        "(#[2]) 8 2064 (ITEM_ID)": (2211, "inanimate", "dislike"),
        "(#[2]) 2064 8 (ITEM_ID)": (2212, "inanimate", "dislike"),
        "(#[2]) 8 (ITEM_ID) (?!(1040|2064))": (2203, "inanimate", "no_response"),
    }

    #
    # Build a list of codemap lines.

    # The first line says *any* code matching 1 or 2 gets the tags 200, "_any", 2, ... etc.
    # This tags all matching stimulus events, it is not contingent the response.
    # It is not necessary but it is useful here, we will see why shortly.
    study_code_map = [
        ("(#[1234])", 0, "cal", "cal", 0, "study", 0, -1, "cal", "cal"),
        ("(#[12])", 200, "_any", "_any", 2, "study", 2, -1, "_any", "_any"),
    ]

    # plug each row of the pictmem item info into the template and append the
    # result to the list of codemap lines
    for idx, row in pm_items.query("phase == 'study'").iterrows():
        for pattern, tags in study_code_tags.items():
            code_tags = (
                pattern.replace(
                    "ITEM_ID", str(row.item_id)
                ),  # current item number goes in the template
                *(str(t) for t in tags),
                *(str(c) for c in row),  # this adds the rest of the item to the tags
            )
            study_code_map.append(code_tags)

    # convert the list of lines to a pandas.DataFrame and save as a tab separated text file
    pm_study_codemap = pd.DataFrame(study_code_map, columns=pm_study_codemap_cols)
    pm_study_codemap.to_csv(PM_STUDY_CODEMAP_F, sep="\t", index=False)

    print(pm_study_codemap.shape)
    print(pm_study_codemap)


def make_pm_test_phase_codemap():

    # read the item information table
    pm_items = pd.read_csv(PM_ITEM_ID_BY_SCN_F, delim_whitespace=True).query(
        "scn in ['studyp1', 'testp1']"
    )

    # test phase codemap column names
    pm_test_codemap_cols = [
        "regexp",
        "test_bin_id",
        "animacy",
        "stimulus",
        "test_response",
        "accuracy",
    ] + list(pm_items.columns)

    # test phase template: stimulus, old/new response (include pre-prompt anticipations)
    test_code_tags = {
        # new stim animate
        "(#1) 8 (ITEM_ID) 2064": (1100, "animate", "distractor", "new", "cr"),
        "(#1) 8 2064 (ITEM_ID)": (1101, "animate", "distractor", "new", "cr"),
        "(#1) 2064 8 (ITEM_ID)": (1102, "animate", "distractor", "new", "cr"),
        "(#1) 8 (ITEM_ID) 1040": (1110, "animate", "distractor", "old", "fa"),
        "(#1) 8 1040 (ITEM_ID)": (1111, "animate", "distractor", "old", "fa"),
        "(#1) 1040 8 (ITEM_ID)": (1112, "animate", "distractor", "old", "fa"),
        "(#1) 8 (ITEM_ID) (?!(2064|1040))": (
            1103,
            "animate",
            "distractor",
            "none",
            "nr",
        ),
        # new stim inanimate
        "(#2) 8 (ITEM_ID) 2064": (1200, "inanimate", "distractor", "new", "cr"),
        "(#2) 8 2064 (ITEM_ID)": (1201, "inanimate", "distractor", "new", "cr"),
        "(#2) 2064 8 (ITEM_ID)": (1202, "inanimate", "distractor", "new", "cr"),
        "(#2) 8 (ITEM_ID) 1040": (1210, "inanimate", "distractor", "old", "fa"),
        "(#2) 8 1040 (ITEM_ID)": (1211, "inanimate", "distractor", "old", "fa"),
        "(#2) 1040 8 (ITEM_ID)": (1212, "inanimate", "distractor", "old", "fa"),
        "(#2) 8 (ITEM_ID) (?!(2064|1040))": (
            1203,
            "inanimate",
            "distractor",
            "none",
            "nr",
        ),
        # old stim animate
        "(#3) 8 (ITEM_ID) 1040": (1300, "animate", "studied", "old", "hit"),
        "(#3) 8 1040 (ITEM_ID)": (1301, "animate", "studied", "old", "hit"),
        "(#3) 1040 8 (ITEM_ID)": (1302, "animate", "studied", "old", "hit"),
        "(#3) 8 (ITEM_ID) 2064": (1310, "animate", "studied", "new", "miss"),
        "(#3) 8 2064 (ITEM_ID)": (1311, "animate", "studied", "new", "miss"),
        "(#3) 2064 8 (ITEM_ID)": (1312, "animate", "studied", "new", "miss"),
        "(#3) 8 (ITEM_ID) (?!(2064|1040))": (1303, "animate", "studied", "none", "nr"),
        # old stim inanimate
        "(#4) 8 (ITEM_ID) 1040": (1400, "inanimate", "studied", "old", "hit"),
        "(#4) 8 1040 (ITEM_ID)": (1401, "inanimate", "studied", "old", "hit"),
        "(#4) 1040 8 (ITEM_ID)": (1402, "inanimate", "studied", "old", "hit"),
        "(#4) 8 (ITEM_ID) 2064": (1410, "inanimate", "studied", "new", "miss"),
        "(#4) 8 2064 (ITEM_ID)": (1411, "inanimate", "studied", "new", "miss"),
        "(#4) 2064 8 (ITEM_ID)": (1412, "inanimate", "studied", "new", "miss"),
        "(#4) 8 (ITEM_ID) (?!(2064|1040))": (
            1403,
            "inanimate",
            "studied",
            "none",
            "nr",
        ),
    }

    # initialize the code map to tag stimulus codes, not response contingent
    test_code_map = [
        (
            "(#[1234])",
            0,
            "cal",
            "cal",
            "cal",
            "cal",
            0,
            "test",
            "cal",
            "-1",
            "cal",
            "cal",
        ),
        (
            "(#[1234])",
            10,
            "_any",
            "_any",
            "_any",
            "_any",
            1,
            "test",
            "_any",
            "-1",
            "_any",
            "_any",
        ),
        (
            "(#[1])",
            11,
            "animate",
            "distractor",
            "_any",
            "_any",
            1,
            "test",
            1,
            "-1",
            "_any",
            "_any",
        ),
        (
            "(#[2])",
            12,
            "inanimate",
            "distractor",
            "_any",
            "_any",
            1,
            "test",
            2,
            "-1",
            "_any",
            "_any",
        ),
        (
            "(#[3])",
            13,
            "animate",
            "studied",
            "_any",
            "_any",
            1,
            "test",
            3,
            "-1",
            "_any",
            "_any",
        ),
        (
            "(#[4])",
            14,
            "inanimate",
            "studied",
            "_any",
            "_any",
            1,
            "test",
            4,
            "-1",
            "_any",
            "_any",
        ),
    ]

    # iterate through the item info and plug the item number into the template lines
    for idx, row in pm_items.query("phase == 'test'").iterrows():
        for pattern, tags in test_code_tags.items():
            # condition_id is 1, 2, 3, or 4 only plug into the relevant template lines.
            if re.match(r"^\(#" + str(row.condition_id), pattern):
                code_tags = (
                    pattern.replace("ITEM_ID", str(row.item_id)),
                    tags[0],
                    *(str(t) for t in tags[1:]),
                    *(str(c) for c in row),
                )
                test_code_map.append(code_tags)

    pm_test_codemap = pd.DataFrame(test_code_map, columns=pm_test_codemap_cols)

    # write test demo phase codemap
    pm_test_codemap.to_csv(PM_TEST_CODEMAP_F, sep="\t", index=False)

    print(pm_test_codemap.shape)
    print(pm_test_codemap)


if __name__ == "__main__":
    make_pm_item_id_by_scn()
    make_pm_study_phase_codemap()
    make_pm_test_phase_codemap()
