Automating Qualtrics Survey Building with Python
================================================

**qualtrics.py** is a simple Python library for scripting the creation of
qualtrics surveys.
It provides a convenient interface to the Qualtrics survey-definitions REST
API.

The current goal of this library is **not** full coverage of the Qualtrics
API, nor even of the survey-definitions API, nor even of all of the
configuration options for the questions types it does cover.
The goal is *just enough* coverage for me to be able to create the types of
surveys I need with the configuration options I need.

However, the library and the API are pretty straight-forward, so it's pretty
easy to extend the coverage as needed if you want to do that. Some notes on
the API and tips for extending the library are included below, and PRs are
welcome (try to follow a similar interface and provide good defaults for new
options).

Status: Early draft.

TODO:

* [x] basic API wrapper for key question types
* [x] class-based interface for more succinct survey building
* [ ] documentation
* [ ] more question types and configuration options
* [ ] class-based interface for the return types of the other API methods,
  not just creating fresh surveys?

Note: This library is mainly for building surveys. It is not for
downloading survey responses, though Qualtrics offers an APi for that.
For the latter, see for example
  [QualtricsAPI](https://github.com/Jaseibert/QualtricsAPI)
or various tools built for R or other languages.


Installation
------------

Python dependencies:

1. requests (`pip install requests`) for making the API calls.
2. tqdm (`pip install tqdm`) for displaying progress bars (making many API
  calls can take some time)---TODO: make this an optional dependency.


Installing the library:

1. For now it's just a single script: copy or symlink **qualtrics.py** into
   your project directory so that you can import it from your script.


Setup:

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


Quick start
-----------

In the following examples, `API_TOKEN` and `DATA_CENTER` contain strings
determined per above instructions.


Create a survey with a single text question with text "Hello, world!".

```python
import qualtrics as qq

# build the survey data structure
survey = qq.Survey(name="Test Survey")
survey.add_question(qq.TextGraphicQuestion(text_html="Hello, world!"))

# use the API to create the survey within your Qualtrics account
api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)
survey.create(api)
```


Create a survey with three blocks of four questions each, separated by page
breaks:

```python
import qualtrics as qq

# build the survey data structure
survey = qq.Survey(name="Test Survey")
for i in range(3):
    block = survey.add_block(qq.Block())
    for j in range(4):
        block.add_question(qq.TextGraphicQuestion(
            text_html=f"Block {i}, question {j}",
        ))
        block.add_page_break()

# upload the survey to Qualtrics
api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)
survey.create(api)
```


Alternatively, provide the questions and blocks to the survey via the
constructor:

```python
import qualtrics as qq

qq.Survey(
    name="Test Survey",
    blocks=[
        qq.Block(questions=[
            q
            for j in range(4)
            for q in (
                qq.TextGraphicQuestion(text_html=f"Block {i}, question{j}"),
                qq.PageBreak()
            ) 
        ])
        for i in range(3)
    ]
).create(qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER))
```


Most question types allow a `script_js` parameter, which is a string that
becomes JavaScript code attached to the question. The supported JS functions
are those from the Qualtrics JavaScript Question API,
  [documented here](https://api.qualtrics.com/82bd4d5c331f1-qualtrics-java-script-question-api-class).
The most common usage is to attach code that runs on page load, on page
ready, on page submission[^submit], and on page unloading. Attach a script such as
the following (based on the default code from the web editor).

[^submit]:
  Note that page submission triggers each time the user presses the submit
  button for the page, even if, for example, the validation fails because of
  some missing answers, and they end up staying on the page... so this code
  might run multiple times!

```js
Qualtrics.SurveyEngine.addOnload(function() {
	/* Place your JavaScript here to run when the page loads*/
});

Qualtrics.SurveyEngine.addOnReady(function() {
	/* Place your JavaScript here to run when the page is fully displayed*/
});

Qualtrics.SurveyEngine.addOnPageSubmit(function() {
	/* Place your JavaScript here to run when the submit button is pressed */
});

Qualtrics.SurveyEngine.addOnUnload(function() {
	/* Place your JavaScript here to run when the page is unloaded*/
});
```
This script should be passed to the `script_js` field of a question
constructor as a Python string. To make constructing this string a little
easier, this library provides a builder class `QuestionJS`, which can be used
as follows:

```python
q = TextGraphicQuestion(
      text_html="<p>Hello, world!</p>",
      script_js=QuestionJS() # builder pattern
        .on_load('console.log("loaded!")')
        .on_ready('console.log("ready!")')
        .on_ready('console.log("ready! again!")')
        .on_submit('console.log("submitting!")')
        .on_unload('console.log("unloaded!")')
        .script(), # always end with .script(), which converts to a string
```

It seems that an arbitrary number of chunks of code can be attached to each
event (which is why I chose to use the builder pattern for this, rather than,
say, a constructor with four optional arguments).


Finally, one can make API calls directly, without wrapper classes. This
includes methods for viewing, modifying, and deleting surveys from the
Qualtrics account. For example, one useful pattern is to start the script by
removing the survey(s) created in previous runs.

```python
import qualtrics as qq
import tqdm                 # `pip install tqdm`

api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)

# find all surveys
surveys = api.list_surveys()['elements']
print("found", len(surveys), "surveys total")

# filter for matching surveys
surveys = [s for s in surveys if s['name'] == "Test Survey"]
print("found", len(surveys), "surveys with name 'Test Survey'")

# delete these surveys
for survey in tqdm.tqdm(surveys):
    api.delete_survey(survey['id'])

```

This pattern is actually already provided as a library function:
`qq.delete_all_surveys_by_name(api, survey_name)`.


Features
--------

(TODO: proper documentation)

**Survey Definitions API**

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
  * Text/graphics questions (including customisable HTML and JS)
  * Timing questions
  * Slider questions (configurable number and bounds of sliders)
  * Constant-sum questions with sliders (configurable number
    and bounds of sliders, configurable sum)
  * TODO: Multiple choice, multiple answer, many various other question
    types.
  * See also: blocks (above) for appending page breaks, which are not
    technically questions, but can be mixed with questions in a block.


Notes
-----

**How can I find out about the Qualtrics survey builder API?**

The qualtrics API documentation has an overview of the survey-builder API,
and information about each of the available methods:

* https://api.qualtrics.com/ZG9jOjg3NzY2Nw-building-surveys
* https://api.qualtrics.com/ZG9jOjg3NzY4Mg-survey-api-introduction
* https://api.qualtrics.com/60d24f6897737-qualtrics-survey-api

The last link is the full reference. Unfortunately, not all of the methods
appear to be documented accurately, so some trial and error is necessary to
figure out which fields are needed and how to achieve certain modifications.

To get started, see this tutorial:

* https://api.qualtrics.com/ZG9jOjg3NzY4Mw-example-use-cases-walkthrough

**How can I learn more about the required data format, for surveys or
for questions?**

Create a survey with the required format in the editor. Then use the API to
'get' the survey or question and see what the JSON looks like. Try creating a
new survey or question based on that JSON, possibly using trial and error
to discover which fields are really necessary to include in the posted data.


**How can I add JS to questions?**

I don't seem to be able to update or partial-update with QuestionJS field,
but I can totally create new questions with this field, so we're good to go.


**How can I add JS to surveys?**

It doesn't appear possible to configure the survey while creating it.

Yes, OK, to configure a survey uses a separate API call after the survey has
been created (survey-builder/{survey_id}/options or something).

That path appears to let you customise the CSS and a HTML Header and Footer
for the survey page. These HTML scripts can contain arbitrary JS via script
tags, so that's how we can get global JS.


**How can I organise questions using blocks?**

Things that work:

* creating empty blocks (BlockElements removed or set to []) THEN creating
  questions with an optional parameter that specifies the block ID of the
  block you actually want them to join.
* creating a question without a block ID parameter puts it in the default
  block. For surveys with a single block, this is all you need.

Things that don't work:

* creating a block with BlockElements containing questions that don't exist
* creating a block with BlockElements containing questions that do exist, but
  are already in the default block
* creating questions and then deleting the default block
* even creating questions (in the default block) and then updating the
  BlockElements of the default block to remove them, and then trying to add
  them back to the blockelements in a new block being created? the questions
  do remain in the survey, though.
* providing "ReferencedBlockID" while creating the block (this must
  do something else, perhaps to do with flow? It's not clear from the docs)

Things that might work, haven't tried (only need one thing that works!):

* creating an empty block and then editing questions out of the old block's
  element list and then back into the new block's element list?
