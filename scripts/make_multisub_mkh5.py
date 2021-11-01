"""create mkh5 format .h5 and epoch files with multiple subjects for testing

Each "subject" is a copy of sub000
"""

import os
import sys
from pathlib import Path
import warnings
import shutil
import pprint as pp
import numpy as np
import h5py
import mkpy
import spudtr
import mkpy.mkh5 as mkh5


warnings.filterwarnings("always", category=UserWarning)
MDE_HOME = Path(".").resolve().parents[0]

print(os.environ["CONDA_DEFAULT_ENV"])
print(sys.version)
for pkg in [mkpy, spudtr]:
    print(pkg.__name__, pkg.__version__, pkg.__file__)

# calibration parameters
CAL_KWARGS = dict(
    n_points=5,  # samples to average
    cal_size=10,  # pulse step in uV
    lo_cursor=-40,  # center of pre-step interval in ms
    hi_cursor=40,  # center of post-step interval in ms
    cal_ccode=0,  # log_ccode for calibration pulse data block
)

# use these to set the epoch table name, and pre, post stimulus boundaries
EPOCH_SPECS = {
    "ms100": (-50, 50),
    "ms1500": (-750, 750),
}

FFORMATS = ["h5", "pdh5", "feather"]


# build some different h5 data group trees
N_SUBS = [3, 4]
N_EXPS = len(N_SUBS)

# multiple sub_ids at top level
DATA_GROUP_PATHS = {
    "test_a": [f"s{s:02d}" for s in range(N_SUBS[0])]
}

# split session experiment
DATA_GROUP_PATHS["test_b"] = [
    f"s{sub:02d}/{visit}" for sub in range(N_SUBS[1]) for visit in ['baseline', 'yr1', 'yr2'] 
]

# multiple expts, multiple sub_ids
DATA_GROUP_PATHS["test_c"] = []
for expt_n in range(N_EXPS):
    for sub_n in range(N_SUBS[expt_n]):
        DATA_GROUP_PATHS["test_c"].append(f"expt_{expt_n+1}/s{sub_n:02}")

def jitter_data(mkh5_f):
    """jitter EEG ata w/ random normal noise, skip cal data blocks"""

    h5_data = mkh5.mkh5(mkh5_f)
    dbps = h5_data.dblock_paths
    for dbp in dbps:
        hdr, data = h5_data.get_dblock(dbp)
        eeg_chans = [
            stream
            for stream in hdr["streams"].keys()
            if "dig_chan" in hdr["streams"][stream]["source"]
        ]

        cal_dblocks = set([
            hdr["streams"][eeg_chan]["cals"]["cal_dblock"][0]
            for eeg_chan in eeg_chans
        ])

        # skip this dblock if it was used for calibration
        if any(dbp in cal_dblock for cal_dblock in cal_dblocks):
            print("not jittering cal dblock: ", dbp)
            continue
        else:
            print("jittering ", dbp)

        # add channel-wise scaled normal random variability
        with h5py.File(mkh5_f, 'r+') as raw_h5:
            for eeg_chan in eeg_chans:
                raw_h5[dbp][eeg_chan] += np.random.normal(
                    loc=0,
                    scale=raw_h5[dbp][eeg_chan].astype(float).std(),
                    size=(len(raw_h5[dbp]), ),
                )

    
