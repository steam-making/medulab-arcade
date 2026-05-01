from html import escape

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Chapter, Item, LearningProgram, ProgramType


PROGRAM_TYPE_NAME = "대회 대비"


def html_paragraphs(*lines):
    return "".join(f"<p>{escape(line)}</p>" for line in lines if line)


def html_with_code(lines, code=""):
    html = html_paragraphs(*lines)
    if code:
        html += f"<pre><code>{escape(code.strip())}</code></pre>"
    return html


def coding(title, explain_lines, hint, answer_code, example_input="", expected_output=""):
    return {
        "title": title,
        "explain_html": html_paragraphs(*explain_lines),
        "hint": hint,
        "answer_code": answer_code.strip(),
        "example_input": example_input,
        "expected_output": expected_output,
        "item_type": "problem",
    }


def objective(title, explain_lines, options, answer, hint="", explanation="", stem_code=""):
    return {
        "title": title,
        "explain_html": html_with_code(explain_lines, stem_code),
        "hint": hint,
        "answer_code": answer.strip().upper(),
        "example_input": "\n".join(options),
        "expected_output": explanation,
        "item_type": "objective",
    }


def example(title, explain_lines, answer_code, expected_output, hint=""):
    return {
        "title": title,
        "explain_html": html_paragraphs(*explain_lines),
        "hint": hint,
        "answer_code": answer_code.strip(),
        "example_input": "",
        "expected_output": expected_output,
        "item_type": "example",
    }


def chapter(title, content, items):
    return {"title": title, "content": content, "items": items}


