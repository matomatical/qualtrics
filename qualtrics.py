"""
Qualtrics Survey Builder
========================

**qualtrics.py** is a simple Python library for scripting the creation of
Qualtrics surveys. It provides convenient wrapper methods for accessing the
Qualtrics survey-definitions REST API, along with a convenient object-oriented
interface for building virtual surveys to load through that API.

See README for a more detailed overview.
"""


# # # CONVENTIONS
# In my editor I use simple expression-based code-folding that folds on a
# double line break. That's why conceptual blocks (e.g. imports, section
# titles, class definitions, class methods, functions) are mostly separated
# with double line breaks, and code within blocks has at most single line
# breaks.
# 
# Oh, and I use a thin editor too, so I try to keep lines <80 characters
# wide. Thanks in advance.
#                                                                       ~Matt


# # # IMPORTS

import os
import sys
import json

# mandatory dependencies
import requests
    
# optional dependencies
try:
    import tqdm
except ImportError:
    import notqdm as tqdm


# # # SURVEYS


class _Survey:
    """
    Abstract base class representing a virtual Qualtrics survey.

    Functionality:

    * Stores survey name and global survey options (such as Header HTML and
      CSS) provided at construction time or through methods.

    * The create method uses a Survey Builder API connection to create a real
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

        * `api` (QualtricsSurveyBuilderAPI object):
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

    * The create method uses a Survey Builder API connection to create a real
      survey and upload these options and questions to it.
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

        * `api` (QualtricsSurveyBuilderAPI object):
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
          uploaded.

        Returns:

        * `survey_id` (str): The ID of the newly-created survey, to be used
          with future API calls for accessing, modifying, and deleting this
          survey.
        """
        survey_id = super().create(api)
        
        n_questions = len(self.questions)
        print(f"populating survey: {n_questions} questions")
        progress = tqdm(total=n_questions, dynamic_ncols=True)
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

    * The create method uses a Survey Builder API connection to create a real
      survey and upload these options, blocks, and block-questions to it.
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

        * `api` (QualtricsSurveyBuilderAPI object):
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
        progress = tqdm(total=n_blocks+n_questions, dynamic_ncols=True)
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

    * The create method uses a Survey Builder API connection to create a real
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
        """
        self.elements.append(flow)


    def create(self, api):
        """
        Compose the virtual survey as a real Qualtrics survey by executing a
        series of Qualtrics survey definitions API calls.

        Parameters:

        * `api` (QualtricsSurveyBuilderAPI object):
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
        progress = tqdm(total=n_blocks+n_questions, dynamic_ncols=True)
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


# # # FLOWS


class _FlowElement:
    def __init__(self, children=(), **kwargs):
        self.children = list(children)
        self.kwargs = kwargs


    def append_flow(self, flow):
        self.children.append(flow)
        return flow


    def append_block(self, block):
        self.append_flow(BlockFlow(block))
        return block


    def compile(self, flow_id, block_id_map):
        """
        inputs:

        flow_id: the flow_id for this element
        block_id_map: dictionary from block object to block id string
        
        outputs:

        1. data: a dictionary describing this element's flow including any
           children if present
        2. max_id: the maximum flow_id among this element and its children
        """
        # element data
        data = {
            'FlowID': f"FL_{flow_id}",
            **self.kwargs,
        }
        # children's data
        children_data = []
        for child in self.children:
            child_data, flow_id = child.compile(flow_id + 1, block_id_map)
            children_data.append(child_data)
        # put it together (if there are children)
        if children_data:
            data['Flow'] = children_data
        # return
        return data, flow_id


    def get_block_flows(self):
        for child in self.children:
            yield from child.get_block_flows()


class BlockFlow(_FlowElement):

    def __init__(self, block):
        self.block = block


    def compile(self, flow_id, block_id_map):
        # element data
        return {
            'FlowID': f"FL_{flow_id}",
            'Type': "Block",
            'ID': block_id_map[self.block],
            'Autofill': [],
        }, flow_id
    

    def get_block_flows(self):
        yield self
    