def make_p50(test_name, paths, export_epochs=False):
    """paired click recording and data interchange epochs"""

    crw = MDE_HOME / "mkdig/sub000p5.crw"  # EEG recording
    log = MDE_HOME / "mkdig/sub000p5.x.log"  # events
    yhdr = MDE_HOME / "mkpy/sub000p5.yhdr"  # extra header info

    # set calibration data filenames
    cals_crw = MDE_HOME / "mkdig/sub000c5.crw"
    cals_log = MDE_HOME / "mkdig/sub000c5.x.log"
    cals_yhdr = MDE_HOME / "mkpy/sub000c5.yhdr"

    # HDF5 file with EEG recording, events, and header
    p50_h5_f = MDE_HOME / f"multisub_data/p50_{test_name}.h5"
    p50_h5 = mkh5.mkh5(p50_h5_f)
    p50_h5.reset_all()
    for dgp in paths:
        p50_h5.create_mkdata(dgp, crw, log, yhdr)
        p50_h5.append_mkdata(dgp, cals_crw, cals_log, cals_yhdr)
        p50_h5.calibrate_mkdata(dgp, **CAL_KWARGS)

    # randomly swizzle EEG data a bit 
    jitter_data(p50_h5_f)

    # snapshot calibrated h5 file before tagging events
    no_epochs_h5_f = Path(str(p50_h5_f).replace('.h5', '_no_epoch_tables.h5'))
    shutil.copyfile(p50_h5_f, no_epochs_h5_f)

    # 1. scan event code pattern tags into the event table
    p50_event_table = p50_h5.get_event_table(MDE_HOME / "mkpy/p50_codemap.ytbl")

    for epoch_name, (pre, post) in EPOCH_SPECS.items():
        print(epoch_name, pre, post)

        # 2. set the epoch_table names and interval boundaries
        p50_h5.set_epochs(epoch_name, p50_event_table, pre, post)

        # 3. optionally export the epochs DATA ... EEG and events.
        if export_epochs:
            # multiple export formats for demonstration, in practice pick one format
            for ffmt in FFORMATS:
                _fname = f"{str(p50_h5_f).replace('.h5','')}.{epoch_name}.epochs.{ffmt}"
                print(f"exporting p50 {epoch_name} as {ffmt}: {_fname}")

                p50_h5.export_epochs(epoch_name, _fname, file_format=ffmt)


def make_p3(test_name, paths, export_epochs=False):
    """counterbalanced hi tone, low tone oddball recording and epochs"""

    # set filenames
    crw = MDE_HOME / "mkdig/sub000p3.crw"  # EEG recording
    log = MDE_HOME / "mkdig/sub000p3.x.log"  # events
    yhdr = MDE_HOME / "mkpy/sub000p3.yhdr"  # extra header info

    # set calibration data filenames
    cals_crw = MDE_HOME / "mkdig/sub000c.crw"
    cals_log = MDE_HOME / "mkdig/sub000c.x.log"
    cals_yhdr = MDE_HOME / "mkpy/sub000c.yhdr"

    # HDF5 file with EEG recording, events, and header
    p3_h5_f = MDE_HOME / f"multisub_data/p3_{test_name}.h5"

    # build mkpy.mkh5 format data file and calibrate
    p3_h5 = mkh5.mkh5(p3_h5_f)
    p3_h5.reset_all()
    for path in paths:
        p3_h5.create_mkdata(path, crw, log, yhdr)
        p3_h5.append_mkdata(path, cals_crw, cals_log, cals_yhdr)
        p3_h5.calibrate_mkdata(path, **CAL_KWARGS)

    # randomly jitter EEG data 
    jitter_data(p3_h5_f)

    # snapshot calibrated h5 file before tagging events
    no_epochs_h5_f = Path(str(p3_h5_f).replace('.h5', '_no_epoch_tables.h5'))
    shutil.copyfile(p3_h5_f, no_epochs_h5_f)

    
    # 1. scan events into the event table
    p3_event_table = p3_h5.get_event_table(MDE_HOME / "mkpy/p3_codemap.ytbl")

    for epoch_name, (pre, post) in EPOCH_SPECS.items():
        print(epoch_name, pre, post)

        # 2. set the epoch specs
        p3_h5.set_epochs(epoch_name, p3_event_table, pre, post)

        # 3. optionally export epochs
        if export_epochs:
            for ffmt in FFORMATS:

                _fname = f"{str(p3_h5_f).replace('.h5','')}.{epoch_name}.epochs.{ffmt}"
                print(f"exporting p3 {epoch_name} as {ffmt}: {_fname}")
                p3_h5.export_epochs(epoch_name, _fname, file_format=ffmt)