def build_python_a_data():
    items_20 = [
        objective(
            "실전 A-01: len 함수 결과",
            ["문자열 'arcade'의 길이를 구한 값으로 맞는 것을 고르세요."],
            ["A. 5", "B. 6", "C. 7", "D. 8"],
            "B",
            explanation="'arcade'는 6글자이므로 정답은 B입니다.",
        ),
        objective(
            "실전 A-02: 홀수 판별식",
            ["정수 n이 홀수인지 판별하는 조건식으로 가장 알맞은 것을 고르세요."],
            ["A. n % 2 == 0", "B. n // 2 == 1", "C. n % 2 == 1", "D. n / 2 == 1"],
            "C",
            explanation="홀수 판별은 나머지가 1인지 확인하면 됩니다.",
        ),
        objective(
            "실전 A-03: 리스트 첫 요소",
            ["nums = [4, 8, 9] 일 때 첫 번째 요소를 꺼내는 코드를 고르세요."],
            ["A. nums[0]", "B. nums[1]", "C. nums[-1]", "D. nums(0)"],
            "A",
            explanation="파이썬 리스트 인덱스는 0부터 시작합니다.",
        ),
        objective(
            "실전 A-04: 반복 횟수",
            ["for i in range(3): 에서 반복되는 횟수는 몇 번인지 고르세요."],
            ["A. 2번", "B. 3번", "C. 4번", "D. 5번"],
            "B",
            explanation="range(3)은 0, 1, 2 총 3번 반복됩니다.",
        ),
        objective(
            "실전 A-05: 문자열 대문자 변환",
            ["문자열 text를 모두 대문자로 바꾸는 메서드를 고르세요."],
            ["A. text.big()", "B. text.upper()", "C. text.top()", "D. text.cap()"],
            "B",
            explanation="대문자 변환은 upper() 메서드를 사용합니다.",
        ),
        coding(
            "실전 A-06: 세 수의 합",
            ["공백으로 구분된 정수 세 개가 입력되면 합을 출력하세요."],
            "split으로 나누고 int로 바꾼 뒤 더하세요.",
            "nums = input().split()\nprint(int(nums[0]) + int(nums[1]) + int(nums[2]))",
            "3 4 5",
            "12",
        ),
        coding(
            "실전 A-07: 짝수만 한 줄씩 출력",
            ["정수 N이 입력되면 1부터 N까지의 짝수를 한 줄에 하나씩 출력하세요."],
            "반복문 안에서 i % 2 == 0 인지 확인하세요.",
            "n = int(input())\nfor i in range(1, n + 1):\n    if i % 2 == 0:\n        print(i)",
            "6",
            "2\n4\n6",
        ),
        coding(
            "실전 A-08: 단어 뒤집기",
            ["문자열이 입력되면 거꾸로 뒤집어 출력하세요."],
            "슬라이싱 [::-1]을 사용해 보세요.",
            "text = input().strip()\nprint(text[::-1])",
            "python",
            "nohtyp",
        ),
        coding(
            "실전 A-09: 가장 큰 수 찾기",
            ["공백으로 구분된 정수 네 개가 입력되면 가장 큰 수를 출력하세요."],
            "현재 최대값을 저장하며 비교하세요.",
            "nums = [int(x) for x in input().split()]\nmax_value = nums[0]\nfor n in nums:\n    if n > max_value:\n        max_value = n\nprint(max_value)",
            "8 3 14 5",
            "14",
        ),
        coding(
            "실전 A-10: 모음 개수",
            ["영문 문자열이 입력되면 모음 a, e, i, o, u 의 개수를 출력하세요."],
            "문자를 하나씩 검사하세요.",
            "text = input().strip()\ncount = 0\nfor ch in text:\n    if ch in 'aeiouAEIOU':\n        count += 1\nprint(count)",
            "banana",
            "3",
        ),
        coding(
            "실전 A-11: 1부터 N까지 합",
            ["정수 N이 입력되면 1부터 N까지의 합을 출력하세요."],
            "합계를 저장하는 변수를 만드세요.",
            "n = int(input())\ntotal = 0\nfor i in range(1, n + 1):\n    total += i\nprint(total)",
            "5",
            "15",
        ),
        coding(
            "실전 A-12: 공백 제거",
            ["문장이 입력되면 공백을 모두 제거한 문자열을 출력하세요."],
            "replace를 떠올려 보세요.",
            "text = input()\nprint(text.replace(' ', ''))",
            "a b c d",
            "abcd",
        ),
        coding(
            "실전 A-13: 3의 배수 개수",
            ["공백으로 구분된 정수 다섯 개가 입력되면 3의 배수 개수를 출력하세요."],
            "하나씩 검사하며 개수를 세세요.",
            "nums = input().split()\ncount = 0\nfor x in nums:\n    if int(x) % 3 == 0:\n        count += 1\nprint(count)",
            "3 4 6 7 9",
            "3",
        ),
        coding(
            "실전 A-14: 별 계단 거꾸로 출력",
            ["정수 N이 입력되면 N개 별부터 1개 별까지 줄여 가며 출력하세요."],
            "range의 감소를 이용하세요.",
            "n = int(input())\nfor i in range(n, 0, -1):\n    print('*' * i)",
            "3",
            "***\n**\n*",
        ),
        coding(
            "실전 A-15: 두 문자열 이어 붙이기",
            ["첫 줄과 둘째 줄에 문자열이 하나씩 입력되면 붙여서 출력하세요."],
            "문자열 더하기를 사용하세요.",
            "a = input().strip()\nb = input().strip()\nprint(a + b)",
            "hello\npython",
            "hellopython",
        ),
        coding(
            "실전 A-16: 리스트 평균",
            ["공백으로 구분된 정수 다섯 개가 입력되면 평균을 출력하세요."],
            "합계를 개수로 나누면 됩니다.",
            "nums = [int(x) for x in input().split()]\nprint(sum(nums) / len(nums))",
            "10 20 30 40 50",
            "30.0",
        ),
        coding(
            "실전 A-17: 첫 글자와 마지막 글자",
            ["문자열이 입력되면 첫 글자와 마지막 글자를 공백으로 구분해 출력하세요."],
            "인덱스 0과 -1을 사용하세요.",
            "text = input().strip()\nprint(text[0], text[-1])",
            "coding",
            "c g",
        ),
        coding(
            "실전 A-18: 점수 등급",
            ["점수가 입력되면 90 이상 A, 80 이상 B, 70 이상 C, 나머지 D를 출력하세요."],
            "큰 구간부터 비교하세요.",
            "score = int(input())\nif score >= 90:\n    print('A')\nelif score >= 80:\n    print('B')\nelif score >= 70:\n    print('C')\nelse:\n    print('D')",
            "85",
            "B",
        ),
        coding(
            "실전 A-19: 중복 없는 단어 출력",
            ["공백으로 구분된 단어들이 입력되면 처음 나온 순서대로 중복 없이 출력하세요."],
            "결과 리스트에 없을 때만 추가하세요.",
            "words = input().split()\nresult = []\nfor word in words:\n    if word not in result:\n        result.append(word)\nprint(' '.join(result))",
            "a b a c b",
            "a b c",
        ),
        coding(
            "실전 A-20: 숫자 문자열 각 자리 합",
            ["숫자로만 이루어진 문자열이 입력되면 각 자리 숫자의 합을 출력하세요."],
            "문자 하나씩 int로 바꾸면 됩니다.",
            "text = input().strip()\ntotal = 0\nfor ch in text:\n    total += int(ch)\nprint(total)",
            "50231",
            "11",
        ),
    ]

    return [
        chapter(
            "대회 구조와 객관식 워밍업",
            "Python A 기본 규칙과 가이드 예시 객관식을 선택형으로 먼저 익힙니다.",
            [
                example(
                    "Python A 대회 구성 이해",
                    [
                        "Python A는 12세 이하 부문입니다.",
                        "가이드 기준으로 90분 동안 진행되며, 기본 입력/출력과 반복문, 조건문이 중요합니다.",
                    ],
                    "print('Python A Ready')",
                    "Python A Ready",
                ),
                objective(
                    "가이드 객관식 1: 이진수 숫자",
                    ["컴퓨터의 이진수 체계에 사용되는 두 숫자를 고르세요."],
                    ["A. 0, 1", "B. 0, 2", "C. 1, 2", "D. 1, 10"],
                    "A",
                    explanation="이진수는 0과 1만 사용합니다.",
                ),
                objective(
                    "가이드 객관식 2: 튜플에서 'A' 꺼내기",
                    ["y = ('A', 'B', 'C', 'D') 일 때 'A'를 반환하는 문장을 고르세요."],
                    ["A. y[-3]", "B. y[1]", "C. y[0]", "D. y[4]"],
                    "C",
                    explanation="튜플의 첫 요소는 인덱스 0입니다.",
                ),
                objective(
                    "가이드 객관식 3: 슬라이싱 결과",
                    ["l = [1, 2, 3, 4, 5, 6, 7, 8, 9] 일 때 l[2:4] 결과를 고르세요."],
                    ["A. [2, 3]", "B. [1, 2, 3, 4]", "C. [3, 4]", "D. [2, 3, 4]"],
                    "C",
                    explanation="슬라이싱 끝 인덱스는 포함되지 않으므로 [3, 4] 입니다.",
                ),
                objective(
                    "가이드 객관식 4: continue 실행 결과",
                    ["'Python'을 순회하며 'n'일 때 continue 하는 코드의 결과를 고르세요."],
                    ["A. []", "B. ['P', 'y', 't', 'h']", "C. ['P', 'y', 't', 'h', 'o']", "D. ['P', 'y', 't', 'h', 'o', 'n']"],
                    "C",
                    explanation="'n'만 건너뛰므로 ['P', 'y', 't', 'h', 'o']가 남습니다.",
                    stem_code="result = []\nfor ch in 'Python':\n    if ch == 'n':\n        continue\n    result.append(ch)\nprint(result)",
                ),
            ],
        ),
        chapter(
            "가이드 예시 프로그래밍 5문제",
            "공식 가이드의 Python A 예시 문제를 그대로 연습합니다.",
            [
                coding(
                    "예시 1: 소문자를 대문자로 바꾸기",
                    ["소문자 한 글자가 주어지면 해당 대문자를 출력하세요."],
                    "upper()를 사용하세요.",
                    "ch = input().strip()\nprint(ch.upper())",
                    "a",
                    "A",
                ),
                coding(
                    "예시 2: N x N 별 사각형",
                    ["양의 정수 N(4 < N < 40)이 입력되면 N행 N열 별표를 출력하세요."],
                    "반복문 안에서 '*' * n 을 출력하세요.",
                    "n = int(input())\nfor _ in range(n):\n    print('*' * n)",
                    "5",
                    "*****\n*****\n*****\n*****\n*****",
                ),
                coding(
                    "예시 3: 합이 정확히 N이 되는 두 수 조합 개수",
                    ["첫 줄에 N, 둘째 줄에 쉼표로 구분된 서로 다른 양의 정수들이 주어집니다.", "서로 다른 두 수를 골라 합이 N이 되는 조합 개수를 출력하세요."],
                    "i < j 인 모든 쌍을 검사하세요.",
                    "target = int(input())\nnums = input().strip().split(',')\ncount = 0\nfor i in range(len(nums)):\n    for j in range(i + 1, len(nums)):\n        if int(nums[i]) + int(nums[j]) == target:\n            count += 1\nprint(count)",
                    "6\n1,2,3,4,5",
                    "2",
                ),
                coding(
                    "예시 4: 369 통과 게임에서 처음 틀린 아이 찾기",
                    ["첫 줄에 아이 수 N, 둘째 줄에 말한 값들이 쉼표로 주어집니다.", "3이 포함되거나 3의 배수인 수는 0으로 말해야 합니다."],
                    "turn + 1 이 실제 말해야 하는 수입니다.",
                    "n = int(input())\nspoken = input().strip().split(',')\nfor turn in range(len(spoken)):\n    number = turn + 1\n    expected = str(number)\n    if number % 3 == 0 or '3' in str(number):\n        expected = '0'\n    if spoken[turn].strip() != expected:\n        print((turn % n) + 1)\n        break",
                    "3\n1,2,0,4,5,6,7",
                    "3",
                ),
                coding(
                    "예시 5: 1개~3개씩 물건 옮기기 경우의 수",
                    ["N개의 물건을 한 번에 1개, 2개, 3개씩 옮길 수 있을 때 모든 방법의 수를 출력하세요."],
                    "dp[n] = dp[n-1] + dp[n-2] + dp[n-3] 입니다.",
                    "n = int(input())\nif n == 1:\n    print(1)\nelif n == 2:\n    print(2)\nelif n == 3:\n    print(4)\nelse:\n    dp = [0] * (n + 1)\n    dp[1] = 1\n    dp[2] = 2\n    dp[3] = 4\n    for i in range(4, n + 1):\n        dp[i] = dp[i - 1] + dp[i - 2] + dp[i - 3]\n    print(dp[n])",
                    "3",
                    "4",
                ),
            ],
        ),
        chapter(
            "Python A 추가 실전 연습",
            "가이드 예시와 비슷한 난이도의 추가 문제입니다.",
            [
                coding(
                    "추가 1: 대문자 문자열 만들기",
                    ["영문 소문자 문자열이 입력되면 모두 대문자로 바꾸어 출력하세요."],
                    "upper()를 사용하세요.",
                    "text = input().strip()\nprint(text.upper())",
                    "python",
                    "PYTHON",
                ),
                coding(
                    "추가 2: 오른쪽 삼각형 별 출력",
                    ["정수 N이 입력되면 1개부터 N개까지 별을 출력하세요."],
                    "반복문으로 별 개수를 늘리세요.",
                    "n = int(input())\nfor i in range(1, n + 1):\n    print('*' * i)",
                    "4",
                    "*\n**\n***\n****",
                ),
                coding(
                    "추가 3: 정확히 목표가 되는 세 수 조합 개수",
                    ["첫 줄에 목표값 N, 둘째 줄에 쉼표로 구분된 서로 다른 양의 정수들이 주어집니다.", "세 수를 골라 합이 N이 되는 조합 개수를 출력하세요."],
                    "i < j < k 인 세 인덱스를 모두 검사하세요.",
                    "target = int(input())\nnums = input().strip().split(',')\ncount = 0\nfor i in range(len(nums)):\n    for j in range(i + 1, len(nums)):\n        for k in range(j + 1, len(nums)):\n            if int(nums[i]) + int(nums[j]) + int(nums[k]) == target:\n                count += 1\nprint(count)",
                    "9\n1,2,3,4,5",
                    "2",
                ),
            ],
        ),
        chapter(
            "실전 20문제 세트",
            "Python A 실전 대비용 20문제 세트입니다. 앞의 5문제는 객관식, 나머지는 코딩 연습입니다.",
            items_20,
        ),
    ]