class RootFlow(_FlowElement):

    def __init__(self, children=()):
        super().__init__(
            children=children,
            Type='Root',
        )
    

    def flow_data(self, block_id_map):
        data, max_id = self.compile(flow_id=1, block_id_map=block_id_map)
        data['Properties'] = {
            'Count': max_id,
            'RemovedFieldsets': [],
        }
        return data


class BlockRandomizerFlow(_FlowElement):
    
    def __init__(self, n_samples, even_presentation, children=()):
        super().__init__(
            children=children,
            Type="BlockRandomizer",
            SubSet=n_samples,
            EvenPresentation=even_presentation,
        )


class GroupFlow(_FlowElement):

    def __init__(self, description="Untitled Group", children=()):
        super().__init__(
            children=children,
            Type="Group",
            Description=description,
        )


class EndSurveyFlow(_FlowElement):

    def __init__(self):
        super().__init__(Type="EndSurvey")
    

    def append_flow(self, flow):
        raise Exception("this type of flow has no children")


# # # BLOCKS


class Block:

    def __init__(self, questions=(), description="Standard Question Block"):
        self.questions = list(questions)
        self.description = description


    def append_question(self, question):
        self.questions.append(question)


    def append_page_break(self):
        self.questions.append(PageBreak())
        

# # # QUESTIONS


class PageBreak:
    def create(self, api, survey_id, block_id=None):
        api.create_page_break(survey_id=survey_id, block_id=block_id)


class _Question:

    def __init__(self, data):
        self.data = data


    def create(self, api, survey_id, block_id=None):
        api.create_question(
            survey_id=survey_id,
            question_data=self.data,
            block_id=block_id,
        )


class MultipleChoiceQuestion(_Question):
    def __init__(
        self,
        data_export_tag,
        options=(),
        text_html="",
        script_js="",
        force_response=False,
        selection_method="button-list", # or "dropdown-list"
        recode_values={},
        # TODO: randomisation?
    ):
        # convert string options into option objects
        # options = [
        #     opt if isinstance(opt, _Option) else BasicOption(opt)
        #     for opt in options
        # ]

        get_options = []
        for opt in options:
            if isinstance(opt, _Option):
                get_options.append(opt)
            elif opt == "Self-specified":
                get_options.append(TextOption(opt))
            else:
                get_options.append(BasicOption(opt))

        if selection_method == "button-list":
            selector = {'Selector': "SAVR", 'SubSelector': "TX"}
        elif selection_method == "dropdown-list":
            selector = {'Selector': "DL", 'SubSelector': ""}
        else:
            raise ValueError(f"unknown selection_method {selection_method!r}")
        super().__init__(data={
            'Selector': selector['Selector'],
            'SubSelector': selector['SubSelector'],
            'QuestionType': "MC",
            'ChoiceOrder': list(range(1, len(get_options)+1)),
            'Choices': {i: o.data for i, o in enumerate(get_options, start=1)},
            'DataExportTag': data_export_tag,
            'QuestionText': text_html,
            'QuestionJS': script_js,
            'Validation': {
                'Settings': {
                    'ForceResponse': "ON" if force_response else "OFF",
                    'ForceResponseType': "ON",
                    'Type': "None"
                },
            },
            'RecodeValues': recode_values,
            'Language': [],
        })

class _Option:
    pass

class BasicOption(_Option):
    def __init__(self, label):
        self.data = {
            "Display": label,
        }

class TextOption(_Option):
    def __init__(self, label):
        self.data = {
            "Display": label,
            "TextEntry": "true", # Qualtrics expects this as a string for some reason...
        }


# TODO: MultipleAnswer version of multiple choice question?


