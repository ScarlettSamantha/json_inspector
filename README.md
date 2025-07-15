# Json inspector

<div align="center">

![Logo](json_inspector/assets/application_icon_256.png)

</div>

Json inspector is a simple tool originally meant to explore my game’s JSON save files.

This version is a more polished rewrite in Python 3.13+ and Qt6. It’s built for performance—save games can be ~100 MB of JSON—so parsing and UI tasks run in background threads.

## Download

### Binary

Please download the [latest](https://git.scarlettbytes.nl/scarlett/json-inspector/-/releases) installer/binary for your os.

- `.msi` for Windows  
- `.deb` for Ubuntu/Debian

### Python
> For windows substitute python3 for python. As python3 just leads to their store to download some version of it.

```bash
git clone https://git.scarlettbytes.nl/scarlett/json-inspector.git 
cd json-inspector
pip3 install -r requirements.txt
python3 run.py [/dir/to/file.json[.gz]]
```

## How to run

### Binary

After installing you should be able to run it via the GUI of your OS by searching for json inspector.
It will also register (on linux at-least) the `json-inspector` command which also opens the application and takes a path to a file to open with.

### Python

- With a file argument

`python run.py /path/to/file.json[.gz]`

- Without arguments

`python run.py`

Opens a file selector dialog.

## File association

To integrate with your OS, go to `Settings` > `Settings…` > `Associate JSON files with this app`. This will register .json and not .json.gz files to open automatically in the app.

## Requirements 

It uses little resources except when loading, writing and searching, for hardware the following should be sufficient:
- 1-2gb dedicated ram (~100mb json file)
- Quad core processor (to keep it responsive).

These requirements are only needed if you are running the script directly as python:

**Runtime**  
- Qt6  
- orjson (optional; falls back to stdlib json)  
- gzip support (builtin)
- psutil

**Build (if running from source)**  
- Python 3.13+  
- PyQt6  

## How to build

To build locally on linux for a `deb` file, you can just use `docker compose up`. 
It should build inside the container and exit after being build.