"""
Qualtrics Survey Definition API
===============================

This module provices convenient wrapper methods for accessing the 
Qualtrics survey-definitions REST API.

It is considered lower-level than the object-oriented interface constituted
by the other modules in this library. Those modules call into this code
(mostly through the `surveys` module, specially the `create` methods of the
various survey classes, but also in some other places).
For building surveys, it is recommended to use the higher-level tools in
those other modules.

The `recipes` module provides some other examples of direct usage of this
module's functionality. See also the Qualtrics API documentation, in
particular these links:

* https://api.qualtrics.com/ZG9jOjg3NzY2Nw-building-surveys
    (overview)
* https://api.qualtrics.com/ZG9jOjg3NzY4Mg-survey-api-introduction
    (overlapping information with first link)
* https://api.qualtrics.com/60d24f6897737-qualtrics-survey-api
    (full reference)
* https://api.qualtrics.com/ZG9jOjg3NzY4Mw-example-use-cases-walkthrough
    (tutorial/walkthrough)

Note: Unfortunately, the documentation is not 100% comprehensive, nor 100%
accurate on the specific parameters and data expected by various API routes.
Nevertheless it gives a good overview of the API routes that are wrapped in
this module.

The methods are all synchronous / blocking, because it makes scripting the
survey creation much simpler and rate-limiting a non-issue.
"""

import sys

import requests


