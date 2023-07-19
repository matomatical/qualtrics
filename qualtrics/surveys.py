"""
Qualtrics Virtual Surveys
=========================

This module contains classes for various kinds of virtual surveys. The
surveys support building a complex virtual survey in Python and then calling
their `.create` method with a REST API (see api module) to upload this survey
to Qualtrics as a real survey.
"""

import json

try: # optional dependency on tqdm
    import tqdm
except ImportError:
    import qualtrics.notqdm as tqdm

from qualtrics.flows import RootFlow, BlockFlow
from qualtrics.questions import PageBreak


class _Survey:
    """
    Abstract base class representing a virtual Qualtrics survey.

    Functionality:

    * Stores survey name and global survey options (such as Header HTML and
      CSS) provided at construction time or through methods.

    * The create method uses a Survey Definition API connection to create a real
      survey and upload these options to it.

    The contents of the survey are stored and uploaded by the inheriting
    subclass.

    Instructions for inheriting:

    * Subclasses should remember to call this class's constructor and
      pass along any options provided at constructor time.

    * Subclasses overriding the 'create' method should probably start with a
      call to this class's create method to avoid having to repeat that code.
    """


    def __init__(self, name="Test Survey", options={}, **kw_options):
        """
        Base class constructor for a virtual survey.

        Parameters:

        * `name` (str):
          The survey name.
          Default: 'Test Survey' (conventional during survey development)

        * `options` (dict):
          A dictionary of survey options.
          The format is based on the survey definitions API. If you are
          unfamiliar with this format, it may be best to use the helper
          methods for configuring particular options---they are individually
          documented.
          Default: empty dictionary.
        
        * `**kw_options`:
          Further options may be provided as keyword arguments.
        
        Notes:

        * If a key appears in both `options` and `kw_options`, the latter's
          value is used.
        """
        self.name = name
        self.options = options | kw_options


    def set_name(self, name):
        """
        Overwrite the name set on the survey at construction time.

        Parameters:

        * `name` (str): The new name.
        """
        self.name = name


    def set_options(self, options={}, **kw_options):
        """
        Update the survey options with new options.

        Parameters:

        * `options` (dict):
          A dictionary of survey options.
          The format is based on the survey definitions API. If you are
          unfamiliar with this format, it may be best to use the helper
          methods for configuring particular options---they are individually
          documented.
          Default: empty dictionary.
        
        * `**kw_options`:
          Further options may be provided as keyword arguments.
        
        Notes:

        * If a key appears in both `options` and `kw_options`, the latter's
          value is used.
        
        * The internal survey options dictionary is modified through an
          in-place union operation (`|=`). This means:
          * If there are options with keys already set on the survey, and
            these keys do not appear in `options` or `kw_options`, then those
            options will not be changed.
          * If there are options with keys already set on the survey, and
            these keys do appear in `options` or `kw_options`, then those
            options' values are changed to the values from `options` and
            `kw_options` (if the key appears in both, `kw_options` is used).
        """
        self.options |= options | kw_options


    def set_header_html(self, header_html=""):
        """
        Set the global header HTML for the survey. This HTML is inserted
        before the survey on every page of the survey.

        Parameters:

        * `header_html` (str):
          Source code (HTML) to be used for the survey header.

        Notes:

        * Each time this method is called the header HTML is overwritten
          (it does not accummulate).
        
        * The HTML code can include JavaScript inside `<script />` elements.
          (Not the case for some other HTML fields, such as Questions.)
        
        * The header HTML is stored in the internal dictionary under the key
          `"Header"`. Therefore this method will interact with any options
          set through other means based on this key.
        """
        self.options['Header'] = header_html


    def set_footer_html(self, footer_html=""):
        """
        Set the global header HTML for the survey. This HTML is inserted
        after the survey on every page of the survey.

        Parameters:

        * `footer_html` (str):
          Source code (HTML) to be used for the survey footer.

        Notes:

        * Each time this method is called the footer HTML is overwritten
          (it does not accummulate).
        
        * The footer HTML is stored in the internal dictionary under the key
          `"Footer"`. Therefore this method will interact with any options
          set through other means based on this key.
        
        * The HTML code can include JavaScript inside `<script />` elements.
          (Not the case for some other HTML fields, such as Questions.)
        """
        self.options['Footer'] = footer_html


    def set_custom_css(self, custom_css=""):
        """
        Set the global custom stylesheet for the survey. This stylesheet is
        linked on every page of the survey.

        Parameters:

        * `custom_css` (str):
          Source code (CSS) to be used for the survey custom stylesheet.

        Notes:
        
        * Each time this method is called the custom CSS is overwritten
          (it does not accummulate).
        
        * The custom CSS is stored, wrapped in a dictionary, in the internal
          options dictionary under the key `"CustomStyles"`.
          Therefore this method will interact with any options set through
          other means based on this key.
        """
        self.options['CustomStyles'] = {'customCSS': custom_css}


    def set_external_css_url(self, external_css_url=""):
        """
        Set a global custom remote stylesheet for the survey. This stylesheet is
        linked on every page of the survey.

        Parameters:

        * `external_css_url` (str):
          URL for a remote stylesheet to be used for the survey.

        Notes:
        
        * Each time this method is called the URL is overwritten. I am not
          aware of a way to add multiple remote stylesheets through this
          field (but I haven't looked---it may be possible).
        
        * The external CSS URL is stored in the internal options dictionary
          under the key `"ExternalCSS"`.
          Therefore this method will interact with any options set through
          other means based on this key.
        """
        self.options['ExternalCSS'] = external_css_url


    def set_show_back_button(self, show_back_button=False):
        """
        Configure whether the back button is shown on each page of the
        survey. Used to control whether to allow participants to back-track
        to earlier pages in the survey, or not.

        Parameters:

        * `show_back_button` (bool):
          True if the back button should be visible, else false.
          The Qualtrics default, active if this option is not explicitly
          configured, is (???).

        Notes:

        * The show back button flag is stored (JSON-encoded) in the internal
          options dictionary under the key `"BackButton"`.
          Therefore this method will interact with any options set through
          other means based on this key.
        """
        self.options["BackButton"] = json.dumps(show_back_button)


    def set_progress_bar_display(self, progress_bar_display="VerboseText"):
        """
        Configure whether and how the progress bar should be displayed on
        each page of the survey.

        Parameters:

        * `progress_bar_display` (str):
          One of a small number of magic strings defined by the Qualtrics
          survey-definitions API:
          * `"VerboseText"`---???
          * (what other options are there?)

        Notes:
        
        * The progress bar display mode is stored in the internal options
          dictionary under the key `"ProgressBarDisplay"`.
          Therefore this method will interact with any options set through
          other means based on this key.
        """
        self.options["ProgressBarDisplay"] = progress_bar_display


    def create(self, api):
        """
        Compose the virtual survey as a real Qualtrics survey by executing a
        series of Qualtrics survey definitions API calls.

        Parameters:

        * `api` (`QualtricsSurveyDefinitionAPI` object):
          An API object that contains the credentials for the Qualtrics
          account you want the survey to show up under.

        Qualtrics API methods used:

        * Calls `api.create_survey` to create a fresh survey in the account.
        * Calls `api.partial_update_survey_options` to upload `self`'s
          internal options dictionary to the newly-created survey. This
          configures the survey with any options that have been passed to
          `self` at construction time (or since via the `set_options` or
          the dedicated configuration methods).
        
        Prints:

        * A couple of diagnostic progress messages.
        * A link to edit the newly-created survey in the Qualtrics web
          editor.
        * A link to preview the newly-created survey in the Qualtrics survey
          previewer.

        Returns:

        * `survey_id` (str): The ID of the newly-created survey, to be used
          with future API calls for accessing, modifying, and deleting this
          survey.
        """
        print("creating survey... ", end="", flush=True)
        survey_id = api.create_survey(survey_name=self.name)['SurveyID']
        print("survey created with id", survey_id)
            
        if len(self.options) > 0:
            print("configuring survey... ", end="", flush=True)
            api.partial_update_survey_options(
                survey_id=survey_id,
                options_data=self.options,
            )
            print("survey configured")

        print("editor: ", api.link_to_edit_survey(survey_id))
        print("preview:", api.link_to_preview_survey(survey_id))

        return survey_id


