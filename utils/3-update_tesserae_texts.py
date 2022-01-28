import shutil

# Helper functions
def rmtree_check(path):
    try:
        shutil.rmtree(path)
    except:
        pass

## Delete existing text folder
rmtree_check('texts')

## Rename temp folder
shutil.move('temp', 'texts')