class MatrixTableQuestion(_Question):
    def __init__(
        self,
        data_export_tag, # ??
        text_html,
        script_js="",
        options=(),
        answers=(),
    ):
        # SEE: src/drafts/demographics.py (down the bottom) for an example
        super().__init__(data={
            'QuestionType': "Matrix",
            'Selector': "Likert",
            'SubSelector': "SingleAnswer",
            # TODO: Choices and ChoiceOrder
            # TODO: Answers and AnswerOrder
            # TODO: Validation
            # TODO: What is ChoiceDataExportTags? What is DefaultChoices?
        })


class TextEntryQuestion(_Question):
    def __init__(
        self,
        data_export_tag,
        text_html,
        script_js="",
        force_response=False,
        size_of_response="single-line", # or "multi-line", or "essay"
    ):
        if size_of_response == "single-line":
            selector = "SL"
        elif size_of_response == "multi-line":
            selector = "ML"
        elif size_of_response == "essay":
            selector = "ESTB"
        else:
            raise ValueError(f"unknown size_of_response {size_of_response!r}")

        super().__init__(data={
            'QuestionType': "TE",
            'Selector': selector,
            'DataExportTag': data_export_tag,
            'QuestionText': text_html,
            'QuestionJS': script_js,
            'Validation': {
                'Settings': {
                    'ForceResponse': "ON" if force_response else "OFF",
                    'ForceResponseType': "ON",
                    'Type': "None"
                },
            },
            'Language': [],
            # unclear if needed?
            # 'SearchSource': {"AllowFreeResponse": "false"}, # ?
            # 'DefaultChoices': False,
        })
    

class TextGraphicQuestion(_Question):
    def __init__(self, text_html, script_js=""):
        super().__init__(data={
            'QuestionText': text_html,
            'QuestionJS': script_js,
            'QuestionType': 'DB',
            'Selector': 'TB',
            'Language': [], # this silences a translation warning...
        })


class TimingQuestion(_Question):
    def __init__(self, data_export_tag):
        super().__init__(data={
            'QuestionType': 'Timing',
            'Selector': 'PageTimer',
            'DataExportTag': data_export_tag,
            'Choices': {
                '1': {'Display': 'First Click'},
                '2': {'Display': 'Last Click'},
                '3': {'Display': 'Page Submit'},
                '4': {'Display': 'Click Count'}
            },
            'Configuration': {
                'MaxSeconds': '0',
                'MinSeconds': '0',
            },
            'DefaultChoices': False,
            'Language': [],
        })


class CaptchaQuestion(_Question):
    def __init__(self, data_export_tag="reCAPTCHA", text_html=""):
        super().__init__(data={
            'QuestionType': 'Captcha',
            'Selector': 'V2',
            'DataExportTag': data_export_tag,
            'QuestionDescription': text_html,
            'QuestionText': text_html,
            'QuestionText_Unsafe': text_html,
            'GradingData': [],
            'Language': [],
        })


class SliderQuestion(_Question):
    def __init__(self,
        data_export_tag,
        text_html,
        script_js="",
        num_sliders=None,
        choice_labels=None,
        slider_min=0,
        slider_max=100,
        force_response=True,
    ):
        # validate both choice_labels and num_sliders agree
        if choice_labels is None and num_sliders is None:
            raise ValueError("provide either choice_labels or num_sliders")
        elif choice_labels is None:
            choice_labels = ["",] * num_sliders
        elif num_sliders is None:
            num_sliders = len(choice_labels)
        elif len(choice_labels) != num_slides:
            raise ValueError("choice_labels and num_sliders disagree")
        # proceed...
        super().__init__(data={
            'DataExportTag': data_export_tag,
            'ChoiceOrder': list(range(num_sliders)),
            'Choices': {
                i: {'Display': label}
                for i, label in enumerate(choice_labels)
            },
            'Configuration': {
                'CSSliderMin': slider_min,
                'CSSliderMax': slider_max,
                'CustomStart': False,
                'GridLines': 10,
                'MobileFirst': True,
                'NotApplicable': False,
                'NumDecimals': "0",
                'QuestionDescriptionOption': 'UseText',
                'ShowValue': True,
                'SnapToGrid': False,
            },
            'Language': [],
            'QuestionText': text_html,
            'QuestionJS':   script_js,
            'QuestionType': 'Slider',
            'Selector': 'HSLIDER',
            'Validation': {
                'Settings': {
                    'ForceResponse': 'ON' if force_response else 'OFF',
                    'ForceResponseType': 'ON' if force_response else 'OFF',
                    'Type': 'None'
                }
            }
        })


