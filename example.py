import qualtrics as qq

# use the API to create the survey within your Qualtrics account
api = qq.QualtricsSurveyDefinitionAPI(API_TOKEN, DATA_CENTER)

# build the survey data structure
survey_options = qq.SurveyOptions(back_button='true', progress_bar_display='VerboseText') # set back button, set progress bar
survey = qq.BlockSurvey(name="<your survey name>", options=survey_options.data)

NUM_BLOCKS = 3
NUM_QUESTIONS = 10

for i in range(NUM_BLOCKS):
    # create a block
    block = qq.Block(description="<your block's description>")
    for q_index in range(NUM_QUESTIONS):

        # add a multiple choice question into this block
        block.append_question(qq.MultipleChoiceQuestion(
            data_export_tag="Q"+str(i)+"."+str(q_index)+".1",
            options=["Choice 1", "Choice 2", "Choice 3"],
            text_html="Select a choice",
            force_response=True,
        ))

        # add a slider question into this block
        block.append_question(qq.SliderQuestion(
            data_export_tag="Q"+str(i)+"."+str(q_index)+".2",
            num_sliders=1,
            text_html="Rate your answer from 0 to 100",
            force_response=True
        ))

        # add a text entry question into this block
        block.append_question(qq.TextEntryQuestion(
            data_export_tag="Q"+str(i)+"."+str(q_index)+".3",
            text_html="Text input",
            size_of_response="multi-line",
            force_response=True
        ))

        block.append_page_break()
    survey.append_block(block)

survey.create(api)
