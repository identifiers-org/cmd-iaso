# cmd-iaso

IASO was the Greek goddess of cures, remedies and modes of healing. cmd-iaso is a command-line tool to help the curators of the identifiers.org registry. Firstly, it provides the functionality to scrape data from the resource providers in the registry. With this information, the curator is walked through an interactive curation system of the discovered issues. The goal of cmd-iaso is to aid the curators in upholding the health and integrity of the identifiers.org registry.

## Development and Licensing
`cmd-iaso` was developed by [Moritz Langenstein](https://github.com/MoritzLangenstein) under the supervision of [Manuel Bernal Llinares](https://github.com/mbdebian) for the identifiers.org [registry](https://registry.identifiers.org) created by the [European Bioinformatics Institute](https://www.ebi.ac.uk/). The project is published under the MIT License.

## Project structure
This repository consists of four main parts:
- `iaso` Python package
- `cmd-iaso` command-line tool entry point (located in `iaso/cli.py`)
- `cmd-iaso-docker.py` wrapper to help running `cmd-iaso` inside a Docker container
- `iaso.plugins` package path to register validator plugins for the tool

The codebase is formatted using the [black code style](https://github.com/psf/black) and tested using the [tox automation project](https://tox.readthedocs.io/en/latest/) and [pytest](https://docs.pytest.org/en/latest/).

This overview will delve into the details of `cmd-iaso`, `cmd-iaso-docker.py` and `iaso.plugins` However, we leave it up to the reader to look into the `iaso` codebase themselves should they wish to see some of the implementation details.

## Installation
There are three ways to install the functionality of this tool, all of which bring differences in isolation and control. All of these methods start by cloning the git repository using either HTTPS:
```
> git clone https://github.com/identifiers-org/cmd-iaso.git
```
or SSL:
```
> git clone git@github.com:identifiers-org/cmd-iaso.git
```

### Python setuptools
To install the `iaso` package and `cmd-iaso` tool directly into your Python implementation, you can make direct use of the `setup.py` script:
```
> python3 setup.py install
```
Note that this will also install all of the dependencies into your current Python environment. To create some isolation, you can use a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html) and install `cmd-iaso` in there.

### Makefile
If you want to automatically install `cmd-iaso` inside a fresh and isolated virtual environment, you can simply run:
```
> make install
```
In contrast to the direct setuptools method, `cmd-iaso` will not be registered in your path automatically. To register the command-line extensions, you can run:
```
> source command-line-extensions.sh
```

### Docker container
If you have already installed [Docker](https://docs.docker.com/get-docker/), you can simply run
```
> python3 cmd-iaso-docker.py
```
This command will build the Docker container during the first run. The `cmd-iaso-docker.py` wrapper mirrors the functionality of `cmd-iaso`, so every command that you can run as
```
> cmd-iaso COMMAND ARGS OPTIONS
```
can also be run as
```
> python3 cmd-iaso-docker COMMAND ARGS OPTIONS
```
There are a few small differences in semantics between running `cmd-iaso` and `python3 cmd-iaso-docker`, however. Firstly, all (file) paths mentioned in the arguments must already exist, which also means that in Docker mode, the tool will always complain about overwriting existing files. Secondly, any environment variables visible to `cmd-iaso`, for instance through the `.env` file will not be visible to the containerised tool. Lastly, if you want to use any custom curation validator plugins (see below), you will need to add a new layer to the Docker container to install them inside as well. Otherwise, they will not be found by `python3 cmd-iaso-docker`.

## Configuration
`cmd-iaso` comes with many commands and options. While this document will outline their functionality, you can always provide the `--help` option to any command to read a description of the command and its available options. Most options have default values, while some always require a user-provided value. All options can be provided either via the command-line or via environment variables. `cmd-iaso` also supports reading a `.env` file to get the values of the environment variables. Note that providing command-line options will always overwrite environment variables. A default configuration is provided in `config.default` which is automatically copied to `.env` by `make install`. Please refer to the `--help` pages to find out about the names of the supported environment variables.

## Helper commands
### Environemental information
To print a description of your current runtime environment, you can run:
```
> cmd-iaso environment
```

### Pretty-printed registry
To print the current status of the identifiers.org registry, you can use:
```
> cmd-iaso registry
```

## Data scraping
Before performing curation of the resource providers in the identifiers.org registry, `cmd-iaso` needs to scrape some data. This section will outline how to configure and run the scraping pipeline.

### [Optional]: Extracting LUIs from the load balancing logs of identifiers.org
If you want the data scraping to probe valid resource LUIs, you need to provide the tool with a list of them. One way to get some heuristically more likely to be valid LUIs, you can extract them from the load balancing logs of identifiers.org:
```
> cmd-iaso logs2luis LOGS VALID_NAMESPACE_IDS [--resolution-endpoint RESOLUTION_ENDPOINT]
```
Here, `LOGS` refers to the folder in which the logs are stored, `VALID_NAMESPACE_IDS` is the file path to which the list of extracted LUIs will be written. Optionally, `--resolution-endpoint RESOLUTION_ENDPOINT` can be provided to specify a custom resolution API endpoint, for instance in order not to overload the public one.

### Generating the jobs for the data scraping pipeline
`cmd-iaso` needs to know exactly which resource providers and LUIs it will probe during the scraping. To generate the jobs specification file, you can run:
```
> cmd-iaso jobs JOBS [--valid VALID] [--random RANDOM] [--valid-namespace-ids VALID_NAMESPACE_IDS]
```
This command will attempt to use `VALID` valid LUIs for each resource provider in addition to generating `RANDOM` random LUIs per provider. Iff `VALID` is greater than one, you must also provide `--valid-namespace-ids VALID_NAMESPACE_IDS` where `VALID_NAMESPACE_IDS` points to the file you generated using `cmd-iaso logs2luis`. The final list of jobs will be saved at the `JOBS` file path.
Note that the resulting jobs list of this command is random. Both the random LUIs and the selection of valid LUIs is random on each run of this command. Furthermore, note that this command will attempt to use valid LUIs from a different namespace if some namespace does not have enough valid LUIs specified in `VALID_NAMESPACE_IDS`. Therefore, as long as there are enough LUIs in `VALID_NAMESPACE_IDS`, it will use more than `VALID` LUIs from some namespaces to compensate for others.

### [Optional]: Launching your own scraping proxy
`cmd-iaso` uses an HTTPS intercepting proxy to detect and flag some common error cases without exposing the rest of the scraping pipeline to them. While `cmd-iaso scrape` can launch its own proxy (see below), you can also launch your own:
```
> cmd-iaso proxy3 [--port PORT] [--timeout TIMEOUT]
```
`PORT` specifies the free port the proxy should run on. `TIMEOUT` specifies in seconds how long the proxy should wait internally for resources on the Internet to respond. It is recommended to choose a lower timeout for the proxy than for the scraping command.

### Running the data scraping pipeline
To run the data scraping pipeline, you must first create a new folder to save the collected data dumps in, for instance:
```
> mkdir dump
```
Now, you can run the data scaping command to run the jobs defined in the `JOBS` file and save the results in the `DUMP` folder:
```
> cmd-iaso scrape JOBS DUMP [--proxy PROXY] [--chrome CHROME] [--workers WORKERS] [--timeout TIMEOUT]
```
This command is highly customisable. Firstly, you can automatically launch a proxy (this is default option but can also be done explicitly using `--proxy launch`) or connect to an existing one by providing its address, e.g. `--proxy localhost:8080`. The `--chrome` option should be used with care, as it provides the path to the Chrome browser executable. By not providing this option, `cmd-iaso` will use a version of Chromium that is automatically downloaded if required. `WORKERS` specifies the number of processes that should be launched in parallel to work on different scraping jobs. Lastly, `TIMEOUT` specifies in seconds a baseline timeout that will be used to cancel too long-running scraping jobs.
Running this command will take some time, so a progress bar is provided to keep the user informed. It is also important to note that this command will report any unexpected errors to stdout. Additional edge case handling might be added to deal with them more gracefully in the future.

### Converting the raw data dumps into a structured datamine
The collected raw data dumps contain mostly raw information about the scraped resources. To collect and compress this data into a structured format that can be read by the curation process, you can run:
```
> cmd-iaso dump2datamine DUMP DATAMINE
```
which will read the data dumps from the `DUMP` folder and save the datamine to the `DATAMINE` file path.

## Interactive curation
The primary purpose of `cmd-iaso` is to aide the curator in their curation process. The interactive curation is run on the datamine file created from the data scraping pipeline using the `cmd-iaso dump2datamine` command.

### Curation validators
`cmd-iaso` uses validator plugins to provide customisable modularised validation of the resource providers. Each validator is a subclass of the `iaso.curartion.error.CurationError` class:
```python
from abc import ABC, abstractmethod

class CurationError(ABC):
    @staticmethod
    @abstractmethod
    def check_and_create(get_compact_identifier, provider):
        pass

    @abstractmethod
    def format(self, formatter):
        pass
```
Curation validators must be registered in the `iaso.plugins` module using setuptools entry points. For instance, to register a class `MyValidator` you should write:
```python
from setuptools import setup

setup(
    ...
    entry_points={
        "iaso.plugins": [
            "my-validator = my_module.my_validator:MyValidator",
        ],
    },
    ...
)
```
`cmd-iaso` comes with the following validators by default:
- `redirection-chain` displays the entire redirection chain of a resource and, therefore, marks every resource as erroneous
- `dns-error` detects DNS errors caught by the scraping proxy
- `ssl-error` detects SSL errors caught by the scraping proxy
- `invalid-response` detects invalid HTTP responses
- `http-status-error` detects requests that resulted in HTTP error codes
- `scheme-only-redirect` detects redirects where only the scheme of the URL changed, e.g. `http://url` -> `https://url`

To list all validators that are registered with `cmd-iaso`, you can use
```
> cmd-iaso curate --list-validators
```

### Curation user-interaction
The interactive curation tool is composed of three components which can all run either in the terminal or in the Chrome browser. The selection is independent for each component to allow for maximum customisability. All of the component-options can either be set to `terminal` or to `chrome`.

The **Controller** allows the curator to navigate through the resource providers which have been flagged as problematic. The controller component can be set by the `--controller` option.
The **Navigator** leads the curator to the provider's corresponding namespace page in the identifiers.org registry. If the navigator is in Chrome mode and the curator is logged in, the navigator will automatically enter edit mode for the relevant resource information. The navigator component can be set by the `--navigator` option.
The **Informant*** formats and presents information about the discovered issues with each resource provider to the curator. The informant component can be set by the `--informant` option.

Iff any of the components are set to `chrome`, the curator must also provide the `--chrome` option to select how the curation pipeline should connect to Chrome. It can either `launch` a new instance or connect to an existing one if its address, e.g. `localhost:9222` is provided. Note that in order to connect to a running Chrome browser, it must have been started with the `--remote-debugging-port=PORT` option, where `PORT` would be `9222` in this case.

All of these options have to be provided via the command line or environment variables. Otherwise, the curator will be asked for their value via a prompt:
```
> cmd-iaso curate --controller CONTROLLER --navigator NAVIGATOR --informant INFORMANT [--chrome CHROME]
```

### Starting a new curation session
Curation is performed in sessions to enable the curator to pause and save their progress. Furthermore, they can then resume the curation later on. While the information on how the curation is run, i.e. whether the components are run in the terminal or the Chrome browser, is session independent, the `DATAMINE` file and selected curation validators are fixed per session. The session also remembers the point at which the curator left off. To start a new session, you can use:
```
> cmd-iaso curate [...] start DATAMINE {-v VALIDATOR} [--session SESSION]
```
This command starts a new session using the `DATAMINE` file created by the `dump2datamine` command and will save it either to the `SESSION` file path -- if provided -- or the default `session.gz` location. If the curator does not want to save the session, they can provide the `--discard-session` instead. The `-v VALIDATOR` / `--validate VALIDATOR` option can be provided multiple times to explicitly name all validator modules which should be enabled in this session. By default, `dns-error`, `invalid-response` and `http-status-error` are enabled.

### Resuming an existing session
An existing session at the `SESSION` file path can be resumed using:
```
> cmd-iaso curate [...] resume SESSION
```
This command will also warn the curator if they have already completed curation on this session.
