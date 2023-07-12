Usage Guide
===========

This guide contains:

* A brief background on Qualtrics survey structure
* A conceptual overview of the library and how to use it
* A description of the three available 'survey types'
* A few examples

This guide assumes you have followed the instructions in the
[README](README.md#installation) pertaining to installing the library and
getting your API "token" and data center ID.
In the following, `API_TOKEN` and `DATA_CENTER` contain the results of the
latter steps as strings.

Background: Qualtrics
---------------------

This application has the following features:

1. **Questions:**
   The user can create arbitrary collections of questions.
   * The questions can be of various question types (e.g., multiple choice,
     sliders, text response, Likert matrix questions).
   * Each question can be configured with specific details (HTML
     descriptions, option labels, even certain JavaScript functions).
2. **Blocks:**
   Once questions have been created, they can be arranged into 'question
   blocks', which roughly correspond to 'pages' in the rendered survey
   (though blocks can also have 'page breaks' making a single block span
   multiple pages).
3. **Flows:**
   For complex surveys, it is possible to design an intricate flowchart
   governing the sequence of blocks presented to participants.
   * For example, the survey can branch to different blocks based on earlier
     participant responses.
   * Or, the flowchart can be configured to randomly order a sequence of
     blocks, or randomly select a subset of blocks to show each
     participant---these features are useful for designing randomised
     controlled experiments (where different participants are shown
     slightly different surveys).
4. **Preview:**
   Qualtrics also provides a preview of (roughly) how the survey will look to
   participants, including interactivity, input validation, and any custom
   flows.

Background: Qualtrics API
-------------------------

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

Conceptual overview of automated survey construction
----------------------------------------------------

How to script the creation of a Qualtrics survey?

Conceptual introduction to three main survey types
--------------------------------------------------

TODO

Survey type 1: Basic Survey
---------------------------

Create a survey with a single text question with text "Hello, world!".
The `BasicSurvey` class is appropriate for surveys with a single block of
questions.

```python
import qualtrics as qq

# build the survey data structure
survey = qq.BasicSurvey(name="Test Survey")
survey.append_question(qq.TextGraphicQuestion(text_html="Hello, world!"))

# use the API to create the survey within your Qualtrics account
api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)
survey.create(api)
```

Survey type 2: Block Survey
---------------------------

Create a survey with three blocks of four questions each, separated by page
breaks. The `BlockSurvey` class is appropriate for surveys with multiple
blocks, presented one after another:

```python
import qualtrics as qq

# build the survey data structure
survey = qq.BlockSurvey(name="Test Survey")
for i in range(3):
    block = survey.append_block(qq.Block())
    for j in range(4):
        block.append_question(qq.TextGraphicQuestion(
            text_html=f"Block {i}, question {j}",
        ))
        block.append_page_break()

# upload the survey to Qualtrics
api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)
survey.create(api)
```

Alternatively, provide the questions and blocks to the survey directly
via the survey constructor:

```python
import qualtrics as qq

qq.BlockSurvey(
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

Survey type 3: Flow Survey
--------------------------

Create a survey with a more complex flow, for example randomly presenting one
of three blocks (arbitrary Qualtrics survey flows are also possible). For any
survey with a non-standard flow, use the `FlowSurvey` class.

```python
import qualtrics as qq

survey = qq.FlowSurvey(name="Test Survey")
randomizer = survey.append_flow(qq.BlockRandomizerFlow(
    n_samples=1,            # choose one of the child blocks
    even_presentation=True, # balance between participants
))
for i in range(3):
    block = randomizer.append_block(qq.Block())
    for j in range(4):
        block.append_question(qq.TextGraphicQuestion(f"Block {i}, question {j}"))

survey.create(qq.QualtricsSurveyDefinitionsAPI(API_TOKEN, DATA_CENTER))
```


Questions with JavaScript
-------------------------

Most question types allow a `script_js` parameter, which is a string that
becomes JavaScript code attached to the question. The supported JS functions
are those from the Qualtrics JavaScript Question API,
  [documented here](https://api.qualtrics.com/82bd4d5c331f1-qualtrics-java-script-question-api-class).
The most common usage is to attach code that runs on page load, on page
ready, on page submission[^submit], and on page unloading. Attach a script such as
the following (based on the default code from the web editor).

[^submit]: Note that page submission triggers each time the user presses the
  submit button for the page, even if, for example, the validation fails
  because of some missing answers, and they end up staying on the page... so
  this code might run multiple times!

```python
TextGraphicQuestion(
    text_html="<p>Hello, world!</p>",
    script_js="""// js
        Qualtrics.SurveyEngine.addOnload(function() {
            console.log("loaded!");
        });
        Qualtrics.SurveyEngine.addOnReady(function() {
            console.log("ready!");
        });
        Qualtrics.SurveyEngine.addOnReady(function() {
            console.log("ready again!");
        });
        Qualtrics.SurveyEngine.addOnPageSubmit(function() {
            console.log("submitting!");
        });
        Qualtrics.SurveyEngine.addOnUnload(function() {
            console.log("unloaded!");
        });
    """,
)
```

To make constructing this string a little easier, this library provides a
builder class `QuestionJS` that automatically wraps the added js code in the
necessary method calls. Thus the following example is equivalent to the
above:

```python
TextGraphicQuestion(
    text_html="<p>Hello, world!</p>",
    script_js=QuestionJS() # builder pattern
        .on_load('console.log("loaded!");')
        .on_ready('console.log("ready!");')
        .on_ready('console.log("ready! again!");')
        .on_submit('console.log("submitting!");')
        .on_unload('console.log("unloaded!");')
        .script(), # always call .script() (converts to str) 
)
```

It seems that an arbitrary number of chunks of code can be attached to each
event (which is why I chose to use the builder pattern for this, rather than,
say, a constructor with four optional arguments).

(TODO: There is one more method now "on_click" which binds to anything
clicking the qualtrics question div, see the examples in the JS
documentation).


Under the hood: Direct API access
---------------------------------

Finally, one can make API calls directly, without wrapper classes. This
includes methods for viewing, modifying, and deleting surveys from the
Qualtrics account.

Example: Deleting automatically-generated surveys
-------------------------------------------------

For example, one useful pattern is to start the script by removing the
survey(s) created in previous runs.

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


Extending the library
---------------------

**How can I learn more about the required data format, for surveys or
for questions?**

Create a survey with the required format in the editor. Then use the API to
'get' the survey or question and see what the JSON looks like. Try creating a
new survey or question based on that JSON, possibly using trial and error
to discover which fields are really necessary to include in the posted data.


Notes: API Boundaries
---------------------

Unfortunately, the API documentation is not exactly comprehensive or up to
date. Making things work is mostly trial-and-error. Here I collect some notes
from while I was experimenting with how to achieve certain tasks via the API.

**How can I add JS to questions?**

I don't seem to be able to update or partial-update with QuestionJS field,
but I can totally create new questions with this field, so we're good to go.


**How can I add JS to surveys?**

It doesn't appear possible to configure the survey while creating it.

Aha! To configure a survey uses a separate API call after the survey has
been created (`survey-builder/{survey_id}/options` or something).

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

Things that don't work (API error or no effect):

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

