"""
Qualtrics API Recipies
======================

Functions that showcase usage of the API methods in ways other than survey
building (which is covered pretty well by the `surveys` module).
"""

import os
import json


try: # optional dependency on tqdm
    import tqdm
except ImportError:
    import qualtrics.notqdm as tqdm


def delete_all_surveys_by_name(
    api,
    survey_name,
    print_surveys=False,
    save_surveys=False,
):
    """
    Helper function to remove all functions with a given name from a
    qualtrics account using the API. Mostly useful for periodic cleaning up
    an account after a large number of surveys named 'Test Survey' have been
    automatically generated during survey development.

    > WARNING: Deleting a survey using the API also deletes any responses
    > gathered with the survey. That is, it can result in irreversible data
    > loss! So only do this if your surveys have no responses or if you are
    > really sure you don't need the data any more.

    Parameters:

    * `api` (of `QualtricsSurveyDefinitionAPI` class):
      An API object that contains the credentials for the Qualtrics
      account you want the surveys to be cleared from.
    
    * `survey_name` (str):
      Surveys with this name (exact string match) will be deleted.

    * `print_surveys` (bool, default `False`):
      If `True`, the function will log the JSON associated with each deleted
      survey to the command line just before it is deleted. If `False`, no
      such logging.
    
    * `save_surveys` (bool `False`, or str path):
      If `False`, the surveys are not saved. If truthy string, the string is
      interpreted as a filesystem path to a directory. This directory should
      exist or there will be an error. Anyway assuming it exists, inside will
      be saved a JSON file for each deleted survey, named with the survey's
      unique ID.

    Qualtrics API methods used:

    * One call to `api.list_surveys()` gets all survey names and IDs.
    * (If `print_surveys` or `save_surveys` is not `False`) one call per
      survey-to-be-deleted to `api.get_survey`.
    * One call per survey-to-be-deleted to `api.delete_survey`, obviously.

    Requests for input:

    * To avoid accidental data deletion, this function will request
      confirmation via command line input to make sure you really want to
      delete surveys. You can fork & patch it if you like to live
      dangerously.

    Prints:

    * A few diagnostic messages.
    * A dynamic progress bar while the identified surveys are deleted
      (if optional dependency tqdm is installed).
    * (If `print_surveys` is `True`) the JSON representation of deleted
      surveys.

    File I/O:

    * (If `save_surveys` is a path to an existing directory) saves the JSON
      representation of each deleted survey as a JSON file named with the
      survey's ID (and the extension `.json`).

    Notes:

    * Sometimes inexplicably crashes or freezes during API communication and
      you have to restart it. Sorry, not sure why, doesn't seem worth
      figuring out at this point.
    """
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
    header_html=None,
    footer_html=None,
    custom_css=None,
    script_js=None
):
    """
    Patch the global configuration of an existing Qualtrics survey.

    Parameters:

    * `api` (of `QualtricsSurveyDefinitionAPI` class):
      An API object that contains the credentials for the Qualtrics
      account containing the survey you want to update.
    
    * `survey_id` (str):
      The survey with this ID will be updated. The Qualtrics Survey ID can be
      found in the survey's settings somewhere (sorry, I forgot where right
      now), or in the URL of the the web editor while editing the survey
      (also the preview URL has it, and probably the distribution URL too).

    * `header_html` (str, optional):
      Source code (HTML) to be used for the survey header. This HTML is
      inserted before the survey on every page of the survey, and can contain
      JavaScript in `<script />` elements.
    
    * `footer_html` (str, optional):
      Source code (HTML) to be used for the survey footer. This HTML is
      inserted after the survey on every page of the survey, and can contain
      JavaScript in `<script />` elements.

    * `custom_css` (str, optional):
       Source code (CSS) to be used for the survey custom stylesheet.
       This stylesheet is linked on every page of the survey.

    * `script_js` (str, optional):
       Source code (JavaScript) to be added for you in a script tag to the
       HTML footer (if provided).
    
    Qualtrics Survey Definition API calls:

    * one call to `api.partial_update_survey_options`, which, if I recall
      correctly, actually involves two REST calls: first getting the existing
      options and second uploading the amended options.

    Notes:

    * Not all global survey configuration options are supported by this
      recipe, but more could in principle be added to this method in the
      future. Anyway, this gives you the idea.
    
    * Options that are not included here, if set on the identified survey,
      will not be changed by this method.
    
    * The same goes for the options included here (for header, footer, and
      css): these will not be canged in the online survey if the arguments
      are excluded from this call. However, as soon as any string is
      provided (including if any `script_js` is provided, in the case of the
      footer), then this will be uploaded and will override the existing
      option value.
    """
    options = {}
    if script_js is not None:
        if footer_html is None:
            footer_html = ""
        footer_html += "\n\n<script>\n" + script_js + "\n</script>\n"
    if footer_html is not None:
        options['Footer'] = footer_html
    if header_html is not None:
        options['Header'] = header_html
    if custom_css is not None:
        # despite what the qualtrics API docs say, this takes actually css
        # string *wrapped in a dictionary*
        options['CustomStyles'] = {"customCSS": custom_css},
    # ready to make the API call
    api.partial_update_survey_options(
        survey_id=survey_id,
        options_data=options,
    )