class QualtricsSurveyDefinitionAPI:
    """
    Qualtrics Survey Definition API wrapper. Provides convenient methods for
    actuating each of the major methods on the Survey Definition API. Stores
    the base URL and API token that are needed to make each API call.
    """


    def __init__(
        self,
        api_token,
        data_center,
        user_agent="user of library github:matomatical/qualtrics",
        debug=False,
    ):
        """
        Construct a Qualtrics Survey Definition API wrapper.

        Parameters:

        * `api_token` (str): API Token gleaned from the Qualtrics website.
          This token identifies your Qualtrics account, which is the account
          where the modifications will take place. It's also your access key,
          don't share it with people you don't trust---they will gain access
          to all of your surveys and response data.

          Should look something like:
          `"aaaaaAAaAaAAAAAaAaaaaAAaAaAaaAaaAAA1AaAA"`

        * `data_center` (str): The subdomain for your data center. Also
          gleaned from the Qualtrics website. For example, could look like
          `"syd1"` or `"melbourneuni.au1"`.

          (In the case of Melbourne University, I think the former is
          explicitly listed but the latter works better for the automatic
          generation of preview links, but I could be misremembering.)
        
        * `user_agent` (str, recommended but optional): The user agent string
          sent along with each of your requests. This identifies you to the
          Qualtrics API server. If you include some identifying information
          in your user agent, it can help the Qualtrics networking people to
          diagnose issues you might accidentally be causing on their end with
          your use of the library.

          By default, the library identifies you as "user of library
          github:matomatical/qualtrics".

        * `debug` (bool, default `False`): If true, some API requests are
        printed to stderr during interaction with the server. Useful because
        it shows you the data that comes back with a response, including if
        the response made the program crash, so you see if the Qualtrics
        server sent you a helpful error message.
        """
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
        """
        An internal helper method for sending API requests, handling endpoint
        computation and also JSON encoding and JSON decoding of data to be
        sent/received (actually the latter is handled by requests, but,
        conceptually, it happens inside this method).

        Blocking.
        """
        # perform the request
        response = method(
            url     = self.apiurl + endpoint,
            headers = self.headers,
            json    = data,
        )
        # parse the response
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
        """
        Get a list of all surveys in the account.

        Requests:

        * GET to `surveys`

        Blocking.
        """
        return self._get(endpoint="surveys")

    
    # # One survey


    def get_survey(self, survey_id):
        """
        For the survey with ID `survey_id` (str), get the full survey data.

        Requests:

        * GET to `survey-definitions/{survey_id}`

        Blocking.
        """
        return self._get(endpoint=f"survey-definitions/{survey_id}")


    def create_survey(self, survey_name):
        """
        Create a new survey with the name `survey_name` (str, < 100 chars).

        Requests:

        * POST name to `survey-definitions`

        Blocking.
        """
        return self._post(
            endpoint="survey-definitions",
            data={
                "SurveyName": survey_name,
                "Language": "EN",
                "ProjectCategory": "CORE",
            },
        )


    def delete_survey(self, survey_id, warn=True):
        """
        Delete the survey with ID `survey_id`.
    
        > WARNING: Deleting a survey using the API also deletes any responses
        > gathered with the survey. That is, it can result in irreversible
        > data loss! So only do this if your surveys have no responses or if
        > you are really sure you don't need the data any more.

        Because of the potential for data loss, by default this method
        stops to ask for user input before proceeding. If you really want
        to override this check, you can set the flag `warn=False`. This is
        not recommended.

        Requests:

        * DELETE to `survey-definitions/{survey_id}`

        Blocking.
        """
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
        """
        For the survey with ID `survey_id` (str), get the options.

        Requests:

        * GET to `survey-definitions/{survey_id}/options`
        
        Blocking.
        """
        return self._get(endpoint=f"survey-definitions/{survey_id}/options")


    def update_survey_options(self, survey_id, options_data):
        """
        For the survey with ID `survey_id` (str), update the options to the
        dictionary `options_data`.

        Requests:

        * PUT `options_data` to `survey-definitions/{survey_id}/options`
        
        Blocking.
        """
        return self._put(
            endpoint=f"survey-definitions/{survey_id}/options",
            data=options_data,
        )


    def partial_update_survey_options(self, survey_id, options_data):
        """
        For the survey with ID `survey_id` (str), update the options to the
        dictionary `options_data`, preserving options that are already set
        and are not under keys included in `options_data`.

        Requests:

        * GET to `survey-definitions/{survey_id}/options`
        * PUT to `survey-definitions/{survey_id}/options`
          (attaching the updated survey options data)

        Blocking.
        """
        old_options_data = self.get_survey_options(survey_id=survey_id)
        new_options_data = old_options_data | options_data
        return self.update_survey_options(
            survey_id=survey_id,
            options_data=new_options_data,
        )

    
    # # Questions


    def list_questions(self, survey_id):
        """
        For the survey with ID `survey_id` (str) get the question list.

        Requests:

        * GET to `survey-definitions/{survey_id}/questions`

        Blocking.
        """
        return self._get(
            endpoint=f"survey-definitions/{survey_id}/questions",
        )


    def get_question(self, survey_id, question_id):
        """
        For the survey with ID `survey_id` (str) and the question with ID
        `question_id`, get the question data.

        Requests:

        * GET to `survey-definitions/{survey_id}/questions/{question_id}`

        Blocking.
        """
        return self._get(
            endpoint=f"survey-definitions/{survey_id}/questions/{question_id}",
        )


    def create_question(self, survey_id, question_data, block_id=None):
        """
        For the survey with ID `survey_id` (str), create a new question with
        question data `question_data`. If `block_id` is provided, add this
        question to the block with block ID `block_id`. Else, add it to the
        default block.

        Requests:

        * POST question data to `survey-definitions/{survey_id}/questions`
          (with an optional query `?blockId={block_id}`)

        Blocking.
        """
        query = "" if block_id is None else f"?blockId={block_id}"
        return self._post(
            endpoint=f"survey-definitions/{survey_id}/questions" + query,
            data=question_data,
        )


    def update_question(self, survey_id, question_id, question_data):
        """
        For the survey with ID `survey_id` (str) and the question with
        question ID `question_id`, update the question data to the given
        `question_data`.

        Requests:

        * PUT to `survey-definitions/{survey_id}/questions/{question_id}`
          (attaching new question data)

        Blocking.
        """
        return self._put(
            endpoint=f"survey-definitions/{survey_id}/questions/{question_id}",
            data=question_data,
        )


    def partial_update_question(self, survey_id, question_id, question_data):
        """
        For the survey with ID `survey_id` (str) and the question with
        question ID `question_id`, update the question data to the given
        `question_data`, keeping existing question data for missing fields.

        Requests:

        * GET to `survey-definitions/{survey_id}/questions/{question_id}`
        * PUT to `survey-definitions/{survey_id}/questions/{question_id}`
          (attaching updated question data).

        Blocking.
        """
        # NOTE: doesn't appear to be working for new(?) fields...
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
        """
        For the survey with ID `survey_id` (str), remove the question with
        question ID `question_id` from the survey.

        Requests:

        * DELETE to `survey-definitions/{survey_id}/questions/{question_id}`
        
        Blocking.
        """
        return self._delete(
            endpoint=f"survey-definitions/{survey_id}/questions/{question_id}",
        )


    # # Blocks
    
    def list_blocks(self, survey_id):
        """
        For the survey with ID `survey_id` (str) get the block list.

        Requests:

        * GET to `survey-definitions/{survey_id}`
          (extracts the list of blocks from the resulting survey data)

        Blocking.
        """
        survey = self.get_survey(survey_id=survey_id)
        return list(survey['Blocks'].values()) # originally dict {id: block}


    def get_block(self, survey_id, block_id):
        """
        For the survey with ID `survey_id` (str) and the block with ID
        `block_id`, get the block data.

        Requests:

        * GET to `survey-definitions/{survey_id}/blocks/{block_id}`

        Blocking.
        """
        return self._get(
            endpoint=f"survey-definitions/{survey_id}/blocks/{block_id}",
        )


    def create_block(self, survey_id, block_description=""):
        """
        For the survey with ID `survey_id` (str), create a new empty sandard
        block with the description `block_description`.

        Requests:

        * POST block data to `survey-definitions/{survey_id}/blocks`

        Blocking.
        """
        return self._post(
            endpoint=f"survey-definitions/{survey_id}/blocks",
            data={
                'Description': block_description,
                'Type': 'Standard',
            },
        )


    def update_block(self, survey_id, block_id, block_data):
        """
        For the survey with ID `survey_id` (str) and the block with block ID
        `block_id`, update the block data to the given `block_data`.

        Requests:

        * PUT block data to `survey-definitions/{survey_id}/blocks/{block_id}`

        Blocking.
        """
        return self._put(
            endpoint=f"survey-definitions/{survey_id}/blocks/{block_id}",
            data=block_data,
        )


    def create_page_break(self, survey_id, block_id):
        """
        For the survey with ID `survey_id` (str) and the block with ID
        `block_id`, append a page break to the block's list of elements.

        Requests:

        * GET to `survey-definitions/{survey_id}/blocks/{block_id}`
        * PUT block data to `survey-definitions/{survey_id}/blocks/{block_id}`
          (the block data is the same as the result of GET but with the page
          break added)

        Blocking.
        """
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
        """
        For the survey with ID `survey_id` (str), remove the block with
        block ID `block_id` from the survey.

        Requests:

        * DELETE to `survey-definitions/{survey_id}/blocks/{block_id}`
        
        Blocking.
        """
        return self._delete(
            endpoint=f"survey-definitions/{survey_id}/blocks/{block_id}",
        )


    # # Flows


    def get_flow(self, survey_id):
        """
        For the survey with ID `survey_id` (str), get the flow element tree.

        Requests:

        * GET to `survey-definitions/{survey_id}/flow`
        
        Blocking.
        """
        return self._get(endpoint=f"survey-definitions/{survey_id}/flow")


    def update_flow(self, survey_id, flow_data):
        """
        For the survey with ID `survey_id` (str), update the flow element
        tree to that described by the dictionary `flow_data`.

        Requests:

        * PUT `flow_data` to `survey-definitions/{survey_id}/flow`
        
        Blocking.
        """
        return self._put(
            endpoint=f"survey-definitions/{survey_id}/flow",
            data=flow_data,
        )


    def update_flow_element(self, survey_id, flow_id, flow_element_data):
        """
        For the survey with ID `survey_id` (str), update the data of flow
        element with ID `flow_id` (str), to the data contained in
        `flow_element_data`.

        Requests:

        * PUT `flow_element_data` to `survey-definitions/{survey_id}/{flow_id}`

        Blocking.
        """
        return self._put(
            endpoint=f"survey-definitions/{surveu_id}/flow/{flow_id}",
            data=flow_element_data,
        )


    # # Other


    def link_to_edit_survey(self, survey_id):
        """
        Compute based on the stored data center URL a link to the web editor
        page for the survey with ID `survey_id`.

        No requests.
        """
        return f"{self.url}/survey-builder/{survey_id}/edit"


    def link_to_preview_survey(self, survey_id):
        """
        Compute based on the stored data center URL a link to a preview page
        for the survey with ID `survey_id`.

        No requests.
        """
        return f"{self.url}/jfe/preview/{survey_id}"

