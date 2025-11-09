


# yamlfmt

`yamlfmt` is an extensible command line tool or library to format yaml files. 


## Tools
### yamlfmt


#### Installation

```bash
# Find version of the release you are targetting  here https://github.com/google/yamlfmt/releases

VERSION="0.20.0"
curl -L -o yamlfmt_${VERSION}_Linux_x86_64.tar.gz https://github.com/google/yamlfmt/releases/download/v${VERSION}/yamlfmt_${VERSION}_Linux_x86_64.tar.gz

tar -xzf yamlfmt_${VERSION}_Linux_x86_64.tar.gz
chmod +x yamlfmt

sudo mv yamlfmt /usr/local/bin/
yamlfmt --version
```

#### Configuration File

The `yamlfmt` command can be configured through a yaml file called `.yamlfmt`. This file can live in your working directory, a path specified through a [CLI flag](./docs/command-usage.md#operation-flags), or in the standard global config path on your system (see docs for specifics).
For in-depth configuration documentation see [Config](docs/config-file.md).


### Basic Usage

See [Command Usage](./docs/command-usage.md) for in-depth information and available flags.

To run the tool with all default settings, run the command with a path argument:
```bash
yamlfmt x.yaml y.yaml <...>
```
You can specify as many paths as you want. You can also specify a directory which will be searched recursively for any files with the extension `.yaml` or `.yml`.
```bash
yamlfmt .
```

You can also use an alternate mode that will search paths with doublestar globs by supplying the `-dstar` flag. 
```bash
yamlfmt -dstar **/*.{yaml,yml}
```
See the [doublestar](https://github.com/bmatcuk/doublestar) package for more information on this format.

Yamlfmt can also be used in ci/cd pipelines which supports running containers. The following snippet shows an example job for GitLab CI:
```yaml
yamllint:
  image: ghcr.io/google/yamlfmt:latest
  script:
    - yamlfmt -lint .
```
The Docker image can also be used to run yamlfmt without installing it on your system. Just mount the directory you want to format as a volume (`/project` is used by default):
```bash
docker run -v "$(pwd):/project" ghcr.io/google/yamlfmt:latest <yamlfmt args>
```