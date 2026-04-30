from html import escape

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Chapter, Item, LearningProgram, ProgramType


COURSE_NAME = "COS Pro 파이썬 3급 대비"
PROGRAM_TYPE_NAME = "자격증 대비"


def html_paragraphs(*lines):
    return "".join(f"<p>{escape(line)}</p>" for line in lines if line)


def problem(title, explain_lines, hint, answer_code, example_input="", expected_output=""):
    return {
        "title": title,
        "explain_html": html_paragraphs(*explain_lines),
        "hint": hint,
        "answer_code": answer_code.strip(),
        "example_input": example_input,
        "expected_output": expected_output,
    }


def build_course_data():
    chapters = []

    # ── 1장: 기본 출력과 변수 ──────────────────────────────────────────────────
    chapters.append({
        "title": "기본 출력과 변수",
        "content": "print 함수, 변수 선언, 기본 자료형(int, str, float)을 익힙니다.",
        "items": [
            problem(
                "Hello, Python! 출력하기",
                ["화면에 Hello, Python! 을 출력하세요."],
                "print 함수 안에 문자열을 넣어보세요.",
                'print("Hello, Python!")',
                "",
                "Hello, Python!",
            ),
            problem(
                "두 줄 출력하기",
                ["첫째 줄에 COS, 둘째 줄에 Pro 를 출력하세요."],
                "print를 두 번 사용하면 됩니다.",
                'print("COS")\nprint("Pro")',
                "",
                "COS\nPro",
            ),
            problem(
                "정수 변수 출력하기",
                ["변수 score에 100을 저장하고 출력하세요."],
                "score = 100 처럼 대입한 뒤 print로 출력하세요.",
                "score = 100\nprint(score)",
                "",
                "100",
            ),
            problem(
                "문자열 변수 만들기",
                ["변수 name에 파이썬을 저장하고 출력하세요."],
                "문자열은 따옴표로 감쌉니다.",
                'name = "파이썬"\nprint(name)',
                "",
                "파이썬",
            ),
            problem(
                "두 변수 출력하기",
                ["변수 a에 10, b에 20을 저장한 뒤 두 값을 공백으로 구분해 출력하세요."],
                "print(a, b) 형태를 사용하세요.",
                "a = 10\nb = 20\nprint(a, b)",
                "",
                "10 20",
            ),
            problem(
                "변수 값 바꾸기",
                ["변수 x에 5를 저장한 뒤 x를 10으로 바꾸고 출력하세요."],
                "같은 변수명으로 다시 대입하면 됩니다.",
                "x = 5\nx = 10\nprint(x)",
                "",
                "10",
            ),
            problem(
                "문자열과 숫자 구분 출력",
                ["첫째 줄에 정수 7, 둘째 줄에 문자열 seven 을 출력하세요."],
                "숫자는 따옴표 없이, 문자열은 따옴표로 감쌉니다.",
                'print(7)\nprint("seven")',
                "",
                "7\nseven",
            ),
            problem(
                "소수점 변수 출력",
                ["변수 pi에 3.14를 저장하고 출력하세요."],
                "float 값은 그대로 대입하면 됩니다.",
                "pi = 3.14\nprint(pi)",
                "",
                "3.14",
            ),
            problem(
                "True / False 출력",
                ["변수 flag에 True를 저장하고 출력하세요."],
                "파이썬의 불리언 값은 True, False 입니다.",
                "flag = True\nprint(flag)",
                "",
                "True",
            ),
            problem(
                "세 줄 자기소개",
                ["첫째 줄 이름:홍길동, 둘째 줄 학교:메듀랩, 셋째 줄 목표:자격증취득 을 출력하세요."],
                "print를 세 번 사용해 각각 출력하세요.",
                'print("이름:홍길동")\nprint("학교:메듀랩")\nprint("목표:자격증취득")',
                "",
                "이름:홍길동\n학교:메듀랩\n목표:자격증취득",
            ),
        ],
    })

    # ── 2장: 입력과 연산자 ───────────────────────────────────────────────────
    chapters.append({
        "title": "입력과 연산자",
        "content": "input 함수로 값을 받고 산술·비교·논리 연산자를 사용합니다.",
        "items": [
            problem(
                "두 수의 합",
                ["한 줄에 정수 두 개가 공백으로 입력됩니다. 두 수의 합을 출력하세요."],
                "split 후 각각 int로 변환하세요.",
                "a, b = map(int, input().split())\nprint(a + b)",
                "3 7",
                "10",
            ),
            problem(
                "두 수의 차",
                ["한 줄에 정수 두 개가 입력됩니다. 첫 번째 수에서 두 번째 수를 뺀 값을 출력하세요."],
                "a - b 형태입니다.",
                "a, b = map(int, input().split())\nprint(a - b)",
                "15 6",
                "9",
            ),
            problem(
                "두 수의 곱",
                ["한 줄에 정수 두 개가 입력됩니다. 곱을 출력하세요."],
                "* 연산자를 사용하세요.",
                "a, b = map(int, input().split())\nprint(a * b)",
                "4 8",
                "32",
            ),
            problem(
                "몫과 나머지",
                ["한 줄에 정수 두 개가 입력됩니다. 첫 번째를 두 번째로 나눈 몫과 나머지를 공백으로 구분해 출력하세요."],
                "// 와 % 연산자를 사용하세요.",
                "a, b = map(int, input().split())\nprint(a // b, a % b)",
                "13 4",
                "3 1",
            ),
            problem(
                "섭씨를 화씨로",
                ["섭씨 온도가 입력되면 화씨 온도를 소수 첫째 자리까지 출력하세요. (공식: F = C × 9/5 + 32)"],
                "round(값, 1) 로 소수 첫째 자리까지 반올림하세요.",
                "c = float(input())\nf = c * 9 / 5 + 32\nprint(round(f, 1))",
                "25",
                "77.0",
            ),
            problem(
                "초를 분과 초로 변환",
                ["초 단위 정수가 입력되면 몇 분 몇 초인지 공백으로 구분해 출력하세요."],
                "분은 // 60, 나머지 초는 % 60 입니다.",
                "s = int(input())\nprint(s // 60, s % 60)",
                "130",
                "2 10",
            ),
            problem(
                "원의 넓이",
                ["반지름이 정수로 입력되면 원의 넓이를 소수 둘째 자리까지 출력하세요. (π = 3.14)"],
                "넓이 = 반지름 * 반지름 * 3.14 입니다.",
                "r = int(input())\nprint(round(r * r * 3.14, 2))",
                "5",
                "78.5",
            ),
            problem(
                "두 수를 바꿔 출력",
                ["한 줄에 두 정수가 입력됩니다. 두 수의 순서를 바꿔 출력하세요."],
                "출력 순서만 바꾸면 됩니다.",
                "a, b = map(int, input().split())\nprint(b, a)",
                "10 20",
                "20 10",
            ),
            problem(
                "세 수의 평균",
                ["한 줄에 정수 세 개가 입력됩니다. 평균을 출력하세요."],
                "합을 3으로 나누세요. 실수 나눗셈을 사용하세요.",
                "a, b, c = map(int, input().split())\nprint((a + b + c) / 3)",
                "10 20 30",
                "20.0",
            ),
            problem(
                "두 자리 수 각 자리 합",
                ["두 자리 정수가 입력되면 십의 자리와 일의 자리의 합을 출력하세요."],
                "문자열로 받아 각 자리를 int로 변환해 더하세요.",
                "n = input().strip()\nprint(int(n[0]) + int(n[1]))",
                "47",
                "11",
            ),
        ],
    })

    # ── 3장: 조건문 ──────────────────────────────────────────────────────────
    chapters.append({
        "title": "조건문",
        "content": "if, elif, else 문으로 조건 분기를 처리합니다.",
        "items": [
            problem(
                "더 큰 수 출력",
                ["정수 두 개가 입력되면 더 큰 수를 출력하세요."],
                "if-else 로 두 수를 비교하세요.",
                "a, b = map(int, input().split())\nif a > b:\n    print(a)\nelse:\n    print(b)",
                "8 13",
                "13",
            ),
            problem(
                "짝수 홀수 판별",
                ["정수가 입력되면 짝수면 짝수, 홀수면 홀수를 출력하세요."],
                "% 2 == 0 이면 짝수입니다.",
                'n = int(input())\nif n % 2 == 0:\n    print("짝수")\nelse:\n    print("홀수")',
                "7",
                "홀수",
            ),
            problem(
                "양수 음수 0 판별",
                ["정수가 입력되면 양수, 음수, 0 중 알맞은 것을 출력하세요."],
                "세 경우를 if-elif-else 로 처리하세요.",
                'n = int(input())\nif n > 0:\n    print("양수")\nelif n < 0:\n    print("음수")\nelse:\n    print("0")',
                "-5",
                "음수",
            ),
            problem(
                "성적 등급 출력",
                ["점수가 입력되면 90 이상 A, 80 이상 B, 70 이상 C, 그 외 F를 출력하세요."],
                "큰 값부터 차례로 비교하세요.",
                'score = int(input())\nif score >= 90:\n    print("A")\nelif score >= 80:\n    print("B")\nelif score >= 70:\n    print("C")\nelse:\n    print("F")',
                "85",
                "B",
            ),
            problem(
                "합격 여부 출력",
                ["점수가 입력되면 60 이상이면 합격, 아니면 불합격을 출력하세요."],
                "조건 하나만 판단하면 됩니다.",
                'n = int(input())\nif n >= 60:\n    print("합격")\nelse:\n    print("불합격")',
                "59",
                "불합격",
            ),
            problem(
                "절댓값 출력",
                ["정수가 입력되면 절댓값을 출력하세요."],
                "음수일 때 -1을 곱하면 됩니다.",
                "n = int(input())\nif n < 0:\n    print(-n)\nelse:\n    print(n)",
                "-12",
                "12",
            ),
            problem(
                "연령대 출력",
                ["나이가 입력되면 13 미만은 어린이, 19 미만은 청소년, 그 외는 성인을 출력하세요."],
                "작은 구간부터 비교하세요.",
                'age = int(input())\nif age < 13:\n    print("어린이")\nelif age < 19:\n    print("청소년")\nelse:\n    print("성인")',
                "17",
                "청소년",
            ),
            problem(
                "3과 5의 공배수 판별",
                ["정수가 입력되면 3과 5 모두의 배수이면 YES, 아니면 NO를 출력하세요."],
                "두 조건을 and 로 연결하세요.",
                'n = int(input())\nif n % 3 == 0 and n % 5 == 0:\n    print("YES")\nelse:\n    print("NO")',
                "15",
                "YES",
            ),
            problem(
                "가장 큰 수 출력",
                ["정수 세 개가 입력되면 가장 큰 수를 출력하세요."],
                "최댓값 변수를 두고 하나씩 비교하세요.",
                "a, b, c = map(int, input().split())\nmax_v = a\nif b > max_v:\n    max_v = b\nif c > max_v:\n    max_v = c\nprint(max_v)",
                "4 12 7",
                "12",
            ),
            problem(
                "두 수가 같은지 확인",
                ["정수 두 개가 입력되면 두 수가 같으면 SAME, 다르면 DIFFERENT를 출력하세요."],
                "== 연산자로 비교하세요.",
                'a, b = map(int, input().split())\nif a == b:\n    print("SAME")\nelse:\n    print("DIFFERENT")',
                "5 5",
                "SAME",
            ),
        ],
    })

    # ── 4장: 반복문 ──────────────────────────────────────────────────────────
    chapters.append({
        "title": "반복문",
        "content": "for, while, range, break, continue 를 사용해 반복 처리를 합니다.",
        "items": [
            problem(
                "1부터 n까지 출력",
                ["정수 n이 입력되면 1부터 n까지 한 줄에 하나씩 출력하세요."],
                "range(1, n+1) 을 사용하세요.",
                "n = int(input())\nfor i in range(1, n + 1):\n    print(i)",
                "5",
                "1\n2\n3\n4\n5",
            ),
            problem(
                "1부터 n까지의 합",
                ["정수 n이 입력되면 1부터 n까지의 합을 출력하세요."],
                "누적 합 변수를 만들어 반복 안에서 더하세요.",
                "n = int(input())\ntotal = 0\nfor i in range(1, n + 1):\n    total += i\nprint(total)",
                "10",
                "55",
            ),
            problem(
                "구구단 한 단 출력",
                ["정수 n이 입력되면 n × 1 부터 n × 9 까지 한 줄에 하나씩 출력하세요."],
                "range(1, 10) 을 사용하세요.",
                "n = int(input())\nfor i in range(1, 10):\n    print(n * i)",
                "3",
                "3\n6\n9\n12\n15\n18\n21\n24\n27",
            ),
            problem(
                "거꾸로 세기",
                ["정수 n이 입력되면 n부터 1까지 한 줄에 하나씩 출력하세요."],
                "range(n, 0, -1) 처럼 감소 범위를 사용하세요.",
                "n = int(input())\nfor i in range(n, 0, -1):\n    print(i)",
                "4",
                "4\n3\n2\n1",
            ),
            problem(
                "짝수만 출력",
                ["정수 n이 입력되면 1부터 n까지 짝수를 한 줄에 하나씩 출력하세요."],
                "% 2 == 0 조건을 반복 안에서 확인하세요.",
                "n = int(input())\nfor i in range(1, n + 1):\n    if i % 2 == 0:\n        print(i)",
                "8",
                "2\n4\n6\n8",
            ),
            problem(
                "별 삼각형 출력",
                ["정수 n이 입력되면 1행에 별 1개, 2행에 별 2개 … n행에 별 n개를 출력하세요."],
                "'*' * i 처럼 문자열 곱셈을 사용하세요.",
                "n = int(input())\nfor i in range(1, n + 1):\n    print('*' * i)",
                "4",
                "*\n**\n***\n****",
            ),
            problem(
                "역삼각형 출력",
                ["정수 n이 입력되면 n행에 별 n개, … 1행에 별 1개 형태로 출력하세요."],
                "range(n, 0, -1) 을 사용하세요.",
                "n = int(input())\nfor i in range(n, 0, -1):\n    print('*' * i)",
                "4",
                "****\n***\n**\n*",
            ),
            problem(
                "팩토리얼 계산",
                ["정수 n이 입력되면 n! 값을 출력하세요."],
                "곱셈 누적 변수 result = 1 에서 시작해 차례로 곱하세요.",
                "n = int(input())\nresult = 1\nfor i in range(1, n + 1):\n    result *= i\nprint(result)",
                "6",
                "720",
            ),
            problem(
                "while 반복: 입력 합산",
                ["정수를 한 줄씩 입력받아 0이 입력되면 중단하고 합계를 출력하세요."],
                "while True: … if n == 0: break 구조를 사용하세요.",
                "total = 0\nwhile True:\n    n = int(input())\n    if n == 0:\n        break\n    total += n\nprint(total)",
                "3\n5\n2\n0",
                "10",
            ),
            problem(
                "짝수 합 구하기",
                ["정수 n이 입력되면 1부터 n까지 짝수들의 합을 출력하세요."],
                "짝수일 때만 total에 더하세요.",
                "n = int(input())\ntotal = 0\nfor i in range(1, n + 1):\n    if i % 2 == 0:\n        total += i\nprint(total)",
                "10",
                "30",
            ),
        ],
    })

    # ── 5장: 문자열 처리 ─────────────────────────────────────────────────────
    chapters.append({
        "title": "문자열 처리",
        "content": "len, upper, lower, replace, split, count, find 등 문자열 메서드를 익힙니다.",
        "items": [
            problem(
                "문자열 길이 구하기",
                ["문자열이 입력되면 글자 수를 출력하세요."],
                "len 함수를 사용하세요.",
                "s = input()\nprint(len(s))",
                "python",
                "6",
            ),
            problem(
                "대문자로 변환",
                ["영문 문자열이 입력되면 모두 대문자로 출력하세요."],
                "upper 메서드를 사용하세요.",
                "s = input().strip()\nprint(s.upper())",
                "hello",
                "HELLO",
            ),
            problem(
                "소문자로 변환",
                ["영문 문자열이 입력되면 모두 소문자로 출력하세요."],
                "lower 메서드를 사용하세요.",
                "s = input().strip()\nprint(s.lower())",
                "PYTHON",
                "python",
            ),
            problem(
                "문자열 뒤집기",
                ["문자열이 입력되면 뒤집어 출력하세요."],
                "슬라이싱 [::-1] 을 사용하세요.",
                "s = input().strip()\nprint(s[::-1])",
                "abcde",
                "edcba",
            ),
            problem(
                "공백을 밑줄로 교체",
                ["문장이 입력되면 공백을 모두 밑줄(_)로 바꿔 출력하세요."],
                "replace(' ', '_') 를 사용하세요.",
                "s = input()\nprint(s.replace(' ', '_'))",
                "hello world",
                "hello_world",
            ),
            problem(
                "특정 문자 개수 세기",
                ["첫 줄에 문장, 둘째 줄에 찾을 문자가 입력됩니다. 해당 문자의 개수를 출력하세요."],
                "count 메서드를 사용하세요.",
                "s = input()\nc = input().strip()\nprint(s.count(c))",
                "banana\na",
                "3",
            ),
            problem(
                "첫 글자와 마지막 글자",
                ["문자열이 입력되면 첫 글자와 마지막 글자를 공백으로 구분해 출력하세요."],
                "인덱스 0과 -1을 사용하세요.",
                "s = input().strip()\nprint(s[0], s[-1])",
                "coding",
                "c g",
            ),
            problem(
                "더 긴 문자열 출력",
                ["두 문자열이 한 줄씩 입력됩니다. 더 긴 문자열을 출력하세요. 길이가 같으면 첫 번째 문자열을 출력하세요."],
                "len으로 길이를 비교하세요.",
                "a = input().strip()\nb = input().strip()\nif len(a) >= len(b):\n    print(a)\nelse:\n    print(b)",
                "apple\nbanana",
                "banana",
            ),
            problem(
                "문자열 회문 확인",
                ["문자열이 입력되면 앞뒤가 같으면 YES, 아니면 NO를 출력하세요."],
                "원본과 뒤집은 문자열을 비교하세요.",
                "s = input().strip()\nif s == s[::-1]:\n    print('YES')\nelse:\n    print('NO')",
                "racecar",
                "YES",
            ),
            problem(
                "따옴표 붙여서 출력",
                ['문자열이 입력되면 양쪽에 큰따옴표를 붙여 출력하세요. 예: hello → "hello"'],
                'f-string: f\'"{s}"\' 처럼 작성하세요.',
                's = input().strip()\nprint(f\'"{s}"\')',
                "hello",
                '"hello"',
            ),
        ],
    })

    # ── 6장: 리스트 기초 ─────────────────────────────────────────────────────
    chapters.append({
        "title": "리스트 기초",
        "content": "리스트 생성, 인덱스, append, pop, sort, len 등을 익힙니다.",
        "items": [
            problem(
                "리스트 합계",
                ["한 줄에 정수 다섯 개가 입력됩니다. 합계를 출력하세요."],
                "map(int, input().split()) 으로 받아 sum 으로 더하세요.",
                "nums = list(map(int, input().split()))\nprint(sum(nums))",
                "1 2 3 4 5",
                "15",
            ),
            problem(
                "리스트 최댓값",
                ["한 줄에 정수 다섯 개가 입력됩니다. 가장 큰 수를 출력하세요."],
                "첫 값을 max_v 로 놓고 순회하며 비교하세요.",
                "nums = list(map(int, input().split()))\nmax_v = nums[0]\nfor n in nums:\n    if n > max_v:\n        max_v = n\nprint(max_v)",
                "3 7 2 9 4",
                "9",
            ),
            problem(
                "리스트 최솟값",
                ["한 줄에 정수 다섯 개가 입력됩니다. 가장 작은 수를 출력하세요."],
                "최솟값 변수를 두고 비교하세요.",
                "nums = list(map(int, input().split()))\nmin_v = nums[0]\nfor n in nums:\n    if n < min_v:\n        min_v = n\nprint(min_v)",
                "3 7 2 9 4",
                "2",
            ),
            problem(
                "리스트 오름차순 정렬",
                ["한 줄에 정수 네 개가 입력됩니다. 오름차순으로 정렬해 공백으로 구분해 출력하세요."],
                "sort 메서드를 사용하세요.",
                "nums = list(map(int, input().split()))\nnums.sort()\nprint(*nums)",
                "9 2 5 1",
                "1 2 5 9",
            ),
            problem(
                "리스트 뒤집어 출력",
                ["한 줄에 단어 네 개가 입력됩니다. 순서를 뒤집어 공백으로 구분해 출력하세요."],
                "reverse 메서드 또는 슬라이싱 [::-1] 을 사용하세요.",
                "words = input().split()\nwords.reverse()\nprint(*words)",
                "one two three four",
                "four three two one",
            ),
            problem(
                "50보다 큰 수의 개수",
                ["한 줄에 정수 다섯 개가 입력됩니다. 50보다 큰 수가 몇 개인지 출력하세요."],
                "조건을 만족할 때마다 count를 늘리세요.",
                "nums = list(map(int, input().split()))\ncount = 0\nfor n in nums:\n    if n > 50:\n        count += 1\nprint(count)",
                "30 55 80 42 61",
                "3",
            ),
            problem(
                "첫 번째와 마지막 값",
                ["한 줄에 정수 다섯 개가 입력됩니다. 첫 번째와 마지막 값을 공백으로 구분해 출력하세요."],
                "인덱스 0 과 -1 을 사용하세요.",
                "nums = list(map(int, input().split()))\nprint(nums[0], nums[-1])",
                "5 3 8 1 7",
                "5 7",
            ),
            problem(
                "특정 값이 있는지 확인",
                ["첫 줄에 정수 다섯 개, 둘째 줄에 정수 한 개가 입력됩니다. 해당 정수가 리스트에 있으면 YES, 없으면 NO를 출력하세요."],
                "in 연산자를 사용하세요.",
                "nums = list(map(int, input().split()))\ntarget = int(input())\nif target in nums:\n    print('YES')\nelse:\n    print('NO')",
                "1 3 5 7 9\n5",
                "YES",
            ),
            problem(
                "마지막 값 제거 후 길이",
                ["한 줄에 정수 다섯 개가 입력됩니다. 마지막 값을 제거하고 남은 리스트의 길이를 출력하세요."],
                "pop 으로 마지막 값을 제거하세요.",
                "nums = list(map(int, input().split()))\nnums.pop()\nprint(len(nums))",
                "1 2 3 4 5",
                "4",
            ),
            problem(
                "새 값 추가 후 합계",
                ["첫 줄에 정수 세 개, 둘째 줄에 정수 한 개가 입력됩니다. 둘째 줄 정수를 리스트에 추가한 뒤 합계를 출력하세요."],
                "append 후 sum 을 사용하세요.",
                "nums = list(map(int, input().split()))\nnew = int(input())\nnums.append(new)\nprint(sum(nums))",
                "1 2 3\n4",
                "10",
            ),
        ],
    })

    # ── 7장: 함수 기초 ───────────────────────────────────────────────────────
    chapters.append({
        "title": "함수 기초",
        "content": "def 로 함수를 정의하고 return 값을 활용하는 연습을 합니다.",
        "items": [
            problem(
                "두 수의 합 함수",
                ["정수 두 개가 입력되면 add(a, b) 함수를 이용해 합을 출력하세요."],
                "def add(a, b): return a + b 형태입니다.",
                "def add(a, b):\n    return a + b\n\na, b = map(int, input().split())\nprint(add(a, b))",
                "5 7",
                "12",
            ),
            problem(
                "제곱 함수",
                ["정수가 입력되면 square(n) 함수를 이용해 제곱을 출력하세요."],
                "return n * n 을 반환하세요.",
                "def square(n):\n    return n * n\n\nn = int(input())\nprint(square(n))",
                "6",
                "36",
            ),
            problem(
                "절댓값 함수",
                ["정수가 입력되면 my_abs(n) 함수를 이용해 절댓값을 출력하세요."],
                "음수면 -n, 아니면 n 을 반환하세요.",
                "def my_abs(n):\n    if n < 0:\n        return -n\n    return n\n\nn = int(input())\nprint(my_abs(n))",
                "-8",
                "8",
            ),
            problem(
                "최댓값 반환 함수",
                ["정수 두 개가 입력되면 bigger(a, b) 함수로 더 큰 값을 출력하세요."],
                "if 로 비교해 큰 값을 return 하세요.",
                "def bigger(a, b):\n    if a > b:\n        return a\n    return b\n\na, b = map(int, input().split())\nprint(bigger(a, b))",
                "4 19",
                "19",
            ),
            problem(
                "짝수 판별 함수",
                ["정수가 입력되면 is_even(n) 함수로 짝수면 True, 홀수면 False를 출력하세요."],
                "return n % 2 == 0 을 사용하세요.",
                "def is_even(n):\n    return n % 2 == 0\n\nn = int(input())\nprint(is_even(n))",
                "4",
                "True",
            ),
            problem(
                "인사 함수",
                ["이름이 입력되면 greet(name) 함수로 안녕하세요, 이름님! 을 출력하세요."],
                "함수 안에서 print 하거나 f-string 을 반환하세요.",
                "def greet(name):\n    print(f'안녕하세요, {name}님!')\n\nname = input().strip()\ngreet(name)",
                "민지",
                "안녕하세요, 민지님!",
            ),
            problem(
                "리스트 합계 함수",
                ["한 줄에 정수 네 개가 입력됩니다. total(nums) 함수로 합계를 출력하세요."],
                "sum 내장 함수를 활용해도 됩니다.",
                "def total(nums):\n    return sum(nums)\n\nnums = list(map(int, input().split()))\nprint(total(nums))",
                "1 2 3 4",
                "10",
            ),
            problem(
                "모음 개수 함수",
                ["영문 단어가 입력되면 count_vowels(word) 함수로 모음(a e i o u) 개수를 출력하세요."],
                "각 문자가 'aeiou' 에 있는지 확인하세요.",
                "def count_vowels(word):\n    count = 0\n    for ch in word.lower():\n        if ch in 'aeiou':\n            count += 1\n    return count\n\nword = input().strip()\nprint(count_vowels(word))",
                "banana",
                "3",
            ),
            problem(
                "할인 가격 함수",
                ["가격과 할인율(%)이 한 줄에 입력됩니다. discount(price, rate) 함수로 할인 후 가격을 출력하세요."],
                "price * (100 - rate) // 100 을 반환하세요.",
                "def discount(price, rate):\n    return price * (100 - rate) // 100\n\nprice, rate = map(int, input().split())\nprint(discount(price, rate))",
                "12000 25",
                "9000",
            ),
            problem(
                "문자 반복 함수",
                ["문자열과 반복 횟수가 한 줄에 입력됩니다. repeat(s, n) 함수로 문자열을 n번 반복해 출력하세요."],
                "return s * n 을 사용하세요.",
                "def repeat(s, n):\n    return s * n\n\nparts = input().split()\ns = parts[0]\nn = int(parts[1])\nprint(repeat(s, n))",
                "ha 3",
                "hahaha",
            ),
        ],
    })

    # ── 8장: 실전 모의고사 1 ─────────────────────────────────────────────────
    chapters.append({
        "title": "실전 모의고사 1",
        "content": "COS Pro 3급 출제 유형을 그대로 반영한 실전 모의고사입니다. 10문제를 40분 안에 풀어보세요.",
        "items": [
            problem(
                "[모의1-1] 입력값 그대로 출력",
                ["문자열이 한 줄 입력됩니다. 입력값을 그대로 출력하세요."],
                "input() 결과를 바로 print 하면 됩니다.",
                "s = input()\nprint(s)",
                "COS Pro",
                "COS Pro",
            ),
            problem(
                "[모의1-2] 두 수의 합과 곱",
                ["한 줄에 정수 두 개가 입력됩니다. 합을 첫째 줄에, 곱을 둘째 줄에 출력하세요."],
                "각각 + 와 * 연산자를 사용하세요.",
                "a, b = map(int, input().split())\nprint(a + b)\nprint(a * b)",
                "3 4",
                "7\n12",
            ),
            problem(
                "[모의1-3] 짝수 홀수 판별",
                ["정수가 입력되면 짝수면 Even, 홀수면 Odd를 출력하세요."],
                "% 2 결과로 판단하세요.",
                "n = int(input())\nif n % 2 == 0:\n    print('Even')\nelse:\n    print('Odd')",
                "9",
                "Odd",
            ),
            problem(
                "[모의1-4] 숫자 역순 출력",
                ["정수 n이 입력되면 n부터 1까지 한 줄에 하나씩 출력하세요."],
                "range(n, 0, -1) 을 사용하세요.",
                "n = int(input())\nfor i in range(n, 0, -1):\n    print(i)",
                "5",
                "5\n4\n3\n2\n1",
            ),
            problem(
                "[모의1-5] 문자열 길이와 첫 글자",
                ["문자열이 입력되면 첫째 줄에 길이, 둘째 줄에 첫 글자를 출력하세요."],
                "len 과 인덱스 0 을 사용하세요.",
                "s = input().strip()\nprint(len(s))\nprint(s[0])",
                "python",
                "6\np",
            ),
            problem(
                "[모의1-6] 점수 등급 출력",
                ["점수가 입력되면 90 이상 A, 80 이상 B, 70 이상 C, 60 이상 D, 그 외 F를 출력하세요."],
                "큰 값부터 elif 로 비교하세요.",
                "s = int(input())\nif s >= 90:\n    print('A')\nelif s >= 80:\n    print('B')\nelif s >= 70:\n    print('C')\nelif s >= 60:\n    print('D')\nelse:\n    print('F')",
                "73",
                "C",
            ),
            problem(
                "[모의1-7] 리스트 최댓값과 합계",
                ["한 줄에 정수 다섯 개가 입력됩니다. 첫째 줄에 최댓값, 둘째 줄에 합계를 출력하세요."],
                "최댓값은 반복 비교, 합계는 sum 을 활용하세요.",
                "nums = list(map(int, input().split()))\nmax_v = nums[0]\nfor n in nums:\n    if n > max_v:\n        max_v = n\nprint(max_v)\nprint(sum(nums))",
                "3 8 1 5 4",
                "8\n21",
            ),
            problem(
                "[모의1-8] 특정 문자 제거",
                ["문자열이 입력되면 모든 공백을 제거해 출력하세요."],
                "replace(' ', '') 를 사용하세요.",
                "s = input()\nprint(s.replace(' ', ''))",
                "a b c d",
                "abcd",
            ),
            problem(
                "[모의1-9] 두 수 비교 함수",
                ["정수 두 개가 입력되면 compare(a, b) 함수를 만들어 a > b 면 1, a == b 면 0, a < b 면 -1 을 출력하세요."],
                "세 경우를 if-elif-else 로 처리하세요.",
                "def compare(a, b):\n    if a > b:\n        return 1\n    elif a == b:\n        return 0\n    else:\n        return -1\n\na, b = map(int, input().split())\nprint(compare(a, b))",
                "5 3",
                "1",
            ),
            problem(
                "[모의1-10] 구구단 전체 출력",
                ["정수 n이 입력되면 1단부터 n단까지 각 단의 결과를 한 줄에 하나씩 출력하세요. 형식: 단×배수=결과"],
                "중첩 for 문을 사용하세요.",
                "n = int(input())\nfor i in range(1, n + 1):\n    for j in range(1, 10):\n        print(f'{i}x{j}={i*j}')",
                "2",
                "1x1=1\n1x2=2\n1x3=3\n1x4=4\n1x5=5\n1x6=6\n1x7=7\n1x8=8\n1x9=9\n2x1=2\n2x2=4\n2x3=6\n2x4=8\n2x5=10\n2x6=12\n2x7=14\n2x8=16\n2x9=18",
            ),
        ],
    })

    # ── 9장: 실전 모의고사 2 ─────────────────────────────────────────────────
    chapters.append({
        "title": "실전 모의고사 2",
        "content": "조금 더 응용된 COS Pro 3급 스타일 문제입니다. 실제 시험처럼 풀어보세요.",
        "items": [
            problem(
                "[모의2-1] 이름에 님 붙이기",
                ["이름이 입력되면 이름 뒤에 님을 붙여 출력하세요."],
                "문자열 이어 붙이기 또는 f-string 을 사용하세요.",
                "name = input().strip()\nprint(name + '님')",
                "홍길동",
                "홍길동님",
            ),
            problem(
                "[모의2-2] 두 수의 차의 절댓값",
                ["정수 두 개가 입력되면 두 수의 차의 절댓값을 출력하세요."],
                "큰 수에서 작은 수를 빼거나, abs 를 사용하세요.",
                "a, b = map(int, input().split())\nprint(abs(a - b))",
                "8 13",
                "5",
            ),
            problem(
                "[모의2-3] 세 수의 최솟값",
                ["정수 세 개가 입력되면 가장 작은 수를 출력하세요."],
                "최솟값 변수를 두고 하나씩 비교하세요.",
                "a, b, c = map(int, input().split())\nmin_v = a\nif b < min_v:\n    min_v = b\nif c < min_v:\n    min_v = c\nprint(min_v)",
                "5 2 8",
                "2",
            ),
            problem(
                "[모의2-4] 범위 안의 수 개수",
                ["한 줄에 정수 다섯 개가 입력됩니다. 10 이상 50 이하인 수의 개수를 출력하세요."],
                "and 로 두 조건을 연결하세요.",
                "nums = list(map(int, input().split()))\ncount = 0\nfor n in nums:\n    if 10 <= n <= 50:\n        count += 1\nprint(count)",
                "5 15 30 55 45",
                "3",
            ),
            problem(
                "[모의2-5] 문자열 앞뒤 공백 제거 후 길이",
                ["문자열이 입력되면 앞뒤 공백을 제거한 뒤 길이를 출력하세요."],
                "strip 메서드 후 len 을 적용하세요.",
                "s = input().strip()\nprint(len(s))",
                "  hello  ",
                "5",
            ),
            problem(
                "[모의2-6] 문자열 반복 출력",
                ["문자열과 반복 횟수가 한 줄에 입력됩니다. 해당 횟수만큼 반복해 출력하세요."],
                "문자열 * 정수 형태를 사용하세요.",
                "parts = input().split()\ns = parts[0]\nn = int(parts[1])\nprint(s * n)",
                "abc 3",
                "abcabcabc",
            ),
            problem(
                "[모의2-7] 1부터 n까지 홀수 합",
                ["정수 n이 입력되면 1부터 n까지 홀수들의 합을 출력하세요."],
                "홀수 조건을 반복 안에서 확인하세요.",
                "n = int(input())\ntotal = 0\nfor i in range(1, n + 1):\n    if i % 2 == 1:\n        total += i\nprint(total)",
                "9",
                "25",
            ),
            problem(
                "[모의2-8] 리스트에서 짝수만 출력",
                ["한 줄에 정수 다섯 개가 입력됩니다. 짝수만 한 줄에 하나씩 출력하세요."],
                "각 값에 % 2 == 0 조건을 적용하세요.",
                "nums = list(map(int, input().split()))\nfor n in nums:\n    if n % 2 == 0:\n        print(n)",
                "1 2 3 4 5",
                "2\n4",
            ),
            problem(
                "[모의2-9] 단어 수 세기",
                ["문장이 입력되면 공백으로 나뉜 단어 수를 출력하세요."],
                "split 결과의 len 을 구하면 됩니다.",
                "words = input().split()\nprint(len(words))",
                "I love Python programming",
                "4",
            ),
            problem(
                "[모의2-10] 성적 처리 함수",
                ["점수가 입력되면 get_grade(score) 함수를 만들어 90 이상 A, 80 이상 B, 70 이상 C, 그 외 F를 출력하세요."],
                "함수 안에서 if-elif-else 로 등급을 반환하세요.",
                "def get_grade(score):\n    if score >= 90:\n        return 'A'\n    elif score >= 80:\n        return 'B'\n    elif score >= 70:\n        return 'C'\n    else:\n        return 'F'\n\nn = int(input())\nprint(get_grade(n))",
                "78",
                "C",
            ),
        ],
    })

    # ── 10장: 실전 모의고사 3 ────────────────────────────────────────────────
    chapters.append({
        "title": "실전 모의고사 3",
        "content": "기출 유형을 종합한 최종 모의고사입니다. 실제 시험 환경처럼 40분 안에 도전하세요.",
        "items": [
            problem(
                "[모의3-1] 정수 두 개로 사칙연산",
                ["정수 두 개가 한 줄에 입력됩니다. 합, 차, 곱, 나눗셈 결과를 각각 한 줄씩 출력하세요. 나눗셈은 실수로 출력하세요."],
                "각 연산 결과를 차례로 print 하세요.",
                "a, b = map(int, input().split())\nprint(a + b)\nprint(a - b)\nprint(a * b)\nprint(a / b)",
                "10 4",
                "14\n6\n40\n2.5",
            ),
            problem(
                "[모의3-2] 별 사각형",
                ["정수 n이 입력되면 n행 n열의 별 사각형을 출력하세요."],
                "'*' * n 을 n번 출력하세요.",
                "n = int(input())\nfor i in range(n):\n    print('*' * n)",
                "3",
                "***\n***\n***",
            ),
            problem(
                "[모의3-3] 합격 여부와 평균",
                ["세 과목 점수가 한 줄에 입력됩니다. 평균을 첫째 줄에 출력하고, 평균이 60 이상이면 합격, 미만이면 불합격을 둘째 줄에 출력하세요."],
                "평균 계산 후 조건을 판단하세요.",
                "a, b, c = map(int, input().split())\navg = (a + b + c) / 3\nprint(avg)\nif avg >= 60:\n    print('합격')\nelse:\n    print('불합격')",
                "70 80 90",
                "80.0\n합격",
            ),
            problem(
                "[모의3-4] 문자열 대소문자 교환",
                ["영문 문자열이 입력되면 대문자는 소문자로, 소문자는 대문자로 바꿔 출력하세요."],
                "swapcase 메서드를 사용하세요.",
                "s = input().strip()\nprint(s.swapcase())",
                "Hello World",
                "hELLO wORLD",
            ),
            problem(
                "[모의3-5] 1부터 n까지 합: while 문 사용",
                ["정수 n이 입력되면 while 문을 사용해 1부터 n까지의 합을 출력하세요."],
                "i <= n 조건을 확인하며 i를 증가시키세요.",
                "n = int(input())\ntotal = 0\ni = 1\nwhile i <= n:\n    total += i\n    i += 1\nprint(total)",
                "10",
                "55",
            ),
            problem(
                "[모의3-6] 리스트 평균",
                ["한 줄에 정수 다섯 개가 입력됩니다. 평균을 출력하세요."],
                "sum / len 을 사용하세요.",
                "nums = list(map(int, input().split()))\nprint(sum(nums) / len(nums))",
                "10 20 30 40 50",
                "30.0",
            ),
            problem(
                "[모의3-7] 특정 문자로 시작하는 단어 개수",
                ["첫 줄에 단어 여러 개가 공백으로 구분되어 입력되고, 둘째 줄에 알파벳 한 글자가 입력됩니다. 해당 문자로 시작하는 단어의 수를 출력하세요."],
                "word[0] == ch 로 확인하세요.",
                "words = input().split()\nch = input().strip()\ncount = 0\nfor word in words:\n    if word[0] == ch:\n        count += 1\nprint(count)",
                "apple art banana avocado\na",
                "3",
            ),
            problem(
                "[모의3-8] 두 리스트 합치기",
                ["첫 줄과 둘째 줄에 각각 정수 세 개가 입력됩니다. 두 줄의 수를 이어 붙여 합계를 출력하세요."],
                "리스트끼리 + 로 합친 뒤 sum 을 사용하세요.",
                "a = list(map(int, input().split()))\nb = list(map(int, input().split()))\nprint(sum(a + b))",
                "1 2 3\n4 5 6",
                "21",
            ),
            problem(
                "[모의3-9] 회문 검사 함수",
                ["문자열이 입력되면 is_palindrome(s) 함수로 회문이면 YES, 아니면 NO를 출력하세요."],
                "s == s[::-1] 로 비교하세요.",
                "def is_palindrome(s):\n    if s == s[::-1]:\n        return 'YES'\n    return 'NO'\n\ns = input().strip()\nprint(is_palindrome(s))",
                "level",
                "YES",
            ),
            problem(
                "[모의3-10] 숫자 자릿수 합",
                ["양의 정수가 입력되면 각 자리 숫자의 합을 출력하세요."],
                "문자열로 변환 후 각 문자를 int 로 바꿔 더하세요.",
                "n = input().strip()\ntotal = 0\nfor ch in n:\n    total += int(ch)\nprint(total)",
                "12345",
                "15",
            ),
        ],
    })

    total_items = sum(len(chapter["items"]) for chapter in chapters)
    if total_items != 100:
        raise ValueError(f"문항 수가 100개가 아닙니다: {total_items}")
    return chapters


