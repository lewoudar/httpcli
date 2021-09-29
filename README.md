# httpcli

This project is a proof of concept of a modern python networking cli which can be *simple* and *easy* to maintain using
some of the best packages in the python ecosystem:

- [click](https://click.palletsprojects.com/) for the foundation of a CLI application. There is also
  [asyncclick](https://github.com/python-trio/asyncclick) that I used in this project which is a tiny wrapper around
  click to provide asynchronous support.
- [rich](https://github.com/willmcgugan/rich) for pretty printing in the terminal.
- [httpx](https://www.python-httpx.org/) for HTTP protocol stuff.
- [anyio](https://anyio.readthedocs.io/en/stable/) for concurrency.
- [pytest](https://docs.pytest.org/en/latest/contents.html)
  and [pytest-trio](https://pytest-trio.readthedocs.io/en/stable/)
  for easy testing.

This is not a complete and mature project like [httpie](https://httpie.io/) but I want to implement some features not
present in this beautiful package like:

- [HTTP2](https://fr.wikipedia.org/wiki/Hypertext_Transfer_Protocol/2) support
- more authentication scheme support like digest and oauth2
- easy cookies support
- support of posix signals like SIGINT and SIGTERM
- completion feature
- git "did you mean" like feature
- [sse](https://fr.wikipedia.org/wiki/Server-sent_events) support

## Evolution

I'm not quite sure if I will continue improving it without any motivation (sponsoring?) but it is already useful if you
want to test it, you just need to have [poetry](https://python-poetry.org/docs/) dependency manager and install the
project locally (`poetry install`). This will install two commands:

- `http` useful when you don't want the cli to verify server certificate.
- `https` when you need to verify server certificate.

## Usage

Hopefully subcommand usage should be straightforward, but I will point some specific cases.

```shell
Usage: http [OPTIONS] COMMAND [ARGS]...

  HTTP CLI

Options:
  --config-file FILENAME          A configuration file with options used to
                                  set the cli. Note that the file takes
                                  precedence over the other options.
  -t, --timeout FLOAT             Time for request to complete, a negative
                                  value means there is no timeout.
  --follow-redirects / -N, --no-follow-redirects
                                  flag to decide if http redirections must be
                                  followed
  --auth JSON_AUTH                A json string representing authentication
                                  information.
  --http-version [h1|h2]          Version of http used to make the request.
  --proxy URL                     Proxy url.
  --version                       Show the version and exit.
  --help                          Show this message and exit.

Commands:
  delete              Performs http DELETE request.
  download            Process download of urls given as arguments.
  get                 Performs http GET request.
  head                Performs http HEAD request.
  install-completion  Install completion script for bash, zsh and fish...
  options             Performs http OPTIONS request.
  patch               Performs http PATCH request.
  post                Performs http POST request.
  put                 Performs http PUT request.
  sse                 Reads and print SSE events on a given url.
```

### Global cli configuration

There are some options that can be configured on the root command. These options can be read from a `yaml` file using
option `--config-file`. The config file looks lie the following:

```yaml
# all options have default values, no need to specify them all
httpcli:
  http_version: h2
  follow_redirects: true
  proxy: https://proxy.com
  # timeout may be null to specify that you don't want a timeout
  timeout: 5.0
  auth:
    type: oauth2
    flow: password
    username: user
    password: pass
  # for https you also have the verify option to pass a custom certificate used to authenticate the server
  verify: /path/to/certificate
```

Those options can also be configured via environment variables. They are all prefixed with `HTTP_CLI_` and they can be
in lowercase or uppercase. Here is the same configuration as above but using environment variables:

```shell
HTTP_CLI_HTTP_VERSION=h2
HTTP_CLI_FOLLOW_REDIRECTS=true
HTTP_CLI_PROXY=https://proxy.com
HTTP_CLI_TIMEOUT=5.0
# here value is passed as json
HTTP_CLI_AUTH={"type": "oauth2", "flow": "password", "username": "user", "password": "pass"}
HTTP_CLI_VERIFY=/path/to/certificate
```

### Commands

#### install-completion

This is obviously the first command you will want to use to have subcommand and option autocompletion. You don't need to
do that for the two cli `http` and `https`. Doing it with one will install the other. The current shells supported
are `bash`, `zsh` and `fish`. To use autocompletion for subcommands, just enter the first letter and use `TAB` key
twice. For option autocompletion, enter the first dash and use `TAB` twice.

#### get, head, option, delete

The usage should be pretty straightforward for these commands.

```shell
http get --help
Usage: http get [OPTIONS] URL

  Performs http GET request.

  URL is the target url.

Options:
  -c, --cookie COOKIE  Cookie passed to the request, can by passed multiple
                       times.
  -H, --header HEADER  Header passed to the request, can by passed multiple
                       times.
  -q, --query QUERY    Querystring argument passed to the request, can by
                       passed multiple times.
  --help               Show this message and exit.
```

You can play with it using https://pie.dev. Here is a simple example:

```shell
http get https://pie.dev/get -c my:cookie -q my:query -H X-MY:HEADER
```

#### post, put, patch

There are some subtleties with these commands. I will use `post` in the following examples but the same apply to `put`
and `patch`.

**json data**

If you play with json, in case you only have string values, you can do this:

```shell
# here we are sending {"foo": "bar", "hello": "world"} to https://pie.dev/post
http post https://pie.dev/post -j foo:bar -j hello:world
```

If you need to send other values than strings, you will need to pass the json encoded value with a slightly different
syntax, `:=` instead of `=`.

```shell
http post https://pie.dev/post -j number:='2' -j boolean:='true' -j fruits:='["apple", "pineapple"]'
```

If you have a deeply nested structure you can't write simple in the terminal, you can use of json file instead.
Considering we have a file *fruits.json* with the following content:

```json
[
  "apple",
  "pineapple"
]
```

You can use the file like it:

```shell
http post https://pie.dev/post -j fruits:@fruits.json
```

**form data**

First you need to know that you can't pass **form data and json data in the same request**. You must choose between the
two methods. The basic usage is the following:

```shell
https post https://pie.dev/post -f foo:bar -f number:2
```

If you need to send files, here is what you can do:

```shell
# this will send the key "foo" with the value "bar" and the key "photo" with the file photo.jpg
https post https://pie.dev/post -f foo:bar -f photo:@photo.jpg
```

If you want to send raw data, use the following form:

```shell
https post https://pie.dev/post --raw 'raw content'
```

You can also pass the raw content in a file:

```shell
# you can put what you want in your file, just be sure to set the correct content-type
https post https://pie.dev/post --raw @hello.txt
```

#### download

You can pass urls as arguments. Files will be downloaded in the current directory. If you wish to change the directory
where files should be put, pass the `-d` option with the path of the desired destination folder.

```shell
# this will downloads two files and put them in the downloads directory of the current user
https download https://pie.dev/image/jpeg https://pie.dev/image/png -d ~/downloads
```

You can use a file to specify all the resources to download. There should be **one url per line**. Consider a file
`urls.txt` having the following content:

```text
https://pie.dev/image/svg
https://pie.def/image/webp
```

You can download urls from the file and urls from the command line at the same time:

```shell
https download https://pie.dev/image/jpeg -f urls.txt
```

#### sse

If you want to listen sse events from an endpoint, you can simply do this:

```shell
# The sse command will not stop if the data are sent without interruption, which is almost always the case
# with sse, so if you want to stop it, just Ctrl + C ;)
https sse https://endpoint.com/sse
```

## What needs to be improved?

If I were to continue the development of the project, here are the points to review/enhance:

- adapt code to support httpx 1.0 . At the moment of writing it is still in beta, but there is at least one breaking
  change concerning `allow_redirects` option.
- add more authentication schemes, mainly all the oauth2 flows, but may be some others like
  [macaroon](https://neilmadden.blog/2020/07/29/least-privilege-with-less-effort-macaroon-access-tokens-in-am-7-0/)...
- support multiple proxy values
- session support
- add CI/CD
- improve code coverage (not 100% yet)
- refactor a bit the code, currently I don't like the structure of my helpers modules. Also auth support can be
  refactored using this [technique](https://www.python-httpx.org/advanced/#customizing-authentication) I was not aware
  of when starting this project.
- add autocompletion featurefor other shells like ksh, powershell or powercore
- and probably more... :)