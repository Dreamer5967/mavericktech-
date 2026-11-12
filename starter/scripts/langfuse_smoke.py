"""Run only after credentials and langfuse are installed. Sends one test trace."""
from langfuse import get_client
lf=get_client()
with lf.start_as_current_observation(as_type='span',name='aegis-setup-smoke') as obs:
    obs.update(input={'mode':'SETUP_TEST'},output={'result':'trace_transport_only'})
lf.flush()
print('Check your project for aegis-setup-smoke. This is not an accuracy benchmark.')
