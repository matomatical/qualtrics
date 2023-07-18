"""
Qualtrics Virtual Survey Flows
==============================

This module provides definitions for virtual survey flow elements making up
virtual survey flow trees, and in turn governing the sequence of blocks seen
by participants in the Qualtrics survey. During a survey, the sequence of
blocks the participant experiences is based on a tree traversal with the
exact details depending on the semantics of each flow element (tree node).
To get a feel for what is possible with flow elements, I recommend playing
around in the flows tab of the Qualtrics web editor.

The classes herein all inherit from an abstract base class `_FlowElement`,
which provides a `children` field forming the core of the tree structure, and
an `append_flow` method to add new children.
The `_FlowElement` class also implements a compilation method used for
recursively aggregating a flow tree into a single dictionary for uploading
through the API.

The available flow elements are as follows:

* `RootFlow`: The root of a flow tree. Traverses children in order, like a
  `GroupFlow`. Also provides a `flow_data` method that initialises the
  compilation during Qualtrics uploading.

* `GroupFlow`: A non-leaf element with multiple elements as children,
  which are traversed in sequence.

* `BlockRandomizerFlow`: A non-leaf element. Configurable such that the
  traversal will enter a random subset of one or more of its children,
  in a random order, depending on the participant.
  * Can be used for selecting conditions in a randomised experiment (subset
    of size 1).
  * Can also for shuffling a sequence of blocks/flow-subtrees (subset of size
    n, where n is the number of children).

* `BlockFlow`: A leaf element. Each `BlockFlow` element has a `Block`
  attached to it. When the traversal hits such a flow element, the
  participant is shown the attached block.

* `EndSurveyFlow`: Another leaf element. Traversing here ends the survey
  for the participant, like if they had finished the traversal.
"""


