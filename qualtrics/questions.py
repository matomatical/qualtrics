"""
Qualtrics Virtual Questions
===========================

This module contains classes for various kinds of questions. The idea of the
library is that you will construct questions with the definitions in this
module and then add them to a virtual survey (see the surveys module) before
using the methods of those virtual survey objects to upload your survey to
Qualtrics as a real survey using API calls.

All question wrappers here inherit from the base class `_Question`.
The question types so far implemented are as follows.

* `TextGraphicQuestion`: Just display some HTML, possibly including graphics.

* `TextEntryQuestion`: A text entry box (multiple sizes available).

* `MultipleChoiceQuestion`: A multiple choice question. Also includes
  dropdown-list-based selection of a single element.

* `(TODO): MultipleAnswer version of multiple choice question?

* `MatrixTableQuestion`: A collection of multiple choice questions stacked in
  a table (so there is a matrix of radio buttons).

* `SliderQuestion`: A question where the participant enters one or more
  values using sliders.

* `ConstantSumQuestion`: Like a slider question but the values have to add up
  to a specific amount.

* `TimingQuestion`: A special question that is invisible to the participants
  but collects information about how long they spend on the survey page and
  logs it to the response data file.

* `CaptchaQuestion`: A Google ReCAPTCHA embedded into a question, the
  participant has to pass it to proceed to the next page.

  Disclaimer: I do not endorse using Google in general or ReCAPTCHA in
  particular. It's like, they should at least *pay* people to mine their
  cognitive labour while they proceed to automate the human species into
  obsolecense. Sorry for getting political. It just grinds my gears.

* `PageBreak`: Treated as a question for the purposes of the virtual survey
  API, this represents a break between survey pages within a single question
  block.

Note that even if a question type is listed here it doesn't mean all the
configuration options from the Qualtrics web editor are available in this
wrapper.
"""

import json


class _Question:
    """
    Abstract base class for question objects.

    All questions eventually need to be uploaded through the API using the
    `create_question` method. This method takes a dictionary of 'question
    data' that determines the type and contents of the question to be
    uploaded. The role of this base class is to store that data and provide
    the `create` method that makes the API call. Inheriting classes provide a
    nicer wrapper for creating such question data dictionaries through
    keywords or with sensible defaults, etc.
    """

    def __init__(self, data):
        self.data = data

    def create(self, api, survey_id, block_id=None):
        api.create_question(
            survey_id=survey_id,
            question_data=self.data,
            block_id=block_id,
        )


class TextGraphicQuestion(_Question):
    """
    `TextGraphicQuestion`: just display some HTML, possibly including
    graphics.

    `TextEntryQuestion`: a text entry box (multiple sizes available).

    `MultipleChoiceQuestion`: a multiple choice question.

    `MatrixTableQuestion`: a collection of multiple choice questions stacked
    in a table (so there is a matrix of radio buttons).

    `SliderQuestion`: a question where the participant enters one or more
    values using sliders.

    `ConstantSumQuestion`: like a slider question but the values have to add
    up to a specific amount.

    `TimingQuestion`: A special question that is invisible to the
    participants but collects information about how long they spend on the
    survey page and logs it to the response data file.

    `CaptchaQuestion`: A Google ReCAPTCHA embedded into a question, the
    participant has to pass it to proceed to the next page.

    Disclaimer: I do not endorse using Google in general or ReCAPTCHA in
    particular. It's like, they should at least *pay* people to mine their
    cognitive labour while they proceed to automate the human species into
    obsolecense. Sorry for getting political. It just grinds my gears.

    `PageBreak`: Treated as a question for the purposes of the virtual survey
    API, this represents a break between survey pages within a single
    question block.
    """
    def __init__(self, text_html, script_js=""):
        super().__init__(data={
            'QuestionText': text_html,
            'QuestionJS': script_js,
            'QuestionType': 'DB',
            'Selector': 'TB',
            'Language': [], # this silences a translation warning...
        })


