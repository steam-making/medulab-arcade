import os
import sys
import django

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medulab_arcade.settings")
django.setup()

from courses.models import LearningProgram, Chapter, Item

def run():
    try:
        program = LearningProgram.objects.get(id=8)
    except LearningProgram.DoesNotExist:
        print("Course ID 8 not found.")
        return

    # Find or create "05 사전테스트" chapter
    chapter, created = Chapter.objects.get_or_create(
        program=program,
        number=5, # assuming 5 based on "05"
        defaults={'title': '사전테스트'}
    )
    if not created:
        chapter.title = '사전테스트'
        chapter.save()

    # Problem 1
    Item.objects.update_or_create(
        chapter=chapter,
        number=1,
        key="pretest_1",
        defaults={
            'title': '1. 정수 제곱근 (반올림)',
            'item_type': 'problem',
            'explain_html': '''<p><strong>제목 설명:</strong></p>
<p>음수가 아닌 정수 n이 주어짐(0≤n≤10<sup>9</sup>), N의 산술 제곱근을 계산하고 반환하면 결과를 가장 가까운 정수로 반올림해야합니다. 즉, 가장 큰 정수 x를 찾으십시오. x<sup>2</sup>≤n。</p>
<p><strong>예:</strong></p>
<p>입력 4, 출력 2 (때문에 2² = 4), 정수 x의 제곱근은 2 입니다.</p>
<p>입력 8, 출력 2 (때문에 2² = 4 &lt; 8 과 3² = 9 &gt; 8), 따라서 가장 큰 정수 x는 2 입니다.</p>
<p><strong>입력 설명:</strong><br>음수가 아닌 정수 n(0 ≤ n ≤ 10<sup>9</sup>)</p>
<p><strong>출력 설명:</strong><br>N의 산술 제곱근의 정수 부분을 나타내는 정수</p>''',
            'example_input': '8',
            'expected_output': '2',
        }
    )

    # Problem 2
    Item.objects.update_or_create(
        chapter=chapter,
        number=2,
        key="pretest_2",
        defaults={
            'title': '2. 가장 긴 지속적으로 증가하는 하위 시퀀스',
            'item_type': 'problem',
            'explain_html': '''<p><strong>제목 설명:</strong></p>
<p>정수 nums의 배열이 주어지면 가장 긴 연속 증가 서브 시퀀스 (LCS) 의 길이를 찾습니다. 지속적으로 증가하는 하위 시퀀스는 다음과 같이 정의됩니다. 요소는 원래 배열에 지속적으로 위치하며 엄격하게 증가합니다 (예: 인접한 요소가 만족 nums[i] &lt; nums[i+1]).</p>
<p><strong>입력 설명:</strong><br>배열 nums를 나타 내기 위해 공백으로 구분 된 정수 줄을 입력하십시오 (배열 길이가 초과하지 않음 10<sup>4</sup>, 요소 범위는 -10<sup>9</sup>에서 10<sup>9</sup>)</p>
<p><strong>출력 설명:</strong><br>가장 긴 연속 증가 하위 시퀀스의 길이를 나타내는 정수를 출력</p>''',
            'example_input': '1 3 5 4 7',
            'expected_output': '3',
        }
    )

    # Problem 3
    Item.objects.update_or_create(
        chapter=chapter,
        number=3,
        key="pretest_3",
        defaults={
            'title': '3. 完美数对 (완전한 숫자 쌍)',
            'item_type': 'problem',
            'explain_html': '''<p><strong>제목 설명:</strong></p>
<p>주어진 두 양의 정수 m 및 n (1 ≤ m ≤ n ≤ 10<sup>6</sup>), 다음 조건을 만족하는 간격 [m, n] 에서 모든 양의 정수의 쌍 (a, b) 을 계산합니다.</p>
<ol>
<li>엄격하게 증가: a &lt; b</li>
<li>제품은 완전한 제곱 번호입니다: a × b 완전히 정사각형입니다 (예: 정수 k가 있습니다. a × b = k²)</li>
</ol>
<p><strong>입력 설명:</strong><br>통계적 간격 범위를 나타내는 공간으로 구분 된 두 개의 정수 m과 n을 입력하십시오.</p>
<p><strong>출력 설명:</strong><br>조건을 만족하는 쌍 (a, b) 의 총 수를 나타내는 정수를 출력</p>
<p><strong>설명의 예:</strong><br>범위 [1, 10] 에서 조건을 만족하는 숫자 쌍은 다음과 같습니다.<br>
(1, 4)：1 × 4 = 4 = 2²<br>
(1, 9)：1 × 9 = 9 = 3²<br>
(2, 8)：2 × 8 = 16 = 4²<br>
(4, 9)：4 × 9 = 36 = 6²</p>''',
            'example_input': '1 10',
            'expected_output': '4',
        }
    )

    # Problem 4
    Item.objects.update_or_create(
        chapter=chapter,
        number=4,
        key="pretest_4",
        defaults={
            'title': '4. 최단 경로 문제 (장애물이있는 가중 그리드)',
            'item_type': 'problem',
            'explain_html': '''<p><strong>제목 설명:</strong></p>
<p>주어진 m×n 각 셀은 무게 (양의 정수 또는 -1) 를 가지며, 여기서 -1 의 무게를 가진 셀은 장애물 (통과 불가) 을 나타낸다. 왼쪽 상단 모서리 (0, 0) 에서 시작하여 매번 오른쪽 또는 아래로 이동하여 오른쪽 하단 모서리에 도달 할 수 있습니다. (m-1, n-1) 최단 경로 무게 (경로는 장애물을 통과 할 수 없음). 그렇지 않은 경우 반환 -1.</p>
<p><strong>입력 설명:</strong><br>두 개의 정수 입력 m 과 n (1 ≤ m, n ≤ 100), 그리드의 행과 열 수를 나타내는 공간으로 구분<br>
다음 m행: 각 행 n 공백으로 구분 된 정수, 그리드에서 각 셀의 가중치를 나타냅니다. 여기서 -1 은 장애물을 나타내고 다른 양의 정수는 법적 가중치입니다.</p>
<p><strong>출력 설명:</strong><br>왼쪽 상단 모서리에서 오른쪽 하단 모서리까지의 최단 경로 가중치를 나타내는 정수를 출력하고 도달하지 않은 경우 출력 -1</p>''',
            'example_input': '3 3\n1 2 3\n4 5 -1\n6 7 8',
            'expected_output': '23',
        }
    )

    # Problem 5
    Item.objects.update_or_create(
        chapter=chapter,
        number=5,
        key="pretest_5",
        defaults={
            'title': '5. 다차원 콘테스트 순위 (그룹화 및 타임 스탬프 포함)',
            'item_type': 'problem',
            'explain_html': '''<p><strong>제목 설명:</strong></p>
<p>국제 대회에서 참가자는 국가별로 A, B, C 및 D의 네 그룹으로 나뉩니다. 각 플레이어의 정보는 다음과 같습니다.</p>
<ul>
<li>입력 번호: 6 자리 국가 코드 형식의 7 자리 문자열 (예: 국가 A 플레이어 번호는 A000001 부터 시작)</li>
<li>점수: 0-1000 사이의 정수</li>
<li>제출 타임 스탬프: 두 번째로 정확한 정수 (1684321567 인 경우)</li>
</ul>
<p><strong>Collation (높은 우선 순위):</strong></p>
<ol>
<li>국가 우선 순위: 그룹화 순서 A &gt; B &gt; C &gt; D (즉, 국가 A의 선수 순위는 항상 다른 국가보다 높습니다)</li>
<li>점수의 하강 순서: 같은 국가 내에서 높은 점수를 가진 사람들이 1 위를 차지합니다.</li>
<li>제출 시간의 오름차순: 점수가 동일하고 국가가 동일하면 이전 제출 시간 (더 작은 타임 스탬프) 을 가진 플레이어가 1 위를 차지합니다.</li>
<li>엔트리 번호의 오름차순: 위의 조건이 동일하면 개별 번호의 오름차순으로 정렬됩니다 (예: 000001 &lt; 000002)</li>
</ol>
<p><strong>입력 설명:</strong><br>정수 입력 n (1 ≤ n ≤ 10<sup>5</sup>), 플레이어 수를 나타냅니다.<br>
다음 n 행의 각 줄에는 국가 코드 (A/B/C/D), 개인 번호 (6 자리, 선행 0 없음), 점수 (정수), 타임 스탬프 (정수), 공백으로 구분 된 네 가지 정보가 포함됩니다. (예: A 000001 950 1684321567)</p>
<p><strong>출력 설명:</strong><br>순위 (A000001 인 경우), 각 숫자에 대해 하나의 행으로 모든 플레이어의 전체 항목 번호를 높음</p>
<p><strong>설명의 예:</strong><br>Country A 플레이어는 동일한 A000002 및 A000001 점수를 가지고 있지만 이전 제출보다 더 높은 A000002 등급입니다.<br>
국가 B는 B000001 점수가 높지만 국가 A보다 국가 우선 순위가 낮아 최하위입니다.</p>''',
            'example_input': '3\nA 000001 900 1684321567\nB 000001 950 1684321568\nA 000002 900 1684321566',
            'expected_output': 'A000002\nA000001\nB000001',
        }
    )
    print("Successfully added 5 pre-test problems to Course ID 8, Chapter 5.")

if __name__ == '__main__':
    run()