class ConstantSumQuestion(_Question):
    def __init__(self,
        data_export_tag,
        text_html,
        script_js="",
        num_sliders=None,
        choice_labels=None,
        slider_min=0,
        slider_max=100,
        sum_max=100,
        selector='bar',
    ):
        # validate both choice_labels and num_sliders agree
        if choice_labels is None and num_sliders is None:
            raise ValueError("provide either choice_labels or num_sliders")
        elif choice_labels is None:
            choice_labels = ["",] * num_sliders
        elif num_sliders is None:
            num_sliders = len(choice_labels)
        elif len(choice_labels) != num_slides:
            raise ValueError("choice_labels and num_sliders disagree")
        if selector == 'slider':
            selector_string = 'HSLIDER'
        elif selector == 'bar':
            selector_string = 'HBAR'
        # TODO: third type, based on choices, different (involves typing)
        else:
            raise ValueError("selector should be 'slider' or 'bar'")
        # proceed...
        super().__init__(data={
            'DataExportTag': data_export_tag,
            'ChoiceOrder': list(range(num_sliders)),
            'Choices': {
                i: {'Display': label}
                for i, label in enumerate(choice_labels)
            },
            'Configuration': {
                'CSSliderMin': slider_min,
                'CSSliderMax': slider_max,
                'CustomStart': False,
                'GridLines': 10,
                'NumDecimals': '0',
                'QuestionDescriptionOption': 'UseText',
                'ShowValue': True
            },
            'ClarifyingSymbolType': 'None',
            'Language': [],
            'QuestionText': text_html,
            'QuestionJS':   script_js,
            'QuestionType': 'CS',
            'Selector': selector_string,
            'Validation': {
                'Settings': {
                    'ChoiceTotal': '100',
                    'EnforceRange': None,
                    'Type': 'ChoicesTotal',
                },
            }
        })


# # # JAVASCRIPT FOR QUESTIONS


class QuestionJS:
    def __init__(self):
        self.scripts = []

    def script(self):
        return "\n\n".join(self.scripts)
    
    def on_load(self, script):
        # yes, it's really lowercase l in "load", unlike the others...
        self.scripts.append(self._engine_wrap("load", script))
        return self

    def on_click(self, script):
        return self.on_load(f"""this.questionclick = function(event, element) {{
            {script}
        }};""");

    def on_ready(self, script):
        self.scripts.append(self._engine_wrap("Ready", script))
        return self
    
    def on_submit(self, script):
        self.scripts.append(self._engine_wrap("PageSubmit", script, "type"))
        return self
    
    def on_unload(self, script):
        self.scripts.append(self._engine_wrap("Unload", script))
        return self
    
    @staticmethod
    def _engine_wrap(method, script, *args):
        return "Qualtrics.SurveyEngine.addOn{}(function({}){{{}}});".format(
            method,
            ','.join(args),
            f'\n{script}\n',
        )


# # # SURVEY BUILDER API


