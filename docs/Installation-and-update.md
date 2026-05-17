# 📦 Installation and update

OpenDoor is distributed as a Python CLI application and as an official project Docker image. It can be installed with Arch Linux AUR, BlackArch Linux, Homebrew, pipx, pip, Docker, or run directly from a source checkout.

For most users, the recommended installation methods are:

| Environment | Recommended method |
|---|---|
| Arch Linux | AUR |
| BlackArch Linux | pacman |
| macOS | Homebrew |
| Containerized usage | Docker / GHCR |
| General CLI usage | pipx |
| Existing Python environment | pip |
| Development | editable source install |
| Package verification | source build |

---

## 🐧 Arch Linux / AUR

OpenDoor is available in the Arch User Repository.

Install with an AUR helper:

```shell
yay -S opendoor
```

Manual AUR installation:

```shell
git clone https://aur.archlinux.org/opendoor.git
cd opendoor
makepkg -si
```

Verify the installation:

```shell
opendoor --version
opendoor --help
```

Update with an AUR helper:

```shell
yay -Syu opendoor
```

For manual AUR installations, update from the package repository:

```shell
cd opendoor
git pull
makepkg -si
```

---

## 🐉 BlackArch Linux

OpenDoor is available in BlackArch Linux.

Install from BlackArch:

```shell
sudo pacman -Syu
sudo pacman -S opendoor
```

For Arch Linux users with the BlackArch repository enabled:

```shell
sudo pacman -S opendoor
```

Verify the installation:

```shell
opendoor --version
opendoor --help
```

Update OpenDoor with the system packages:

```shell
sudo pacman -Syu opendoor
```

---

## 🍺 Homebrew 

Homebrew is the recommended installation method for macOS users.

```shell
brew install opendoor
```

Verify the installation:

```shell
opendoor --version
opendoor --help
```

Update OpenDoor with Homebrew:

```shell
brew update
brew upgrade opendoor
```

If you maintain or use a custom tap, installation may look like this:

```shell
brew install stanislav-web/opendoor/opendoor
```