class TextEntryQuestion(_Question):
    """
    A text entry box. Multiple sizes are available (one line, multiple lines,
    large 'essay' box).
    """
    def __init__(
        self,
        data_export_tag,
        text_html,
        script_js="",
        force_response=False,
        size_of_response="single-line", # or "multi-line", or "essay"
    ):
        """
        A text entry box. Multiple sizes are available (one line, multiple
        lines, large 'essay' box).

        Parameters:

        * `data_export_tag` (str): A unique code to identify the responses to
          this question in the data export. Should be unique compared to all
          other questions in the survey.

        * `text_html` (str): Source code (HTML) to insert before the
          input.

          No `<script/>` elements are allowed (use the `script_js` parameter
          for JavaScript).

        * `script_js` (str, default empty): Source code (JavaScript) to
          attach to the question. See the `question_js` module for advice on
          how to use this field.

        * `force_response` (bool, default `False`): If true, the participant
          can't move to the next page of the survey until they give some
          input in this text field (a small red asterisk is shown to indicate
          a mandatory question). If false, the participant can skip the
          question.

        * `size_of_response` (str, default `"single-line"`): One of a small
          number of available string options:
          * `"single-line"`: For a small input field that fits a single line
             of text.
          * `"multi-line"`: For a medium-sized input field that fits a few
            lines of text.
          * `"essay"`: For a large input field that fits many lines of text
            (designed for longer responses).
        """
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
    

class MultipleChoiceQuestion(_Question):
    """
    A multiple choice question. Also includes dropdown-list-based selection
    of a single element. Everyone knows what these things are generally,
    but in Qualtrics, there are various configuration options to document...
    """
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
        """
        A multiple choice question. Everyone knows what these are generally.
        But in Qualtrics, there are various configuration options. Let me
        tell you about those.

        Parameters:

        * `data_export_tag` (str): A unique code to identify the responses to
          this question in the data export. Should be unique compared to all
          other questions in the survey.

        * `options` (iterable of str or `_Option` subclasses): A list of
          options.
          * Strings will be converted into option labels.
          * It is also possible to create options that allow text entry by
            passing in a `TextOption` object in this interable.
          * Also, the string `"Self-specified"` is magic and if included will
            be converted into a text entry option (why is that?)

        * `text_html` (str): Source code (HTML) to insert before the
          input.

          No `<script/>` elements are allowed (use the `script_js` parameter
          for JavaScript).

        * `script_js` (str, default empty): Source code (JavaScript) to
          attach to the question. See the `question_js` module for advice on
          how to use this field.

        * `force_response` (bool, default `False`): If true, the participant
          can't move to the next page of the survey until they give some
          selection (a small red asterisk is shown to indicate a mandatory
          question). If false, the participant can skip the question.

        * `selection_method` (str, default `"button-list"`): One of a small
          number of available string options:
          * `"button-list"`: For traditional multiple choice question, with a
            list of buttons presented to the participant, and they can choose
            one of them at a time by clicking on the button. Best for small
            numbers of options.
          * `"dropdown-list"`: For dropdown-list-based questions. The
            participant can open a list, and scroll through to find their
            preferred choice. Best for long lists of options.

        * `recode_values` (dict): I forgot what this one does, sorry.
          Something about how the answers are stored in the data export
          maybe?
        """
        wrapped_options = []
        for opt in options:
            if isinstance(opt, _Option):
                wrapped_options.append(opt)
            elif opt == "Self-specified":
                wrapped_options.append(TextOption(opt))
            else:
                wrapped_options.append(BasicOption(opt))

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
            'ChoiceOrder': list(range(1, len(wrapped_options)+1)),
            'Choices': {i: o.data for i, o in enumerate(wrapped_options, start=1)},
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
    """Abstract base class for detecting subclasses."""
    pass

class BasicOption(_Option):
    """
    Multiple choice question option with just a label.
    """
    def __init__(self, label):
        self.data = {
            "Display": label,
        }

class TextOption(_Option):
    """
    Multiple choice question option with a label accompanied by a text entry
    field.
    """
    def __init__(self, label):
        self.data = {
            "Display": label,
            # Qualtrics wants this to be encoded as a string for some reason:
            "TextEntry": json.dumps(True),
        }


class MatrixTableQuestion(_Question):
    """
    A collection of multiple choice questions stacked in a table (so there is
    a matrix of radio buttons).
    """
    def __init__(
        self,
        data_export_tag, # ??
        text_html,
        script_js="",
        options=(),
        answers=(),
    ):
        """
        A collection of multiple choice questions stacked in a table (so
        there is a matrix of radio buttons).

        Parameters:

        * `data_export_tag` (str): A unique code to identify the responses to
          this question in the data export. Should be unique compared to all
          other questions in the survey.

        * `text_html` (str): Source code (HTML) to insert before the input.

          No `<script/>` elements are allowed (use the `script_js` parameter
          for JavaScript).

        * `script_js` (str, default empty): Source code (JavaScript) to
          attach to the question. See the `question_js` module for advice on
          how to use this field.

        * `options` (iterable of str): TODO: Document.

        * `answers` (iterable of str): TODO: Document.

        """
        super().__init__(data={
            'QuestionType': "Matrix",
            'Selector': "Likert",
            'SubSelector': "SingleAnswer",
            # TODO: Choices and ChoiceOrder
            # TODO: Answers and AnswerOrder
            # TODO: Validation
            # TODO: What is ChoiceDataExportTags? What is DefaultChoices?
        })


