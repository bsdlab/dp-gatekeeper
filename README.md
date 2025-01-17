# Gatekeeper Dareplane Module
This module provides a control functionality to validate json commands vs predefined limits defined in a configuration file.
It implements these controls for specific to given I/O modules. When using the `dp-gatekeeper` in a full Dareplane setup you have to specify the target configuration file, which will tell the gatekeeper how to validate the incoming commands.
Currently implemented I/O modules are:


| module | comment |
|--------|---------|
| [dp-ao-communication](https://github.com/bsdlab/dp-ao-communication)| Communication module using the Neuro Omega SDK|


## Configuration
Example configurations can be found under `./configs`
