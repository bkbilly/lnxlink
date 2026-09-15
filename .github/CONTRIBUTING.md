# Contributing to LNXlink

The process is straight-forward.

 - Fork the LNXlink [git repository](https://github.com/bkbilly/lnxlink).
 - If LNXlink is installed, uninstall it.
 - Install as a [developer](https://bkbilly.gitbook.io/lnxlink/setup).
 - Read the [documentation](https://bkbilly.gitbook.io/lnxlink/development) for the modules or take a look at the [currently used modules](https://github.com/bkbilly/lnxlink/tree/master/lnxlink/modules).
 - Create a Pull Request.

## Checks before opening a pull request

Activate the development environment and install pre-commit if needed:

```bash
python -m pip install pre-commit
python -m pre_commit run --all-files
```

The pinned [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) defines the
checks: requirements, Black, Ruff, Pylint, and basic file checks. Ruff is the
linter; `ruff format` does not replace Black. Some hooks edit files. Inspect the
diff, keep the intended changes, and rerun until every hook passes. Include any
intentional dependency changes found by the requirements check in the pull request.

Run the relevant runtime tests as well. After pushing, inspect GitHub Actions
for the new commit and confirm that its `Python Checks` run passed.

`Docker Test` also publishes images on push events and requires `HUB_USERNAME`
and `HUB_TOKEN`. A registry-login failure before the build is separate from a
failed code check or build.

## Feature suggestions

If you want to suggest a new feature, create a new feature request issue.