def build_python_b_data():
    items_20 = [
        objective(
            "실전 B-01: 함수 호출 개념",
            ["파이썬 함수에 대한 설명으로 올바른 것을 고르세요."],
            ["A. 정의만 하면 자동 실행된다", "B. 정의 후 호출해야 실행된다", "C. 항상 프로그램 첫 줄에 있어야 한다", "D. def와 함수 본문은 같은 들여쓰기여야 한다"],
            "B",
            explanation="함수는 정의 후 반드시 호출해야 실행됩니다.",
        ),
        objective(
            "실전 B-02: 딕셔너리 값 순회",
            ["딕셔너리 d의 값(value)들만 순회하는 코드를 고르세요."],
            ["A. for x in d", "B. for x in d.keys()", "C. for x in d.items()", "D. for x in d.values()"],
            "D",
            explanation="values()는 값 목록을 순회합니다.",
        ),
        objective(
            "실전 B-03: 튜플 역순",
            ["튜플 t를 역순으로 뒤집는 표현식을 고르세요."],
            ["A. t[::-1]", "B. t.reverse()", "C. reverse(t)", "D. t[-1]"],
            "A",
            explanation="시퀀스 역순 슬라이싱은 [::-1]입니다.",
        ),
        objective(
            "실전 B-04: 소수 판별 핵심",
            ["양의 정수 num이 소수인지 검사할 때 가장 핵심이 되는 조건을 고르세요."],
            ["A. num % 1 == 0", "B. 2부터 num-1까지 나누어 떨어지는 수가 없는지 확인", "C. num > 100인지 확인", "D. 문자열로 바꾸어 길이를 확인"],
            "B",
            explanation="소수는 1과 자기 자신 외에는 나누어 떨어지지 않습니다.",
        ),
        objective(
            "실전 B-05: 리스트 정렬 메서드",
            ["리스트 nums를 오름차순으로 제자리 정렬하는 메서드를 고르세요."],
            ["A. nums.order()", "B. nums.sort()", "C. nums.sorted()", "D. sort(nums)만 가능하다"],
            "B",
            explanation="리스트 자체를 정렬할 때는 sort()를 사용합니다.",
        ),
        coding(
            "실전 B-06: 직사각형 둘레",
            ["직사각형 가로와 세로가 입력되면 둘레를 출력하세요."],
            "둘레는 2 * (가로 + 세로) 입니다.",
            "a, b = map(int, input().split())\nprint(2 * (a + b))",
            "3 4",
            "14",
        ),
        coding(
            "실전 B-07: 소수 판별",
            ["양의 정수 N이 입력되면 소수이면 YES, 아니면 NO를 출력하세요."],
            "2부터 N-1까지 나누어 보세요.",
            "n = int(input())\nif n < 2:\n    print('NO')\nelse:\n    prime = True\n    for i in range(2, n):\n        if n % i == 0:\n            prime = False\n            break\n    print('YES' if prime else 'NO')",
            "7",
            "YES",
        ),
        coding(
            "실전 B-08: 리스트 내림차순 출력",
            ["공백으로 구분된 정수들이 입력되면 내림차순으로 정렬해 출력하세요."],
            "sort(reverse=True)를 사용하세요.",
            "nums = [int(x) for x in input().split()]\nnums.sort(reverse=True)\nprint(*nums)",
            "5 1 4 2 3",
            "5 4 3 2 1",
        ),
        coding(
            "실전 B-09: 가장 긴 단어 길이",
            ["공백으로 구분된 단어들이 입력되면 가장 긴 단어의 길이를 출력하세요."],
            "현재 최댓길이를 저장하세요.",
            "words = input().split()\nbest = 0\nfor word in words:\n    if len(word) > best:\n        best = len(word)\nprint(best)",
            "code python algorithm",
            "9",
        ),
        coding(
            "실전 B-10: 문자 빈도수",
            ["문자열이 입력되면 각 문자의 등장 횟수를 처음 등장한 순서대로 문자:개수 형식으로 출력하세요."],
            "딕셔너리와 순서 리스트를 함께 사용하세요.",
            "text = input().strip()\ncounts = {}\norder = []\nfor ch in text:\n    if ch not in counts:\n        counts[ch] = 0\n        order.append(ch)\n    counts[ch] += 1\nfor ch in order:\n    print(ch + ':' + str(counts[ch]))",
            "level",
            "l:2\ne:2\nv:1",
        ),
        coding(
            "실전 B-11: 팩토리얼",
            ["정수 N이 입력되면 N! 값을 출력하세요."],
            "곱셈 누적 변수를 사용하세요.",
            "n = int(input())\nresult = 1\nfor i in range(1, n + 1):\n    result *= i\nprint(result)",
            "5",
            "120",
        ),
        coding(
            "실전 B-12: 회문 판별",
            ["문자열이 입력되면 앞뒤가 같으면 YES, 아니면 NO를 출력하세요."],
            "뒤집은 문자열과 비교하세요.",
            "text = input().strip()\nprint('YES' if text == text[::-1] else 'NO')",
            "radar",
            "YES",
        ),
        coding(
            "실전 B-13: 세 수 중 가운데 값",
            ["정수 세 개가 입력되면 크기순으로 가운데 값을 출력하세요."],
            "정렬한 뒤 인덱스 1을 출력하세요.",
            "nums = [int(x) for x in input().split()]\nnums.sort()\nprint(nums[1])",
            "9 2 5",
            "5",
        ),
        coding(
            "실전 B-14: 단어별 길이 출력",
            ["공백으로 구분된 단어들이 입력되면 각 단어와 길이를 단어:길이 형식으로 출력하세요."],
            "반복문으로 한 단어씩 처리하세요.",
            "words = input().split()\nfor word in words:\n    print(word + ':' + str(len(word)))",
            "loop data python",
            "loop:4\ndata:4\npython:6",
        ),
        coding(
            "실전 B-15: 연속한 세 수 곱의 합",
            ["쉼표로 구분된 정수들이 입력되면 현재 순서 그대로 연속한 세 수의 곱의 합을 출력하세요."],
            "i, i+1, i+2를 차례대로 곱해서 더하세요.",
            "nums = [int(x) for x in input().strip().split(',')]\ntotal = 0\nfor i in range(len(nums) - 2):\n    total += nums[i] * nums[i + 1] * nums[i + 2]\nprint(total)",
            "1,3,4,2",
            "36",
        ),
        coding(
            "실전 B-16: 두 수 조합 최대 합",
            ["공백으로 구분된 정수들이 입력되면 서로 다른 두 수의 합 중 최댓값을 출력하세요."],
            "가장 큰 두 수를 찾으면 됩니다.",
            "nums = [int(x) for x in input().split()]\nnums.sort(reverse=True)\nprint(nums[0] + nums[1])",
            "4 9 1 7 3",
            "16",
        ),
        coding(
            "실전 B-17: 행별 합 출력",
            ["첫 줄에 행 수가 입력되고, 이후 각 줄에 정수 세 개가 입력되면 각 줄의 합을 출력하세요."],
            "반복해서 한 줄씩 처리하세요.",
            "n = int(input())\nfor _ in range(n):\n    a, b, c = map(int, input().split())\n    print(a + b + c)",
            "2\n1 2 3\n4 5 6",
            "6\n15",
        ),
        coding(
            "실전 B-18: 단어 사전순 정렬",
            ["공백으로 구분된 단어들이 입력되면 사전순으로 정렬해 출력하세요."],
            "sort()를 사용하세요.",
            "words = input().split()\nwords.sort()\nprint(' '.join(words))",
            "pear apple banana",
            "apple banana pear",
        ),
        coding(
            "실전 B-19: 최대 연속 구간 합",
            ["공백으로 구분된 정수들이 입력되면 연속 구간의 합 중 최댓값을 출력하세요."],
            "현재 위치에서 끝나는 최대합을 갱신하세요.",
            "nums = [int(x) for x in input().split()]\ncurrent = nums[0]\nbest = nums[0]\nfor i in range(1, len(nums)):\n    current = max(nums[i], current + nums[i])\n    best = max(best, current)\nprint(best)",
            "-2 1 -3 4 -1 2 1 -5 4",
            "6",
        ),
        coding(
            "실전 B-20: 점프 DP 기초",
            ["첫 줄에 칸 수 N, 둘째 줄에 각 칸 점수가 공백으로 입력됩니다.", "한 번에 1칸 또는 2칸씩 앞으로 갈 수 있을 때 마지막 칸에 도착하며 얻을 수 있는 최대 점수를 출력하세요."],
            "뒤에서부터 DP를 채우거나 앞에서부터 누적해도 됩니다.",
            "n = int(input())\nscores = [int(x) for x in input().split()]\nif n == 1:\n    print(scores[0])\nelse:\n    dp = [0] * n\n    dp[0] = scores[0]\n    dp[1] = scores[1] + max(0, dp[0])\n    for i in range(2, n):\n        dp[i] = scores[i] + max(dp[i - 1], dp[i - 2])\n    print(dp[-1])",
            "5\n1 10 30 100 30",
            "171",
        ),
    ]

    return [
        chapter(
            "대회 구조와 객관식 워밍업",
            "Python B 핵심 문법과 가이드 예시 객관식을 실제 선택형으로 연습합니다.",
            [
                example(
                    "Python B 대회 구성 이해",
                    [
                        "Python B는 18세 이하 부문입니다.",
                        "함수, 딕셔너리, 알고리즘, 자료구조 개념이 Python A보다 더 강조됩니다.",
                    ],
                    "print('Python B Ready')",
                    "Python B Ready",
                ),
                objective(
                    "가이드 객관식 1: 참이 되는 표현식",
                    ["다음 중 참을 반환하는 표현식을 고르세요."],
                    ["A. 3 != 3", "B. 5 > 4 > 3", "C. 8 % 2 == 1", "D. False"],
                    "B",
                    explanation="연속 비교 5 > 4 > 3 은 True 입니다.",
                ),
                objective(
                    "가이드 객관식 2: 함수 설명",
                    ["함수에 대한 설명으로 올바른 것을 고르세요."],
                    ["A. 항상 프로그램 맨 앞에 있어야 한다", "B. 정의 후에는 호출해야 실행된다", "C. def와 함수 본문은 같은 들여쓰기여야 한다", "D. 정의만 하면 자동 실행된다"],
                    "B",
                    explanation="함수는 정의 후 호출해야 실행됩니다.",
                ),
                objective(
                    "가이드 객관식 3: is_prime 함수 의미",
                    ["다음 함수가 판별하는 대상을 고르세요."],
                    ["A. 덧셈 계산", "B. 소수 판별", "C. 루프 인덱스", "D. 정렬된 목록"],
                    "B",
                    explanation="is_prime은 소수 여부를 판별하는 함수입니다.",
                    stem_code="def is_prime(num):\n    if num < 2:\n        return False\n    for i in range(2, num):\n        if num % i == 0:\n            return False\n    return True",
                ),
                objective(
                    "가이드 객관식 4: 딕셔너리 값 순회",
                    ["딕셔너리 d를 순회할 때 변수 x가 값(value)을 의미하는 표현식을 고르세요."],
                    ["A. for x in d", "B. for x in d.keys()", "C. for x in d.items()", "D. for x in d.values()"],
                    "D",
                    explanation="values()는 값들만 순회합니다.",
                ),
                objective(
                    "가이드 객관식 5: 튜플 역순 슬라이싱",
                    ["t = ('bian', 'cheng', 'sai') 일 때 t[::-1] 결과를 고르세요."],
                    ["A. ('sai', 'cheng', 'bian')", "B. ['sai', 'cheng', 'bian']", "C. {'sai', 'cheng', 'bian'}", "D. 런타임 오류"],
                    "A",
                    explanation="튜플도 슬라이싱으로 역순 출력할 수 있습니다.",
                ),
            ],
        ),
        chapter(
            "가이드 예시 프로그래밍 5문제",
            "공식 가이드의 Python B 예시 문제를 현재 플랫폼에 맞춰 연습합니다.",
            [
                coding(
                    "예시 1: 직사각형 넓이",
                    ["직사각형의 길이와 너비를 입력받아 넓이를 출력하세요."],
                    "두 수를 곱하세요.",
                    "parts = input().replace(',', ' ').split()\nprint(int(parts[0]) * int(parts[1]))",
                    "3 4",
                    "12",
                ),
                coding(
                    "예시 2: 네 자리 수 뒤집기",
                    ["네 자리 양의 정수가 입력되면 역순으로 출력하세요."],
                    "문자열을 뒤집으면 됩니다.",
                    "text = input().strip()\nprint(text[::-1])",
                    "1234",
                    "4321",
                ),
                coding(
                    "예시 3: 세 수 곱의 합이 최대가 되는 배열 찾기",
                    ["쉼표로 구분된 양의 정수들이 입력됩니다.", "배열 순서를 바꾸어 연속한 세 수의 곱의 합이 최대가 될 때 그 최댓값을 출력하세요."],
                    "학습용으로 완전탐색을 사용합니다.",
                    "nums = [int(x) for x in input().strip().split(',')]\nused = [False] * len(nums)\nbest = [-1]\n\ndef score(arr):\n    total = 0\n    for i in range(len(arr) - 2):\n        total += arr[i] * arr[i + 1] * arr[i + 2]\n    return total\n\ndef dfs(path):\n    if len(path) == len(nums):\n        best[0] = max(best[0], score(path))\n        return\n    for i in range(len(nums)):\n        if not used[i]:\n            used[i] = True\n            path.append(nums[i])\n            dfs(path)\n            path.pop()\n            used[i] = False\n\ndfs([])\nprint(best[0])",
                    "1,2,3,4",
                    "36",
                ),
                coding(
                    "예시 4: 두 줄 숫자 공으로 가장 큰 수 만들기",
                    ["두 줄의 숫자 공에서 순서를 유지하며 총 K개를 골라 가장 큰 수를 만드세요."],
                    "최대 부분수열을 만든 뒤 병합하는 그리디 방식입니다.",
                    "a = [int(x) for x in input().strip().split(',')]\nb = [int(x) for x in input().strip().split(',')]\nk = int(input())\n\ndef pick_max(nums, count):\n    drop = len(nums) - count\n    stack = []\n    for n in nums:\n        while drop > 0 and stack and stack[-1] < n:\n            stack.pop()\n            drop -= 1\n        stack.append(n)\n    return stack[:count]\n\ndef greater(left, i, right, j):\n    while i < len(left) and j < len(right) and left[i] == right[j]:\n        i += 1\n        j += 1\n    if j == len(right):\n        return True\n    if i == len(left):\n        return False\n    return left[i] > right[j]\n\ndef merge(left, right):\n    i = 0\n    j = 0\n    result = []\n    while i < len(left) or j < len(right):\n        if greater(left, i, right, j):\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    return result\n\nbest = []\nstart = max(0, k - len(b))\nend = min(k, len(a))\nfor take_a in range(start, end + 1):\n    take_b = k - take_a\n    cand = merge(pick_max(a, take_a), pick_max(b, take_b))\n    if greater(cand, 0, best, 0):\n        best = cand\ntext = ''\nfor n in best:\n    text += str(n)\nprint(text)",
                    "2,5,3\n6,2,4,1\n3",
                    "654",
                ),
                coding(
                    "예시 5: 최대 배달 점수",
                    ["첫 줄에 역 수 N과 경로 수 M, 둘째 줄에 이동 가능한 점프들, 셋째 줄에 각 역 점수가 주어집니다.", "현재 역 0에서 시작할 때 얻을 수 있는 최대 점수를 출력하세요."],
                    "뒤에서부터 최대 점수를 DP로 계산하세요.",
                    "n, m = map(int, input().split())\nsteps = [int(x) for x in input().split()]\nscores = [int(x) for x in input().split()]\ndp = [0] * n\nfor i in range(n - 1, -1, -1):\n    best_next = 0\n    for step in steps:\n        nxt = i + step\n        if nxt < n and dp[nxt] > best_next:\n            best_next = dp[nxt]\n    dp[i] = scores[i] + best_next\nprint(dp[0])",
                    "6 2\n2 3\n1 0 30 100 30 30",
                    "131",
                ),
            ],
        ),
        chapter(
            "Python B 추가 실전 연습",
            "함수와 딕셔너리, 기본 알고리즘 사고를 더 연습합니다.",
            [
                coding(
                    "추가 1: 소수 개수 세기",
                    ["양의 정수 N이 입력되면 2부터 N까지의 소수 개수를 출력하세요."],
                    "소수 판별 함수를 만들고 반복해서 검사하세요.",
                    "def is_prime(num):\n    if num < 2:\n        return False\n    for i in range(2, num):\n        if num % i == 0:\n            return False\n    return True\n\nn = int(input())\ncount = 0\nfor i in range(2, n + 1):\n    if is_prime(i):\n        count += 1\nprint(count)",
                    "10",
                    "4",
                ),
                coding(
                    "추가 2: 단어 빈도 사전 만들기",
                    ["공백으로 구분된 단어들이 입력되면 각 단어의 등장 횟수를 첫 등장 순서대로 출력하세요."],
                    "딕셔너리와 순서 리스트를 사용하세요.",
                    "words = input().split()\ncounts = {}\norder = []\nfor word in words:\n    if word not in counts:\n        counts[word] = 0\n        order.append(word)\n    counts[word] += 1\nfor word in order:\n    print(word + ':' + str(counts[word]))",
                    "red blue red green blue red",
                    "red:3\nblue:2\ngreen:1",
                ),
                coding(
                    "추가 3: 최대 연속 구간 합",
                    ["공백으로 구분된 정수들이 입력되면 연속한 구간의 합 중 최댓값을 출력하세요."],
                    "현재 위치에서 끝나는 최대합을 갱신하세요.",
                    "nums = [int(x) for x in input().split()]\ncurrent = nums[0]\nbest = nums[0]\nfor i in range(1, len(nums)):\n    current = max(nums[i], current + nums[i])\n    best = max(best, current)\nprint(best)",
                    "-2 1 -3 4 -1 2 1 -5 4",
                    "6",
                ),
            ],
        ),
        chapter(
            "실전 20문제 세트",
            "Python B 실전 대비용 20문제 세트입니다. 앞의 5문제는 객관식, 나머지는 코딩 연습입니다.",
            items_20,
        ),
    ]


