"""Verified model loading and read-only phase proposals. No simulator actuation.

Live execution is deliberately unavailable until retraining, contract review and
an independent clearance executor are validated. `actions` is always empty.
"""
import hashlib
import json
from pathlib import Path
import re
from typing import Optional
import numpy as np
import torch
from training.mappo.actor import ActorMLP
from services.planner.coordinator import RecoveryPlannerCoordinator
from services.control.contracts import dimensions, permanent_mask, phase_mapping, require_action_mask


def _build_permanent_mask(junction_cfg,max_action_slots):
    return permanent_mask(junction_cfg,max_action_slots)


def _build_policy_to_sumo_map(junction_cfg):
    return phase_mapping(junction_cfg)


class AEGISInferenceEngine:
    """Diagnostic proposal engine; loaded weights do not confer execution authority."""
    def __init__(self,checkpoint_path:Optional[str]=None,config_dir:Optional[str]=None,
                 use_planner=True,fail_closed=True,device='cpu',expected_checkpoint_sha256=None):
        self.device=device;self.use_planner=use_planner;self.fail_closed=fail_closed
        root=Path(__file__).resolve().parents[2]
        directory=Path(config_dir) if config_dir else root/'configs'
        self.obs_schema=json.loads((directory/'observation_schema.json').read_text())
        self.action_schema=json.loads((directory/'action_mapping.json').read_text())
        self.num_lanes,self.max_phases=dimensions(self.obs_schema)
        self.num_junctions=self.obs_schema['num_junctions']
        raw=self.action_schema['junctions']
        self.junction_list=list(raw.values()) if isinstance(raw,dict) else list(raw)
        if len(self.junction_list)!=self.num_junctions:raise ValueError('Junction count mismatch.')
        self._permanent_masks={j['alias']:permanent_mask(j,self.max_phases) for j in self.junction_list}
        self._policy_to_sumo={j['alias']:phase_mapping(j) for j in self.junction_list}
        self.obs_dim=self.num_lanes*3+self.max_phases+1+self.num_junctions*2
        self.actor=ActorMLP(self.obs_dim,self.max_phases,hidden_dim=64).to(device)
        self.checkpoint_loaded=False
        if checkpoint_path and Path(checkpoint_path).is_file():
            expected=expected_checkpoint_sha256
            if expected is None:
                manifest=json.loads((root/'manifests/model_manifest.json').read_text())
                expected=manifest.get('checkpoint_sha256')
                if manifest.get('status')!='TRAINED_FROZEN' or manifest.get('deployment_status','').startswith('BLOCKED'):
                    raise ValueError('Checkpoint deployment status is blocked; a compatible retrained artifact is required.')
            if not isinstance(expected,str) or re.fullmatch('[0-9a-fA-F]{64}',expected) is None:
                raise ValueError('Verified checkpoint SHA256 is required before loading.')
            digest=hashlib.sha256()
            with Path(checkpoint_path).open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
            if digest.hexdigest()!=expected.lower():raise ValueError('Checkpoint SHA256 mismatch; inference is blocked.')
            state=torch.load(checkpoint_path,map_location=device,weights_only=True)
            self.actor.load_state_dict(state.get('actor_state_dict',state))
            self.checkpoint_loaded=True
        elif fail_closed:
            raise FileNotFoundError('[AEGIS Security Fail-Closed] Verified checkpoint artifact is missing.')
        self.actor.eval()
        self.planner=RecoveryPlannerCoordinator(actor_model=self.actor,horizon_s=30,
            decision_dt=self.obs_schema.get('decision_interval_s',5)) if use_planner else None

    def _apply_permanent_mask(self,jid,caller_mask):
        if jid not in self._permanent_masks:raise ValueError('Unknown junction.')
        return require_action_mask(caller_mask,self._permanent_masks[jid])

    def _policy_to_sumo_phase(self,jid,policy_idx):
        value=self._policy_to_sumo[jid].get(policy_idx)
        if value is None:raise ValueError('Masked action has no SUMO phase mapping.')
        return value

    def step(self,observations,action_masks,run_id,state_revision,sim_time_s):
        """Return diagnostic proposals only, never safe-to-execute phase changes."""
        expected=set(self._permanent_masks)
        if set(observations)!=expected or set(action_masks)!=expected:
            raise ValueError('All configured junction observations and masks are required.')
        masks={jid:self._apply_permanent_mask(jid,action_masks[jid]) for jid in expected}
        for value in observations.values():
            array=np.asarray(value)
            if array.shape!=(self.obs_dim,) or not np.isfinite(array).all():raise ValueError('Invalid observation vector.')
        policies={};proposals={};unavailable={};records=[]
        plan=None
        if self.use_planner:
            plan=self.planner.plan(current_obs=observations,action_masks=masks,run_id=run_id,
                state_revision=state_revision,sim_time_s=sim_time_s)
            records=plan.get('candidate_evaluations',[])
        for jid,obs in observations.items():
            index=plan['first_action'] if plan is not None else self.actor.get_action(obs,masks[jid],deterministic=True)[0]
            if isinstance(index,bool) or not isinstance(index,(int,np.integer)) or not 0<=index<self.max_phases or not masks[jid][index]:
                unavailable[jid]='selected_action_masked';continue
            policies[jid]=int(index);proposals[jid]=self._policy_to_sumo_phase(jid,int(index))
        return {'actions':{},'proposed_sumo_phases':proposals,'policy_actions':policies,
            'unavailable':unavailable,'planner_records':records,'active_signals':{},
            'run_id':run_id,'based_on_revision':state_revision,'state_revision':state_revision,
            'sim_time_s':sim_time_s,'actuation_permitted':False,'requires_transition_validation':True,
            'mode':'READ_ONLY_PROPOSALS','checkpoint_loaded':self.checkpoint_loaded}