def make_wr(test_name, paths, export_epochs=False):
    """continous word-recognition paradigm recording and epochs"""

    # set filenames
    crw = MDE_HOME / "mkdig/sub000wr.crw"  # EEG recording
    log = MDE_HOME / "mkdig/sub000wr.x.log"  # events
    yhdr = MDE_HOME / "mkpy/sub000wr.yhdr"  # extra header info

    # set calibration data filenames
    cals_crw = MDE_HOME / "mkdig/sub000c.crw"
    cals_log = MDE_HOME / "mkdig/sub000c.x.log"
    cals_yhdr = MDE_HOME / "mkpy/sub000c.yhdr"

    # HDF5 file with EEG recording, events, and header
    # wr_h5_f = MDE_HOME / "multisub_data/sub000wr.h5"
    wr_h5_f = MDE_HOME / f"multisub_data/wr_{test_name}.h5"
    wr_h5 = mkh5.mkh5(wr_h5_f)
    wr_h5.reset_all()

    for path in paths:
        wr_h5.create_mkdata(path, crw, log, yhdr)
        wr_h5.append_mkdata(path, cals_crw, cals_log, cals_yhdr)
        wr_h5.calibrate_mkdata(path, **CAL_KWARGS)

    # randomly jitter EEG data
    jitter_data(wr_h5_f)

    # snapshot calibrated h5 file before tagging events
    no_epochs_h5_f = Path(str(wr_h5_f).replace('.h5', '_no_epoch_tables.h5'))
    shutil.copyfile(wr_h5_f, no_epochs_h5_f)

    
    # 1. scan the event codes into the event table
    wr_event_table = wr_h5.get_event_table(MDE_HOME / "mkpy/wr_codemap.xlsx")

    # define the epoch names and boundaries
    for epoch_name, (pre, post) in EPOCH_SPECS.items():
        print(epoch_name, pre, post)

        # set the epoch name and boundaries
        wr_h5.set_epochs(epoch_name, wr_event_table, pre, post)

        # 3. optionally export epochs
        if export_epochs:
            for ffmt in FFORMATS:
                _fname = f"{str(wr_h5_f).replace('.h5','')}.{epoch_name}.epochs.{ffmt}"
                print(f"exporting wr {epoch_name} as {ffmt}: {_fname}")

                # 3. export the pochs
                wr_h5.export_epochs(epoch_name, _fname, file_format=ffmt)


