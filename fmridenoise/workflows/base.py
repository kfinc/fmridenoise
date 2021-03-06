from nipype.pipeline import engine as pe

from fmridenoise.interfaces.bids import BIDSSelect, BIDSLoad, BIDSDataSink
from fmridenoise.interfaces.confounds import Confounds
from fmridenoise.interfaces.denoising import Denoise
from fmridenoise.interfaces.connectivity import Connectivity
from fmridenoise.interfaces.pipeline_selector import PipelineSelector
from nipype.interfaces import fsl, utility as niu, io as nio


import fmridenoise
import os
import glob

def init_fmridenoise_wf(bids_dir,
                        output_dir,
                        derivatives=True,
                        pipelines_paths=glob.glob(os.path.dirname(fmridenoise.__file__) + "/pipelines/*"),
                        #, desc=None,
                        # ignore=None, force_index=None,
                        # model=None, participants=None,
                        base_dir=None, name='fmridenoise_wf'
                        ):

    workflow = pe.Workflow(name='fmridenoise', base_dir=None)

    # 1) --- Selecting pipeline

    # Inputs: fulfilled
    pipelineselector = pe.Node(
       PipelineSelector(),
       name="PipelineSelector")
    pipelineselector.iterables = ('pipeline_path', pipelines_paths)
    # Outputs: pipeline

    # 2) --- Loading BIDS structure

    # Inputs: directory
    loading_bids = pe.Node(
        BIDSLoad(
            bids_dir=bids_dir, derivatives=derivatives
        ),
        name="BidsLoader")
    # Outputs: entities

    # 3) --- Selecting BIDS files

    # Inputs: entities
    selecting_bids = pe.MapNode(
        BIDSSelect(
            bids_dir=bids_dir,
            derivatives=derivatives
        ),
        iterfield=['entities'],
        name='BidsSelector')
    # Outputs: fmri_prep, conf_raw, entities

    # 4) --- Confounds preprocessing

    # Inputs: pipeline, conf_raw
    prep_conf = pe.MapNode(
        Confounds(
            output_dir=output_dir
        ),
        iterfield=['conf_raw'],
        name="ConfPrep")
    # Outputs: conf_prep

    # 5) --- Denoising

    # Inputs: conf_prep
    denoise = pe.MapNode(
        Denoise(
            output_dir=output_dir,
        ),
        iterfield=['fmri_prep', 'conf_prep'],
        name="Denoiser")
    # Outputs: fmri_denoised

    # 6) --- Connectivity estimation

    # Inputs: fmri_denoised
    parcellation_path = os.path.abspath(os.path.join(fmridenoise.__path__[0], "parcellation"))
    parcellation_path = glob.glob(parcellation_path + "/*")[0]

    connectivity = pe.MapNode(
        Connectivity(output_dir=output_dir, parcellation=parcellation_path),
        iterfield=['fmri_denoised'],
        name='ConnCalc')
    # Outputs: conn_mat

    # 7) --- Save derivatives
    # TODO: Fill missing in/out
    ds_confounds = pe.MapNode(BIDSDataSink(base_directory=output_dir, suffix='suff'),
                    iterfield=['in_file', 'entities'],
                    name="ds_confounds")
    ds_denoise = pe.MapNode(BIDSDataSink(base_directory=output_dir, suffix="denoise"),
                    iterfield=['in_file', 'entities'],
                    name="ds_denoise")
    ds_connectivity = pe.MapNode(BIDSDataSink(base_directory=output_dir, suffix="connect"),
                    iterfield=['in_file', 'entities'],
                    name="ds_connectivity")

# --- Connecting nodes

    workflow.connect([
        (loading_bids, selecting_bids, [('entities', 'entities')]),
        (selecting_bids, prep_conf, [('conf_raw', 'conf_raw')]),
        (pipelineselector, prep_conf, [('pipeline', 'pipeline')]),
        (selecting_bids, denoise, [('fmri_prep', 'fmri_prep')]),
        (prep_conf, denoise, [('conf_prep', 'conf_prep')]),
        (denoise, connectivity, [('fmri_denoised', 'fmri_denoised')]),
        (prep_conf, ds_confounds, [('conf_prep', 'in_file')]),
        (loading_bids, ds_confounds, [('entities', 'entities')]), 
        (denoise, ds_denoise, [('fmri_denoised', 'in_file')]),
        (loading_bids, ds_denoise, [('entities', 'entities')]),
        (connectivity, ds_connectivity, [('corr_mat', 'in_file')]),
        (loading_bids, ds_connectivity, [('entities', 'entities')])
    ])

    return workflow


# --- TESTING

if __name__ == '__main__':  # TODO Move parser to module __main__
    import argparse
    import os
    parser = argparse.ArgumentParser("Base workflow")
    parser.add_argument("--bids_dir")
    parser.add_argument("--output_dir")
    args = parser.parse_args()
    bids_dir = '/home/finc/Dropbox/Projects/fitlins/BIDS/'
    output_dir = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/'
    if args.bids_dir is not None:
        bids_dir = args.bids_dir
    if args.output_dir is not None:
        output_dir = args.output_dir
    wf = init_fmridenoise_wf(bids_dir,
                             output_dir,
                             derivatives=True)
    wf.run()
    wf.write_graph("workflow_graph.dot")