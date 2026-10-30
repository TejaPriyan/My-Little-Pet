"""Free Plus installer entry point. Keep its saves separate from the Free edition."""
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
os.environ.setdefault('MY_LITTLE_PET_SAVE_DIR',str(Path(os.environ.get('LOCALAPPDATA',Path.home()))/'MyLittlePetPlusTest'/'save'))
os.environ['MY_LITTLE_PET_EDITION']='Plus - Free'
from main import main
def check_install(report):
    """Headless packaged-app smoke check, using only a temporary profile."""
    import json,tempfile,traceback
    os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    result={'ok':False}
    try:
        with tempfile.TemporaryDirectory(dir=Path(report).resolve().parent) as tmp:
            os.environ['MY_LITTLE_PET_SAVE_DIR']=tmp
            from game import Game
            from save_system import default_data
            from supplies import TOYS
            g=Game();g.start_session(default_data('Mochi','Tester'),False);g.overlay=None
            for key in TOYS:
                g.pet.selected_toy=key;g.pet.energy=90;g.brain._start_play()
                for _ in range(30):g.brain.update(1/60);g.draw()
            g.shutdown();result={'ok':True,'toys':list(TOYS),'edition':'Plus Free'}
    except Exception:
        result['error']=traceback.format_exc()
    Path(report).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return 0 if result['ok'] else 1
if __name__=='__main__':
    sys.exit(check_install(sys.argv[2]) if len(sys.argv)>2 and sys.argv[1]=='--check-install' else main())
