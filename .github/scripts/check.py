"""Run isolated desktop and website checks on Windows and Linux."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
temp_root = root / 'review-temp'
temp_root.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=temp_root) as temp:
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
               TEMP=temp, TMP=temp, TMPDIR=temp,
               MY_LITTLE_PET_SAVE_DIR=str(Path(temp) / 'save'),
               TEJA_SHOTS=str(Path(temp) / 'shots'))
    commands = [[sys.executable, f'teja-pet/tests/{test}.py'] for test in
                ['test_game', 'test_new_features', 'test_upgrade', 'test_profiles']]
    commands += [['node', f'my-little-pet-site/tests/{test}.test.mjs']
                 for test in ['engine', 'assets', 'seo']]
    for command in commands:
        print('Checking:', ' '.join(command), flush=True)
        subprocess.run(command, cwd=root, env=env, check=True, timeout=240)
