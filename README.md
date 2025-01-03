# Mkdocs Framework and Material Theme for the Tanssi Documentation Site

https://docs.tanssi.network

This repo contains the mkdocs config files, theme overrides and css changes.

- [Mkdocs](https://www.mkdocs.org/)
- [Material for Mkdocs](https://squidfunk.github.io/mkdocs-material/)

The actual content is stored in the tanssi-docs repo and pulled into the tanssi-docs sub-directory during build.

- [Tanssi Docs](https://github.com/moondance-labs/tanssi-docs)

## Prerequisites

To get started you need to have [mkdocs](https://www.mkdocs.org/) installed. All dependencies can be installed with a single command, you can run:

```bash
pip install -r requirements.txt
```

## Getting started

With the dependencies installed, let's proceed to clone the necessary repos. In order for everything to work correctly the file structure needs to be the following:

```text
tanssi-mkdocs
|--- /material-overrides/ (folder)
|--- /tanssi-docs/ (repository)
|--- mkdocs.yml
```

So first, lets clone this repository:

```bash
git clone https://github.com/moondance-labs/tanssi-mkdocs
cd tanssi-mkdocs
```

Next, inside the folder just created, clone the [tanssi-docs repository](https://github.com/moondance-labs/tanssi-docs):

```bash
git clone https://github.com/moondance-labs/tanssi-docs
```

Now in the `tanssi-mkdocs` folder (which should be the current one) you can build the site by running:

```bash
cd ..
mkdocs serve
```

After a successful build, the site should be available at `http://127.0.0.1:8000`

## Editing Theme Files

If you're editing any of the files in the `material-overrides` directory, you can run the following command to watch for these changes and render them automatically:

```bash
mkdocs serve --watch-theme
```

Otherwise, you'll need to stop the server (`control + C`) and restart it (`mkdocs serve`) to see the changes.

## Ignoring Excluded Docs Output

Running `mkdocs serve` displays the excluded documents in your terminal. To prevent this effect, you can run:

```bash
mkdocs serve --clean
```

## Disable the Git Dates Plugin

The `git-revision-date-localized` plugin pulls the date of the last git modification of a page. When developing locally, this can slow down your development process, as every time a change is made to a page, the plugin checks for the latest dates for all the pages. To avoid this, you can change your start-up command to disable the plugin by running:

```bash
export ENABLED_GIT_REVISION_DATE=false
mkdocs serve
```

## Improve Reload Times with Dirty Builds

To speed up reload times when running `mkdocs serve`, you can use the `--dirty` flag, which will only reload the pages that have been changed. This will take reload times from ~50 seconds to ~3 seconds.

```bash
mkdocs serve --dirty
```