class BasicSurvey(_Survey):
    """
    Class representing a basic virtual Qualtrics survey, that is, a survey
    comprising a straightforward list of questions (no block structure or
    complex flows, though page breaks are possible).

    Functionality:

    * Stores survey name and global survey options (such as Header HTML and
      CSS) provided at construction time or through methods.

    * Stores a list of questions provided at construction or appended one at
      a time after construction.

    * The create method uses a Survey Definition API connection to create a
      real survey and upload these options and questions to it.
    """


    def __init__(
            self,
            name="Test Survey",
            questions=(),
            options={},
            **kw_options,
        ):
        """
        Constructor for a basic virtual survey.
        
        Parameters:
        
        * `name` (str):
          The survey name.
          Default: 'Test Survey' (conventional during survey development)
        
        * `questions` (iterable of questions):
          A list of questions (e.g. `_Question` or `PageBreak` objects),
          forming the contents of the survey.
          
        * `options` (dict):
          A dictionary of survey options.
          The format is based on the survey definitions API. If you are
          unfamiliar with this format, it may be best to use the helper
          methods for configuring particular options---they are individually
          documented.
          Default: empty dictionary.
        
        * `**kw_options`:
          Further options may be provided as keyword arguments.
        
        Notes:

        * If a key appears in both `options` and `kw_options`, the latter's
          value is used.
        
        * The idea is that the questions will be `_Question` objects or
          `PageBreak` objects, but anything with the appropriate kind of 
          `create` method should work (see documentation for this object's
          `create` method and that of the `_Question` abstract base class).
        """
        super().__init__(name=name, options=options, **kw_options)
        self.questions = list(questions)


    def append_question(self, question):
        """
        Add a new question to the survey's internal list of questions.

        Parameters:

        * `question` (question, e.g. `_Question` or `PageBreak` object).
          The question to add.
        
        Notes:

        * The idea is that the question will be a `_Question` object or
          `PageBreak` object, but anything with the appropriate kind of 
          `create` method should work (see documentation for this object's
          `create` method and that of the `_Question` abstract base class).
        """
        self.questions.append(question)
        return question


    def append_page_break(self):
        """
        Add a new page break to the survey's internal list of questions.

        Notes:

        * This is equivalent to `self.append_question(PageBreak())` but may
          be considered more succinct, and may also satisfy someone who
          finds adding a page break as a question unintuitive.
        """
        self.questions.append(PageBreak())


    def create(self, api):
        """
        Compose the virtual survey as a real Qualtrics survey by executing a
        series of Qualtrics survey definitions API calls.

        Parameters:

        * `api` (QualtricsSurveyDefinitionAPI object):
          An API object that contains the credentials for the Qualtrics
          account you want the survey to show up under.

        Qualtrics API methods used:

        * Calls `api.create_survey` to create a fresh survey in the account.
        * Calls `api.partial_update_survey_options` to upload `self`'s
          internal options dictionary to the newly-created survey. This
          configures the survey with any options that have been passed to
          `self` at construction time (or since via the `set_options` or
          the dedicated configuration methods).
        * For each question in the internal question list, calls the
          question's `create` method, which in turn issues an API call
          (`api.create_question` or `api.create_page_break`).
        
        Prints:

        * A couple of diagnostic progress messages.
        * A link to edit the newly-created survey in the Qualtrics web
          editor.
        * A link to preview the newly-created survey in the Qualtrics survey
          previewer.
        * A dynamic progress bar while the list of questions is sequentially
          uploaded (if optional dependency tqdm is installed).

        Returns:

        * `survey_id` (str): The ID of the newly-created survey, to be used
          with future API calls for accessing, modifying, and deleting this
          survey.
        """
        survey_id = super().create(api)
        
        n_questions = len(self.questions)
        print(f"populating survey: {n_questions} questions")
        progress = tqdm.tqdm(total=n_questions, dynamic_ncols=True)
        for question in self.questions:
            question.create(api, survey_id, block_id=None) # default block
            progress.update()
        progress.close()
        print("survey", survey_id, "populated")

        return survey_id


