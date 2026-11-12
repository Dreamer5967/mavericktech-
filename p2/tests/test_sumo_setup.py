import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from p2.setup_sumo import install, validate_plan


PLAN=json.loads((Path(__file__).resolve().parent.parent/'sumo_dependency_plan.json').read_text(encoding='utf-8'))


class SumoSetupGuards(unittest.TestCase):
    def test_only_approved_four_package_versions_are_accepted(self):
        modified=copy.deepcopy(PLAN)
        modified['packages'].append({'name':'torch','version':'9','sha256':'0'*64})
        with self.assertRaises(ValueError):
            validate_plan(modified)

    def test_changed_version_is_rejected(self):
        modified=copy.deepcopy(PLAN)
        modified['packages'][0]['version']='1.28.0'
        with self.assertRaises(ValueError):
            validate_plan(modified)

    def test_missing_hash_is_rejected(self):
        modified=copy.deepcopy(PLAN)
        modified['packages'][0]['sha256']='unverified'
        with self.assertRaises(ValueError):
            validate_plan(modified)

    def test_without_approval_no_installer_or_process_can_run(self):
        with patch.dict(os.environ,{},clear=True),patch('p2.setup_sumo.subprocess.run') as run:
            with self.assertRaisesRegex(RuntimeError,'approval'):
                install(PLAN)
            run.assert_not_called()


if __name__=='__main__':
    unittest.main()
