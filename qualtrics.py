# # # # QUALTRICS SURVEY BUILDER TOOLS

import sys
import json

import requests
import tqdm         # TODO: remove/make optional dependency


# # # SURVEY


class Survey:
    
    def __init__(self,
        name,
        blocks=None,
        questions=None,
        header_html=None,
        footer_html=None,
        custom_css=None,
        external_css_url=None,
    ):
        # mandatory name
        self.name = name

        # optional questions
        self.questions = []
        if questions:
            for question in questions:
                self.add_question(question)
        
        # optional blocks
        self.blocks = []
        if blocks:
            for block in blocks:
                self.add_block(block)
        
        # optional config
        self.header_html = ""
        self.footer_html = ""
        self.custom_css = ""
        self.external_css_url = ""
        self.configured = False
        self.configure(
            header_html=header_html,
            footer_html=footer_html,
            custom_css=custom_css,
            external_css_url=external_css_url,
        )

    
    def configure(self, 
        header_html=None,
        footer_html=None,
        custom_css=None,
        external_css_url=None,
    ):
        if header_html is not None:
            self.header_html = header_html
            self.configured = True
        if footer_html is not None:
            self.footer_html = footer_html
            self.configured = True
        if custom_css is not None:
            self.custom_css = custom_css
            self.configured = True
        if external_css_url is not None:
            self.external_css_url = external_css_url
            self.configured = True

    
    def add_block(self, block):
        self.blocks.append(block)
        return block


    def add_question(self, question):
        self.questions.append(question)
        return question

    
    def create(self, api):
        # todo: delete old surveys?
        
        # create
        print("creating survey... ", end="", flush=True)
        survey_id = api.create_survey(survey_name=self.name)['SurveyID']
        print("survey created with id", survey_id)
        
        # config
        if self.configured:
            print("configuring survey... ", end="", flush=True)
            api.partial_update_survey_options(
                survey_id=survey_id,
                options_data={
                    'Header': self.header_html,
                    'Footer': self.footer_html,
                    'CustomStyles': {"customCSS": self.custom_css},
                    'ExternalCSS': self.external_css_url,
                },
            )
            print("survey configured")

        # populate
        n_blocks = len(self.blocks)
        n_questions = len(self.questions) \
                      + sum(len(b.questions) for b in self.blocks)
        print(f"populating survey: {n_blocks} blocks, {n_questions} questions")
        progress = tqdm.tqdm(total=n_blocks+n_questions, dynamic_ncols=True)
        for question in self.questions:
            question.create(api=api, survey_id=survey_id) # default block
            progress.update()
        for block in self.blocks:
            block.create(api=api, survey_id=survey_id, progress=progress)
            progress.update()

        progress.close()
        
        print("survey", survey_id, "created")
        print("edit survey at:", api.edit_survey_link(survey_id=survey_id))


# # # BLOCKS


class Block:

    def __init__(self, questions=None):
        if questions is None:
            questions = []
        self.questions = []
        for question in questions:
            self.add_question(question)


    def add_question(self, question):
        self.questions.append(question)
    

    def add_page_break(self):
        self.questions.append(PageBreak())


    def create(self, api, survey_id, progress=None):
        # create
        block_id = api.create_block(survey_id=survey_id)['BlockID']
        
        # populate
        for question in self.questions:
            question.create(api=api, survey_id=survey_id, block_id=block_id)
            if progress is not None: progress.update()
        

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


class TextGraphicQuestion(_Question):
    def __init__(self, text_html, script_js=""):
        super().__init__(data={
            'QuestionText': text_html,
            'QuestionJS':   script_js,
            'QuestionType': 'DB',
            'Selector':     'TB',
            'Language':     [], # this silences a translation warning...
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

    def create_block(self, survey_id):
        return self._post(
            endpoint=f"survey-definitions/{survey_id}/blocks",
            data={
                'Description': 'Standard Question Block',
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


    # # Other

    def edit_survey_link(self, survey_id):
        return self.url + "/survey-builder/" + survey_id + "/edit"


# # # RECIPES


def delete_all_surveys_by_name(api, survey_name, print_surveys=False):
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
    for survey in tqdm.tqdm(surveys):
        survey_id = survey["id"]
        if print_surveys:
            tqdm.tqdm.write(json.dumps(api.get_survey(survey_id), indent=2))
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

