import os
import sys
import django
import re

# 현재 경로를 sys.path에 추가
sys.path.append(os.getcwd())

# 장고 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
django.setup()

from courses.models import Item

def clean_data():
    items = Item.objects.all()
    count = 0
    for item in items:
        changed = False
        
        # 1. explain_html에서 중복되는 example-box 제거
        if '<div class=\'example-box\'>' in item.explain_html or '<div class="example-box">' in item.explain_html:
            # <div class='example-box'>...</div> 패턴 제거
            item.explain_html = re.sub(r'<div class=[\'"]example-box[\'"]>.*?</div>', '', item.explain_html, flags=re.DOTALL)
            changed = True
        
        # 2. answer_code에서 세미콜론(;) 후 개행 추가 (사용자 요청: 개행되서 보이도록)
        if ';' in item.answer_code and '\n' not in item.answer_code:
            item.answer_code = item.answer_code.replace(';', ';\n')
            changed = True
            
        # 3. 리터럴 \n 문자열 처리 (백슬래시 n을 실제 개행으로)
        if '\\n' in item.explain_html:
            item.explain_html = item.explain_html.replace('\\n', '<br>')
            changed = True
            
        if changed:
            item.save()
            count += 1
            print(f"Updated Item: {item.title}")
            
    print(f"Total {count} items cleaned and updated.")

if __name__ == "__main__":
    clean_data()
