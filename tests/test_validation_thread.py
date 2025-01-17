import time
from pathlib import Path

import pytest
import toml
from dareplane_utils.stream_watcher.lsl_stream_watcher import StreamWatcher
from pylsl import StreamInfo, StreamOutlet, resolve_streams

from gatekeeper.gatekeepers.ao_gatekeeper import AOGateKeeper
from gatekeeper.main import run_gatekeeper
from gatekeeper.utils.logging import logger

logger.setLevel("DEBUG")


def test_spawning_the_lsl_streams():

    cfg_pth = Path("./configs/ao_comm_cfg.toml")
    cfg = toml.load(cfg_pth)

    info = StreamInfo(cfg["lsl"]["inlet_name"], "test", 1, 0, "string", "test_inlet")
    in_outlet = StreamOutlet(info)
    th, stop_event = run_gatekeeper(cfg_pth)

    time.sleep(0.5)

    streams = resolve_streams()
    names = [n.name() for n in streams]
    assert cfg["lsl"]["outlet_name"] in names

    stop_event.set()
    th.join()

    time.sleep(0.5)

    streams2 = resolve_streams()
    names2 = [n.name() for n in streams2]
    assert cfg["lsl"]["outlet_name"] not in names2


def test_cmd_from_lsl_to_lsl(tmp_path):
    tmp_path = Path("./")
    cfg = {
        "lsl": {
            "inlet_name": "test_inlet_stream",
            "outlet_name": "test_outlet_stream",
        },
        "target": {"module": "dp-ao-communication"},
        "bounds": {
            "max_amp_mA": 6,
            "charge_discharge_time_ratio": 1,
            "charge_discharge_amp_ratio": 1,
            "max_width_ms": 0.2,
            "freq_range": [130, 130],
            "black_list_freq": [],
            "white_list_contacts": ["10273", "10276"],
            "grace_period_s": 0,
        },
    }

    info = StreamInfo(cfg["lsl"]["inlet_name"], "test", 1, 0, "string", "test_inlet")
    in_outlet = StreamOutlet(info)

    tmp_cfg = tmp_path / "test_cfg.toml"
    toml.dump(cfg, tmp_cfg.open("w"))
    th, stop_event = run_gatekeeper(tmp_cfg)

    # StreamWatcher to check if the command was forwarded
    sw_out = StreamWatcher(cfg["lsl"]["outlet_name"])
    sw_out.connect_to_stream()
    sw_out.update()

    # STOP

    ok_msg = 'STARTSTIM|{"FirstPhaseAmpl_mA": 6.0, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -6.0, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'
    in_outlet.push_sample([ok_msg])
    time.sleep(0.1)  # just to ensure any communication is finished
    sw_out.update()

    assert sw_out.n_new == 1
    assert sw_out.unfold_buffer()[-1][0] == ok_msg
    sw_out.n_new = 0

    fail_msg = 'STARTSTIM|{"FirstPhaseAmpl_mA": 6.1, "FirstPhaseWidth_mS": 0.2, "SecondPhaseAmpl_mA": -6.0, "SecondPhaseWidth_mS": 0.2, "Freq_hZ": 130, "FirstPhaseDelay_mS": 0, "SecondPhaseDelay_mS": 0, "Duration_sec": 1, "StimChannel": "10273", "ReturnChannel": "10276"}'

    in_outlet.push_sample([fail_msg])
    time.sleep(0.1)
    sw_out.update()

    assert sw_out.n_new == 0

    stop_event.set()
    th.join()
