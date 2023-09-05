# Mkdocs Framework and Material Theme for the Tanssi Documentation Site
 
https://docs.tanssi.network

This repo contains the mkdocs config files, theme overrides and css changes.

- [Mkdocs](https://www.mkdocs.org/)
- [Material for Mkdocs](https://squidfunk.github.io/mkdocs-material/)

The actual content is stored in the tanssi-docs repo and pulled into the tanssi-docs sub-directory during build.

- [Tanssi Docs](https://github.com/moondance-labs/tanssi-docs)

## Pre-requisites

To get started you need to have [mkdocs](https://www.mkdocs.org/) installed. All dependencies can be installed with a single command, you can run:

```
pip install -r requirements.txt
```

## Getting started

With the dependencies installed, let's proceed to clone the necessary repos. In order for everything to work correctly the file structure needs to be the following:

```
tanssi-mkdocs
|--- /material-overrides/ (folder)
|--- /tanssi-docs/ (repository)
|--- mkdocs.yml
```

So first, lets clone this repository:

```
git clone https://github.com/moondance-labs/tanssi-mkdocs
cd tanssi-mkdocs
```

Next, inside the folder just created, clone the [tanssi-docs repository](https://github.com/moondance-labs/tanssi-docs):

```
git clone https://github.com/moondance-labs/tanssi-docs
```

Now in the `tanssi-mkdocs` folder (which should be the current one) you can build the site by running:

```
cd ..
mkdocs serve
```

After a successful build, the site should be available at `http://127.0.0.1:8000`
