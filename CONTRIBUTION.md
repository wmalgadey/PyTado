# Contributing to PyTado

Thank you for considering contributing to PyTado! This document provides guidelines to help you get started with your contributions. Please follow the instructions below to ensure a smooth contribution process.

## Development Environment

1. **Prepare your development environment**:
   - Clone the repository: `git clone https://github.com/yourusername/PyTado.git`
   - Navigate to the project directory: `cd PyTado`
   - Set up a virtual environment: `python3 -m venv .venv`
   - Activate the virtual environment:
     - On macOS/Linux: `source .venv/bin/activate`
     - On Windows: `.venv\Scripts\activate`
   - Install the dependencies: `pip install -r requirements.txt` and `pip install -e .`

2. **Install pre-commit hooks** (Reminder to add pre-commit hooks in the future):
   - Install pre-commit: `pip install pre-commit`
   - Set up the pre-commit hooks: `pre-commit install`

3. **Run tests with coverage**:
   - Execute the test suite with `coverage run -m pytest`

By following these steps, you can ensure that your contributions are of the highest quality and are properly tested before they are merged into the project.

## Issues

If you encounter a problem or have a suggestion, please open a [new issue](https://github.com/wmalgadey/PyTado/issues/new/choose). Select the most appropriate type from the options provided:

- **Bug Report**: If you've identified an issue with an existing feature that isn't performing as documented or expected, please select this option. This will help us identify and rectify problems more efficiently.
- **Feature Request**: If you have an idea for a new feature or an enhancement to the current ones, select this option. Additionally, if you feel that a certain feature could be optimized or modified to better suit specific scenarios, this is the right category to bring it to our attention.
- **General Question**: If you are unsure or have a general question, please join our [GitHub Discussions](https://github.com/wmalgadey/PyTado/discussions).

After choosing an issue type, a pre-formatted template will appear. Provide as much detail as possible within this template. Your insights and contributions help improve the project, and we genuinely appreciate your effort.

## Pull Requests

### PR Title

We follow the [conventional commit convention](https://www.conventionalcommits.org/en/v1.0.0/) for our PR titles. The title should adhere to the structure below:

```
<type>[optional scope]: <description>
```

The common types are:
- `feat` (enhancements)
- `fix` (bug fixes)
- `docs` (documentation changes)
- `perf` (performance improvements)
- `refactor` (major code refactorings)
- `tests` (changes to tests)
- `tools` (changes to package spec or tools in general)
- `ci` (changes to our CI)
- `deps` (changes to dependencies)

If your change breaks backwards compatibility, indicate so by adding `!` after the type.

Examples:
- `feat(cli): add Transcribe command`
- `fix: ensure hashing function returns correct value for random input`
- `feat!: remove deprecated API` (a change that breaks backwards compatibility)

### PR Description

After opening a new pull request, a pre-formatted template will appear. Provide as much detail as possible within this template. A good description can speed up the review process to get your code merged.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](https://www.contributor-covenant.org/version/2/0/code_of_conduct/). By participating in this project, you agree to abide by its terms.

Thank you for your contributions!