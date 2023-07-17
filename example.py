"""
Example of automated survey generation. Assembles a survey with the following
structure:

* three blocks, each with
  * ten pages, each with
    * one multiple choice question
    * one slider question
    * and one text input question
"""

import qualtrics as qq

# STAGE 1: create and configure the virtual survey data structure
survey = qq.BlockSurvey(
    name="Test Survey",
)
survey.set_show_back_button(True)
survey.set_progress_bar_display('VerboseText')


# STAGE 2: populate the survey with blocks (and the blocks with questions)
NUM_BLOCKS = 3
NUM_QUESTION_PAGES_PER_BLOCK = 10

for i in range(NUM_BLOCKS):
    # create a block
    block = qq.Block(description="<your block's description>")
    for q_index in range(NUM_QUESTION_PAGES_PER_BLOCK):
        # add a multiple choice question into this page of the block
        block.append_question(qq.MultipleChoiceQuestion(
            data_export_tag="Q"+str(i)+"."+str(q_index)+".1",
            options=["Choice 1", "Choice 2", "Choice 3"],
            text_html="Select a choice",
            force_response=True,
        ))

        # add a slider question into this page of the block
        block.append_question(qq.SliderQuestion(
            data_export_tag="Q"+str(i)+"."+str(q_index)+".2",
            num_sliders=1,
            text_html="Rate your answer from 0 to 100",
            force_response=True,
        ))

        # add a text entry question into this page of the block
        block.append_question(qq.TextEntryQuestion(
            data_export_tag="Q"+str(i)+"."+str(q_index)+".3",
            text_html="Text input",
            size_of_response="multi-line",
            force_response=True,
        ))
        
        # add a page break (future questions will be added to the next page
        # of the block)
        block.append_page_break()

    # once the block is finished, add it to the survey
    survey.append_block(block)


# STAGE 3 use the API to create the survey within your Qualtrics account

# TODO (ye who wants to run this example): fill in 'API_TOKEN' and
# 'DATA_CENTER' with your access codes following instructions in the README
API_TOKEN   = "" # COMPLETE ME
DATA_CENTER = "" # COMPLETE ME

# wrap the access codes in an API wrapper object
api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)

# pass the API to the virtual survey, it will upload itself to your Qualtrics
# account
survey.create(api)
