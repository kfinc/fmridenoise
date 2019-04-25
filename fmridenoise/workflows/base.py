from ..interfaces.denoising import Denoise
from..interfaces.pipeline_selector import PipelineSelector

import fmridenoise
import os
import glob
from nipype import Node, Workflow, Function, MapNode
from nipype.interfaces import DataSink
import fmridenoise.interfaces as interfaces
from nipype import config
config.enable_debug_mode()
def init_fmridenoise_wf(bids_dir, derivatives=True,
                        # out_dir,
                        pipelines_paths = glob.glob(os.path.dirname(fmridenoise.__path__[0]) + "/pipelines/*"),
                        #, desc=None,
                        # ignore=None, force_index=None,
                        # model=None, participants=None,
                        base_dir=None, name='fmridenoise_wf'
                        ):
    wf = Workflow(name='fmridenoise', base_dir=None)
    # PipelineSelector
    # Inputs: pieline_path: Path - fulfilled - iterates over pipelines
    pipelineselector = Node(PipelineSelector(), name="PipelineSelector")
    pipelineselector.iterables = ('pipeline_path', pipelines_paths)
    # Outputs: pipeline: Dict

    # BidsLoader
    # Inputs: directory
    loading_bids = Node(interfaces.BIDSLoad(), name="BidsLoader")
    loading_bids.inputs.bids_dir = bids_dir
    loading_bids.inputs.derivatives = derivatives
    # Outputs: entities

    #BidsSelector
    # Inputs: bids_dir: Directory - fulfilled
    selecting_bids = Node(
        interfaces.BIDSSelect(),
        name='BidsSelector')
    selecting_bids.inputs.bids_dir = bids_dir
    selecting_bids.inputs.derivatives = derivatives
    # Outputs: fmri_preprocessed, confounds_raw, entities

    # Inputs: pipeline: Dict, conf_raw: File
    confound_prep = MapNode(interfaces.Confounds(), name="ConfoundPrep", iterfield=['conf_raw'])
    # Outputs: conf_prep: File

    # AnyDataDumper - Node that converts anything into string, debug purpose
    def data_dump(data, dump_path):
        with open(dump_path, 'a') as dump_file:
            dump_file.write(str(data))
        return data
    anydatadumper = Node(Function(input_names=['data', 'dump_path'], output_names=['data'], function=data_dump), name="AnyDataDumper")
    anydatadumper.inputs.dump_path = "/home/siegfriedwagner/Documents/results/data_conf"
    anydatadumper1 = Node(Function(input_names=['data', 'dump_path'], output_names=['data'], function=data_dump), name="AnyDataDumper1")
    anydatadumper1.inputs.dump_path = "/home/siegfriedwagner/Documents/results/data"
    # Datasink
    # datasink = Node(DataSink(), name="sink")
    # datasink.inputs.base_directory = "/home/siegfriedwagner/Documents/results"
    # datasink.inputs.contatiner = 'container'
    # General connections
    wf.connect([(loading_bids, selecting_bids, [('entities', 'entities')])])
    wf.connect([(selecting_bids, confound_prep, [('confounds_raw', 'conf_raw')])])
    wf.connect([(pipelineselector, confound_prep, [('pipeline', 'pipeline')])])
    wf.connect([(confound_prep, anydatadumper, [('conf_prep', 'data')])])
    wf.connect([(selecting_bids, anydatadumper1, [('confounds_raw', 'data')])])
    return wf
#prepconfounds = Node()

if __name__ == '__main__':

    bids_dir = os.path.join(os.path.dirname(fmridenoise.__path__[0]), 'bids_data/')
    wf = init_fmridenoise_wf(bids_dir)
    wf.write_graph("workflow_graph.dot")
    wf.run()