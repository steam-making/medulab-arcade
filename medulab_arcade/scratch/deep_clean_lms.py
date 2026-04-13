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

def deep_clean_data():
    items = Item.objects.all()
    count = 0
    patterns = [
        r'<h4>예시 코드</h4>.*?<pre>.*?</pre>',
        r'<h4>예시 출력</h4>.*?<pre>.*?</pre>',
        r'<h4>예상 출력</h4>.*?<pre>.*?</pre>',
        r'<h5>예시 코드</h5>.*?<pre>.*?</pre>',
        r'<h5>예시 출력</h5>.*?<pre>.*?</pre>',
        # div 껍데기만 남은 경우 등 다양한 패턴 대응
        r'<div class=[\'"]example-box[\'"]>.*?</div>',
        # 태그 없이 텍스트 헤더만 있는 경우도 최소한으로 대응 (위험할 수 있으니 h4/h5 위주)
        r'<strong>예시 코드</strong>.*?<pre>.*?</pre>',
        r'<strong>예시 출력</strong>.*?<pre>.*?</pre>',
    ]
    
    for item in items:
        original = item.explain_html
        cleaned = original
        
        for p in patterns:
            cleaned = re.sub(p, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # 마지막으로 빈 태그들 정리 (선택적)
        cleaned = cleaned.strip()
        
        if cleaned != original:
            item.explain_html = cleaned
            item.save()
            count += 1
            print(f"Deep Cleaned: {item.title}")
            
    print(f"Total {count} items deep cleaned.")

if __name__ == "__main__":
    deep_clean_data()
