# Implementation of a gatekeeper that checks for valid stimulation commands / e.g. tracking current stim state and enforcing grace period
import json
import time
from dataclasses import dataclass, field

from gatekeeper.utils.logging import logger


@dataclass
class AOGateKeeper:
    max_amp_mA: float
    max_width_ms: float
    freq_range: list
    white_list_contacts: list
    charge_discharge_time_ratio: float
    charge_discharge_amp_ratio: float
    last_stim_command_time_ns: float = time.perf_counter_ns()
    stimulator: str = "not_specified"
    black_list_freq: list = field(default_factory=list)
    grace_period_s: float = 0

    def validate_stim_command(self, cmd: str) -> bool:

        # Using the gatekeeper here (different from control-room callback triggers)
        config = json.loads(cmd.split("|")[1])
        pcomm = cmd.split("|")[0]

        # Turning off only requires grace period check
        if pcomm == "STOPSTIM":
            gp_passed = self.check_grace_period()

            # Reset grace period, as the command will be used
            if gp_passed:
                self.last_stim_command_time_ns = time.perf_counter_ns()

            return gp_passed

        # -------------- checks for STARTSTIM command --------------

        checks = []

        # If time since last valid command is not larger than grace period
        # returning invalid
        checks.append(self.check_grace_period())

        # check stim channel in white list
        checks.append(self.check_stim_channel_in_white_list(config["StimChannel"]))
        checks.append(self.check_return_channel_in_white_list(config["ReturnChannel"]))

        # Check that stim command is charge balanced
        checks.append(
            self.check_charge_balance(
                config["FirstPhaseAmpl_mA"],
                config["FirstPhaseWidth_mS"],
                config["SecondPhaseAmpl_mA"],
                config["SecondPhaseWidth_mS"],
            )
        )

        # Check that amplitudes to not exceed max_amp
        #    amplitude 1
        checks.append(self.check_amplitude(config["FirstPhaseAmpl_mA"]))
        #    amplitude 2
        checks.append(self.check_amplitude(config["SecondPhaseAmpl_mA"]))

        # Check that width is in limit
        checks.append(self.check_stimulation_width(config["FirstPhaseWidth_mS"]))
        checks.append(self.check_stimulation_width(config["SecondPhaseWidth_mS"]))

        # check ratio of amplitudes
        checks.append(
            self.check_pulse_ampl_ratio(
                config["FirstPhaseAmpl_mA"], config["SecondPhaseAmpl_mA"]
            )
        )
        # check ratio of widths
        checks.append(
            self.check_pulse_width_ratio(
                config["FirstPhaseWidth_mS"], config["SecondPhaseWidth_mS"]
            )
        )

        # check valid frequency
        checks.append(self.check_frequency_in_admissible_range(config["Freq_hZ"]))

        # all checks valid
        if all(checks):

            # logger.debug("Valid stimulation command - resetting grace period")
            self.last_stim_command_time_ns = time.perf_counter_ns()

            return True

        else:
            tests = [
                "grace_period",
                "stim_channel",
                "charge_balance",
                "amp1",
                "amp2",
                "width1",
                "width2",
                "freq",
            ]
            logger.debug(f"Validation failure: {dict(zip(tests, checks))}")
            return False

    def check_grace_period(self) -> bool:
        dt = (time.perf_counter_ns() - self.last_stim_command_time_ns) * 1e-9
        # logger.debug(
        #     f"Time since last command: {dt} - grace_period: {self.grace_period_s}"
        # )

        return dt > self.grace_period_s

    def check_parameter_completeness(self, config: dict) -> bool:
        expected_keys = [
            "StimChannel",
            "ReturnChannel",
            "Duration_sec",
            "FirstPhaseAmpl_mA",
            "FirstPhaseWidth_mS",
            "SecondPhaseAmpl_mA",
            "SecondPhaseWidth_mS",
            "Freq_hZ",
            "FirstPhaseDelay_mS",
            "SecondPhaseDelay_mS",
        ]
        return all([k in config.keys() for k in expected_keys])

    def check_charge_balance(self, a1: float, w1: float, a2: float, w2: float) -> bool:
        return a1 * w1 + a2 * w2 == 0

    def check_stim_channel_in_white_list(self, channel: str | int) -> bool:
        if isinstance(channel, int):
            channel = str(channel)

        return channel in self.white_list_contacts

    def check_return_channel_in_white_list(self, channel: str | int) -> bool:
        if isinstance(channel, int):
            channel = str(channel)

        return channel in self.white_list_contacts

    def check_amplitude(self, amp: float) -> bool:
        return amp <= self.max_amp_mA

    def check_frequency_in_admissible_range(self, freq: float) -> bool:
        return freq >= self.freq_range[0] and freq <= self.freq_range[1]

    def check_stimulation_width(self, width: float) -> bool:
        return width <= self.max_width_ms

    def check_pulse_ampl_ratio(self, a1: float, a2: float) -> bool:
        # using abs as balance is checked separately
        return abs(a1) / abs(a2) == self.charge_discharge_amp_ratio

    def check_pulse_width_ratio(self, w1: float, w2: float) -> bool:
        return w1 / w2 == self.charge_discharge_time_ratio


## For AO stimulator with our dp-ao-control / dareplane-ao-communication module
# /*
# * The Following functions are available:
# *      STARTREC()
# *      STOPREC()
# *      STARTSTIM(
# *                              parameter1: StimChannel,
# *                              parameter2: FirstPhaseDelay_mS,
# *                              parameter3: FirstPhaseAmpl_mA,
# *                              parameter4: FirstPhaseWidth_mS,
# *                              parameter5: SecondPhaseDelay_mS,
# *                              parameter6: SecondPhaseAmpl_mA,
# *                              parameter7: SecondPhaseWidth_mS,
# *                              parameter8: Freq_hZ,
# *                              parameter9: Duration_sec,
# *                              parameter10: ReturnChannel
# *      )
# *      STOPSTIM(parameter1: StimChannel)
# *      SETPATH(parameter1: Path)
# *
# *      e.g.:
# *      STOPSTIM|10287
# */