![Homebrew Formula Downloads](https://img.shields.io/homebrew/installs/dy/opendoor)
---

## 🐳 Docker / GitHub Container Registry

OpenDoor is available as an official project Docker image via GitHub Container Registry.

Pull the latest release image:

```shell
docker pull ghcr.io/stanislav-web/opendoor:latest
```

Verify the image:

```shell
docker run --rm -it ghcr.io/stanislav-web/opendoor:latest --version
docker run --rm ghcr.io/stanislav-web/opendoor:latest --help
```

Run a scan and write reports to the host:

```shell
mkdir -p reports

docker run --rm \
  -v "$PWD/reports:/work/reports" \
  ghcr.io/stanislav-web/opendoor:latest \
  --host https://example.com \
  --reports json,html \
  --reports-dir reports
```

Run with a custom local wordlist:

```shell
mkdir -p reports

docker run --rm \
  -v "$PWD/reports:/work/reports" \
  -v "$PWD/wordlists:/work/wordlists:ro" \
  ghcr.io/stanislav-web/opendoor:latest \
  --host https://example.com \
  --wordlist /work/wordlists/custom.txt \
  --reports json,html \
  --reports-dir reports
```

Run with a remote HTTP(S) wordlist without mounting a wordlist directory:

```shell
mkdir -p reports

docker run --rm \
  -v "$PWD/reports:/work/reports" \
  ghcr.io/stanislav-web/opendoor:latest \
  --host https://example.com \
  --wordlist https://example.com/wordlists/custom.txt \
  --reports json,html \
  --reports-dir reports
```

Remote wordlists are downloaded into OpenDoor's managed temporary workspace before scan start and are limited to 500 MB.

Use a pinned release tag for reproducible runs:

```shell
docker pull ghcr.io/stanislav-web/opendoor:latest
docker run --rm ghcr.io/stanislav-web/opendoor:latest --version
```

---

## 🧰 pipx

`pipx` installs Python CLI applications into isolated environments and exposes their commands globally. This is the recommended method for most non-Homebrew CLI users.

### Linux and macOS

```shell
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install opendoor
```

Verify:

```shell
opendoor --version
```

Update:

```shell
pipx upgrade opendoor
```

Uninstall:

```shell
pipx uninstall opendoor
```

### Windows PowerShell

Install Python first if it is not already available:

```powershell
winget install Python.Python.3
```

Install pipx:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

Reopen PowerShell, then install OpenDoor:

```powershell
pipx install opendoor
opendoor --version
```

Update:

```powershell
pipx upgrade opendoor
```

---

## 🐍 pip

Use `pip` when you intentionally want OpenDoor installed into the current Python environment.

### Linux and macOS

```shell
python3 -m pip install --upgrade opendoor
opendoor --version
```

Update:

```shell
python3 -m pip install --upgrade opendoor
```

Uninstall:

```shell
python3 -m pip uninstall opendoor
```

### Windows PowerShell

```powershell
py -m pip install --upgrade pip
py -m pip install --upgrade opendoor
opendoor --version
```

Update:

```powershell
py -m pip install --upgrade opendoor
```

![PyPI - Downloads](https://img.shields.io/pypi/dm/opendoor?link=https%3A%2F%2Fpypi.org%2Fproject%2Fopendoor%2F)

---

## 🧾 Run from source

Use this mode if you want to run OpenDoor directly from a source checkout without installing it as a package.

### Linux and macOS

```shell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor

python3 -m pip install -r requirements.txt
python3 opendoor.py --version
python3 opendoor.py --host https://example.com
```

### Windows PowerShell

```powershell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor

py -m pip install -r requirements.txt
py opendoor.py --version
py opendoor.py --host https://example.com
```

---

## 🛠️ Development installation

Use an editable installation when contributing to OpenDoor, running tests, or validating changes locally.

### Linux and macOS

```shell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
python -m pip install -e .

opendoor --version
opendoor --help
```

### Windows PowerShell

```powershell
git clone https://github.com/stanislav-web/OpenDoor.git
cd OpenDoor

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-dev.txt
python -m pip install -e .

opendoor --version
opendoor --help
```

---

## 🏗️ Build from source

This flow is useful for maintainers, package builders, and release verification.

```shell
python3 -m pip install --upgrade build
python3 -m build
```

Generated artifacts are written to:

```text
dist/
```

Install a locally built wheel:

```shell
python3 -m pip install dist/opendoor-*.whl
```

Install a locally built source archive:

```shell
python3 -m pip install dist/opendoor-*.tar.gz
```

Do not hardcode old wheel filenames in scripts or documentation. Use the generated artifact names from `dist/`.

---

## 🧪 Verify runtime assets

A packaged OpenDoor installation should include the built-in configuration and dictionaries.

Useful verification commands:

```shell
opendoor --version
opendoor --help
```

For package maintainers, also verify that the installed package includes runtime assets such as:

```text
opendoor.conf
data/directories.dat
data/subdomains.dat
data/useragents.dat
data/proxies.dat
data/ignored.dat
```

Transport profile examples are examples only. Never distribute real OpenVPN or WireGuard credentials, private keys, or production profiles.

---

## 🔄 Update strategy

Use the same package manager that installed OpenDoor. Do not mix package managers for the same installation. For example, do not update a Homebrew or system package with `pip`.

OpenDoor also provides a safe helper command:

```shell
opendoor --update
```

`--update` does not self-update the scanner, execute package-manager commands, or contact the network. It prints update instructions for common installation types and includes the current Python interpreter path for the active environment. That interpreter-specific command is intentional: it helps avoid updating the wrong virtual environment.

| Installed with | Update command |
|---|---|
| AUR helper | `yay -Syu opendoor` |
| Manual AUR build | `git pull && makepkg -si` |
| BlackArch / pacman | `sudo pacman -Syu opendoor` |
| Debian / Kali package | `sudo apt update && sudo apt install --only-upgrade opendoor` |
| Homebrew | `brew update && brew upgrade opendoor` |
| Docker / GHCR | `docker pull ghcr.io/stanislav-web/opendoor:latest` |
| pipx | `pipx upgrade opendoor` |
| pip | `python -m pip install --upgrade opendoor` from the same Python environment |
| Windows pip | `py -m pip install --upgrade opendoor` |
| Source checkout | `git pull --ff-only` and reinstall/editable-install if needed |

For source checkouts used as editable installs, refresh the checkout and reinstall in the current environment:

```shell
git pull --ff-only
python -m pip install -e .
```

For Windows PowerShell source checkouts:

```powershell
git pull --ff-only
python -m pip install -e .
```

---

## 🧯 Common issues

### `mkdocs: command not found`

This is relevant only when building documentation locally. Install documentation dependencies in a virtual environment:

```shell
python3 -m venv .docs-venv
source .docs-venv/bin/activate
python -m pip install -r docs/requirements.txt
python -m mkdocs build --strict
```

### `externally-managed-environment`

Some Python distributions, including Homebrew Python, prevent global `pip install` into the system environment.

Use a virtual environment, pipx, or Homebrew instead of forcing installation into the system Python.

Do not use `--break-system-packages` unless you fully understand the risk.

### Command not found after installation

Check that your package manager's binary directory is in `PATH`.

For pipx:

```shell
python3 -m pipx ensurepath
```

For Arch Linux AUR manual builds, confirm that the package installed successfully:

```shell
pacman -Qs opendoor
```

For BlackArch Linux, confirm that the package is available from enabled repositories:

```shell
pacman -Ss opendoor
```

Then reopen the terminal.
