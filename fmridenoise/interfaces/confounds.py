from fmridenoise.utils import confound_prep
### temporary solution #########################################################
# import sys
# sys.path.insert(0, '/home/kmb/Desktop/Neuroscience/Projects/' + \
#                    'confound_removal/nbraingroup/fmridenoise/utils')
# from confound_prep import prep_conf_df
################################################################################
import pandas as pd
import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename
from fmridenoise.utils.confound_prep import prep_conf_df
import fmridenoise

class ConfoundsInputSpec(BaseInterfaceInputSpec):
    pipeline = traits.Dict(
        desc='denoising pipeline',
        mandatory=True)
    conf_raw = File(
        exist=True,
        desc='confounds table',
        mandatory=True)

class ConfoundsOutputSpec(TraitedSpec):
    conf_prep = File(
        exists=True,
        desc="preprocessed confounds table")

class Confounds(BaseInterface):
    input_spec = ConfoundsInputSpec
    output_spec = ConfoundsOutputSpec

    def _run_interface(self, runtime):

        fname = self.inputs.conf_raw
        conf_df_raw = pd.read_csv(fname, sep='\t')

        # Preprocess confound table acording to pipeline
        conf_df_prep = prep_conf_df(conf_df_raw, self.inputs.pipeline)

        # Create new filename and save
        path, base, _ = split_filename(fname)
        fname_prep = f"{path}/{base}_{self.inputs.pipeline['name']}_prep.tsv"
        conf_df_prep.to_csv(fname_prep, sep='\t', index=False)
        self._results['conf_prep'] = fname_prep
        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        fname = self.inputs.conf_raw
        path, base, _ = split_filename(fname)
        fname_prep = f"{path}/{base}_{self.inputs.pipeline['name']}_prep.tsv"
        outputs["conf_prep"] = fname_prep

        return outputs

if __name__ == "__main__":
    import fmridenoise.utils.utils as ut

    path_to_json = os.path.join(os.path.dirname(fmridenoise.__path__[0]), 'fmridenoise', 'pipelines', '36_parameters_spikes.json')
    jdicto = ut.load_pipeline_from_json(path_to_json)
    #confpath = "/home/kmb/Desktop/Neuroscience/" + \
    #    "Projects/confound_removal/nbraingroup/fmridenoise/pipelines/sub-kb01_task-prlrew_desc-confounds_regressors.tsv"
    confpath = "/home/siegfriedwagner/Documents/git/fmridenoise/bids_data/derivatives/fmriprep/sub-01/func/sub-01_task-rhymejudgment_desc-confounds_regressors.tsv"
    cf = Confounds()
    cf.inputs.pipeline = jdicto
    cf.inputs.conf_raw = confpath
    result = cf.run()
    print(result.outputs)
