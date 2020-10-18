import os
import sys
import mkpy
import spudtr
import mkpy.mkh5 as mkh5

from pathlib import Path
import warnings

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
    "ms3000": (-1500, 1500),
    "ms10000": (-5000, 5000),
}

FFORMATS = ["h5", "pdh5", "feather"]


def make_p50():
    """paired click recording and data interchange epochs"""

    crw = MDE_HOME / "mkdig/sub000p5.crw"  # EEG recording
    log = MDE_HOME / "mkdig/sub000p5.x.log"  # events
    yhdr = MDE_HOME / "mkpy/sub000p5.yhdr"  # extra header info

    # set calibration data filenames
    cals_crw = MDE_HOME / "mkdig/sub000c5.crw"
    cals_log = MDE_HOME / "mkdig/sub000c5.x.log"
    cals_yhdr = MDE_HOME / "mkpy/sub000c5.yhdr"

    # HDF5 file with EEG recording, events, and header
    p50_h5_f = MDE_HOME / "data/sub000p50.h5"

    # build mkpy.mkh5 format data file and calibrate
    p50_h5 = mkh5.mkh5(p50_h5_f)
    p50_h5.reset_all()
    p50_h5.create_mkdata("sub000", crw, log, yhdr)

    p50_h5.append_mkdata("sub000", cals_crw, cals_log, cals_yhdr)
    p50_h5.calibrate_mkdata("sub000", **CAL_KWARGS)

    # 1. scan event code pattern tags into the event table
    p50_event_table = p50_h5.get_event_table(MDE_HOME / "mkpy/p50_codemap.ytbl")

    for epoch_name, (pre, post) in EPOCH_SPECS.items():
        print(epoch_name, pre, post)

        # 2. set the epoch_table names and interval boundaries
        p50_h5.set_epochs(epoch_name, p50_event_table, pre, post)

        # multiple export formats for demonstration, in practice pick one format
        for ffmt in FFORMATS:
            _fname = f"{MDE_HOME}/data/sub000p50.{epoch_name}.epochs.{ffmt}"
            print(f"exporting p50 {epoch_name} as {ffmt}: {_fname}")

            # 3.  export the epochs DATA ... EEG and events.
            p50_h5.export_epochs(epoch_name, _fname, file_format=ffmt)


def make_p3():
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
    p3_h5_f = MDE_HOME / "data/sub000p3.h5"

    # build mkpy.mkh5 format data file and calibrate
    p3_h5 = mkh5.mkh5(p3_h5_f)
    p3_h5.reset_all()
    p3_h5.create_mkdata("sub000", crw, log, yhdr)

    p3_h5.append_mkdata("sub000", cals_crw, cals_log, cals_yhdr)
    p3_h5.calibrate_mkdata("sub000", **CAL_KWARGS)

    # 1. scan events into the event table
    p3_event_table = p3_h5.get_event_table(MDE_HOME / "mkpy/p3_codemap.ytbl")

    for epoch_name, (pre, post) in EPOCH_SPECS.items():
        print(epoch_name, pre, post)

        # 2. set the epoch specs
        p3_h5.set_epochs(epoch_name, p3_event_table, pre, post)

        # multiple export formats for demonstration, in practice pick one format
        for ffmt in FFORMATS:

            _fname = f"{MDE_HOME}/data/sub000p3.{epoch_name}.epochs.{ffmt}"
            print(f"exporting p3 {epoch_name} as {ffmt}: {_fname}")

            # 3. this exports the epochs DATA ... EEG and events.
            p3_h5.export_epochs(epoch_name, _fname, file_format=ffmt)


