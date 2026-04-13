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

def beautify_code_smart(code):
    if not code: return ""
    
    # 1. 세미콜론 뒤 개행
    code = code.replace(';', ';\n')
    
    # 2. 콜론(:) 뒤 개행 및 들여쓰기 (문자열 내부 패턴 제외)
    # 정규표현식: 콜론 뒤에 공백이 있고, 그 뒤가 따옴표로 닫히지 않는 경우 등을 고려해야 함
    # 하지만 더 간단한 방법은 'if ', 'else:', 'elif ', 'while ', 'for ', 'def ', 'class ' 뒤의 콜론만 타겟팅하는 것임
    
    keywords = ['if', 'else', 'elif', 'while', 'for', 'def', 'class']
    lines = code.split('\n')
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        # 키워드로 시작하고 콜론으로 끝나는 구문 (한 줄로 붙어 있는 경우 분리)
        # 예: if age >= 8: print(...) -> if age >= 8:\n     print(...)
        
        found_kw = False
        for kw in keywords:
            if stripped.startswith(kw) and ':' in stripped:
                # 콜론 위치 찾기 (문자열 밖의 첫 콜론)
                # 단순화를 위해 줄 끝의 콜론이나 ': ' 패턴을 검사
                if ': ' in stripped:
                    parts = stripped.split(': ', 1)
                    new_lines.append(parts[0] + ':')
                    new_lines.append('     ' + parts[1])
                    found_kw = True
                    break
                elif stripped.endswith(':'):
                    # 이미 잘 분리된 경우
                    new_lines.append(line)
                    found_kw = True
                    break
        
        if not found_kw:
            new_lines.append(line)
            
    code = '\n'.join(new_lines)
    
    # 중복 개행 정리
    code = re.sub(r'\n+', '\n', code)
    
    return code.strip()

def fix_all_formatting_smart():
    items = Item.objects.all()
    count = 0
    for item in items:
        new_code = beautify_code_smart(item.answer_code)
        if new_code != item.answer_code:
            item.answer_code = new_code
            item.save()
            count += 1
            print(f"Smart Beautified: {item.title}")
            
    print(f"Total {count} items refined.")

if __name__ == "__main__":
    fix_all_formatting_smart()
