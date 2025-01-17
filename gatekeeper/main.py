from pathlib import Path
from threading import Event, Thread
from time import sleep

import toml
from dareplane_utils.stream_watcher.lsl_stream_watcher import StreamWatcher
from pylsl import StreamInfo, StreamOutlet

from gatekeeper.gatekeepers.ao_gatekeeper import AOGateKeeper
from gatekeeper.utils.logging import logger

GKMAP = {"dp-ao-communication": AOGateKeeper}


def run_validation_thread(cfg: dict, stop_event: Event):

    gk = GKMAP[cfg["target"]["module"]](**cfg["bounds"])
    sw_in = StreamWatcher(cfg["lsl"]["inlet_name"])
    sw_in.connect_to_stream()
    sleep(0.3)

    in_info = sw_in.inlet.info()

    # spawn an outlet with the same meta information, but a different name and UUID
    out_name = cfg["lsl"]["outlet_name"]
    out_info = StreamInfo(
        name=out_name,
        type=in_info.type(),
        channel_count=in_info.channel_count(),
        nominal_srate=in_info.nominal_srate(),
        channel_format=in_info.channel_format(),
    )
    outlet = StreamOutlet(out_info)

    while not stop_event.is_set():

        sw_in.update()

        if sw_in.n_new > 0:

            logger.debug(f"{sw_in.n_new=}")
            new_msgs = sw_in.unfold_buffer()[-sw_in.n_new :]
            for msg in new_msgs:
                if gk.validate_stim_command(msg[0]):
                    # msg is ok -> forward message
                    logger.debug(
                        f"{msg[0]} is a valid command, will be forwarded to {out_name}"
                    )
                    outlet.push_sample(msg)

            sw_in.n_new = 0

        # 1ms as the LSL stream for string data is slow in the readout anyways (~9ms on MacOS)
        sleep(0.001)


def run_gatekeeper(cfg_file: Path = Path("./configs/ao_comm_cfg.toml")):

    cfg = toml.load(cfg_file)

    stop_event = Event()
    stop_event.clear()

    th = Thread(target=run_validation_thread, args=(cfg, stop_event))
    th.start()

    return th, stop_event