class SliderQuestion(_Question):
    """
    A question where the participant enters one or more values using sliders.
    """
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
        """
        A question where the participant enters one or more values using sliders.

        Parameters:
        
        * `data_export_tag` (str): A unique code to identify the responses to
          this question in the data export. Should be unique compared to all
          other questions in the survey.

        * `text_html` (str): Source code (HTML) to insert before the input.

          No `<script/>` elements are allowed (use the `script_js` parameter
          for JavaScript).

        * `script_js` (str, default empty): Source code (JavaScript) to
          attach to the question. See the `question_js` module for advice on
          how to use this field.

        * `num_sliders` (int, optional if `choice_labels` is provided):
          The number of sliders to present the user with (default, length of
          `choice_labels`).

        * `choice_labels` (list of str, optional if `num_sliders` is
          provided): Labels for the sliders (default, a list of blank labels,
          if `num_sliders` is provided but `choice_labels` is not).

        * `slider_min` (float, default 0): Lower bound on the slider(s)'s
          input range.
        
        * `slider_max` (float, default 100): Upper bound on the slider(s)'s
          input range.

        * `force_response` (bool, default `True`): If true, the participant
          can't move to the next page of the survey until they give some
          selection (a small red asterisk is shown to indicate a mandatory
          question). If false, the participant can skip the question.

        Notes:

        * If provided and `choice_labels` is also provided, then `num_sliders`
          should be the length of `choice_labels`. If either is provided but
          the other is not, then the missing parameter will be inferred from
          the provided parameter.
        * Unlike the other questions, default forced response is true here,
          for legacy reasons. Sorry!
        """
        # validate both choice_labels and num_sliders agree
        if choice_labels is None and num_sliders is None:
            raise ValueError("provide either choice_labels or num_sliders")
            # TODO: it would be reasonable to infer a single blank slider here
        elif choice_labels is None:
            choice_labels = ["",] * num_sliders
        elif num_sliders is None:
            num_sliders = len(choice_labels)
        elif len(choice_labels) != num_sliders:
            raise ValueError("choice_labels and num_sliders disagree")
        
        # set gridlines
        slider_diff = slider_max - slider_min
        if slider_diff > 20:
            slider_diff = 9

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
                'GridLines': slider_diff,
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
    """
    Like a slider question but the values have to add up to a specific
    amount.
    """
    def __init__(self,
        data_export_tag,
        text_html,
        script_js="",
        num_sliders=None,
        choice_labels=None,
        slider_min=0,
        slider_max=100,
        sum_max=100,
        selector="bar",
    ):
        """
        A question where the participant enters one or more values using
        sliders, and the values have to add up to a specific amount.

        Parameters:
        
        * `data_export_tag` (str): A unique code to identify the responses to
          this question in the data export. Should be unique compared to all
          other questions in the survey.

        * `text_html` (str): Source code (HTML) to insert before the input.

          No `<script/>` elements are allowed (use the `script_js` parameter
          for JavaScript).

        * `script_js` (str, default empty): Source code (JavaScript) to
          attach to the question. See the `question_js` module for advice on
          how to use this field.

        * `num_sliders` (int, optional if `choice_labels` is provided):
          The number of sliders to present the user with (default, length of
          `choice_labels`).

          The final value should be at least 2 so that this type of question
          is meaningful.

        * `choice_labels` (list of str, optional if `num_sliders` is
          provided): Labels for the sliders (default, a list of blank labels,
          if `num_sliders` is provided but `choice_labels` is not).

        * `slider_min` (float, default 0): Lower bound on the slider(s)'s
          input range.
        
        * `slider_max` (float, default 100): Upper bound on the slider(s)'s
          input range.

        * `sum_max` (float, default 100): The total that needs to be achieved
          as the sum of the values entered across the sliders.

        * `selector` (str, default `"bar"`): One of a small number of
          possible strings for configuring the slider input interface.
          * `"bar"` (default): Slide some bars.
          * `"slider"`: Slide some balls instead.
          * (TODO: there is a third option in Qualtrics, unexplored.)

          I don't know if there is a functional difference to be honest.
        
        Notes:

        * If provided and `choice_labels` is also provided, then `num_sliders`
          should be the length of `choice_labels`. If either is provided but
          the other is not, then the missing parameter will be inferred from
          the provided parameter.
        * Unlike the other questions, there is no "force response". I think
          this is not a mistake and it's because the question has its own
          validation rules (you have to input numbers that add up to the
          provided target).
        """
        # validate both choice_labels and num_sliders agree
        if choice_labels is None and num_sliders is None:
            raise ValueError("provide either choice_labels or num_sliders")
        elif choice_labels is None:
            choice_labels = ["",] * num_sliders
        elif num_sliders is None:
            num_sliders = len(choice_labels)
        elif len(choice_labels) != num_sliders:
            raise ValueError("choice_labels and num_sliders disagree")
        if num_sliders <= 1:
            raise ValueError("constant sum must have at least 2 sliders!")
        # validate selector string input
        if selector == 'slider':
            selector_string = 'HSLIDER'
        elif selector == 'bar':
            selector_string = 'HBAR'
          
        # set gridlines
        slider_diff = slider_max - slider_min
        if slider_diff > 20:
            slider_diff = 9 # will be 10 ticks on the slider (no of ticks = slider_diff + 1)

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
                'GridLines': slider_diff,
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