class Command(BaseCommand):
    help = "RC.CODE Python A/B 대회 대비 연습 과정을 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="같은 이름의 기존 과정이 있으면 문항을 지우고 다시 생성합니다.",
        )

    def seed_program(self, program_type, course_name, description, chapters_data, replace=False):
        program, created = LearningProgram.objects.get_or_create(
            name=course_name,
            defaults={
                "description": description,
                "program_type": program_type,
                "is_active": True,
            },
        )

        if not created and not replace and program.chapters.exists():
            self.stdout.write(self.style.WARNING(f"'{course_name}' 과정이 이미 있습니다. --replace 옵션을 사용하면 다시 생성합니다."))
            return

        program.description = description
        program.program_type = program_type
        program.is_active = True
        program.save()
        program.chapters.all().delete()

        item_total = 0
        for chapter_index, chapter_data in enumerate(chapters_data, start=1):
            chapter_obj = Chapter.objects.create(
                program=program,
                number=chapter_index,
                title=chapter_data["title"],
                content=chapter_data["content"],
            )

            for item_index, item_data in enumerate(chapter_data["items"], start=1):
                item_total += 1
                Item.objects.create(
                    chapter=chapter_obj,
                    number=item_index,
                    key=f"rc_{program.id}_{chapter_index:02d}_{item_index:02d}",
                    title=item_data["title"],
                    item_type=item_data["item_type"],
                    explain_html=item_data["explain_html"],
                    hint=item_data["hint"],
                    answer_code=item_data["answer_code"],
                    example_input=item_data["example_input"],
                    expected_output=item_data["expected_output"],
                )

        self.stdout.write(self.style.SUCCESS(f"'{course_name}' 과정 생성 완료"))
        self.stdout.write(self.style.SUCCESS(f"- 총 {len(chapters_data)}개 챕터, {item_total}개 문항"))

    @transaction.atomic
    def handle(self, *args, **options):
        program_type, _ = ProgramType.objects.get_or_create(
            name=PROGRAM_TYPE_NAME,
            defaults={"order": 40},
        )

        self.seed_program(
            program_type,
            "RC.CODE Python A 대회 연습",
            "RC.CODE Python A(12세 이하) 가이드를 바탕으로 만든 연습 과정입니다. 가이드 객관식, 공식 예시 5문제, 추가 문제, 실전 20문제 세트를 포함합니다.",
            build_python_a_data(),
            replace=options["replace"],
        )

        self.seed_program(
            program_type,
            "RC.CODE Python B 대회 연습",
            "RC.CODE Python B(18세 이하) 가이드를 바탕으로 만든 연습 과정입니다. 가이드 객관식, 공식 예시 5문제, 추가 문제, 실전 20문제 세트를 포함합니다.",
            build_python_b_data(),
            replace=options["replace"],
        )
