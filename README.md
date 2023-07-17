Automating Qualtrics Survey Building with Python
================================================

**qualtrics.py** is a simple Python library for scripting the creation of
Qualtrics surveys. It provides convenient wrapper methods for accessing the
Qualtrics survey-definitions REST API, along with a convenient object-oriented
interface for building virtual surveys to load through that API.
See 'Concept' section below for more.

*Status: Minimally viable. Un-maintained. Not systematically tested.*

Contents:

1. Concept: Qualtrics Automation---high level library overview.
2. Features
   * an incomplete list of API routes and survey features covered.
   * pointers for people who want to extend the library
3. Quick Start:
   * instructions to get this library installed.
   * instructions to get your API keys and routes.
   * instructions to compile a hello-world survey.
   * for more examples and advice, see [the guide](GUIDE.md).
   * for full library details, see [the reference](REFERENCE.md).
4. Related tools---pointers to other Qualtrics-related code projects.



1. Concept: Qualtrics Automation
--------------------------------

[Qualtrics](https://www.qualtrics.com/) is an online platform for designing
and distributing surveys and collecting responses. The traditional way to
build a Qualtrics survey is to use the survey builder web application.
For simple, small surveys, this is fine.[^rant]
However, in some cases, the web editor is not really sufficient.

1.  **What if one wants to create a survey with *a lot* of questions?**
    Maybe we want a survey with questions that have overlapping configurations
    (such as shared text or options) or are replicated many times between survey
    blocks (and/or different branches of the survey's flow).
    There is some support for sharing questions between blocks (I think), but
    this support is limited to exact question replication, so if questions
    need to have subtle differences, then they need to be replicated fully.
    
    In this case, using the web editor has several issues:

    * It takes an extremely long time to create and configure a large number
      of questions because the editor is fairly slow and clunky.
    * Creating a large number of questions manually is error-prone,
      especially if questions contain intricate data, therefore further
      time-intensive verification work is required (and there may still be
      issues).
    * If there are changes to the survey design after much of this work has
      been completed, necessitating changes to a large number of questions,
      then much of the work must be repeated (plus, one must additionally
      worry about different parts of the survey getting out of sync).

2.  **What if one wants to create a survey with *highly complex* questions?**
    Perhaps the questions require a large amount of HTML and JavaScript, such
    as for the inclusion of interactive widgets into the survey.
    The Qualtrics web survey editor has a built-in source editor for adding
    such source code. In principle, this can be used. However, there are
    a few major issues that come up as the complexity of the code scales.

    * The source behind each question is hidden away in the question's
      configuration, rather than front-and-center, making it a little awkward
      to build surveys with a lot of questions from source.
    * The web editor allows editing HTML or JavaScript, but does not have
      the same level of useful features for editing source as a proper
      native text editor or IDE.
    * Let alone if one wants to generate HTML and/or JavaScript using a
      transpiler or bundler of some kind: to get such code into the web
      editor would require copying and pasting the built files into the
      source fields manually.
    * It is impossible to keep the state of the survey under proper version
      control. (I'm not sure if Qualtrics surveys have some kind of version
      control, actually, but if it does, it can't be of the same calibre as
      a professional source versioning tool such as git).

One idea for addressing these issues is to shift from thinking about the
Qualtrics web editor as a source editor to thinking about it as a compilation
target. Building a Qualtrics survey becomes a two-level process:

1. Edit the 'source code' of a survey within a professional-grade development
   environment (e.g., offline, with text-based files, under version control,
   in a [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) manner,
   potentially using higher-level languages than HTML and JavaScript, etc.).

2. Automatically translate this survey 'source code', somehow, into a survey
   proper on the Qualtrics platform.

Lucky for us, Qualtrics provides a
  [RESTful API for survey building](https://api.qualtrics.com/ZG9jOjg3NzY2Nw-building-surveys),
which enables us to build a tool that implements (2).

The present library provides such a tool. The library allows one to compose a
survey with arbitrarily many arbitrarily complex questions in memory, and
then the upload that survey to Qualtrics using the API.

The contents of the questions can then be created with any means (such as
directly in Python, or by using pandoc to generate question HTML from
markdown, or by using a JavaScript bundler to generate question JS from a
higher-level language or a codebase spread across multiple files and with
various dependencies.

There are some pretty rough edges, and setting up the above pipelines for
very complex surveys can still be a bit messy. However, in my opinion it's
already miles ahead of using the Qualtrics web editor.

Have fun!

[^rant]: Actually, since you asked: let me rant a bit. I have to use
  Qualtrics for a project at work. I don't like Qualtrics, or it's web-based
  survey editor.
  The editor and the surveys generated are slow and clunky---somehow in a way
  that seems worse than the majority of other bloated webware out there.
  I maintain that I don't see why it has to be this way.
  But then again, I'm a bit of a curmudgeon for web stuff generally (my
  personal website uses hand-made CSS, to give you a flavor).
  Anyway, at least Qualtrics developers have had the decency to offer a
  partially-documented API for building surveys programmatically, and I've
  been able to build this library as a way to avoid using their web editor
  almost entirely. So, thanks I guess.

2. Features
-----------

> To be clear: Let me start with a list of *non-features*:
> 
> * Not aiming for coverage of Qualtrics API other than survey-definitions
>   (e.g. for downloading survey responses or managing participants).
>   * See the [list of related tools](#related-tools) for help there.
> * Nor even full coverage of the Qualtrics survey-definitions API, nor even of
>   all of the configuration options for the questions types it does cover
> 
> The goal is *just enough* coverage for me to be able to create the types of
> surveys I need with the configuration options I need.
> 
> However, the library and the API are pretty straight-forward, so it should be
> pretty easy to extend the coverage as needed if you want to do that.

### API coverage

Surveys
 
* List all surveys
* Get survey (by id)
* Create blank survey with a particular name
* Delete survey (by id)

Survey options (for a survey with a particular id)

* Get survey options
* Modify survey options (e.g. to add header HTML/JS, or styling CSS)

Blocks (for a survey with a particular id)

* List all blocks
* Get block (by id)
* Create a new blank standard block
* Delete block (by id)
* Append a page break to a block
* Update a block's options (by id)
* (TODO: easy way to modify common block options such as randomisation)

Questions (for a survey with a particular id)

* Append questions of various kinds to a survey's default block, or a
  particular block

Flows

* get the survey's flowchart
* update the survey's flowchart
* convenient classes for building certain types of flow elements

### Question types

Question types supported (a convenient class is implemented making it easy to
add such questions---all other questions can be uploaded with raw JSON but
this requires investigating the required format + some trial-and-error).

* Text/graphics questions (including customisable HTML and JS)
* Timing questions
* Slider questions (configurable number and bounds of sliders)
* Constant-sum questions with sliders (configurable number
  and bounds of sliders, configurable sum)
* Multiple choice questions (button and drop-down lists)
* Text-entry questions (single-line, multi-line, essay)
* TODO: Multiple answer, many various other question types.
* See also: blocks (above) for appending page breaks, which are not
  technically questions, but can be mixed with questions in a block.

### Error handling

There is no automatic error handling.

Sometimes, the qualtrics API calls will seize up. I don't know why. If the
progress bars are stuck for a while, just quit and start again.

### Contributing

This project is not currently maintained. Issues and PRs will be infrequently
monitored if/when I have time.

If you want to contribute substantially, I advise you fork the project and
take it in the direction you like.

Note on documentation:

* [The guide](GUIDE.md) is written by hand.
  * Please keep it up-to-date with breaking API changes.
  * When implementing a new feature, consider adding an example in the guide.
* [The reference](REFERENCE.md) is automatically generated from the
  docstrings in the source code (qualtrics.py)
  * Do not manually modify REFERENCE.md.
  * Instead, generate it using [`pdoc`](https://pdoc3.github.io/pdoc/).
    * one-time install `pip install pdoc3` (note `pdoc3` not `pdoc`)
    * followed by `pdoc qualtrics.py > REFERENCE.md` to update the reference
      each time the library changes.
  * Obviously, the docstrings in qualtrics.py must be kept up to date.

TODO:

* [x] write the guide
* [x] move into multiple files
* [ ] complete documentation
  * [x] Virtual survey
  * [x] Virtual blocks
  * [x] Virtual QuestionJS
  * [ ] Virtual questions
  * [ ] Virtual flows
  * [ ] API wrapper
  * [x] Recipes
  * [x] notqdm
* [ ] Generate documentation
* [ ] Generate documentation in a convenient format (host with ghp?)

Probably won't get time:

* [ ] Make this into a proper developer section of the readme?
* [ ] Black code formatting?
* [ ] Tests... hahaha...


3. Quick start
--------------

### Installation

Python dependencies:

1. requests (`pip install requests`) for making the API calls.
2. tqdm (`pip install tqdm`) for displaying progress bars (making many API
  calls can take some time)
  * This dependency is optional but the code to make surveys without it has
    not been thoroughly tested and might break

Installing the library:

1. For now it's just a single script: copy or symlink **qualtrics.py** into
   your project directory so that you can import it from your script.

### Get your keys

1. Get your API "token", by following
   [these instructions](https://api.qualtrics.com/ZG9jOjg3NjYzMg-api-key-authentication).
   Keep the token safe, it allows anyone to access your Qualtrics account and
   all of the data within it.
2. Get your "data center ID" by following
   [these instructions](https://api.qualtrics.com/ZG9jOjg3NjYzMw-base-url-and-datacenter-i-ds).
   Actually, I found that in my case using the brand base URL prefix
   (`melbourneuni.au1` for me) also works and is slightly more convenient.

This library will require your API token and data center ID to make API calls
on your behalf.

> NOTE: If you are from the University of Melbourne, make sure you log into
> Qualtrics with your staff account, rather than your student account. I
> heard the student API keys don't work in later steps.

### Hello, world!

From there, a script to create a dead-simple survey is as follows:

```python
import qualtrics as qq

# build the survey data structure
survey = qq.BasicSurvey(name="Test Survey")
for i in range(3):
      survey.append_question(qq.TextGraphicQuestion(
          text_html=f"question {j}",
      ))

# upload the survey to Qualtrics
# see 'Get your keys' above for API_TOKEN and DATA_CENTER
api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)
survey.create(api)
```

### More information

For more usage examples and advice see the [guide](GUIDE.md).

For complete information on library functions see the [reference](REFERENCE.md).


4. Related tools
----------------

I haven't found anything that provides a convenient way to automate survey
*building* (hence making this).

However, there are a few substantial tools that appear to automate other
parts of the qualtrics API. Here are some I noticed based on a quick github
search for 'qualtrics':

Python:

* https://github.com/Jaseibert/QualtricsAPI
* https://github.com/Baguage/pyqualtrics
* https://github.com/willgreenland/surveyhelper
* https://github.com/cwade/py_qualtrics_api

Ruby:

* https://github.com/CambridgeEducation/qualtrics_api

R:

* https://github.com/emma-morgan/QualtricsTools
* https://github.com/cloudyr/qualtrics

PHP:

* https://github.com/UI-Research/qualtrics-api-php

---

Other links to explore later:

* A guide to the Qualtrics Survey File format:
  https://gist.github.com/ctesta01/d4255959dace01431fb90618d1e8c241
* Related R project https://github.com/sumtxt/qsf
* Some more of the qualtrics documentation...

