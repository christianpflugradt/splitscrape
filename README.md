# SPLITSCRAPr

SPLITSCRAPr is a tool to notify you about changes to content on websites.

SPLITSCRAPr scrapes content by splitting. Content will be stored as reference and if it differs on the next run, it'll notify about the new content via e-mail. Split is a primitive alternative to other extraction languages and frameworks such as regular expressions. It is very simple to use but not as versatile and potentially more error-prone.

Some common use cases for this script:
- You are following a blog and want to be informed about new articles -> scrape the landing page that lists the latest articles
- You want to be informed about new releases of your favourite band -> scrape a site that lists their discography
- You are following an article that is regularly updated
- You are interested in new releases of a software -> scrape its changelog
- You are interested in new commits to a github project -> scrape their commit history
- You are interested in updates to an arbitrary list, like problems at project-euler -> scrape their [recent additions](https://projecteuler.net/recent)

Some of these can certainly be addressed through individual options like newsletters but they remain individual and are not universally applicable, in addition through SPLITSCRAPr you can avoid creating an account which will almost always be obligatory if you want to keep updated via mail through services of the respective website itself.

## How to use

SPLITSCRAPr comes as a Python script and is meant to be used in combination with a scheduler. I've chosen Python because it's basically pre-installed on all modern operating systems. SPLITSCRAPr requires [Python 3](https://www.python.org/) and creates files in the current working directory. The following example if installed via [crontab](https://en.wikipedia.org/wiki/Cron) will run SPLITSCRAPr at 6 in the morning, at noon and at 6 in the evening every day, assuming it's located in a directory `/opt/splitscrapr`.

`0 6,12,18 * * * cd /opt/splitscrapr; python3 splitscrapr.py`

The provided configuration file [splitscrapr.yml](splitscrapr.yml) comes with an example site. A site is a definition of something you want to scrape. It has a name representing it, a url to scrape from and most importantly a list of splits to splitscrape content by. The next section will go into details about that.

If [SPLITSCRAPr](splitscrapr.py) is invoked without arguments, the configuration will be read from a file `splitscrapr.yml` in the current working directory. Alternatively a configuration can be passed to the script either as a relative or absolute filename.

Examples:
- `python3 splitscrapr.py myconfig.yml`
- `python3 splitscrapr.py /opt/splitscrapr/myconfig.yml`

**Attention**: Not all websites tolerate bots scraping their content. When using SPLITSCRAPr be aware of the website's general terms and conditions or any other possible violations. Be mindful in how often you scrape a website or your IP address or other means of identification might get blocked.

## Split-scraping by example

SPLITSCRAPr scrapes websites or any other http(s) endpoints. It really doesn't need to be html, it could also scrape a javascript or css file or any other resource representable as text. The [configuration](splitscrapr.yml) provided in this repository contains an example site that checks for new releases of my password manager.

The site url is `https://pflugradts.de/password-manager/` and there are two splits:
```
- sep: "<p class=\"pfl-section\"><span>Releases</span></p>"
pos: 1
- sep: "<p>"
pos: 1
```

The part we're interested in is right after the html code `<p class=\"pfl-section\"><span>Releases</span></p>` so we split the content by it and look at the remaining content at pos `1`, since everything before that code is at pos `0`. Each release is enclosed in a `<p>` tag so that'll be our second split and we're again interested in the code at pos `1` because the content comes immediately after the first `<p>` tag. What we're actually grabbing from the site is something like `<a href="/downloads/pwman3/pwman3-2.3.7.jar">2.3.7</a> released 10 Feb 2023</p>`. Because this is invalid html, we define extracontent in the site configuration:

```
extracontent:
  pre: "<html><body><p>"
  post: "</body></html>"
```

With this configuration the final content is something like this: `<html><body><p><a href="/downloads/pwman3/pwman3-2.3.7.jar">2.3.7</a> released 10 Feb 2023</p></body></html>`

Upon release of a new version, like a 2.3.8 or a 2.4.0, this exact content will be sent as html e-mail to the recipients listed for that site.

To add your own site to the configuration you will have to define suitable splits yourself. You will have to check the original content for that, in case of html to view the website as source code. In most modern web browsers you can do that by prefixing the url with `view-source:`. 

SPLITSCRAPr uses Python's [split function](https://docs.python.org/3/library/stdtypes.html#str.split) to split content. The split separator will actually be removed through this operation. To get a feeling for how this works launch the Python REPL (just input `python` if you have it installed) and type in `'1,2,3,4,5'.split(',')[2]`. Modify the string (`'1,2,3,4,5'`), the split separator (`','`) and the index (`[2]`) to make yourself familiar with it.

See the debugging section further below for more tips.

## Configuration

SPLITSCRAPr requires a complete configuration file in [yaml](https://yaml.org/) format. There are no hidden defaults, everything must be provided in that file. That shouldn't cause any problems though as [an example](splitscrapr.yml) is provided and the configuration is not very extensive.

If you're not familiar with yaml you should enclose all string values in quotes, like `"value"`. Quotes within strings must be escaped with a back slash, like `"value with \"quotes\" in it"`. You can write a list in yaml using square brackets, like `[1, 2, 3]` is a list containing the numbers 1, 2 and 3. For a list of "objects" you can use dashes:

```
sites:
  - name: foo
    url: https://foo.example.org
    enabled: true
  - name: bar
    url: https://bar.example.org
    enabled: true
  - name: baz 
    url: https://baz.example.org
    enabled: true
```
This shortened example contains three sites (foo, bar and baz) each with three properties (name, url and enabled)

This section will describe all configurable parameters:

| Field | values | Description |
| --- | --- | --- |
| **logging.level** | debug, info, warn, error | `error` logs only actual failures including stacktraces; there are currently no additional logs at `warning` level; `info` informs about updated definitions (when scraped content is updated); `debug` prints out everything including when the script starts and finishes, at debug level you can also see how many seconds it took to access and download content |
| **logging.format** | string | `fmt` value of Python's `logging.formatter` |
| **logging.dateformat** | string | `datefmt` value of Python's `logging.formatter` |
| **logging.logtostdout** | true, false | if true logs are written to stdout |
| **logging.file.logtofile** | true, false | if true logs are written to a log file |
| **logging.file.filename** | string, valid file name | file name of the log file |
| **logging.file.maxbytes** | int | maximum size of the log file in bytes |
| **logging.file.backups** | int | number of rotations for the log file; e.g. if set to 3, three more files will be written to keep old logs, extending the original log file name with `.1`, `.2` and `.3` |
| **http.useragent** | string | the user-agent http header sent when downloading content; some websites may deny access depending on the user-agent specified |
| **smtp.server** | string, valid domain name | domain name of the smtp server to be used to send mails |
| **smtp.port** | int, valid smtp port | port of the smtp server to be used to send mails |
| **smtp.user** | string | user for smtp server authentication |
| **smtp.password** | string | password for smtp server authentication |
| **sites** | list | list of sites SPLITSCRAPr should manage |
| **sites.name** | string, valid file name | arbitrary name to represent a site |
| **sites.url** | string, valid url | url of the endpoint to scrape, must start with `https://` or `http://` |
| **sites.splits** | list | list of split rules to scrape specific content from a website |
| **sites.splits.sep** | string | the separator to split content into a list of sub-contents |
| **sites.splits.pos** | int | the position in the list of sub-contents to process further; the index is 0 based so if there is only one match for the separator the content before it will be stored at pos 0 and the content after at pos 1, specifying a pos such as 2 will result in an error |
| **sites.extracontent** | structure | enriches content after scraping it |
| **sites.extracontent.pre** | string | adds an arbitrary string before the scraped content |
| **sites.extracontent.post** | string | adds an arbitrary string after the scraped content |
| **sites.extracontent.fixrelativelinks** | true, false | if true tries to fix links so they can be clicked from the update notification mail (html specific), e.g. a link `/foo.html` for a site with url `https://bar.baz` will be changed to `https://bar.baz/foo.html` |
| **sites.contenttype** | plain, html | sets content type for the notification mail to be sent; typically set to html if html content is parsed; in theory all subtypes supported by Python's `email.mime.text.MIMEText` subtype argument are supported |
| **sites.recipients** | list of valid e-mail addresses | recipients that should be notified about a content update |
| **sites.backups** | int | number of backups stored for content, e.g. if set to 3 for a site named `foo` the previous three updates will be stored in files `foo.1`, `foo.2` and `foo.3` in addition to the latest content stored in a file `foo` in the current working directory |
| **sites.enabled** | true, false | if true the site will be processed, if not it will be skipped (useful if something is not working yet) |

## Debugging

With some basic programming knowledge you can easily modify the [script](splitscrapr.py), add print statements or whatever you want. SPLITSCRAPr uses the Python logging framework and logs all exceptions with a stacktrace. You can set the log level to debug in the configuration to get as many details as possible.

The biggest obstacle will likely be the definition of splits for a website. SPLITSCRAPr offers the [splitscrapr-debug-site script](splitscrapr-debug-site.py) to support you in that matter. You should have a look at a website's source code first to find some suitable splits. Once that is done you can use the aforementioned script to test your splits.

Let's say you have a site `foo` with three splits but they're not working as intended and cause a `list index out of range` error in the last split.

Run the script to get the remaining content after every split: `python3 splitscrapr-debug-site.py foo`

The script will fail due to the list index out of range error but it will write everything processed up to that point into files:
- `foo.0` will contain the original unprocessed content retrieved from the url specified for that site
- `foo.1` will contain the content after applying the first split
- `foo.2` will contain the content after applying the second split
- there is no `foo.3` because the third split couldn't be applied

From looking at the file `foo.2` it should be obvious why the last split couldn't be applied. If it's not, copy the file content to clipboard, enter the Python REPL and input `a = """`. Now paste the content previously copied to clipboard, add `"""` and press enter. You now have the file content in a variable `a` and can apply the split by inputting `a.split("<SEP>")[<POS>]`, replacing `<SEP>` with the separator configured for that split and `<POS>` with the position configured for that split. Adjust the separator and position until you achieve the desired result. Remember that positions are 0-based and the separator itself will be removed from the content. Also remember that the first position (`0`) will always denote the content before the separator, even if it's an empty string.

## Further development

SPLITSCRAPr does not support any sort of authentication so only anonymously accessible content can be scraped.

SPLITSCRAPr does not support regular expressions or any other alternatives to splitting content.

If anyone finds this script useful and would like to provide or ask for a certain feature, feel free to get in touch with me, submit an issue or a merge request. Otherwise I'll mostly add features when I myself am in need of them.