class _FlowElement:
    """
    Abstract base class for flow tree nodes and leaves. Serves three main
    functions:

    1. Stores the data associated with the flow element configuring its type
       and behaviour.

    2. Stores a list of children. The constructor takes an initial list and
       the methods `append_flow` and `append_block` extend this list.
      
    3. Implement recursive traversal algorithms, such as:
       * A recursive compilation algorithm that takes a flow tree by the root
         and produces a single dictionary containing the entire flow tree
         structure, for uploading to Qualtrics through the API. See `compile`.
       * A recursive traversal to ield all of the block flows in the tree
         (to easily access all of the blocks comprising a flow survey).
         See `get_block_flows`.
    
    Notes for subclassing:

    * All subclasses not overriding `compile` should pass their data and flow
      element type along to the superclass constructor to be stored and later
      compiled into the flow data to be uploaded to Qualtrics.

    * Subclasses with children should pass children along to the superclass
      constructor.

    * Subclasses that represent leaf nodes don't pass an initial list to the
      superclass constructor and override `append_flow` to raise an Exception
      (this is sufficient since `append_block` calls `append_flow`
      internally).
    """
    def __init__(self, children=(), **kwargs):
        """
        Initialise abstract base class for flow elements.

        Parameters:

        * `children` (iterable of `_FlowElement` objects): the initial
          children stored by the element.

        * `**kwargs` (keyword arguments): necessary data for deciding the
          flow element type and configuring its parameters in Qualtrics.
          Will be included in the result of `compile`.
        """
        self.children = list(children)
        self.kwargs = kwargs

    def append_flow(self, flow):
        """
        Add `flow` (of class `_FlowElement`) to the list of children.
        """
        self.children.append(flow)
        return flow

    def append_block(self, block):
        """
        A shortcut method to add a `BlockFlow` wrapping a given `block` (of
        class `Block`) to the list of children.
        """
        self.append_flow(BlockFlow(block))
        return block

    def compile(self, flow_id, block_id_map):
        """
        Implement a recursive compilation algorithm that takes a flow tree by
        the root and produces a single dictionary containing the entire flow
        tree structure, for uploading to Qualtrics through the API.

        Parameters:

        * `flow_id` (int): A unique integer to be allocated to this flow
          element, used to create its unique flow ID string.
        
        * `block_id_map` (dict) a global dictionary mapping `Block` objects
          to unique string block IDs.
        
        Returns: A tuple containing two elements:

        0. `data` (dict): a dictionary describing this element's flow
           including any descendents if present.

        1. `max_id` (int): the maximum `flow_id` int allocated to this
           element or any of its descendents in the tree. The next unique
           integer is one more than this value.

        Note:

        * This method should not be called directly, only by a `RootFlow`
          element through the `flow_data` method, which understands how to
          initialise it properly.
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
        """
        Iterator performing an in-order traversal of the flow tree and
        yielding those elements that are of type `BlockFlow`.
        """
        for child in self.children:
            yield from child.get_block_flows()


class RootFlow(_FlowElement):
    """
    The root of a flow tree.

    Flow semantics: Traverses children in order, like a `GroupFlow`.
    """

    def __init__(self, children=()):
        """
        The root of a flow tree.
        
        Parameters:

        * `children` (iterable of `_FlowElement` objects): the initial
          children stored by the element.
        """
        super().__init__(
            children=children,
            # kwargs---to be included in eventual data upload, configuring
            # this block element in Qualtrics
            Type='Root', # element type
        )

    def flow_data(self, block_id_map):
        """
        Initialise the compilation of flow data for a Qualtrics upload.

        Parameters:

        * `block_id_map` (dict) a dictionary mapping `Block` objects to
          unique string block IDs. Passed throughout the compilation step
          so that each block flow element can look up the ID for its block.
        """
        data, max_id = self.compile(flow_id=1, block_id_map=block_id_map)
        data['Properties'] = {
            'Count': max_id,
            'RemovedFieldsets': [],
        }
        return data


class GroupFlow(_FlowElement):
    """
    A non-leaf element with multiple elements as children, which are
    traversed in sequence.
    """

    def __init__(self, description="Untitled Group", children=()):
        """
        Parameters:

        * `children` (iterable of `_FlowElement` objects): the initial
          children stored by the element.
        """
        super().__init__(
            children=children,
            # kwargs---to be included in eventual data upload, configuring
            # this block element in Qualtrics
            Type="Group",
            Description=description,
        )


class BlockRandomizerFlow(_FlowElement):
    """
    A non-leaf element, configurable such that the traversal will enter a
    random subset of one or more of its children, in a random order,
    depending on the participant.

    Examples of usage:

    * Can be used for selecting conditions in a randomised experiment (subset
      of size 1).

    * Can also for shuffling a sequence of blocks/flow-subtrees (subset of
      size n, where n is the number of children).
    """
    
    def __init__(self, n_samples, even_presentation=True, children=()):
        """
        Parameters:

        * `n_samples` (int):

        * `even_presentation` (bool, default `True`):

        * `children` (iterable of `_FlowElement` objects): the initial
          children stored by the element.
        """
        super().__init__(
            children=children,
            # kwargs---to be included in eventual data upload, configuring
            # this block element in Qualtrics
            Type="BlockRandomizer",
            SubSet=n_samples,
            EvenPresentation=even_presentation,
        )


class BlockFlow(_FlowElement):
    """
    A leaf element. Each `BlockFlow` element has a single `Block` attached.
    
    Traversal semantics: When the traversal hits this element, the
    participant is shown the attached block.
    """

    def __init__(self, block):
        """
        Parameters:

        * `block` (of class `Block`):

        Note:

        * Does not pass kwargs because it has its own compile method.
        * Does not pass children because it's a leaf node.
        """
        self.block = block

    def compile(self, flow_id, block_id_map):
        """
        Base case for the recursive compilation algorithm (see overriden
        method `_FlowElement.compile` for context).
        
        Implements a recursive compilation algorithm that takes a flow tree
        by the root and produces a single dictionary containing the entire
        flow tree structure, for uploading to Qualtrics through the API.

        Parameters:

        * `flow_id` (int): A unique integer to be allocated to this flow
          element, used to create its unique flow ID string.
        
        * `block_id_map` (dict) a global dictionary mapping `Block` objects
          to unique string block IDs.
        
        Returns: A tuple containing two elements:

        0. `data` (dict): a dictionary describing this element's flow
           including any descendents if present.

        1. `max_id` (int): the maximum `flow_id` int allocated to this
           element or any of its descendents in the tree. The next unique
           integer is one more than this value.

           (In this case, since this is a leaf node, it will just be the
           `flow_id` passed in as an argument.)

        Note:

        * This method should not be called directly, only by a `RootFlow`
          element through the `flow_data` method, which understands how to
          initialise it properly.
        """
        return (
            {
                # element data
                'FlowID': f"FL_{flow_id}",
                'Type': "Block",
                'ID': block_id_map[self.block], # block_id_map used here
                'Autofill': [],
            },
            flow_id,
        )
    
    def get_block_flows(self):
        """
        Yields self. Base case for the block flow generating traversal
        algorithm.
        """
        yield self
    
    def append_flow(self, flow):
        """
        Not available for leaf nodes. Overriding from base class to raise an
        error.
        """
        raise Exception("this type of flow has no children")
    
    def append_block(self, block):
        """
        Not available for leaf nodes. Overriding from base class to raise an
        error.

        Looking to set the block of this block flow element? Set it through
        the constructor.

        Looking to create a list of multiple blocks? Use a GroupFlow element
        instead.
        """
        raise Exception("this type of flow has no children")
    

class EndSurveyFlow(_FlowElement):
    """
    Another leaf element.

    Traversal semantics: When the traversal reaches this element, the survey
    ends for the participant, like if they had finished traversing the whole
    tree.
    """

    def __init__(self):
        """
        Note:

        * Does not pass children because it's a leaf node.
        """
        super().__init__(
            # kwargs---to be included in eventual data upload, configuring
            # this block element in Qualtrics
            Type="EndSurvey"
         )
    
    def append_flow(self, flow):
        """
        Not available for leaf nodes. Overriding from base class to raise an
        error.
        """
        raise Exception("this type of flow has no children")
    
    def append_block(self, block):
        """
        Not available for leaf nodes. Overriding from base class to raise an
        error.
        """
        raise Exception("this type of flow has no children")