class BlockSurvey(_Survey):
    """
    Class representing a block-based virtual Qualtrics survey, that is, a
    survey comprising a straightforward list of blocks, with each block
    comprising a straightforward list of questions (no complex flows).

    Functionality:

    * Stores survey name and global survey options (such as Header HTML and
      CSS) provided at construction time or through methods.

    * Stores a list of blocks provided at construction or appended one at
      a time after construction. The blocks are objects of type `Block` which
      themselves store lists of questions.

    * The create method uses a Qualtrics Survey Definition API connection to
      create a real survey and upload these options, blocks, and
      block-questions to it.
    """


    def __init__(
            self,
            name="Test Survey",
            blocks=(),
            options={},
            **kw_options,
        ):
        """
        Constructor for a block-based virtual survey.
        
        Parameters:
        
        * `name` (str):
          The survey name.
          Default: 'Test Survey' (conventional during survey development)
        
        * `blocks` (iterable of blocks):
          A list of blocks (`Block` objects) forming the contents of the
          survey.
          
        * `options` (dict):
          A dictionary of survey options.
          The format is based on the survey definitions API. If you are
          unfamiliar with this format, it may be best to use the helper
          methods for configuring particular options---they are individually
          documented.
          Default: empty dictionary.
        
        * `**kw_options`:
          Further options may be provided as keyword arguments.
        
        Notes:

        * If a key appears in both `options` and `kw_options`, the latter's
          value is used.
        """
        super().__init__(name=name, options=options, **kw_options)
        self.blocks = list(blocks)


    def append_block(self, block):
        """
        Add a new block to the survey's internal list of blocks.

        Parameters:

        * `block` (object of type `Block`):
          The block to add.

        Returns:

        * `block`
          (so as to support the following usage pattern:)

        Example:

        ```python
        block_survey = BlockSurvey()
        block = block_survey.append_block(Block())
        # ...
        block.append(question)
        ```
        """
        self.blocks.append(block)
        return block


    def create(self, api):
        """
        Compose the virtual survey as a real Qualtrics survey by executing a
        series of Qualtrics survey definitions API calls.

        Parameters:

        * `api` (QualtricsSurveyDefinitionAPI object):
          An API object that contains the credentials for the Qualtrics
          account you want the survey to show up under.

        Qualtrics API methods used:

        * Calls `api.create_survey` to create a fresh survey in the account.
        * Calls `api.partial_update_survey_options` to upload `self`'s
          internal options dictionary to the newly-created survey. This
          configures the survey with any options that have been passed to
          `self` at construction time (or since via the `set_options` or
          the dedicated configuration methods).
        * For each block in the internal block list, calls `api.create_block`
          to add a corresponding block to the Qualtrics survey.
        * For each question in the internal question list of each block,
          calls the question's `create` method, which in turn issues an API
          call (`api.create_question` or `api.create_page_break`).
        
        Prints:

        * A couple of diagnostic progress messages.
        * A link to edit the newly-created survey in the Qualtrics web
          editor.
        * A link to preview the newly-created survey in the Qualtrics survey
          previewer.
        * A dynamic progress bar while the blocks and their internal
          questions are sequentially uploaded.

        Returns:

        * `survey_id` (str): The ID of the newly-created survey, to be used
          with future API calls for accessing, modifying, and deleting this
          survey.
        """
        survey_id = super().create(api)
        
        n_blocks = len(self.blocks)
        n_questions = sum(len(b.questions) for b in self.blocks)
        print(f"populating survey: {n_blocks} blocks, {n_questions} questions")
        progress = tqdm.tqdm(total=n_blocks+n_questions, dynamic_ncols=True)
        for block in self.blocks:
            block_id = api.create_block(survey_id=survey_id, block_description=block.description)['BlockID']
            progress.update()
            for question in block.questions:
                question.create(api, survey_id, block_id=block_id)
                progress.update()
        progress.close()
        print("survey", survey_id, "populated")

        return survey_id


