# GitHound Project

## Description

GitHound is a Python tool for searching secrets in GitHub repositories. It is designed to be fast, efficient, and easy to use. This project provides a command-line interface (CLI) to interact with the GitHound functionality.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/githound.git
    ```
2.  Navigate to the project directory:
    ```bash
    cd githound
    ```
3.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To use GitHound, run the `main.py` script with the desired command-line arguments. For example, to search for secrets in a specific repository, you can use the following command:

```bash
python main.py --query "your-search-query" --repo "owner/repository"
```

For more information on the available options, you can use the `--help` flag:

```bash
python main.py --help
```

## Testing

To run the test suite, use the `pytest` command in the project's root directory:

```bash
pytest