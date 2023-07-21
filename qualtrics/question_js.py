"""
Qualtrics Virtual Question JavaScript Tools
===========================================

This module contains tools for adding javascript that makes use of the
Qualtrics SurveyEngine JavaScript API to qualtrics questions.
Most question types allow a `script_js` parameter, which is a string that
becomes JavaScript code attached to the question.
The supported JS functions are those from the Qualtrics JavaScript Question
API, [documented here](https://api.qualtrics.com/82bd4d5c331f1-qualtrics-java-script-question-api-class).

An example of such a script is as follows:

```javascript
Qualtrics.SurveyEngine.addOnload(function() {
    console.log("loaded!");
});
Qualtrics.SurveyEngine.addOnReady(function() {
    console.log("ready!");
});
Qualtrics.SurveyEngine.addOnReady(function() {
    console.log("ready again!");
});
Qualtrics.SurveyEngine.addOnPageSubmit(function() {
    console.log("submitting!");
});
Qualtrics.SurveyEngine.addOnUnload(function() {
    console.log("unloaded!");
});
```

It can be seen that there is a decent amount of boilerplate to be added to
achieve basic functionalities. The classes in this module attempt to abstract
away that boilerplate and allow an interface for attaching plain JS code to
specific events.
"""


class QuestionJS:
    """
    Apply the builder pattern to construct a single JS source string with
    various snippets attached to various events in different ways.

    For example:

    ```python
    QuestionJS() # builder pattern
        .on_load('console.log("loaded!");')
        .on_ready('console.log("ready!");')
        .on_ready('console.log("ready! again!");')
        .on_submit('console.log("submitting!");')
        .on_unload('console.log("unloaded!");')
        .script(), # always call .script() (converts to str) 
    ```

    (This expression evaluates to the example JS source at the top of this
    module.)
    """
    def __init__(self):
        self.scripts = []

    def script(self):
        """
        Convert the contents of the script store accumulated so far into a
        single JavaScript source string.
        """
        return "\n\n".join(self.scripts)


    def on_load(self, script):
        """
        Attach a snipper that should be attached as an `Onload` function,
        that is, when the page first loads.

        Parameters:

        * `script` (src): The JavaScript source to attach.

        Returns:

        * `self` (for method chaining; builder pattern).
        """
        # yes, it's really lowercase l in "load", unlike the others...
        self.scripts.append(self._engine_wrap("load", script))
        return self


    def on_ready(self, script):
        """
        Attach a snipper that should be attached as an `OnReady` function,
        that is, when the page finishes loading.

        Parameters:

        * `script` (src): The JavaScript source to attach.

        Returns:

        * `self` (for method chaining; builder pattern).
        """
        self.scripts.append(self._engine_wrap("Ready", script))
        return self
    

    def on_submit(self, script):
        """
        Attach a snipper that should be attached as an `OnSubmit` function,
        that is, when the next (or back/prev?) button is pressed.

        (Note that this event triggers even if validation fails and the
        submission is not completed.)

        Parameters:

        * `script` (src): The JavaScript source to attach.

        Returns:

        * `self` (for method chaining; builder pattern).
        """
        self.scripts.append(self._engine_wrap("PageSubmit", script, "type"))
        return self
    

    def on_unload(self, script):
        """
        Attach a snipper that should be attached as an `OnUnload` function,
        that is, when the page finishes unloading. I'm not 100% sure when
        this is but empirically if I recall correctly it happens before the
        next page is loaded.

        Parameters:

        * `script` (src): The JavaScript source to attach.

        Returns:

        * `self` (for method chaining; builder pattern).
        """
        self.scripts.append(self._engine_wrap("Unload", script))
        return self
    

    def on_click(self, script):
        """
        Attach a snipper that should be attached as an `OnCoad` function,
        that is, when the question's div is clicked.

        Internally, the boilerplate for this one is different from the
        others---based on some examples in the Qualtrics JS API docs if I
        recall correctly. The actual method is to attach the code as a
        function to a magic `this.questionclick` variable as an `onload`
        script. Make of that what you will.

        Parameters:

        * `script` (src): The JavaScript source to attach.

        Returns:

        * `self` (for method chaining; builder pattern).
        """
        return self.on_load(f"""this.questionclick = function(event, element) {{
            {script}
        }};""");

    
    @staticmethod
    def _engine_wrap(method, script, *args):
        """
        Private helper function to achieve the Qualtrics SurveyEngine
        boilerplate.
        
        Parameters:

        * `method` (str, e.g., `"load"` or `"Ready"`):
          Goes after `On` in the SurveyEngine method name.
        * `script` (src, JS source):
          The contents of the attached function.
        * `*args` (tuple of str, argument names):
          Any argument names that go with the function to be passed to the
          attach method (actually only used for the argument `type` for
          submission, but I forgot what this argument does exactly. Look it
          up.
        """
        return "Qualtrics.SurveyEngine.addOn{}(function({}){{{}}});".format(
            method,
            ','.join(args),
            f'\n{script}\n',
        )


def setEmbeddedData(key, expression_js):
    """
    Use `key` (str) to store the result of javascript expression
    `expression_js` in the survey's database.
    """
    return f'Qualtrics.SurveyEngine.setEmbeddedData("{key}",{expression_js});'


def getEmbeddedData(key):
    """
    A javascript expression to fetch the data stored in the survey's database
    using `key` (str).
    """
    return f'${{e://Field/{key}}}'