class QualtricsSurveyDefinitionAPI:
    """
    Qualtrics Survey Definition API wrapper. Provides convenient methods for
    actuating each of the major methods on the Survey Definition API.
    """


    def __init__(
        self,
        api_token,
        data_center,
        user_agent = "qualtrics.py",
        debug = False,
    ):
        self.url = f"https://{data_center}.qualtrics.com"
        self.apiurl = self.url + "/API/v3/"
        self.headers = {
            "x-api-token":  api_token,
            "user-agent":   user_agent,
            "content-type": "application/json",
            "accept":       "application/json",
        }
        self.debug = debug


    # # HTTP methods
    def _request(self, method, endpoint, data={}):
        response = method(
            url     = self.apiurl + endpoint,
            headers = self.headers,
            json    = data,
        )
        response_json = response.json()
        if self.debug:
            print(
                "[qualtrics.api]",
                method.__name__[:3].upper(),
                endpoint,
                response_json,
                file=sys.stderr,
            )
        response.raise_for_status()
        if 'result' in response_json:
            return response_json['result']
        else:
            return None # why not be explicit?

    def _get(self, endpoint):
        return self._request(requests.get, endpoint)
    
    def _post(self, endpoint, data):
        return self._request(requests.post, endpoint, data)

    def _put(self, endpoint, data):
        return self._request(requests.put, endpoint, data)

    def _delete(self, endpoint):
        return self._request(requests.delete, endpoint)


    # # All surveys

    def list_surveys(self):
        return self._get(endpoint="surveys")

    
    # # One survey
    
    def get_survey(self, survey_id):
        return self._get(endpoint=f"survey-definitions/{survey_id}")

    def create_survey(self, survey_name):
        return self._post(
            endpoint="survey-definitions",
            data={
                "SurveyName": survey_name,
                "Language": "EN",
                "ProjectCategory": "CORE",
            },
        )

    def delete_survey(self, survey_id, warn=True):
        # bypass warning
        if not warn:
            return self._delete(endpoint=f"survey-definitions/{survey_id}")

        # else go through the whole rigmarole
        print("⚠️ WARNING!")
        print("Are you sure you want to request the deletion of the survey")
        print("with id", survey_id, "?")
        print("Deleting a survey is irreversible and includes the deletion")
        print("of all data collected as part of the survey.")
        i = input("Type 'delete' to proceed, anything else to abort: ")
        if i.strip() == 'delete':
            print("proceeding...")
            return self._delete(endpoint=f"survey-definitions/{survey_id}")
        else:
            print("aborted.")


    # # Survey Options
    
    def get_survey_options(self, survey_id):
        return self._get(endpoint=f"survey-definitions/{survey_id}/options")

    def update_survey_options(self, survey_id, options_data):
        """
        see for options:

        - https://api.qualtrics.com/5d9e865296ce5-update-options
        """
        return self._put(
            endpoint=f"survey-definitions/{survey_id}/options",
            data=options_data,
        )
    
    def partial_update_survey_options(self, survey_id, options_data):
        old_options_data = self.get_survey_options(survey_id=survey_id)
        new_options_data = old_options_data | options_data
        return self.update_survey_options(
            survey_id=survey_id,
            options_data=new_options_data,
        )

    
    # # Questions

    def list_questions(self, survey_id):
        return self._get(
            endpoint=f"survey-definitions/{survey_id}/questions",
        )

    def get_question(self, survey_id, question_id):
        return self._get(
            endpoint=f"survey-definitions/{survey_id}/questions/{question_id}",
        )

    def create_question(self, survey_id, question_data, block_id=None):
        query = "" if block_id is None else f"?blockId={block_id}"
        return self._post(
            endpoint=f"survey-definitions/{survey_id}/questions" + query,
            data=question_data,
        )

    def update_question(self, survey_id, question_id, question_data):
        return self._put(
            endpoint=f"survey-definitions/{survey_id}/questions/{question_id}",
            data=question_data,
        )

    # NOTE: doesn't appear to be working for new(?) fields...
    def partial_update_question(self, survey_id, question_id, question_data):
        old_question_data = self.get_question(
            survey_id=survey_id,
            question_id=question_id,
        )
        new_question_data = old_question_data | question_data
        return self.update_question(
            survey_id=survey_id,
            question_id=question_id,
            question_data=new_question_data,
        )

    def delete_question(self, survey_id, question_id):
        return self._delete(
            endpoint=f"survey-definitions/{survey_id}/questions/{question_id}",
        )


    # # Blocks
    
    def list_blocks(self, survey_id):
        survey = self.get_survey(survey_id=survey_id)
        return list(survey['Blocks'].values()) # originally dict {id: block}

    def get_block(self, survey_id, block_id):
        return self._get(
            endpoint=f"survey-definitions/{survey_id}/blocks/{block_id}",
        )

    def create_block(self, survey_id, block_description=""):
        return self._post(
            endpoint=f"survey-definitions/{survey_id}/blocks",
            data={
                'Description': block_description,
                'Type': 'Standard',
            },
        )

    def update_block(self, survey_id, block_id, block_data):
        return self._put(
            endpoint=f"survey-definitions/{survey_id}/blocks/{block_id}",
            data=block_data,
        )

    def create_page_break(self, survey_id, block_id):
        block_data = self.get_block(
            survey_id=survey_id,
            block_id=block_id,
        )
        block_data['BlockElements'].append(
            {'Type': 'Page Break'}
        )
        return self.update_block(
            survey_id=survey_id,
            block_id=block_id,
            block_data=block_data,
        )

    def delete_block(self, survey_id, block_id):
        return self._delete(
            endpoint=f"survey-definitions/{survey_id}/blocks/{block_id}",
        )


    # # Flows

    def get_flow(self, survey_id):
        return self._get(endpoint=f"survey-definitions/{survey_id}/flow")

    def update_flow(self, survey_id, flow_data):
        return self._put(
            endpoint=f"survey-definitions/{survey_id}/flow",
            data=flow_data,
        )

    def update_flow_element(self, survey_id, flow_id, flow_element_data):
        return self._put(
            endpoint=f"survey-definitions/{surveu_id}/flow/{flow_id}",
            data=flow_element_data,
        )


    # # Other

    def link_to_edit_survey(self, survey_id):
        return f"{self.url}/survey-builder/{survey_id}/edit"

    def link_to_preview_survey(self, survey_id):
        return f"{self.url}/jfe/preview/{survey_id}"


