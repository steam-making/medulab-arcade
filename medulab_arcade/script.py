import re, codecs
with codecs.open('e:/making_project/medulab_arcade/typing_practice/templates/typing_practice/practice_text.html', 'r', 'utf-8') as f:
    text = f.read()

match = re.search(r'(?s)<script>(.*?)</script>', text)
if match:
    script = match.group(1)
    script = re.sub(r'\"\{\{.*?\}\}\"', '\"x\"', script)
    script = re.sub(r'\{\{.*?\}\}', '\"x\"', script)
    with codecs.open('check.js', 'w', 'utf-8') as out:
        out.write(script)
