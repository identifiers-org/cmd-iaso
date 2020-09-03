# cmd-iaso

IASO was the Greek goddess of cures, remedies and modes of healing. cmd-iaso is a command-line tool to help the curators of the [identifiers.org](https://identifiers.org/) registry. Firstly, it provides the functionality to scrape data from the resource providers in the registry. With this information, the curator is walked through an interactive curation system of the discovered issues. The goal of cmd-iaso is to aid the curators in upholding the health and integrity of the [identifiers.org](https://identifiers.org/) registry.

## Development and Licensing
`cmd-iaso` was developed by [Moritz Langenstein](https://github.com/MoritzLangenstein) under the supervision of [Manuel Bernal Llinares](https://github.com/mbdebian) for the [identifiers.org](https://identifiers.org/) [registry](https://registry.identifiers.org) created by the [European Bioinformatics Institute](https://www.ebi.ac.uk/). The project is published under the MIT License.

## Project structure
This repository consists of four main parts:
- `iaso` Python package
- `cmd-iaso` command-line tool entry point (located in `iaso/cli`)
- `cmd-iaso-docker.py` wrapper to help running `cmd-iaso` inside a Docker container
- `iaso.plugins` package path to register validator plugins for the tool
- `athena` analysis Python+Rust package based on the `metis` Rust crate

The codebase is formatted using the [black code style](https://github.com/psf/black) and tested using the [tox automation project](https://tox.readthedocs.io/en/latest/) and [pytest](https://docs.pytest.org/en/latest/).

This overview will delve into the details of `cmd-iaso`, `cmd-iaso-docker.py` and `iaso.plugins` However, we leave it up to the reader to look into the `iaso` codebase themselves should they wish to see some of the implementation details.

## Installation
There are four ways to install the functionality of this tool, all of which bring differences in isolation and control. All of these methods start by cloning the git repository using either HTTPS:
```
> git clone https://github.com/identifiers-org/cmd-iaso.git
```
or SSL:
```
> git clone git@github.com:identifiers-org/cmd-iaso.git
```
All methods apart from the Docker container require an installation of [Python](https://www.python.org/downloads/) 3.6+ and [pip](https://pip.pypa.io/en/stable/installing/). If you want to use `athena` analysis, you also require a stable [Rust](https://www.rust-lang.org/tools/install) installation in your `PATH`.

### pip installation
To install the `iaso` package and `cmd-iaso` tool directly into your Python implementation, you can use pip
```
> pip install .
```
Note that this will also install all of the dependencies into your current Python environment. To create some isolation, you can use a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html) and install `cmd-iaso` in there.

This installation is the most user-friendly as it takes care of any installation dependencies the package has automatically, including `athena` analysis. Therefore, this method requires Rust to be installed in your `PATH`. For more control over this, use the installation based on Python setuptools described below.

### Python setuptools
To install the `iaso` package and `cmd-iaso` tool directly into your Python implementation, you can make direct use of the `setup.py` script:
```
> python3 setup.py install
```
Note that this will also install all of the dependencies into your current Python environment. To create some isolation, you can use a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html) and install `cmd-iaso` in there.

This installation might skip some optional components if their installation dependencies are not already satisfied. If you want to install `athena` analysis with this command, Rust needs to be installed in your `PATH`. Furthermore, you need to install [setuptools-rust](https://pypi.org/project/setuptools-rust/) in your Python environment using:
```
> pip install setuptools-rust
```

### Makefile
If you want to automatically install `cmd-iaso` inside a fresh and isolated virtual environment, you can simply run:
```
> make install
```
In contrast to the direct setuptools method, `cmd-iaso` will not be registered in your path automatically. To register the command-line extensions, you can run:
```
> source command-line-extensions.sh
```
This installation will skip `athena` analysis on its first installation. You will need to manually follow the pip or Python setuptools installation steps described above to reinstall `cmd-iaso` with `athena` analysis in the newly created virtual Python environment.


### Docker container
If you have already installed [Docker](https://docs.docker.com/get-docker/), you can simply run
```
> python3 cmd-iaso-docker.py
```
This command will build the Docker container during the first run. The Docker container will always be installed `athena` analysis support. The `cmd-iaso-docker.py` wrapper mirrors the functionality of `cmd-iaso`, so every command that you can run as
```
> cmd-iaso COMMAND ARGS OPTIONS
```
can also be run as
```
> python3 cmd-iaso-docker.py COMMAND ARGS OPTIONS
```
There are a few small differences in semantics between running `cmd-iaso` and `python3 cmd-iaso-docker`, however. Firstly, all (file) paths mentioned in the arguments must already exist, which also means that in Docker mode, the tool will always complain about overwriting existing files. Secondly, any environment variables visible to `cmd-iaso`, for instance through the `.env` file will not be visible to the containerised tool. Lastly, if you want to use any custom curation validator plugins (see below), you will need to add a new layer to the Docker container to install them inside as well. Otherwise, they will not be found by `python3 cmd-iaso-docker`.

It is also possible to manually run the `docker run` commands yourself using:
```
> docker run -it --init identifiersorg/cmd-iaso COMMAND ARGS OPTIONS
```
Please beware that while you will have more control over the Docker container using this approach, we can provide no guarantees that the commands will run as expected.

## Shell completion
`cmd-iaso` offers some shell completion functionality for [bash](https://www.gnu.org/software/bash), [fish](https://fishshell.com/), [PowerShell](https://msdn.microsoft.com/en-us/powershell/mt173057.aspx) and [zsh](http://www.zsh.org/). If you want to install the shell completion, you can use
```
> cmd-iaso completion install [SHELL] [PATH] [--append/--overwrite] [-i/--case-insensitive/--no-case-insensitive]
```
If you do not specify `SHELL` explicitly, your current shell will be detected automatically and used instead. You can optionally also specify the `PATH` to which the completion script will be appended (`--append`) or which will be overwritten (`--overwrite`). Finally, if you want the completion to be case-insensitive, you can enable that via the `-i` or `--case-insensitive` option. To explicitly disable case-insensitive completion, you can provide the `--no-case-insensitive` flag.

If you do not want `cmd-iaso` to install the shell completion, you can simply use
```
> cmd-iaso completion show [SHELL] [-i/--case-insensitive/--no-case-insensitive]
```
to output the completion script to the terminal.

## Configuration
`cmd-iaso` comes with many commands and options. While this document will outline their functionality, you can always provide the `--help` option to any command to read a description of the command and its available options. Most options have default values, while some always require a user-provided value. All options can be provided either via the command-line or via environment variables. `cmd-iaso` also supports reading a `.env` file to get the values of the environment variables. Note that providing command-line options will always overwrite environment variables. A default configuration is provided in `config.default` which is automatically copied to `.env` by `make install`. Please refer to the `--help` pages to find out about the names of the supported environment variables.

## Helper commands
### Environmental information
To print a description of your current runtime environment, you can run:
```
> cmd-iaso environment
```

### Pretty-printed registry
To print the current status of the [identifiers.org](https://identifiers.org/) registry, you can use:
```
> cmd-iaso registry
```

## Data scraping
Before performing curation of the resource providers in the [identifiers.org](https://identifiers.org/) registry, `cmd-iaso` needs to scrape some data. This section will outline how to configure and run the scraping pipeline.

### [Optional]: Extracting LUIs from the load balancing logs of [identifiers.org](https://identifiers.org/)
If you want the data scraping to probe valid resource LUIs, you need to provide the tool with a list of them. One way to get some heuristically more likely to be valid LUIs, you can extract them from the load balancing logs of [identifiers.org](https://identifiers.org/):
```
> cmd-iaso logs2luis LOGS VALID_NAMESPACE_IDS [--resolution-endpoint RESOLUTION_ENDPOINT]
```
Here, `LOGS` refers to the folder in which the logs are stored, `VALID_NAMESPACE_IDS` is the file path to which the list of extracted LUIs will be written. Optionally, `--resolution-endpoint RESOLUTION_ENDPOINT` can be provided to specify a custom resolution API endpoint, for instance in order not to overload the public one.

### Generating the jobs for the data scraping pipeline
`cmd-iaso` needs to know exactly which resource providers and LUIs it will probe during the scraping. To generate the jobs specification file, you can run:
```
> cmd-iaso jobs JOBS [--valid VALID] [--random RANDOM] [--pings PINGS] [--valid-namespace-ids VALID_NAMESPACE_IDS]
```
This command will attempt to use `VALID` valid LUIs for each resource provider in addition to generating `RANDOM` random LUIs per provider. Iff `VALID` is greater than one, you must also provide `--valid-namespace-ids VALID_NAMESPACE_IDS` where `VALID_NAMESPACE_IDS` points to the file you generated using `cmd-iaso logs2luis`. Each job will be repeated `PINGS` times in the jobs list. The final list of jobs will be saved at the `JOBS` file path.
Note that the resulting jobs list of this command is random. Both the random LUIs and the selection of valid LUIs is random on each run of this command. Furthermore, note that this command will attempt to use valid LUIs from a different namespace if some namespace does not have enough valid LUIs specified in `VALID_NAMESPACE_IDS`. Therefore, as long as there are enough LUIs in `VALID_NAMESPACE_IDS`, it will use more than `VALID` LUIs from some namespaces to compensate for others.

### [Optional]: Launching your own scraping proxy
`cmd-iaso` uses an HTTPS intercepting proxy to detect and flag some common error cases without exposing the rest of the scraping pipeline to them. While `cmd-iaso scrape` can launch its own proxy (see below), you can also launch your own:
```
> cmd-iaso proxy3 [--port PORT] [--timeout TIMEOUT] [--log null|stderr|proxy3.log]
```
`PORT` specifies the free port the proxy should run on. `TIMEOUT` specifies in seconds how long the proxy should wait internally for resources on the Internet to respond. It is recommended to choose a lower timeout for the proxy than for the scraping command. The `--log` option specifies which logging output will be used. 'null' discards all messages, 'stderr' redirects them to stderr and 'proxy3.log' appends them to the proxy3.log file in the current working directory. By default, all messages are discarded.

### Running the data scraping pipeline
To run the data scraping pipeline, you must first create a new folder to save the collected data dumps in, for instance:
```
> mkdir dump
```
Now, you can run the data scaping command to run the jobs defined in the `JOBS` file and save the results in the `DUMP` folder:
```
> cmd-iaso scrape JOBS DUMP [--resume] [--proxy PROXY] [--chrome CHROME] [--workers WORKERS] [--timeout TIMEOUT] [--log null|stderr|scrape.log]
```
This command is highly customisable. Firstly, you can automatically launch a proxy (this is default option but can also be done explicitly using `--proxy launch`) or connect to an existing one by providing its address, e.g. `--proxy localhost:8080`. If a new proxy is launched, its log will be implicitly discared. The `--chrome` option should be used with care, as it provides the path to the Chrome browser executable. By not providing this option, `cmd-iaso` will use a version of Chromium that is automatically downloaded if required. `WORKERS` specifies the number of processes that should be launched in parallel to work on different scraping jobs. Lastly, `TIMEOUT` specifies in seconds a baseline timeout that will be used to cancel too long-running scraping jobs.
Running this command will take some time, so a progress bar is provided to keep the user informed. If you want to pause the scraping, you can iterrupt it using `CTRL-C` or `CMD-C` depending on your operating system. The scraper will then shutdown and wait for all running workers to complete. A paused scraping task can be resumed later on by passing the `--resume` flag to the command. Finally, the `--log` option specifies which logging output will be used. 'null' discards all messages, 'stderr' redirects them to stderr and 'scrape.log' appends them to the scrape.log file in the current working directory. By default, all messages are appended to scrape.log.

### Converting the raw data dumps into a structured datamine
The collected raw data dumps contain mostly raw information about the scraped resources. To collect and compress this data into a structured format that can be read by the curation process, you can run:
```
> cmd-iaso dump2datamine DUMP DATAMINE
```
which will read the data dumps from the `DUMP` folder and save the datamine to the `DATAMINE` file path.

The `dump2datamine` command also allows you to perform analysis on the scraped responses to determine if the resource providers are working as expected. This working state is assessed by the information content of a resource:
- The information content of a resource is the maximum information content per LUI pinged during scraping, i.e. one working LUI is sufficient to be classified as working.
- Only the content which is deterministic per LUI is considered as informative, i.e. random or time-dependent elements are excluded.
- The information content of a LUI is the amount of information that is not shared with other LUIs. Longer segments of information are given a heigher weight than shorter segments in measuring the amount of shared information.
This definition means that any resource that always responds with the same or completely random responses will be classified as defunct. In contrast, if a resource provides deterministic distinct responses for at least one LUI, its information content will be significantly higher.

As the `athena` analysis is very computationally expensive, it is implemented in the Rust library crate `metis`. To enable this optional analysis, `cmd-iaso` must be installed with `athena` analysis support, which is described in the installation guidelines outlined above. You can check whether athena analysis is available by running:
```
> cmd-iaso dump2datamine --check-athena
```
If the `--analyse` flag is passed to the `dump2datamine` command, the analysis will be performed and integrated with the normal dump compaction in the `DATAMINE`. The calculated information contents can then be checked during curation by enabling the `information-content` validator.

## Institution Deduplication
The [identifiers.org](https://identifiers.org/) registry might contain duplicate institution entries which refer to the same entity. In the old platform, a resource's institution was simply stored as a string. As a result of the migration from the old platform, many institution entries still have only their name field filled out, and some names are concatenations of multiple institutions. The institution deduplication command
```
> cmd-iaso dedup4institutions ACADEMINE
```
collects all existing institutions from the registry. It then attempts to link them to the mentioned entities. This process deduplicates the entries and disentangles concatenations of institution names. It also tries to fill in information about the institutions like their name, official URL, ROR ID, country and a description. The results of this command are stored in the `ACADEMINE` file.

## Interactive curation
The primary purpose of `cmd-iaso` is to aide the curator in their curation process. The interactive curation is run either on the datamine file created from the data scraping pipeline using the `cmd-iaso dump2datamine` command or the academine file created from the institution deduplication using the `cmd-iaso dedup4institutions` command.

### Curation validators
`cmd-iaso` uses validator plugins to provide customisable modularised validation of the resource providers. Each validator is a subclass of the `iaso.curation.validator.CurationValidator` class:
```python
from abc import ABC, abstractmethod
from typing import Union

class CurationValidator(ABC):
    @classmethod
    def validate_params(cls, validator_name: str, **kwargs) -> CurationValidator:
        """
        Overwrite this classmethod if your validator can take parameters.
        This method should either raise an exception or return a subclass of cls.
        """
        if len(kwargs) > 0:
            raise click.UsageError(
                click.style(
                    f"The validator {validator_name} does not accept any parameters.",
                    fg="red",
                )
            )

        return cls

    @staticmethod
    @abstractmethod
    def check_and_create(get_compact_identifier, valid_luis_threshold, random_luis_threshold, provider) -> Union[CurationValidator, bool]:
        """
        Returns False iff this data_entry cannot be included during
         curation at all.
        Returns True iff this validator has found nothing to report on
         this data_entry.
        Returns an instance of the particular CurationValidator iff it
         found something to report about this data_entry.
        """
        pass

    @abstractmethod
    def format(self, formatter) -> None:
        pass
```
Here `get_compact_identifier` is a function of the signature:
```python
def get_compact_identifier(lui: str, provider_id: int) -> str:
    ...
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
As a more general alternative, you can also use a `pyproject.toml` file to register your curation validator:
```toml
[project]
name = "My Curation Plugin"

[project.entry-points."iaso.plugins"]
my-validator = "my_module:my_validator:MyValidator"
```
`cmd-iaso` comes with the following validators by default:
- `redirection-chain` displays the entire redirection chain of a resource and, therefore, marks every resource as erroneous
- `dns-error` detects DNS errors caught by the scraping proxy
- `ssl-error` detects SSL errors caught by the scraping proxy
- `invalid-response` detects invalid HTTP responses
- `http-status-error` detects requests that resulted in HTTP error codes
- `scheme-only-redirect` detects redirects where only the scheme of the URL changed, e.g. `http://url` -> `https://url`
- `information-content` displays and puts into context the output of the `athena` analysis

To list all validators that are registered with `cmd-iaso`, you can use
```
> cmd-iaso curate --list-validators
```

### Curation user-interaction
The interactive curation tool is composed of three components which can all run either in the terminal or in the Chrome browser. The selection is independent for each component to allow for maximum customisability. All of the component-options can either be set to `terminal` or to `chrome`.

The **Controller** allows the curator to navigate through the resource providers which have been flagged as problematic. The controller component can be set by the `--controller` option.

The **Navigator** leads the curator to the provider's corresponding namespace page in the [identifiers.org](https://identifiers.org/) registry. If the navigator is in Chrome mode and the curator is logged in, the navigator will automatically enter edit mode for the relevant resource information. The navigator component can be set by the `--navigator` option.

The **Informant** formats and presents information about the discovered issues with each resource provider to the curator. The informant component can be set by the `--informant` option.

Iff any of the components are set to `chrome`, the curator must also provide the `--chrome` option to select how the curation pipeline should connect to Chrome. It can either `launch` a new instance or connect to an existing one if its address, e.g. `localhost:9222` is provided. Note that in order to connect to a running Chrome browser, it must have been started with the `--remote-debugging-port=PORT` option, where `PORT` would be `9222` in this case.
If you want to connect to a running Chrome browser instance on a different machine, for instance if you are calling `cmd-iaso` through SSH, we recommend taking a look at [inlets](https://github.com/inlets/inlets) which allows you to "[e]xpose your local endpoints to the Internet or to another network, traversing firewalls and NAT".

All of these options have to be provided via the command line or environment variables. Otherwise, the curator will be asked for their value via a prompt:
```
> cmd-iaso curate --controller CONTROLLER --navigator NAVIGATOR --informant INFORMANT [--chrome CHROME] [--tags TAGS] {-i TAG} [--statistics]
```

The curation process also allows the curator to tag identified issues. These tags are associated with a fingerprint of that issue and are stored across different curation session. If you want to change the location of this tags storage from its default of `tags.gz`, you can use the `--tags TAGS` option.

The tags are not only a great way to keep notes on recurring or unsolved issues, but they also allow you to hide the issues they tag temporarily. If you want to ignore any issues with a specific tag, you can pass `-i TAG` or `--ignore TAG` for every tag you wish to ignore. By default, the `fixed` and `ignore` tags are ignored. It is important to note that you can change which tags are ignored at any point during curation. You will have to reload an entry, however, for any change in the ignored tags to take effect.

If you want to just get an overview of all the issues identified, you can provide the `--statistics` flag. Instead of launching an interactive curation session, `cmd-iaso` will then only print a statistical summary. Therefore, none of the `--controller`, `--navigator`, `--informant` or `--chrome` options must be provided.

### Starting a new curation session
Curation is performed in sessions to enable the curator to pause and save their progress. Furthermore, they can then resume the curation later on. The settings on how the curation is run, e.g. whether in the terminal or the Chrome browser, is session independent. In contrast, the information dump on which the curation is based is fixed per session. Settings which narrow down the set of issues that are reported are also saved with the session. The session also remembers the point at which the curator left off.

#### Starting a new resource provider curation session
To start a new session for curating resource providers, you can use:
```
> cmd-iaso curate [...] start resources DATAMINE {-v VALIDATOR} [--valid-luis-threshold VALID_LUIS_THRESHOLD] [--random-luis-threshold RANDOM_LUIS_THRESHOLD] [--session SESSION]
```
This command starts a new session using the `DATAMINE` file created by the `dump2datamine` command and will save it either to the `SESSION` file path -- if provided -- or the default `resources_session.gz` location. If the curator does not want to save the session, they can provide the `--discard-session` instead.

The `-v VALIDATOR` / `--validate VALIDATOR` option can be provided multiple times to explicitly name all validator modules which should be enabled in this session. By default, `dns-error`, `invalid-response` and `http-status-error` are enabled. Some validators support parameterisation using a named parameter list suffix of the form `-v VALIDATOR:param=value,flag,param=value`. For instance, the `information-content` validator supports a `threshold` parameter in the range `[0.0, 1.0]` to only report resource providers with an information content smaller or equal to the threshold.

It is also possible to only report errors which occur with a high enough percentage. For instance, to only report errors using valid LUIs if they occur on more than ![50%](https://render.githubusercontent.com/render/math?math=50%5C%25) of the valid LUIs, you can specify `--valid-luis-threshold 50`. Similarly, you can specify `--random-luis-threshold 50` to configure it the same for randomly generated LUIs. By default, all errors on valid LUIs and no errors on random LUIs will be reported. Note that each validator can decide whether to abide by this setting.

The `[...]` between `curate` and `resources` refer to the general curation options discussed above.

#### Starting a new institution curation session
To start a new session for curating institutions, you can use:
```
> cmd-iaso curate [...] start institutions ACADEMINE [--session SESSION]
```
This command starts a new session using the `ACADEMINE` file created by the `dedup4institutions` command and will save it either to the `SESSION` file path -- if provided -- or the default `institutions_session.gz` location. If the curator does not want to save the session, they can provide the `--discard-session` instead.

The `[...]` between `curate` and `institutions` refer to the general curation options discussed above.

### Resuming an existing session
An existing session at the `SESSION` file path can be resumed using:
```
> cmd-iaso curate [...] resume resources/institutions SESSION
```
The `[...]` between `curate` and `resume` refer to the general curation options discussed above.

This command will also warn the curator if they have already completed curation on this session.
