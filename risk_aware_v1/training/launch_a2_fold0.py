#!/usr/bin/env python3
"""Non-invasive launcher for frozen A2 fold-0 training."""
from __future__ import annotations
import importlib, inspect, os, sys
from os.path import join
from pathlib import Path
import torch

ROOT=Path('/root/autodl-tmp/nnunet_brats')
FREEZE=ROOT/'risk_aware_v1_a2_training'
PKG=FREEZE/'trainer_package'
sys.path.insert(0,str(FREEZE))
from trainer_package.nnUNetTrainerModDropAvailabilityMask import nnUNetTrainerModDropAvailabilityMask as FrozenTrainer
from batchgenerators.utilities.file_and_folder_operations import load_json
from nnunetv2.paths import nnUNet_preprocessed
from nnunetv2.utilities.dataset_name_id_conversion import maybe_convert_to_dataset_name
run_module=importlib.import_module('nnunetv2.run.run_training')

EXPECTED_A2=ROOT/'nnUNet_results/Dataset501_BraTS2023/nnUNetTrainerModDropAvailabilityMask__nnUNetPlans__3d_fullres/fold_0'

def frozen_get_trainer(dataset_name_or_id, configuration, fold, trainer_name='nnUNetTrainer', plans_identifier='nnUNetPlans', continue_training=False, device=torch.device('cuda')):
    assert str(dataset_name_or_id) in {'501','Dataset501_BraTS2023'}
    assert configuration=='3d_fullres' and int(fold)==0
    assert trainer_name=='nnUNetTrainerModDropAvailabilityMask'
    assert plans_identifier=='nnUNetPlans' and continue_training is False
    dataset_name=maybe_convert_to_dataset_name(int(dataset_name_or_id)) if not str(dataset_name_or_id).startswith('Dataset') else str(dataset_name_or_id)
    base=join(nnUNet_preprocessed,dataset_name)
    plans=load_json(join(base,plans_identifier+'.json')); plans['continue_training']=False
    dataset_json=load_json(join(base,'dataset.json'))
    trainer=FrozenTrainer(plans=plans,configuration=configuration,fold=int(fold),dataset_json=dataset_json,device=device)
    print('ACTUAL_TRAINER_CLASS='+trainer.__class__.__name__,flush=True)
    print('ACTUAL_TRAINER_SOURCE='+str(Path(inspect.getsourcefile(trainer.__class__)).resolve()),flush=True)
    print('ACTUAL_OUTPUT_DIRECTORY='+trainer.output_folder,flush=True)
    print('PATCH_SIZE='+str(list(trainer.configuration_manager.patch_size)),flush=True)
    print('BATCH_SIZE='+str(trainer.configuration_manager.batch_size),flush=True)
    print('NETWORK_INPUT_CHANNELS=8',flush=True)
    if Path(trainer.output_folder).resolve()!=EXPECTED_A2.resolve(): raise RuntimeError('Unexpected A2 output directory')
    return trainer

def main():
    source=Path(inspect.getsourcefile(FrozenTrainer)).resolve()
    if source.parent!=PKG.resolve(): raise RuntimeError(f'Frozen Trainer source mismatch: {source}')
    if EXPECTED_A2.exists() and any(EXPECTED_A2.iterdir()): raise RuntimeError('BLOCKED_BY_EXISTING_A2_RESULTS')
    print('TRAINER_CLASS=nnUNetTrainerModDropAvailabilityMask',flush=True)
    print('TRAINER_SOURCE='+str(source),flush=True)
    print('DATASET=Dataset501_BraTS2023',flush=True); print('FOLD=0',flush=True); print('CONFIGURATION=3d_fullres',flush=True)
    print('NETWORK_INPUT_CHANNELS=8',flush=True); print('OUTPUT_DIRECTORY='+str(EXPECTED_A2),flush=True)
    run_module.get_trainer_from_args=frozen_get_trainer
    run_module.run_training(dataset_name_or_id='501',configuration='3d_fullres',fold=0,trainer_class_name='nnUNetTrainerModDropAvailabilityMask',plans_identifier='nnUNetPlans',pretrained_weights=None,num_gpus=1,export_validation_probabilities=False,continue_training=False,only_run_validation=False,disable_checkpointing=False,val_with_best=False,device=torch.device('cuda'))

if __name__=='__main__':
    try: main()
    except Exception:
        import traceback; traceback.print_exc(); raise
