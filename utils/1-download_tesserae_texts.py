import os
import shutil
from git import Repo
from pprint import pprint

# Helper functions
def rmtree_check(path):
    try:
        shutil.rmtree(path)
    except:
        pass

def mkdir_check(path):
    rmtree_check(path)
    os.makedirs(path)

## Clone repo
# TODO: Is there a way to only get the texts folder on first pass?
rmtree_check('temp_repo')

# TODO: Add progress bar
Repo.clone_from('https://github.com/tesserae/tesserae','temp_repo');

## Extract texts folder
rmtree_check('temp_texts')

shutil.copytree('temp_repo/texts/grc', 'temp_texts')

rmtree_check('temp_repo')

##Remove Tesserae combined texts
contents = [file for file in sorted(os.listdir('temp_texts'))]

for content in contents:
    if content.endswith('.tess') and content.replace('.tess','') in contents:
        os.remove(f'temp_texts/{content}')

## Move texts to same folder and clean up
# https://stackoverflow.com/a/45704795
mkdir_check('temp')
for root, dirs, files in os.walk('temp_texts', topdown=False):
    for file in files:
        try:
            shutil.move(os.path.join(root, file), 'temp')
        except OSError:
            print(f'Error with {os.path.join(root, file)}...')
            pass

rmtree_check('temp_texts')
