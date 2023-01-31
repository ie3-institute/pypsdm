# python-template

Python template that includes all the basics for your new shiny project.

## Setup 

1. Open a new repository while using this template.
This repository is marked as a template repository.
Github offers you the convenient possibility to open a new repository from a such a template repository.
See [here](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template) for details.
2. Clone your new repository
3. Rename the `python-project` package to your project name (this is where your source code should go). 
4. Install the dependencies (preferably within a fresh virtual environment)
5. Run `pre-commit install`
6. Enjoy!

## What's in here?

### Formatting

To spare you the pain of manually taking care of formatting your code and establish some consistency (remember "äußere Ordnung führt zu innerer Ordnung") it includes [Black](https://black.readthedocs.io/en/stable/) for automated formatting. 
Execute `black .` in the terminal at the project's root directory to format your code.

### Testing

To make sure your code actually does what you think it does! 
The template includes [pytest](https://docs.pytest.org/en/7.1.x/) for that purpose. 
Include the tests in the `tests` directory. Running `pytest` in the terminal at the project's root directory executes all tests and hopefully replaces hoping that your code works by knowing (at least so far as your actual test all relevant cases and boundary conditions). 

### CI

To give you a slap on the wrist if you did not apply the formatter or your tests don't pass there is a [Github Actions](https://github.com/features/actions) workflow at `.github/workflows/simple-ci.yml`. 
After pushing to the remote repository it checks out your code, installs all the dependencies then runs `flake8` for any code style issues and `black --check` to check the formatting. 
Depending on how that went you will see yourself either confronted with a friendly green tick or rather unfriendly red cross at the code window in github (or the `Actions` section of the github repository.) 

### Pre-Commit

To reduce slaps on the wrist there is [pre-commit](https://pre-commit.com/) having your back. 
It installs pre-commit hooks that `black` and `flake8` before the CI gets a chance to complain.
The types of git hooks are configured in `.pre-commit-config.yaml`.
To install the hooks run `pre-commit install` once in the terminal at the project's root directory.

### Dependabot

To keep the dust off your dependencies [Dependabot](https://github.blog/2020-06-01-keep-all-your-packages-up-to-date-with-dependabot/) checks for new versions once a day (according to current cofigurations) and opens Pull-Requests in case it finds any newer versions.
The configuration can be changed at `.github/dependabot.yml`
Keep in mind that dependency updates can break your code.
You safeguard yourself against this by making sure you have all your code tested and the dependency pull request does not break any of them.

## Something Missing? 

We are happy to learn about additional tools for easing the developer workflow. 
Feel free to open an issue or pull-request to make suggestions.