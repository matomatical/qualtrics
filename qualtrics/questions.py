"""
Qualtrics Virtual Questions
===========================

This module contains classes for various kinds of questions. The idea of the
library is that you will construct questions with the definitions in this
module and then add them to a virtual survey (see the surveys module) before
using the methods of those virtual survey objects to upload your survey to
Qualtrics as a real survey using API calls.
"""



class _Question:

    def __init__(self, data):
        self.data = data


    def create(self, api, survey_id, block_id=None):
        api.create_question(
            survey_id=survey_id,
            question_data=self.data,
            block_id=block_id,
        )


class PageBreak(_Question):
    """
    An honorary question. Plays the same role in virtual surveys but slightly
    different role in the API. This inherits from question and overrides all
    methods, in particular doesn't take any data at constructor time.
    """

    def __init__(self):
        pass


    def create(self, api, survey_id, block_id=None):
        """
        Make an API call to append a page break to the identified block of
        the identified survey.

        Parameters:

        * `api` (a `QualtricsSurveyBuilderAPI` object):

        * `survey_id` (str):

        * `block_id` (str or `None`):

        API calls:

        ...
        """
        api.create_page_break(survey_id=survey_id, block_id=block_id)


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
