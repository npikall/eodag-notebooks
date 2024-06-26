import yaml
import getpass
from pathlib import Path

def make_subdirs():
    with open('notebooks/paths_temp.yml', 'r') as f:
        paths_template = yaml.safe_load(f)

    cwd = Path.cwd()

    paths = {}
    for key, val in paths_template.items():
        if 'USERDIR' in val:
            new_val = val.replace('USERDIR', str(cwd))
            final_val = str(Path(new_val))
        elif '~' in val:
            new_val = val.replace('~', str(Path.home()))
            final_val = str(Path(new_val))
        else:
            final_val = val
        paths[key] = final_val

    with open('notebooks/paths.yml', 'w') as outfile:
        yaml.dump(data=paths, stream=outfile)

    dirs = [paths[elem] for elem in ['serialize', 'post', 'shapefiles']]

    for d in dirs:
        dir_path = Path(d)
        if not dir_path.is_dir():
            dir_path.mkdir(parents=False, exist_ok=True)
            print(f'Directory created: {dir_path}')
        else:
            print(f'Directory already exists: {dir_path}')

def set_credentials():
    username = input('Username for CDSE (or q to quit):')
    if username.lower == 'q':
        return None
    pswd = getpass.getpass('Password for CDSE:')

    with open('notebooks/paths.yml', 'r') as f:
        paths = yaml.safe_load(f)
    output_pref = paths['download']

    new_yaml = {'cop_dataspace':{'priority': None,
                                'search': None,
                                'download': {'extract': None, 'outputs_prefix': output_pref},
                                'auth': {'credentials': {'username': username, 'password': pswd}}}}
    
    eodag_path = Path.home() / '.config'/'eodag'
    if not eodag_path.is_dir():
        eodag_path.mkdir(parents=True, exist_ok=True)
        print(f'Directory created: {eodag_path}')
    else:
        print(f'Directory already exists: {eodag_path}')

    eodag_config_file = eodag_path /'eodag.yml'

    with eodag_config_file.open(mode='w') as f:
        yaml.safe_dump(data=new_yaml, stream=f)

def main():
    make_subdirs()
    set_credentials()

if __name__ == '__main__':
    main()
