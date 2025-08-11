import subprocess

config_path = "scripts/custom_clear_preprocessor.py"
notebook_pattern = "docs/nbs/*.ipynb"

command = [
    "jupyter",
    "nbconvert",
    "--config",
    config_path,
    "--to",
    "notebook",
    "--output-dir",
    "docs/nbs",
    notebook_pattern,
]

subprocess.run(command, check=True)