def make_pm(test_name, paths, export_epochs=False):
    """picture recogntion memory recording and epochs"""

    from make_pm_codemaps import PM_STUDY_CODEMAP_F, PM_TEST_CODEMAP_F

    # set filenames
    crw = MDE_HOME / "mkdig/sub000pm.crw"  # EEG recording
    log = MDE_HOME / "mkdig/sub000pm.x.log"  # events
    yhdr = MDE_HOME / "mkpy/sub000pm.yhdr"  # extra header info

    # set calibration data filenames
    cals_crw = MDE_HOME / "mkdig/sub000c.crw"
    cals_log = MDE_HOME / "mkdig/sub000c.x.log"
    cals_yhdr = MDE_HOME / "mkpy/sub000c.yhdr"

    # HDF5 file with EEG recording, events, and header
    pm_h5_f = MDE_HOME / f"multisub_data/pm_{test_name}.h5"

    # convert to HDF5 and calibrate
    pm_h5 = mkh5.mkh5(pm_h5_f)
    pm_h5.reset_all()

    for path in paths:
        pm_h5.create_mkdata(path, crw, log, yhdr)
        pm_h5.append_mkdata(path, cals_crw, cals_log, cals_yhdr)
        pm_h5.calibrate_mkdata(path, **CAL_KWARGS)

    # randomly jitter EEG
    jitter_data(pm_h5_f)
    
    # snapshot calibrated h5 file before tagging events
    no_epochs_h5_f = Path(str(pm_h5_f).replace('.h5', '_no_epoch_tables.h5'))
    shutil.copyfile(pm_h5_f, no_epochs_h5_f)

    # 1. scan study and test phase events into the event tables
    pm_study_event_table = pm_h5.get_event_table(PM_STUDY_CODEMAP_F)
    pm_test_event_table = pm_h5.get_event_table(PM_TEST_CODEMAP_F)

    # --------------------------------------------
    # MODIFY THE STUDY AND TEST PHASE EVENT TABLES
    # ---------------------------------------------

    # 1.1 prune both event tables to unique single trials

    # study phase response tagged single trials are coded
    # with study table bin id > 2000
    pm_study_events_for_epochs = (
        pm_study_event_table.query("is_anchor==True and study_bin_id >= 2000")
        .copy()
        .set_index("item_id")
        .sort_index()
    )

    # test phase response-tagged single trials are coded
    # with test table bin id > 1000
    pm_test_events_for_epochs = (
        pm_test_event_table.query("is_anchor==True and test_bin_id >= 1000")
        .copy()
        .set_index("item_id")
        .sort_index()
    )

    # 1.2 align the study phase items with subsequent test phase subsequent responses
    # align the test phase subsequent responses with the study phase items
    pm_study_events_for_epochs = pm_study_events_for_epochs.join(
        pm_test_events_for_epochs[["test_response", "accuracy"]],
        how="left",
        on="item_id",
    )

    # 1.3 align test phase items with the previous study phase
    # like/dislike responses
    pm_test_events_for_epochs = pm_test_events_for_epochs.join(
        pm_study_events_for_epochs["study_response"], how="left", on="item_id"
    )

    # ---------------------------------------------
    # Set and export epochs
    # ---------------------------------------------
    # loop on the phases
    phases = {"study": pm_study_events_for_epochs, "test": pm_test_events_for_epochs}
    for phase, events in phases.items():
        for epoch_name, (pre, post) in EPOCH_SPECS.items():

            key = f"{phase}_{epoch_name}"
            print(key, pre, post)

            # 2. set the epochs tables
            pm_h5.set_epochs(key, events, pre, post)

            # 3. optionally export epochs
            if export_epochs:
                for ffmt in FFORMATS:
                    _fname = f"{str(pm_h5_f).replace('.h5','')}.{epoch_name}.epochs.{ffmt}"
                    print(f"exporting pm {key} as {ffmt}: {_fname}")
                    pm_h5.export_epochs(key, _fname, file_format=ffmt)


# ------------------------------------------------------------
# Resting EEG
def make_eeg(test_name, paths, export_epochs=False):
    # 1. set the fileHDF5 file and load the EEG data
    eeg_h5_f = MDE_HOME / f"multisub_data/eeg_{test_name}.h5"
    eeg_h5 = mkh5.mkh5(eeg_h5_f)  # wipe previous
    eeg_h5.reset_all()  # wipe previous

    cals_crw = MDE_HOME / "mkdig/sub000c.crw"
    cals_log = MDE_HOME / "mkdig/sub000c.x.log"
    cals_yhdr = MDE_HOME / "mkpy/sub000c.yhdr"
    for path in paths:
        for cond in ["open", "closed"]:
            crw = MDE_HOME / f"mkdig/sub000r{cond[0]}.crw"  # resting EEG eyes open
            log = MDE_HOME / f"mkdig/sub000r{cond[0]}.x.log"  # events
            yhdr = MDE_HOME / f"mkpy/sub000r{cond[0]}.yhdr"  # extra header info

            dgp = f"{path}/{cond}"
            print(dgp)
            eeg_h5.create_mkdata(dgp, crw, log, yhdr)
            eeg_h5.append_mkdata(dgp, cals_crw, cals_log, cals_yhdr)
            eeg_h5.calibrate_mkdata(dgp, **CAL_KWARGS)

    # randomly jitter EEG data
    jitter_data(eeg_h5_f)


if __name__ == "__main__":

    pp.pprint(DATA_GROUP_PATHS)

    # FIX ME: pm export epochs crashed on HDF5 max size error, not sure why
    # check that study-test join doesn't cross column keys?
    # TPU 11/01/21
    export_epochs = False
    for mkh5_maker in [make_eeg, make_p50, make_p3, make_wr, make_pm]:
        for test_name, paths in DATA_GROUP_PATHS.items():
            mkh5_maker(test_name, paths, export_epochs)
        
