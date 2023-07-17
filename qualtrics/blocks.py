"""
Qualtrics Virtual Blocks
========================

This module contains classes for virtual survey blocks. The idea of the
library is that you will populate such blocks with questions using the
definitions in this and other elements modules and then you will add these
blocks to a virtual survey (see the surveys module) before using the methods
of those virtual survey objects to upload your survey to Qualtrics as a real
survey using API calls.
"""


class Block:
    """
    Class representing a vrtual block of questions, as part of a block-based
    or flow-based virtual Qualtrics survey.
    
    Main functionality is to store a list of questions.
    """


    def __init__(self, questions=(), description="Standard Question Block"):
        """
        Constructor for a virtual question block.

        Parameters:
        
        * `questions` (iterable of questions, i.e. objects of class
          `_Question`):
          A list of questions, forming the contents of the block.

        * `description` (str, optional):
          The block description, which is shown at various places in the
          Qualtrics web editor, but is not visible to survey participants.
          Default: 'Standard Question Block' (maybe this was default from
          editor I think?)
        """
        self.questions = list(questions)
        self.description = description


    def append_question(self, question):
        """
        Add a new question to the survey's internal list of questions.

        Parameters:

        * `question` (a `_Question` object): The question to add.
        """
        self.questions.append(question)


    def append_page_break(self):
        """
        Add a new page break to the block's internal list of questions.

        Notes:

        * In the virtual survey model, page breaks are actually treated as
          questions. Calling this method is equivalent to calling
          `.append_question(PageBreak())`.

          This method may be considered more succinct, and may also satisfy
          someone who finds adding a page break as a question unintuitive.
        """
        self.questions.append(PageBreak())

