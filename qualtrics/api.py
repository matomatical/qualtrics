"""
Qualtrics Survey Definitions API
================================

TODO: DOCUMENT
"""

import sys

import requests


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