class FlowSurvey(_Survey):
    """
    Class representing a flow-based virtual Qualtrics survey, that is, a
    survey comprising a tree of 'flows' governing the sequence of blocks
    encountered by survey participants.

    Functionality:

    * Stores survey name and global survey options (such as Header HTML and
      CSS) provided at construction time or through methods.

    * Stores a tree of flows provided at construction or appended to the root
      flow one at a time after construction.
      The flows are objects of type `_Flow`, some of which contain blocks
      (which in turn contain questions), but there are other kinds of flows
      too.

      For more information see the documentation for `_Flow` subclasses, or
      [the guide](guide.md).

    * The create method uses a Survey Definition API connection to create a real
      survey and upload these options, blocks, block-questions, and flows to
      it.
    """


    def __init__(
            self,
            name="Test Survey",
            elements=(),
            options={},
            **kw_options,
        ):
        """
        Constructor for a flow-based virtual survey.
        
        Parameters:
        
        * `name` (str):
          The survey name.
          Default: 'Test Survey' (conventional during survey development)
        
        * `elements` (iterable of flows):
          A list of flow elements (of type `_Flow`), to be attached to the
          root flow.
          
        * `options` (dict):
          A dictionary of survey options.
          The format is based on the survey definitions API. If you are
          unfamiliar with this format, it may be best to use the helper
          methods for configuring particular options---they are individually
          documented.
          Default: empty dictionary.
        
        * `**kw_options`:
          Further options may be provided as keyword arguments.
        
        Notes:

        * If a key appears in both `options` and `kw_options`, the latter's
          value is used.
        """
        super().__init__(name=name, options=options, **kw_options)
        self.elements = list(elements)

    
    def append_flow(self, flow):
        """
        Add a new flow element to the root flow's list of children.

        Parameters:

        * `flow` (object of type `_Flow`): The flow element to add.

        Returns:

        * `flow`: The flow element added, Supports assigning this flow to a
          variable in the same line it is added to the survey.
        """
        self.elements.append(flow)
        return flow
    

    def append_block(self, block):
        """
        A shortcut method to add a `BlockFlow` wrapping a given `block` (of
        class `Block`) to the root flow's list of children.
        """
        self.append_flow(BlockFlow(block))
        return block


    def create(self, api):
        """
        Compose the virtual survey as a real Qualtrics survey by executing a
        series of Qualtrics survey definitions API calls.

        Parameters:

        * `api` (QualtricsSurveyDefinitionAPI object):
          An API object that contains the credentials for the Qualtrics
          account you want the survey to show up under.

        Qualtrics API methods used:

        * Calls `api.create_survey` to create a fresh survey in the account.
        * Calls `api.partial_update_survey_options` to upload `self`'s
          internal options dictionary to the newly-created survey. This
          configures the survey with any options that have been passed to
          `self` at construction time (or since via the `set_options` or
          the dedicated configuration methods).
        * For each block attached to some block_flow in the flow tree
          structure, calls `api.create_block` to add a corresponding block to
          the Qualtrics survey.
        * For each question in the internal question list of each of those
          blocks, calls the question's `create` method, which in turn issues
          an API call (`api.create_question` or `api.create_page_break`).
        * Once all blocks and questions have been added to the survey, the
          flow tree (with the allocated IDs of each uploaded block) is
          uploaded in a single call to `api.update_flow`.
        
        Prints:

        * A couple of diagnostic progress messages.
        * A link to edit the newly-created survey in the Qualtrics web
          editor.
        * A link to preview the newly-created survey in the Qualtrics survey
          previewer.
        * A dynamic progress bar while the internal blocks and their internal
          questions are sequentially uploaded.

        Returns:

        * `survey_id` (str): The ID of the newly-created survey, to be used
          with future API calls for accessing, modifying, and deleting this
          survey.
        """
        survey_id = super().create(api)

        # create element tree
        root = RootFlow(children=self.elements)
        # gather duplicate blocks
        block_ids = {flow.block: None for flow in root.get_block_flows()}

        n_blocks = len(block_ids)
        n_questions = sum(len(b.questions) for b in block_ids)
        print(f"populating survey: {n_blocks} blocks, {n_questions} questions")
        progress = tqdm.tqdm(total=n_blocks+n_questions, dynamic_ncols=True)
        for block in block_ids:
            block_id = api.create_block(survey_id=survey_id)['BlockID']
            block_ids[block] = block_id
            progress.update()
            for question in block.questions:
                question.create(api, survey_id, block_id=block_id)
                progress.update()
        progress.close()
        print("survey", survey_id, "populated")

        # and finally, compile and push the flow
        print("reflowing survey... ", end="", flush=True)
        api.update_flow(
            survey_id=survey_id,
            flow_data=root.flow_data(block_ids),
        )
        print("survey reflowed")

        return survey_id


class SurveyOptions:
    """
    A legacy wrapper class making it a little easier to provide certain
    global configuration options to the survey.

    > DEPRECATED.
    > 
    > Use methods on the `_Survey` class and its subclasses to configure back
    > button and progress bar (and add methods to the `_Survey` class for new
    > configuration options in the future).
    """
    def __init__(
        self,
        back_button='false',
        progress_bar_display="VerboseText",
    ):
        """
        See documentation of `_Survey.set_back_button` and
        `_Survey.set_progress_bar_display` methods.

        (Note this back button parameters takes a JSON-encoded bool).
        """
        self.data = {
            "BackButton": back_button,
            "ProgressBarDisplay": progress_bar_display
        }


