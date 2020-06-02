# Overview

# Running the tool for checking the health of the resources in the registry
This use case will walk through the resources in the registry, for every namespace, using the registered _Sample ID_ to detect possible issues with the resources in each namespace.

## Running this use case in Development
Follow the steps to prepare a working local copy of the tool:
1. Clone the repository
2. Install the tool by running
```
make install
```
3. Load the _command line extensions_
```
source command-line-extensions.sh
```
This will install the tool with along with its default configuration (see configuration section for more details).

For data mining the registry, you need to follow these steps:
1. **Generate the scraping jobs**, generates the jobs for the data scraping subcommand and stores them at the JOBS file path. Each _job_ is a data entry that contains all the information needed by the scrape worker to analyze the resource. This is an example command using all the parameters but the _valid namespace ids_ file parameter, although these parameters can be specified in the _.env_ file that has been created when installing the tool.
```
cmd-iaso jobs <scraping_jobs.json> --valid 1 --random 99
```
2. **Create a folder for your scraping session**, all the scraping session data will be stored in that folder.
```
mkdir my_scraping_session
```
3. **Run the scraping session**, keep in mind that '--proxy launch', '--workers 32' and '--timeout 30' are in the default configuration as well, we're just showing a usage example for them.
```
cmd-iaso scrape <scraping_jobs.json> <my_scraping_session> --proxy launch --workers 32 --timeout 30
```

# cmd-iaso
We'll fill this in later, with documentation on the tool
