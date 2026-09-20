import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'take_snapshot.py'


def load_snapshot_module():
    sys.modules.pop('take_snapshot', None)
    spec = importlib.util.spec_from_file_location('take_snapshot', SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TakeSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.module = load_snapshot_module()

    def tearDown(self):
        sys.modules.pop('take_snapshot', None)

    def test_get_tour_details_uses_public_widgets_feed(self):
        payload = {
            'Data': {
                'Value': {
                    'currMdId': 3,
                    'deadlineDate': '2026-09-20T12:00:00Z',
                }
            }
        }

        with patch.object(self.module, 'get_json', return_value=payload) as get_json:
            details = self.module.get_tour_details()

        self.assertEqual(details, payload['Data']['Value'])
        get_json.assert_called_once_with('/feeds/home/widgets/1.json', params={'v': 2})

    def test_get_tour_details_requires_matchday_and_deadline(self):
        with patch.object(self.module, 'get_json', return_value={'Data': {'Value': {}}}):
            with self.assertRaisesRegex(RuntimeError, 'currMdId and deadlineDate'):
                self.module.get_tour_details()

    def test_main_saves_previous_matchday_after_snapshot_on_rollover(self):
        state = {'tracked_matchday': 2, 'before_taken': True, 'after_taken': False}
        tour = {'currMdId': 3, 'deadlineDate': '2099-01-01T12:00:00Z'}

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            with (
                patch.object(self.module, 'DATA_DIR', data_dir),
                patch.object(self.module, 'STATE_PATH', data_dir / 'state.json'),
                patch.object(self.module, 'get_tour_details', return_value=tour),
                patch.object(self.module, 'load_state', return_value=state),
                patch.object(self.module, 'get_matchday_players', return_value=[{'id': 1}]),
                patch.object(self.module, 'save_snapshot') as save_snapshot,
                patch.object(self.module, 'save_state') as save_state,
            ):
                self.module.main()

        save_snapshot.assert_called_once_with(2, 'after', [{'id': 1}])
        save_state.assert_called_once_with(
            {'tracked_matchday': 3, 'before_taken': False, 'after_taken': False}
        )


if __name__ == '__main__':
    unittest.main()
