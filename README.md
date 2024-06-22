# github_issues

Note: The software in this repository is not meant to be a packaged distribution--at this point these are just sharing scripts and a library that I wrote for the HG002 "Q100" project to submit and track assembly issues in the "HG002-issues" github repository. If you find these scripts useful, and would like to see functionality added, please let me know. Better yet, if you'd like to improve the software yourself, please do!

The program was written by Nancy Fisher Hansen, a staff scientist in the Genome Informatics Section at the National Human Genome Research Institute (NHGRI). Nancy can be reached at nhansen@mail.nih.gov.

## Install

### Dependencies

This program calls the "hub" command distributed [here](https://hub.github.com/) to interact with github. The hub tool needs to be installed, in your path, and configured with access to the repositories you intend to work with in order to run the tools in github_issues. To interact with Google "Sheets", the program uses the [gspread](https://pypi.org/project/gspread/) python library, which will be installed by pip if you follow the instructions in "Local Installation" below.

All other dependencies are installed by the pip installer with the commands in the "Local Installation" section below. Feel free to post installation issues to the issues section of this github repository.

### Local Installation

The easiest way to use github_issues is to install it locally. First clone this github repository:
```
git clone https://github.com/nhansen/github_issues
cd github_issues
```

Create a virtual environment for the project:
```
python3 -m venv venv
source venv/bin/activate
```

Finally use python's pip installer to install and test a development copy for yourself to run:
```
python3 -m pip install -e .
pytest
```


