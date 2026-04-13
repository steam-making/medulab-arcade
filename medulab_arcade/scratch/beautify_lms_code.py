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

def beautify_code(code):
    if not code: return ""
    
    # 1. 세미콜론 뒤 개행 (이미 되어 있을 수 있음)
    code = code.replace(';', ';\n')
    
    # 2. 콜론(:) 뒤 개행 및 들여쓰기 (if, else, for, while, def 등)
    # 단순히 ': '를 ':\n    '로 바꾸면 됨 (기존에 한 줄로 되어 있던 데이터 타겟)
    code = code.replace(': ', ':\n     ')
    
    # 3. else: 또는 elif: 가 줄바꿈 뒤에 바로 오도록 처리 (만약 ; 뒤에 붙어 있었다면)
    # (이미 1번에서 ; 뒤에 \n을 붙였으므로 어느 정도 처리가 됨)
    
    # 4. 중복 개행 정리
    code = re.sub(r'\n+', '\n', code)
    
    return code.strip()

def fix_all_formatting():
    items = Item.objects.all()
    count = 0
    for item in items:
        new_code = beautify_code(item.answer_code)
        if new_code != item.answer_code:
            item.answer_code = new_code
            item.save()
            count += 1
            print(f"Beautified Code for: {item.title}")
            
    print(f"Total {count} items' code beautified.")

if __name__ == "__main__":
    fix_all_formatting()
