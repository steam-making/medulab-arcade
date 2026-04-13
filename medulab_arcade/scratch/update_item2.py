import os
import sys
import django

# 현재 경로를 sys.path에 추가
sys.path.append(os.getcwd())

# 장고 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
django.setup()

from courses.models import Item

try:
    i = Item.objects.get(id=2)
    i.title = "예제2: 여러 줄 출력하기"
    i.explain_html = "<h3>예제2: 여러 줄 출력하기</h3><p>print()를 여러 번 쓰면 여러 줄로 출력됩니다.</p>"
    # 세미콜론을 포함하되 개행하여 가독성 확보
    i.answer_code = 'print("오늘의 시간표");\nprint("1교시: 영어");\nprint("2교시: 수학")'
    i.expected_output = "오늘의 시간표\n1교시: 영어\n2교시: 수학"
    i.save()
    print("Item 2 updated with semicolons and newlines.")
except Exception as e:
    print(f"Error updating item 2: {e}")