def make_wr():
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
    wr_h5_f = MDE_HOME / "data/sub000wr.h5"
    wr_h5 = mkh5.mkh5(wr_h5_f)
    wr_h5.reset_all()
    wr_h5.create_mkdata("sub000", crw, log, yhdr)

    wr_h5.append_mkdata("sub000", cals_crw, cals_log, cals_yhdr)
    wr_h5.calibrate_mkdata("sub000", **CAL_KWARGS)

    # 1. scan the event codes into the event table
    wr_event_table = wr_h5.get_event_table(MDE_HOME / "mkpy/wr_codemap.xlsx")

    # define the epoch names and boundaries
    for epoch_name, (pre, post) in EPOCH_SPECS.items():
        print(epoch_name, pre, post)

        # set the epoch name and boundaries
        wr_h5.set_epochs(epoch_name, wr_event_table, pre, post)

        # multiple export formats for demonstration, in practice pick one
        for ffmt in FFORMATS:
            _fname = f"{MDE_HOME}/data/sub000wr.{epoch_name}.epochs.{ffmt}"
            print(f"exporting wr {epoch_name} as {ffmt}: {_fname}")

            # 3. export the pochs
            wr_h5.export_epochs(epoch_name, _fname, file_format=ffmt)


def make_pm():
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
    pm_h5_f = MDE_HOME / "data/sub000pm.h5"

    # convert to HDF5 and calibrate
    pm_h5 = mkh5.mkh5(pm_h5_f)
    pm_h5.reset_all()
    pm_h5.create_mkdata("sub000", crw, log, yhdr)

    pm_h5.append_mkdata("sub000", cals_crw, cals_log, cals_yhdr)
    pm_h5.calibrate_mkdata("sub000", **CAL_KWARGS)

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

            pm_h5.set_epochs(key, events, pre, post)

            # multiple export formats for demonstration, in practice pick one
            for ffmt in FFORMATS:
                _fname = f"{MDE_HOME}/data/sub000pm.{key}.epochs.{ffmt}"
                print(f"exporting pm {key} as {ffmt}: {_fname}")

                # this exports the epochs DATA ... EEG and events.
                pm_h5.export_epochs(key, _fname, file_format=ffmt)


# ------------------------------------------------------------
# Resting EEG
def make_eeg():
    # 1. set the fileHDF5 file and load the EEG data
    eeg_h5_f = MDE_HOME / f"data/sub000eeg.h5"
    eeg_h5 = mkh5.mkh5(eeg_h5_f)  # wipe previous
    eeg_h5.reset_all()  # wipe previous

    for h5_group in ["open", "closed"]:
        crw = MDE_HOME / f"mkdig/sub000r{h5_group[0]}.crw"  # resting EEG eyes open
        log = MDE_HOME / f"mkdig/sub000r{h5_group[0]}.x.log"  # events
        yhdr = MDE_HOME / f"mkpy/sub000r{h5_group[0]}.yhdr"  # extra header info

        # eyes open, closed EEG data sets
        eeg_h5.create_mkdata(h5_group, crw, log, yhdr)

    # 2. set calibration pulse parameters and files
    pts, pulse, lo, hi, ccode = 5, 10, -40, 40, 0

    cals_crw = MDE_HOME / "mkdig/sub000c.crw"
    cals_log = MDE_HOME / "mkdig/sub000c.x.log"
    cals_yhdr = MDE_HOME / "mkpy/sub000c.yhdr"

    #  A/D square wave cal data are needed for calibration
    eeg_h5.create_mkdata("cals_AD_before", cals_crw, cals_log, cals_yhdr)

    # this copy is scaled as if EEG data for illustration only
    eeg_h5.create_mkdata("cals_10uV_after", cals_crw, cals_log, cals_yhdr)

    for h5_group in ["open", "closed", "cals_10uV_after"]:

        eeg_h5.calibrate_mkdata(
            h5_group,  # data group to calibrate with these cal pulses
            n_points=pts,  # pts to average
            cal_size=pulse,  # uV
            lo_cursor=lo,  # lo_cursor ms
            hi_cursor=hi,  # hi_cursor ms
            cal_ccode=ccode,  # condition code
            use_cals="cals_AD_before",  # alternate data group to find calibration pulses
        )

    print("\n" * 2)
    print("These are the HDF5 datasets in the HDF5 file")
    dblock_paths = eeg_h5.dblock_paths

    print(dblock_paths)


if __name__ == "__main__":

    make_p50()
    make_p3()
    make_wr()
    make_pm()
    make_eeg()
