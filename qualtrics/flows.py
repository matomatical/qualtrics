"""
Qualtrics Virtual Survey Flows
==============================

**qualtrics.py** is a simple Python library for scripting the creation of
Qualtrics surveys. It provides convenient wrapper methods for accessing the
Qualtrics survey-definitions REST API, along with a convenient object-oriented
interface for building virtual surveys to load through that API.

See README for a more detailed overview.
"""


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


