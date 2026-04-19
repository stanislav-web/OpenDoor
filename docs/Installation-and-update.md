Installation and update
=======================

OpenDoor is distributed as a standard Python package and can be installed in several ways depending on your use case.

#### Supported Python
- Python 3.12
- Python 3.13
- Python 3.14

#### PyPI installation
Recommended if you want the package available as a normal Python CLI tool.

```shell
python3 -m pip install --upgrade opendoor
opendoor --host http://www.example.com
```

#### pipx installation
Recommended for end users who want an isolated CLI installation.

##### macOS / Homebrew
```shell
brew install pipx
pipx ensurepath
pipx install opendoor

opendoor --host http://www.example.com
```

##### Linux / generic environments
Install `pipx` using your system package manager or preferred Python tooling, then:

```shell
pipx ensurepath
pipx install opendoor

opendoor --host http://www.example.com
```

#### Local run from repository
Use this mode if you want to run OpenDoor directly from source without installing it globally.

```shell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
python3 -m pip install -r requirements.txt
chmod +x opendoor.py

python3 opendoor.py --host http://www.example.com
```

#### Local development installation
Use this mode if you are developing, testing, or changing the project locally.

```shell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
python -m pip install -e .

opendoor --host http://www.example.com
```

#### Build from source
Recommended for Linux distribution maintainers and release packaging.

```shell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor/
python3 -m pip install --upgrade build
python3 -m build
```

Generated artifacts:

```shell
dist/opendoor-<version>.tar.gz
dist/opendoor-<version>-py3-none-any.whl
```

#### Manual installation from a built wheel

```shell
python3 -m pip install dist/opendoor-5.0.1-py3-none-any.whl
opendoor --host http://www.example.com
```

Update
======

#### Update a PyPI installation
```shell
python3 -m pip install --upgrade opendoor
```

#### Update a pipx installation
```shell
pipx upgrade opendoor
```

#### Update a source checkout
```shell
git pull
python3 -m pip install -e .
```

#### Built-in update command
The built-in command does not modify the local source tree in place anymore.  
It now prints update instructions for modern package-based environments.

```shell
opendoor --update
```

#### Notes for maintainers
OpenDoor now follows a standard Python packaging flow:
- `pyproject.toml` is present
- `setup.py` remains compatible
- source distributions and wheels are produced through `python -m build`
- packaging is suitable for Linux distribution maintainers

