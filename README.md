# PyTado -- Pythonize your central heating

[![Linting and testing](https://github.com/wmalgadey/PyTado/actions/workflows/lint-and-test-matrix.yml/badge.svg)](https://github.com/wmalgadey/PyTado/actions/workflows/lint-and-test-matrix.yml)
[![Build and deploy to pypi](https://github.com/wmalgadey/PyTado/actions/workflows/publish-to-pypi.yml/badge.svg?event=release)](https://github.com/wmalgadey/PyTado/actions/workflows/publish-to-pypi.yml)
[![PyPI version](https://badge.fury.io/py/python-tado.svg)](https://badge.fury.io/py/python-tado)
[![codecov](https://codecov.io/github/wmalgadey/PyTado/graph/badge.svg?token=14TT00IWJI)](https://codecov.io/github/wmalgadey/PyTado)
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

PyTado is a Python module implementing an interface to the Tado web API. It allows a user to interact with their
Tado heating system for the purposes of monitoring or controlling their heating system, beyond what Tado themselves
currently offer.

It is hoped that this module might be used by those who wish to tweak their Tado systems, and further optimise their
heating setups.

---

Original author: Chris Jewell <chrism0dwk@gmail.com>

Licence: GPL v3

Copyright: Chris Jewell 2016-2018

## Disclaimer

Besides owning a Tado system, I have no connection with the Tado company themselves. PyTado was created for my own use,
and for others who may wish to experiment with personal Internet of Things systems. I receive no help (financial or
otherwise) from Tado, and have no business interest with them. This software is provided without warranty, according to
the GNU Public Licence version 3, and should therefore not be used where it may endanger life, financial stakes, or
cause discomfort and inconvenience to others.

## Usage

As of the 15th of March 2025, Tado has updated their OAuth2 authentication flow. It will now use the device flow, instead of a username/password flow. This means that the user will have to authenticate the device using a browser, and then enter the code that is displayed on the browser into the terminal.

PyTado handles this as following:

1. The `_login_device_flow()` will be invoked at the initialization of a PyTado object. This will start the device flow and will return a URL and a code that the user will have to enter in the browser. The URL can be obtained via the method `device_verification_url()`. Or, when in debug mode, the URL will be printed. Alternatively, you can use the `device_activation_status()` method to check if the device has been activated. It returns three statuses: `NOT_STARTED`, `PENDING`, and `COMPLETED`. Wait to invoke the `device_activation()` method until the status is `PENDING`.

2. Once the URL is obtained, the user will have to enter the code that is displayed on the browser into the terminal. By default, the URL has the `user_code` attached, for the ease of going trough the flow. At this point, run the method `device_activation()`. It will poll every five seconds to see if the flow has been completed. If the flow has been completed, the method will return a token that will be used for all further requests. It will timeout after five minutes.

3. Once the token has been obtained, the user can use the PyTado object to interact with the Tado API. The token will be stored in the `Tado` object, and will be used for all further requests. The token will be refreshed automatically when it expires.
The `device_verification_url()` will be reset to `None` and the `device_activation_status()` will return `COMPLETED`.

### Screenshots of the device flow

![Tado device flow: invoking](/screenshots/tado-device-flow-0.png)
![Tado device flow: browser](/screenshots/tado-device-flow-1.png)
![Tado device flow: complete](/screenshots/tado-device-flow-2.png)

### How to not authenticate the device again

It is possible to save the refresh token and reuse to skip the next login.

The following code will use the `refresh_token` file to save the refresh-token after login, and load the refresh-token if you create the Tado interface class again.

If the file doesn't exists, the webbrowser is started and the device authentication url is automatically opened. You can activate the device in the browser. When you restart the program, the refresh-token is reused and no webbrowser will be opened.

```python
import webbrowser   # only needed for direct web browser access

from PyTado.interface.interface import Tado

tado = Tado(token_file_path="/var/tado/refresh_token")

status = tado.device_activation_status()

if status == "PENDING":
    url = tado.device_verification_url()

    webbrowser.open_new_tab(url)

    tado.device_activation()

    status = tado.device_activation_status()

if status == "COMPLETED":
    print("Login successful")
else:
    print(f"Login status is {status}")
```

## Example code

```python
"""Example client for PyTado"""

from PyTado.interface.interface import Tado


def main() -> None:
    """Retrieve all zones, once successfully logged in"""
    tado = Tado()

    print("Device activation status: ", tado.device_activation_status())
    print("Device verification URL: ", tado.device_verification_url())

    print("Starting device activation")
    tado.device_activation()

    print("Device activation status: ", tado.device_activation_status())

    zones = tado.get_zones()
    print(zones)


if __name__ == "__main__":
    main()
```

Note: For developers, there is an `example.py` script in `examples/` which is configured to fetch data from your account.
You can then invoke `python examples/example.py`.


## Contributing

We are very open to the community's contributions - be it a quick fix of a typo, or a completely new feature!

You don't need to be a Python expert to provide meaningful improvements. To learn how to get started, check out our
[Contributor Guidelines](https://github.com/wmalgadey/econnect-python/blob/main/CONTRIBUTING.md) first, and ask for help
in [GitHub Discussions](https://github.com/wmalgadey/PyTado/discussions) if you have questions.

## Development

We welcome external contributions, even though the project was initially intended for personal use. If you think some
parts could be exposed with a more generic interface, please open a [GitHub issue](https://github.com/wmalgadey/PyTado/issues)
to discuss your suggestion.

### Setting up a devcontainer

The easiest way to start, is by opening a CodeSpace here on GitHub, or by using
the [Dev Container][devcontainer] feature of Visual Studio Code.

[![Open in Dev Containers][devcontainer-shield]][devcontainer]

### Dev Environment

To contribute to this repository, you should first clone your fork and then setup your development environment. Clone
your repository as follows (replace yourusername with your GitHub account name):

```bash
git clone https://github.com/yourusername/PyTado.git
cd PyTado
```

Then, to create your development environment and install the project with its dependencies, execute the following
commands in your terminal:

```bash
# Create and activate a new virtual environment
python3 -m venv venv
source venv/bin/activate

# install all dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### Coding Guidelines

To maintain a consistent codebase, we utilize [black][1]. Consistency is crucial as it helps readability, reduces errors,
and facilitates collaboration among developers.

To ensure that every commit adheres to our coding standards, we've integrated [pre-commit hooks][2]. These hooks
automatically run `black` before each commit, ensuring that all code changes are automatically checked and formatted.

For details on how to set up your development environment to make use of these hooks, please refer to the
[Development][3] section of our documentation.

[1]: https://github.com/ambv/black
[2]: https://pre-commit.com/
[3]: https://github.com/wmalgadey/PyTado#development

### Testing

Ensuring the robustness and reliability of our code is paramount. Therefore, all contributions must include at least one
test to verify the intended behavior.

To run tests locally, execute the test suite using `pytest` with the following command:

```bash
pytest tests/ --cov --cov-branch -vv
```

---

A message from the original author:

> This software is at a purely experimental stage. If you're interested and can write Python, clone the Github repo,
> drop me a line, and get involved!
>
> Best wishes and a warm winter to all!
>
> Chris Jewell


[devcontainer-shield]: https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode
[devcontainer]: https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/wmalgadey/PyTado