class SurveyOptions:
    def __init__(
        self,
        back_button = 'false',
        progress_bar_display = "VerboseText",
    ):
        self.data = {
            "BackButton": back_button,
            "ProgressBarDisplay": progress_bar_display
        }


# # # RECIPES


def delete_all_surveys_by_name(
    api,
    survey_name,
    print_surveys=False,
    save_surveys=False,
):
    surveys = api.list_surveys()['elements']
    print("found", len(surveys), "surveys total")
    
    surveys = [s for s in surveys if survey_name == s['name']]
    print("found", len(surveys), "surveys with name", repr(survey_name))
    if len(surveys) == 0:
        return
    
    if input("⚠️ Really delete surveys, including any responses!? (y/n):") != 'y':
        print("aborting survey deletion.")
        return
    
    print("deleting these surveys...")
    for survey in tqdm(surveys):
        survey_id = survey["id"]
        if print_surveys or save_surveys:
            survey = api.get_survey(survey_id)
            if print_surveys:
                tqdm.write(json.dumps(survey, indent=2))
            if save_surveys:
                path = os.path.join(save_surveys, f"{survey_id}.json")
                tqdm.write(f"saving survey {survey_id} to {path}")
                with open(path, 'w') as fp:
                    json.dump(survey, fp, indent=2)
        api.delete_survey(survey_id, warn=False) # already warned above


def style_survey(
    api,
    survey_id,
    header_html="",
    footer_html="",
    custom_css="",
    script_js=None
):
    if script_js is not None:
        header_html += "\n\n<script>\n" + header_js + "\n</script>\n"
        # alternatively, consider putting js html in "Footer"...
    api.partial_update_survey_options(
        survey_id=survey_id,
        options_data={
            # put the html and the js in here (js in <script> tags)
            'Header': header_html,
            'Footer': footer_html,
            # despite what the docs say, this takes actually css string
            # *wrapped in a dictionary*
            'CustomStyles': {"customCSS": custom_css},
        }
    )