class Command(BaseCommand):
    help = "YBM COS Pro 파이썬 3급 대비 과정(100문제)을 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="같은 이름의 과정이 있으면 문항을 모두 지우고 다시 생성합니다.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        program_type, _ = ProgramType.objects.get_or_create(
            name=PROGRAM_TYPE_NAME,
            defaults={"order": 40},
        )

        program, created = LearningProgram.objects.get_or_create(
            name=COURSE_NAME,
            defaults={
                "description": (
                    "YBM IT COS Pro 파이썬 3급 자격증 취득을 위한 단계별 연습 과정입니다. "
                    "출력·변수·연산자·조건문·반복문·문자열·리스트·함수를 체계적으로 익히고, "
                    "실전 모의고사 3세트(각 10문제)로 실제 시험을 대비합니다. "
                    "시험: 10문제 / 40분 / 1,000점 만점 / 600점 이상 합격"
                ),
                "program_type": program_type,
                "is_active": True,
            },
        )

        if not created and not options["replace"] and program.chapters.exists():
            self.stdout.write(
                self.style.WARNING("이미 같은 이름의 과정이 있습니다. 다시 넣으려면 --replace 옵션을 사용하세요.")
            )
            return

        program.description = (
            "YBM IT COS Pro 파이썬 3급 자격증 취득을 위한 단계별 연습 과정입니다. "
            "출력·변수·연산자·조건문·반복문·문자열·리스트·함수를 체계적으로 익히고, "
            "실전 모의고사 3세트(각 10문제)로 실제 시험을 대비합니다. "
            "시험: 10문제 / 40분 / 1,000점 만점 / 600점 이상 합격"
        )
        program.program_type = program_type
        program.is_active = True
        program.save()

        program.chapters.all().delete()

        chapters = build_course_data()
        item_total = 0

        for chapter_index, chapter_data in enumerate(chapters, start=1):
            chapter = Chapter.objects.create(
                program=program,
                number=chapter_index,
                title=chapter_data["title"],
                content=chapter_data["content"],
            )

            for item_index, item_data in enumerate(chapter_data["items"], start=1):
                item_total += 1
                Item.objects.create(
                    chapter=chapter,
                    number=item_index,
                    key=f"cos3_{chapter_index:02d}_{item_index:02d}",
                    title=item_data["title"],
                    item_type="problem",
                    explain_html=item_data["explain_html"],
                    hint=item_data["hint"],
                    answer_code=item_data["answer_code"],
                    example_input=item_data["example_input"],
                    expected_output=item_data["expected_output"],
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"'{COURSE_NAME}' 과정이 생성되었습니다. (총 {item_total}문제)"
            )
        )
