from locale import normalize
import os
import logging
import glob
from chardet import detect
import unicodedata
import re
from tqdm import tqdm

logging.basicConfig(level=logging.INFO,
                    filename="utils/update_tesserae_texts.log",
                    format='%(asctime)s %(message)s') # include timestamp)

## Helper functions

def get_encoding_type(file):
    with open(file, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']

def update_encoding_type(file, encoding=None):
    if not encoding:
        encoding = get_encoding_type(file)
    # add try: except block for reliability
    try: 
        with open(file, 'r', encoding=encoding) as f:
            contents = f.read()
        with open(file, 'w', encoding='utf-8') as f: 
            f.write(contents)
    except UnicodeDecodeError:
        print('Decode Error')
    except UnicodeEncodeError:
        print('Encode Error')

def process_greek(input_token):
    """
    Experimental!
    Fixes diacriticals that are not in the correct order in initial position
    TODO: Check diacriticals in other parts of word
    """
    input_token = input_token.strip()
    if unicodedata.category(input_token[0]).startswith('M'):
        input_token = unicodedata.normalize('NFD', input_token)
        cat_map = [(c, unicodedata.category(c)) for c in input_token]
        split_index = next((i for i, v in enumerate(cat_map) if not v[1].startswith('M')), -1)
        cat_map.insert(0, cat_map.pop(split_index))
        output_token = ''.join([item[0] for item in cat_map])
        output_token  = unicodedata.normalize('NFC', output_token )
    else:
        output_token = input_token
    return output_token

# Fix Latin content in Contra Apionem; cf. https://github.com/tesserae/tesserae/issues/123
text = 'temp/flavius_josephus.contra_apionem.part.2.tess'  
with open(text,'r') as f:
    contents = f.read()

start_idx = contents.find('<j. ap. 2.52>')
if start_idx == -1:
    pass
else:
    end_idx = contents.find('\n', contents.find('<j. ap. 2.113>')) + 1
    contents = contents[:start_idx] + contents[end_idx:]
    with open(text, 'w') as f:
        f.write(contents)
        logging.info(f'File {text}: Removed Latin sections')

# Fix misformatted citation in Arrian, Anabasis at <arr. an. 2.4.7>
text = 'temp/arrian.anabasis.part.2.tess'  
with open(text,'r') as f:
    contents = f.read()

start_idx = contents.find('<arr. an. 2.4.7>')
if start_idx == -1:
    pass
elif contents[start_idx-1] != ' ':
    pass
else:
    contents = contents[:start_idx-1] + '\n' + contents[start_idx:]
    with open(text, 'w') as f:
        f.write(contents)
        logging.info(f'File {text}: Fixed citation')        

# Fix misformatted citation in Arrian, Anabasis at <arr. an. 7.4.8>
text = 'temp/arrian.anabasis.part.7.tess'  
with open(text,'r') as f:
    contents = f.read()

start_idx = contents.find('<arr. an. 7.4.8>')
if start_idx == -1:
    pass
elif contents[start_idx-1] != ' ':
    pass
else:
    contents = contents[:start_idx-1] + '\n' + contents[start_idx:]
    with open(text, 'w') as f:
        f.write(contents)
        logging.info(f'File {text}: Fixed citation')    

# Update non-UTF-8 texts
texts = sorted(glob.glob('temp/*.tess'))
for text in tqdm(texts):
    print(f'Processing {text}')
    enc = get_encoding_type(text)
    if enc != 'utf-8':
        update_encoding_type(text, encoding=enc)
        print(f'ALERT {text}!')
        logging.info(f'File {text} converted from {enc} to utf-8')

    with open(text, 'r') as f:
        contents = f.read()
    
    # Update newline characters   
    if '\r\n' in contents:
        logging.info(f'File {text}: updated newline character to \n')
        contents = contents.replace('\r\n', '\n')

    # Normalize to NFC
    contents = unicodedata.normalize('NFC', contents)

    # Replace corrupted quotation marks
    contents = re.sub(r'â?', ' ', contents)

    # Validate citations; fix word openings
    inlines = contents.split('\n')
    outlines = []
    for line in inlines:
        if line:
            citation, content = line.split('>', 1)
            citation = f'{citation.strip()}>'
            content = content.strip()

            # Fix combining character order
            content_tokens = content.split()
            content = " ".join([process_greek(token) for token in content_tokens])
            
            outline = f'{citation}\t{content}'
            outlines.append(outline)
        else:
            outlines.append('')
    contents = "\n".join(outlines)
    
    with open(text, 'w') as f:
        f.write(contents)
