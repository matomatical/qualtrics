Usage Guide
===========

This guide introduces the qualtrics library and its usage.

The examples in this guide assumes you have followed the instructions in the
[README](README.md#installation) pertaining to installing the library and
getting your API "token" and data center ID. `API_TOKEN` and `DATA_CENTER`
contain the results of the latter steps as strings.

Contents
--------

Introduction:

* A brief background on Qualtrics survey structure and survey
  definitions API
* A conceptual introduction to the library's methods for programmatically
  building and uploading surveys

Examples:

* Examples of the three main survey types:
  1. Basic surveys---a simple sequence of questions;
  2. Block surveys---a sequence of blocks, each block is a sequence of
     questions; and
  3. Flow surveys---more complex survey flows (e.g. randomisation of block
     sequencing or choice for different participants, or branching based on
     participant responses).
* Examples of adding JavaScript to surveys
* Examples of scripting API calls directly

Developer notes:

* Miscellaneous notes on exploring the Qualtrics survey definitions API

Introduction
============

Background: Qualtrics and the Survey Builder API
------------------------------------------------

The Qualtrics web editor supports building surveys by providing the following
features:

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

The **Qualtrics survey definitions API** allows programmatically creating
surveys and adding questions, blocks, and flows to existing surveys.

Overview: Automated survey construction
---------------------------------------

(Note: This is an abstract overview. See the recipes section below for some
concrete examples.)

Now, we understand a bit about qualtrics, and the survey definitions API.
This library is designed to help use the survey definitions API
programmatically. How does that work?

At a high level, a script to upload a survey should work as follows:

0. Import the library (I like `import qualtrics as qq` for short).
1. Build an in-memory object of class `_Survey`: an abstract base class that
   represents a survey as a collection of questions (grouped into blocks
   (orchestrated using flows)).
   1. The construction of this survey starts with instantiating a blank
      survey object.
   2. Then, methods are called on that object to add question objects (or
      block objects (or flow objects)) which have been constructed
      separately.
      * The contents of the questions can come from anywhere. They can be
        hard-coded into the script, or they can be pulled in from other
        development pipelines (such as generated HTML/JS from other tools).
        The library is agnostic on this front.
   3. At some point, the survey object can also have one-time methods called
      to set global survey configuration (such as custom CSS/HTML/JS for the
      whole survey.
2. Call the survey's `.create` method to trigger a sequence of API calls that
   will mirror the survey object's configuration and structure as a new
   Qualtrcis survey in your account.
   1. The `.create` method takes an `QualtricsSurveyDefinitionAPI` object as
      a parameter, which in turn takes your API "token" and data center ID as
      parameters. This is how the script is able to create the survey within
      your Qualtrics account.
   2. The sequence of API calls is roughly as follows:
      * make one API call to create a new blank survey in the account;
      * make one API call to configure the new survey with the global options
        set by the one-time methods (custom CSS/HTML/JS for the whole survey,
        etc.);
      * walk the survey object's internal list(s) of questions (and blocks)
        making one API call for each question (and each block) and adding
        them to the newly created survey;
      * (if there are flows, add an API call to upload these too.)

      For a large survey, this can take some time. The `.create` method
      displays a progress bar so you know how long it will take.
3. At this point, the survey has been created! Usually the next step in your
   workflow will be to preview the survey to see if it looks the way you
   want. The `.create` method attempts to print out a link that will take you
   straight to the survey preview on Qualtrics (as well as one that takes you
   to the editor). But, in general, you can now find your generated survey in
   your account.

The class `_Survey` is an abstract base class. It has three main
instantiations, designed to be used for building surveys at varying scales of
complexity (the simpler ones hide away some of the complex configurations
from the more complex ones).

1. `BasicSurvey`: Questions can be appended using the `append_question`
    method. The questions are added to the default block, resulting in a
    survey that is a single, simple list of questions.
    Use if there is no need for multiple blocks.

2. `BlockSurvey`: Blocks must be separately created using the `Block` class.
    Questions can be appended to the block object using the `append_question`
    method. The block can be appended to the survey using the `append_block`
    method.
    The survey renders as a straightforward sequence of blocks (each block is
    a straightforward sequence of questions).
    Use if there is a need for multiple blocks but no need for complex survey
    flows.

    > Note: It is still possible to make a basic survey with multiple pages,
    > using page breaks. Come to think of it, I don't know a good reason why
    > one would use a block survey instead of a basic survey with page
    > breaks. But you might find one!

3. `FlowSurvey`: Blocks and questions cannot be directly added to the
    survey---instead, a FlowSurvey is a sequence of `_FlowElement` objects. To
    get a feel for what is possible with flow elements, I recommend playing
    around in the flows tab of the Qualtrics web editor. I'll attempt to
    explain anyway. Flow elements form a tree structure, with nodes of vaious
    kinds. The sequence of blocks the participant experiences is based on a
    tree traversal with the exact details depending on the semantics of each
    node type. A few node types are implemented in this library, including
    the following:
    * `GroupFlow`: A non-leaf element---can have multiple elements as
      children, and they are traversed in sequence.
    * `BlockRandomizerFlow`: A non-leaf element. Configurable such that the
      traversal will enter a random one or more of its children, in a random
      order, depending on the participant. Can be used for selecting
      conditions in a randomised experiment or for shuffling a sequence of
      blocks (or block groups, etc.).
    * `BlockFlow`: A leaf element. Each `BlockFlow` element has a `Block`
      attached to it. When the traversal hits such a flow element, the
      participant completes the attached block.
    * `EndSurveyFlow`: Another leaf element. Traversing here ends the survey.

Some examples of each of the survey types are given in the next section.

Examples / Recipes
==================

*Bon appétit!*

Survey type 1: Basic Survey
---------------------------

As described above, the `BasicSurvey` class is appropriate for surveys with a
single block of questions.

> Example: Create a survey with a single text question with text "Hello, world!".
> 
> ```python
> import qualtrics as qq
> 
> # build the survey data structure
> survey = qq.BasicSurvey(name="Test Survey")
> survey.append_question(qq.TextGraphicQuestion(text_html="Hello, world!"))
> 
> # use the API to create the survey within your Qualtrics account
> api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)
> survey.create(api)
> ```

Survey type 2: Block Survey
---------------------------

As described above, the `BlockSurvey` class is appropriate for surveys with
multiple blocks, presented one after another:

> Example: Create a survey with three blocks of four questions each, separated
> by page breaks.
> 
> ```python
> import qualtrics as qq
> 
> # build the survey data structure
> survey = qq.BlockSurvey(name="Test Survey")
> for i in range(3):
>     block = qq.Block()
>     for j in range(4):
>         block.append_question(qq.TextGraphicQuestion(
>             text_html=f"Block {i}, question {j}",
>         ))
>         block.append_page_break()
>     survey.append_block(block)
> 
> # upload the survey to Qualtrics
> api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)
> survey.create(api)
> ```
> 
> Alternatively, provide the questions and blocks to the survey directly via
> the survey constructor:
> 
> ```python
> import qualtrics as qq
> 
> qq.BlockSurvey(
>     name="Test Survey",
>     blocks=[
>         qq.Block(questions=[
>             q
>             for j in range(4)
>             for q in (
>                 qq.TextGraphicQuestion(text_html=f"Block {i}, question{j}"),
>                 qq.PageBreak()
>             ) 
>         ])
>         for i in range(3)
>     ]
> ).create(qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER))
> ```

Survey type 3: Flow Survey
--------------------------

As described above, for any survey with a non-standard flow, use the
`FlowSurvey` class. Arbitrary Qualtrics flows are possible.

> Example: Create a survey that randomly presents one of three blocks.
> 
> ```python
> import qualtrics as qq
> 
> survey = qq.FlowSurvey(name="Test Survey")
> randomizer = survey.append_flow(qq.BlockRandomizerFlow(
>     n_samples=1,            # choose one of the child blocks
>     even_presentation=True, # balance between participants
> ))
> for i in range(3):
>     block = randomizer.append_block(qq.Block())
>     for j in range(4):
>         block.append_question(qq.TextGraphicQuestion(f"Block {i}, question {j}"))
> 
> survey.create(qq.QualtricsSurveyDefinitionsAPI(API_TOKEN, DATA_CENTER))
> ```

Questions with JavaScript
-------------------------

Most question types allow a `script_js` parameter, which is a string that
becomes JavaScript code attached to the question.

The supported JS functions are those from the Qualtrics JavaScript Question
API,
  [documented here](https://api.qualtrics.com/82bd4d5c331f1-qualtrics-java-script-question-api-class).

The most common usage is to attach code that runs at one of various
opportunities:

* On page 'load': some time early in the loading of the page.

* On page 'ready': some time later in the loading of the page (after all
  questions are finished loading, perhaps? unsure).

* On page submission: Every time the user presses the 'next page' button
  (maybe also 'prev page' button if enabled? untested).

  Note that page submission triggers each time the user presses the
  submit button for the page, even if, for example, the validation fails
  because of some missing answers, and they end up staying on the page... so
  this code might run multiple times!

* On page unloading: some time after submission during the transition to the
  next page (untested).

* I added a fifth method, "on click", which uses a different mechanism to the
  above four to bind code to the event of anyone clicking the question div
  element (see the relevant examples in the Quqltrics JS documentation).

The basic Qualtrics way to attach to these events is to attach a script to
the questions as follows (this is based on the default code from the web
editor):

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
// NOTE: on_click is achieved differently, see Qualtrics JS documentation...
```

To make constructing this kind of string a little more ergonomic, this
library provides a builder class `QuestionJS` that automatically wraps the
added js code in the necessary method calls (including achieving the click
event binding.

Thus the following example is equivalent to the above:

> Example: Simple response to each of the four main events
> 
> ```python
> TextGraphicQuestion(
>     text_html="<p>Hello, world!</p>",
>     script_js=QuestionJS() # builder pattern
>         .on_load('console.log("loaded!");')
>         .on_ready('console.log("ready!");')
>         .on_ready('console.log("ready! again!");')
>         .on_submit('console.log("submitting!");')
>         .on_unload('console.log("unloaded!");')
>         .script(), # always call .script() (converts to str) 
> )
> ```

It seems that an arbitrary number of chunks of code can be attached to each
event (which is why I chose to use the builder pattern for this, rather than,
say, a constructor with four optional arguments).


TODO: Example with `QuestionJS().on_click()`?


Making API calls with the library
---------------------------------

So far, we have discussed using survey classes which abstract away the actual
API calls that build the survey inside Qualtrics. However, the library
provides access to these API calls via the `QualtricsSurveyDefinitionsAPI`
class.

There are various API routes wrapped by the library as methods of this class.
This includes methods for viewing, modifying, and deleting surveys from the
Qualtrics account.
These methods provide sensible default parameters that should work, saving
you having to look at the Qualtrics documentation or example JSON.

However, note the following:

* No attempt is made to process the response objects. If you 'get' a
  question or a survey, you get JSON data back, not a `Question` or `Survey`
  object.

* The API routes for adding questions have a free form question data
  parameter, which I have not fully documented. This parameter is for you to
  describe the question type and the question configuration. Sensible
  defaults are provided as the subclasses of the class `\_Question` class
  for certain question types. For the others, you are on your own (but see
  notes for developers below).

The following is an example showcasing using API calls directly to clean up a
qualtrics account with many automatically-generated surveys.

> Example: Deleting automatically-generated surveys
> 
> ```python
> import qualtrics as qq
> import tqdm                 # `pip install tqdm`
> 
> api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)
> 
> # find all surveys
> surveys = api.list_surveys()['elements']
> print("found", len(surveys), "surveys total")
> 
> # filter for matching surveys
> surveys = [s for s in surveys if s['name'] == "Test Survey"]
> print("found", len(surveys), "surveys with name 'Test Survey'")
> 
> # delete these surveys
> for survey in tqdm.tqdm(surveys):
>     api.delete_survey(survey['id'])
> ```
> 
> > BEWARE: This code results in loss of any participant data associated with
> > the surveys)

This pattern is actually already provided as a library function:
`qq.delete_all_surveys_by_name(api, survey_name)`.

A useful development pattern is to call this function periodically as part of
a `make clean` or similar.

Development Notes
=================

Exploring Qualtrics API
-----------------------

The Qualtrics API documentation has a partially-reliable overview of the
survey-builder API, and information about each of the available methods. See
the following links:

* https://api.qualtrics.com/ZG9jOjg3NzY2Nw-building-surveys
    (overview)
* https://api.qualtrics.com/ZG9jOjg3NzY4Mg-survey-api-introduction
    (overlapping information with first link)
* https://api.qualtrics.com/60d24f6897737-qualtrics-survey-api
    (full reference)
* https://api.qualtrics.com/ZG9jOjg3NzY4Mw-example-use-cases-walkthrough
    (tutorial/walkthrough)

Unfortunately, not all of the methods appear to be documented fully nor
accurately, so some trial and error is necessary to figure out which fields
are needed and how to achieve certain modifications.

One way to figure out the required format for a specific modification is as
follows:

1. Create a survey with a question in the required format in the editor.
2. Use the API to 'get' the survey or question and see what the JSON looks
   like.
3. Use this JSON as a basis for the API request to create that same
   configuration programmatically (some trial-and-error required to discover
   which fields are really necessary to include in the posted data).

This is the man method I use to add support for new features to the library,
and you should be able to use it too to add your desired missing feature.

Here I collect some notes from while I was experimenting with how to achieve
certain tasks via the API.

* **How can I add JS to questions?**
  
  I don't seem to be able to update or partial-update with QuestionJS field,
  but I can totally create new questions with this field, so we're good to go.
  
* **How can I add JS to surveys?**
  
  It doesn't appear possible to configure the survey while creating it.
  
  Aha! To configure a survey uses a separate API call after the survey has
  been created (`survey-builder/{survey_id}/options` or something).
  
  That path appears to let you customise the CSS and a HTML Header and Footer
  for the survey page. These HTML scripts can contain arbitrary JS via script
  tags, so that's how we can get global JS.
  
* **How can I organise questions using blocks?**
  
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