class TimingQuestion(_Question):
    """
    A special question that is invisible to the participants but collects
    information about how long they spend on the survey page and logs it to
    the response data file.
    """
    def __init__(self, data_export_tag):
        """
        A special question that is invisible to the participants but collects
        information about how long they spend on the survey page and logs it
        to the response data file.
        
        Parameters:
        
        * `data_export_tag` (str): A unique code to identify the responses to
          this question in the data export. Should be unique compared to all
          other questions in the survey.
        """
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
    """
    A Google ReCAPTCHA embedded into a question, the participant has to pass
    it to proceed to the next page.

    Disclaimer: I do not endorse using Google in general or ReCAPTCHA in
    particular. It's like, they should at least *pay* people to mine their
    cognitive labour while they proceed to automate the human species into
    obsolecense. Sorry for getting political. It just grinds my gears.
    """
    def __init__(self, data_export_tag="reCAPTCHA", text_html=""):
        """
        A special question that is invisible to the participants but collects
        information about how long they spend on the survey page and logs it
        to the response data file.
        
        Parameters:
        
        * `data_export_tag` (str): A unique code to identify the responses to
          this question in the data export. Should be unique compared to all
          other questions in the survey.
        
        * `text_html` (str): Source code (HTML) to insert before the input.

          No `<script/>` elements are allowed. I don't know if it's possible
          to add JavaScript to this kind of question.
        """
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


class PageBreak(_Question):
    """
    Treated as a question for the purposes of the virtual survey API, this
    represents a break between survey pages within a single question block.
    If you are using this library, you can just think of a page
    break as another type of question, with no parameters.

    If you are interested in the internals, note the following:

    * To treat page breaks the same as questions in this library, this class
      inherits from `_Question`.
    * While page breaks play similar roles to questions in Qualtrics itself,
      they are not the same. A different API call is needed to add a page
      break vs. a regular question.
    * Therefore, unlike other `_Question` subclasses, this class does not use
      'question data' and it overrides the `create` method.

    Since there are no parameters, someone who cares a lot about memory could
    do a microoptimisation by caching instances of this class (a single
    instance is all that is needed). But I think it's probably a premature
    optimisation.
    """
    def __init__(self):
        """
        Note: Page breaks have no parameters, so this method does not take
        any data.

        Developer note: Since the `create` method of the superclass is
        overridden, there is no need to call the superclass constructor with
        even an empty data dictionary either.
        """
        pass

    def create(self, api, survey_id, block_id=None):
        """
        Make an API call to append a page break to the identified block of
        the identified survey.

        Parameters:

        * `api` (a `QualtricsSurveyDefinitionAPI` object):
          An API object that contains the credentials for the Qualtrics
          account for the page break to show up under.

        * `survey_id` (str): The ID of the survey.

        * `block_id` (str or `None`): The ID of the block to add the page
          break to. If `None`, the default block is used.

        Qualtrics API calls:

        * One call to `api.create_page_break`.
        ...
        """
        api.create_page_break(survey_id=survey_id, block_id=block_id)
