# # # # QUALTRICS SURVEY BUILDER TOOLS

import os
import sys
import json

import requests
import tqdm         # TODO: remove/make optional dependency


# # # SURVEYS

class _Survey:

    def __init__(self, name, **options):
        self.name = name
        self.options = options


    def set_options(self, **options):
        self.options = self.options | options


    def set_header_html(self, header_html=""):
        self.options['Header'] = header_html

    def set_footer_html(self, footer_html=""):
        self.options['Footer'] = footer_html

    def set_custom_css(self, custom_css=""):
        self.options['CustomStyles'] = {'customCSS': custom_css}


    def set_external_css_url(self, external_css_url=""):
        self.options['ExternalCSS'] = external_css_url


    def create(self, api):
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

    def __init__(self, name, questions=(), **options):
        super().__init__(name, **options)
        self.questions = list(questions)


    def append_question(self, question):
        self.questions.append(question)
        return question


    def create(self, api):
        survey_id = super().create(api)
        
        n_questions = len(self.questions)
        print(f"populating survey: {n_questions} questions")
        progress = tqdm.tqdm(total=n_questions, dynamic_ncols=True)
        for question in self.questions:
            question.create(api, survey_id, block_id=None) # default block
            progress.update()
        progress.close()
        print("survey", survey_id, "populated")


class BlockSurvey(_Survey):

    def __init__(self, name, blocks=(), **options):
        super().__init__(name, **options)
        self.blocks = list(blocks)


    def append_block(self, block):
        self.blocks.append(block)
        return block


    def create(self, api):
        survey_id = super().create(api)
        
        n_blocks = len(self.blocks)
        n_questions = sum(len(b.questions) for b in self.blocks)
        print(f"populating survey: {n_blocks} blocks, {n_questions} questions")
        progress = tqdm.tqdm(total=n_blocks+n_questions, dynamic_ncols=True)
        for block in self.blocks:
            block_id = api.create_block(survey_id=survey_id)['BlockID']
            progress.update()
            for question in block.questions:
                question.create(api, survey_id, block_id=block_id)
                progress.update()
        progress.close()
        print("survey", survey_id, "populated")


class FlowSurvey(_Survey):

    def __init__(self, name, elements=(), **options):
        super().__init__(name, **options)
        self.elements = list(elements)

    
    def append_flow(self, flow):
        self.elements.append(flow)
        return flow


    def create(self, api):
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

    def __init__(self, questions=()):
        self.questions = list(questions)


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
        # TODO: randomisation?
    ):
        # convert string options into option objects
        options = [
            opt if isinstance(opt, _Option) else BasicOption(opt)
            for opt in options
        ]
        if selection_method == "button-list":
            selector = {'Selector': "SAVR", 'SubSelector': "TX"}
        elif selection_method == "dropdown-list":
            selector = {'Selector': "DL"}
        else:
            raise ValueError(f"unknown selection_method {selection_method!r}")
        super().__init__(data=selector | {
            'QuestionType': "MC",
            'ChoiceOrder': list(range(1, len(options)+1)),
            'Choices': {i: o.data for i, o in enumerate(options, start=1)},
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
    for survey in tqdm.tqdm(surveys):
        survey_id = survey["id"]
        if print_surveys or save_surveys:
            survey = api.get_survey(survey_id)
            if print_surveys:
                tqdm.tqdm.write(json.dumps(survey, indent=2))
            if save_surveys:
                path = os.path.join(save_surveys, f"{survey_id}.json")
                tqdm.tqdm.write(f"saving survey {survey_id} to {path}")
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

