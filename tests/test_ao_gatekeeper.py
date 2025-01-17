import time
from copy import deepcopy

import pytest

from gatekeeper.gatekeepers.ao_gatekeeper import AOGateKeeper
from gatekeeper.utils.logging import logger

logger.setLevel("DEBUG")


@pytest.fixture
def gk():

    cfg = {
        "max_amp_mA": 6,
        "charge_discharge_time_ratio": 1,
        "charge_discharge_amp_ratio": 1,
        "max_width_ms": 0.2,
        "freq_range": [130, 130],
        "white_list_contacts": ["10273", "10276"],
    }
    gk = AOGateKeeper(**cfg)
    return gk


def test_setup_with_incomplete_params():

    # only the mandatory params
    cfg = {
        "max_amp_mA": 6,
        "charge_discharge_time_ratio": 1,
        "charge_discharge_amp_ratio": 1,
        "max_width_ms": 0.2,
        "freq_range": [130, 130],
        "white_list_contacts": ["10273", "10276"],
    }

    gk = AOGateKeeper(**cfg)

    # everything is in setup
    for key in cfg.keys():
        assert getattr(gk, key) == cfg[key]

    # assert that each of the missing keys is raising and error
    for k in cfg.keys():
        cfg_copy = deepcopy(cfg)
        del cfg_copy[k]

        with pytest.raises(TypeError):
            gk = AOGateKeeper(**cfg_copy)


def test_ok_msg(gk):

    ok_msg = 'STARTSTIM|{"FirstPhaseAmpl_mA": 6.0, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -6.0, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'
    assert gk.validate_stim_command(ok_msg) is True


def test_amplitude_issues(gk):
    amp_too_high_1 = 'STARTSTIM|{"FirstPhaseAmpl_mA": 6.1, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -5.1, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'

    amp_too_high_2 = 'STARTSTIM|{"FirstPhaseAmpl_mA": 5.1, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -6.1, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'

    amp_imbalanced = 'STARTSTIM|{"FirstPhaseAmpl_mA": 5.1, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -1.1, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'

    assert gk.validate_stim_command(amp_too_high_1) is False
    assert gk.validate_stim_command(amp_too_high_2) is False
    assert gk.validate_stim_command(amp_imbalanced) is False


def test_pulse_width_issues(gk):
    pw_too_high_1 = 'STARTSTIM|{"FirstPhaseAmpl_mA": 5.1, "FirstPhaseWidth_mS": 0.3, "SecondPhaseAmpl_mA": -5.1, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'

    pw_too_high_2 = 'STARTSTIM|{"FirstPhaseAmpl_mA": 5.1, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -5.1, "SecondPhaseWidth_mS": 0.3, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'

    pw_imbalanced = 'STARTSTIM|{"FirstPhaseAmpl_mA": 5.1, "FirstPhaseWidth_mS": 0.3, "SecondPhaseAmpl_mA": -5.1, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'

    assert gk.validate_stim_command(pw_too_high_1) is False
    assert gk.validate_stim_command(pw_too_high_2) is False
    assert gk.validate_stim_command(pw_imbalanced) is False


def test_channel_definition_issues(gk):
    stim_ch_wrong = 'STARTSTIM|{"FirstPhaseAmpl_mA": 5.1, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -5.1, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10274", "ReturnChannel": "10276"}'
    ret_ch_wrong = 'STARTSTIM|{"FirstPhaseAmpl_mA": 5.1, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -5.1, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10279"}'

    assert gk.validate_stim_command(stim_ch_wrong) is False
    assert gk.validate_stim_command(ret_ch_wrong) is False


def test_frequency_issues(gk):

    freq_not_in_range = 'STARTSTIM|{"FirstPhaseAmpl_mA": 5.1, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -5.1, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 131, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'

    assert gk.validate_stim_command(freq_not_in_range) is False
    # check that if freq is indeed a range with more that one frequ, it still works
    gk.freq_range = [130, 131]

    freq_in_range = 'STARTSTIM|{"FirstPhaseAmpl_mA": 5.1, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -5.1, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130.5, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'
    assert gk.validate_stim_command(freq_in_range) is True


def test_grace_period(gk):
    gk.grace_period_s = 0.1

    ok_msg = 'STARTSTIM|{"FirstPhaseAmpl_mA": 6.0, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -6.0, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'

    # Immediate change in on state
    gk.validate_stim_command(ok_msg)
    assert gk.validate_stim_command(ok_msg) is False  # within grace period
    time.sleep(0.1)
    assert gk.validate_stim_command(ok_msg) is True  # within grace period

    # Immediately turning on again
    gk.validate_stim_command("STOPSTIM|{}")
    assert gk.validate_stim_command(ok_msg) is False  # within grace period
    time.sleep(0.1)
    assert gk.validate_stim_command(ok_msg) is True  # within grace period

    # Immediate turning off (still possible manually on AO machine, but not via algo)
    gk.validate_stim_command(ok_msg)
    assert gk.validate_stim_command("STOPSTIM|{}") is False  # within grace period
    time.sleep(0.1)
    assert gk.validate_stim_command("STOPSTIM|{}") is True  # within grace period
