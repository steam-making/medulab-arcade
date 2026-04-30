from html import escape

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Chapter, Item, LearningProgram, ProgramType


COURSE_NAME = "COS Pro 파이썬 2급 대비"
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

    # ── 1장: 리스트 심화 ─────────────────────────────────────────────────────
    chapters.append({
        "title": "리스트 심화",
        "content": "리스트 컴프리헨션, 2차원 리스트, 슬라이싱, enumerate, zip 등 고급 리스트 활용을 익힙니다.",
        "items": [
            problem(
                "리스트 컴프리헨션으로 제곱 리스트",
                ["정수 n이 입력되면 1부터 n까지 각 수의 제곱으로 이루어진 리스트를 출력하세요."],
                "[x**2 for x in range(1, n+1)] 형태를 사용하세요.",
                "n = int(input())\nresult = [x**2 for x in range(1, n+1)]\nprint(result)",
                "5",
                "[1, 4, 9, 16, 25]",
            ),
            problem(
                "짝수만 골라내기 (컴프리헨션)",
                ["한 줄에 정수 여러 개가 입력됩니다. 짝수만 추출해 리스트로 출력하세요."],
                "[x for x in nums if x % 2 == 0] 형태를 사용하세요.",
                "nums = list(map(int, input().split()))\nresult = [x for x in nums if x % 2 == 0]\nprint(result)",
                "1 2 3 4 5 6",
                "[2, 4, 6]",
            ),
            problem(
                "2차원 리스트 합계",
                ["3행 3열로 정수 9개가 세 줄에 걸쳐 입력됩니다. 모든 원소의 합을 출력하세요."],
                "2중 for 또는 sum(sum(row) for row in matrix) 를 사용하세요.",
                "matrix = []\nfor _ in range(3):\n    row = list(map(int, input().split()))\n    matrix.append(row)\ntotal = 0\nfor row in matrix:\n    for val in row:\n        total += val\nprint(total)",
                "1 2 3\n4 5 6\n7 8 9",
                "45",
            ),
            problem(
                "2차원 리스트 대각선 합",
                ["3행 3열 행렬이 세 줄에 입력됩니다. 왼쪽 위에서 오른쪽 아래로의 대각선 합을 출력하세요."],
                "인덱스 i, i 를 사용하세요.",
                "matrix = [list(map(int, input().split())) for _ in range(3)]\ntotal = sum(matrix[i][i] for i in range(3))\nprint(total)",
                "1 2 3\n4 5 6\n7 8 9",
                "15",
            ),
            problem(
                "enumerate 로 인덱스와 값 출력",
                ["단어 여러 개가 한 줄에 입력됩니다. 0번 인덱스부터 인덱스:단어 형식으로 한 줄씩 출력하세요."],
                "for i, word in enumerate(words): 를 사용하세요.",
                "words = input().split()\nfor i, word in enumerate(words):\n    print(f'{i}:{word}')",
                "apple banana cherry",
                "0:apple\n1:banana\n2:cherry",
            ),
            problem(
                "zip으로 두 리스트 합산",
                ["두 줄에 각각 정수 세 개씩 입력됩니다. 같은 위치의 값을 더한 결과를 공백으로 구분해 출력하세요."],
                "for a, b in zip(list1, list2): 를 사용하세요.",
                "a = list(map(int, input().split()))\nb = list(map(int, input().split()))\nresult = [x + y for x, y in zip(a, b)]\nprint(*result)",
                "1 2 3\n4 5 6",
                "5 7 9",
            ),
            problem(
                "리스트 슬라이싱으로 중간 부분 추출",
                ["한 줄에 정수 여섯 개가 입력됩니다. 인덱스 2부터 4까지(4 포함)의 원소를 출력하세요."],
                "슬라이싱 [2:5] 를 사용하세요.",
                "nums = list(map(int, input().split()))\nprint(*nums[2:5])",
                "10 20 30 40 50 60",
                "30 40 50",
            ),
            problem(
                "리스트 중복 제거 후 정렬",
                ["정수 여러 개가 한 줄에 입력됩니다. 중복을 제거하고 오름차순으로 정렬해 출력하세요."],
                "set 으로 중복 제거 후 sorted 로 정렬하세요.",
                "nums = list(map(int, input().split()))\nresult = sorted(set(nums))\nprint(*result)",
                "3 1 4 1 5 9 2 6 5 3",
                "1 2 3 4 5 6 9",
            ),
            problem(
                "리스트 회전",
                ["한 줄에 정수 다섯 개와 회전 횟수 k가 한 줄씩 입력됩니다. 리스트를 왼쪽으로 k번 회전한 결과를 출력하세요."],
                "nums[k:] + nums[:k] 형태를 사용하세요.",
                "nums = list(map(int, input().split()))\nk = int(input())\nresult = nums[k:] + nums[:k]\nprint(*result)",
                "1 2 3 4 5\n2",
                "3 4 5 1 2",
            ),
            problem(
                "조건부 리스트 변환",
                ["한 줄에 정수 여러 개가 입력됩니다. 짝수는 그대로, 홀수는 -1을 곱해 출력하세요."],
                "컴프리헨션 안에 조건식 x if x%2==0 else -x 를 사용하세요.",
                "nums = list(map(int, input().split()))\nresult = [x if x % 2 == 0 else -x for x in nums]\nprint(*result)",
                "1 2 3 4 5",
                "-1 2 -3 4 -5",
            ),
        ],
    })

    # ── 2장: 딕셔너리와 집합 심화 ────────────────────────────────────────────
    chapters.append({
        "title": "딕셔너리와 집합 심화",
        "content": "딕셔너리의 items, keys, values, get, setdefault 와 집합 연산을 익힙니다.",
        "items": [
            problem(
                "단어 빈도 계산",
                ["단어 여러 개가 한 줄에 입력됩니다. 각 단어가 몇 번 나오는지 단어:횟수 형식으로 입력 순서에 따라 출력하세요."],
                "setdefault(word, 0) 또는 get(word, 0)+1 을 활용하세요.",
                "words = input().split()\ncount = {}\nfor w in words:\n    count[w] = count.get(w, 0) + 1\nfor k, v in count.items():\n    print(f'{k}:{v}')",
                "apple banana apple cherry banana apple",
                "apple:3\nbanana:2\ncherry:1",
            ),
            problem(
                "딕셔너리 값 중 최댓값 키",
                ["딕셔너리 형태로 이름:점수 쌍이 여러 줄 입력됩니다. 점수가 가장 높은 이름을 출력하세요. 입력의 마지막은 END 입니다."],
                "items() 로 순회하며 최대 값을 찾으세요.",
                "scores = {}\nwhile True:\n    line = input().strip()\n    if line == 'END':\n        break\n    name, score = line.split(':')\n    scores[name] = int(score)\nbest = max(scores, key=scores.get)\nprint(best)",
                "Alice:90\nBob:85\nChris:95\nEND",
                "Chris",
            ),
            problem(
                "두 딕셔너리 병합",
                ["두 줄에 각각 key:value 쌍이 콤마로 구분되어 입력됩니다. 두 딕셔너리를 합쳐 key를 오름차순으로 정렬해 출력하세요."],
                "update 메서드나 ** 언패킹으로 병합하세요.",
                "def parse(line):\n    d = {}\n    for item in line.split(','):\n        k, v = item.strip().split(':')\n        d[k.strip()] = v.strip()\n    return d\na = parse(input())\nb = parse(input())\nmerged = {**a, **b}\nfor k in sorted(merged):\n    print(f'{k}:{merged[k]}')",
                "a:1, b:2\nc:3, d:4",
                "a:1\nb:2\nc:3\nd:4",
            ),
            problem(
                "집합 교집합·합집합·차집합",
                ["두 줄에 각각 정수 여러 개가 입력됩니다. 합집합, 교집합, 차집합(첫째-둘째)을 각각 정렬해 출력하세요."],
                "set 연산자 |, &, - 를 사용하세요.",
                "a = set(map(int, input().split()))\nb = set(map(int, input().split()))\nprint(*sorted(a | b))\nprint(*sorted(a & b))\nprint(*sorted(a - b))",
                "1 2 3 4 5\n3 4 5 6 7",
                "1 2 3 4 5 6 7\n3 4 5\n1 2",
            ),
            problem(
                "딕셔너리로 학생 성적 관리",
                ["이름과 점수가 공백으로 구분된 줄이 여러 개 입력됩니다. 마지막 줄은 END 입니다. 모든 학생의 평균 점수를 소수 첫째 자리로 출력하세요."],
                "점수 합계를 학생 수로 나누세요.",
                "scores = {}\nwhile True:\n    line = input().strip()\n    if line == 'END':\n        break\n    name, score = line.split()\n    scores[name] = int(score)\nprint(round(sum(scores.values()) / len(scores), 1))",
                "Alice 90\nBob 80\nChris 70\nEND",
                "80.0",
            ),
            problem(
                "중복 없는 문자 개수",
                ["문자열이 입력되면 서로 다른 문자의 수를 출력하세요."],
                "set 으로 중복을 제거하고 len 을 사용하세요.",
                "s = input().strip()\nprint(len(set(s)))",
                "mississippi",
                "4",
            ),
            problem(
                "딕셔너리 키 존재 확인 후 업데이트",
                ["첫 줄에 초기 재고(상품명:수량, 콤마 구분), 둘째 줄에 판매 상품명이 입력됩니다. 판매 후 해당 상품 수량을 1 줄이고 출력하세요. 없으면 없음을 출력하세요."],
                "get 으로 확인 후 값을 수정하세요.",
                "stock = {}\nfor item in input().split(','):\n    k, v = item.strip().split(':')\n    stock[k.strip()] = int(v.strip())\nname = input().strip()\nif name in stock:\n    stock[name] -= 1\n    print(f'{name}:{stock[name]}')\nelse:\n    print('없음')",
                "사과:5, 바나나:3, 포도:2\n바나나",
                "바나나:2",
            ),
            problem(
                "두 집합이 같은지 확인",
                ["두 줄에 각각 정수 여러 개가 입력됩니다. 두 집합이 같으면 SAME, 다르면 DIFFERENT를 출력하세요."],
                "set 변환 후 == 로 비교하세요.",
                "a = set(map(int, input().split()))\nb = set(map(int, input().split()))\nprint('SAME' if a == b else 'DIFFERENT')",
                "1 2 3\n3 1 2",
                "SAME",
            ),
            problem(
                "딕셔너리 값 역순 정렬 출력",
                ["이름:점수 쌍 여러 개가 콤마로 구분되어 입력됩니다. 점수 높은 순으로 이름만 한 줄씩 출력하세요."],
                "sorted(d.items(), key=lambda x: x[1], reverse=True) 를 사용하세요.",
                "d = {}\nfor item in input().split(','):\n    k, v = item.strip().split(':')\n    d[k.strip()] = int(v.strip())\nfor name, _ in sorted(d.items(), key=lambda x: x[1], reverse=True):\n    print(name)",
                "Alice:85, Bob:92, Chris:78",
                "Bob\nAlice\nChris",
            ),
            problem(
                "리스트를 딕셔너리로 변환",
                ["키 목록과 값 목록이 한 줄씩 입력됩니다. 두 리스트를 묶어 딕셔너리로 만든 뒤 키 오름차순으로 출력하세요."],
                "dict(zip(keys, values)) 를 사용하세요.",
                "keys = input().split()\nvals = input().split()\nd = dict(zip(keys, vals))\nfor k in sorted(d):\n    print(f'{k}:{d[k]}')",
                "c a b\n3 1 2",
                "a:1\nb:2\nc:3",
            ),
        ],
    })

    # ── 3장: 문자열 처리 심화 ────────────────────────────────────────────────
    chapters.append({
        "title": "문자열 처리 심화",
        "content": "format, join, split, strip, find, startswith, endswith 와 문자열 알고리즘을 익힙니다.",
        "items": [
            problem(
                "단어 역순으로 문장 재구성",
                ["문장이 입력되면 단어 순서를 거꾸로 해 출력하세요."],
                "split 후 reverse 또는 슬라이싱 [::-1] 을 사용하세요.",
                "words = input().split()\nprint(' '.join(words[::-1]))",
                "I love Python programming",
                "programming Python love I",
            ),
            problem(
                "문자열에서 숫자만 추출",
                ["영숫자가 섞인 문자열이 입력되면 숫자만 이어 붙여 출력하세요."],
                "isdigit 메서드로 확인하세요.",
                "s = input().strip()\nprint(''.join(ch for ch in s if ch.isdigit()))",
                "a1b2c3d4",
                "1234",
            ),
            problem(
                "가장 많이 나온 단어",
                ["문장이 입력되면 가장 많이 등장한 단어를 출력하세요. 동률이면 먼저 나온 단어를 출력하세요."],
                "딕셔너리로 빈도를 세고 max 로 찾으세요.",
                "words = input().split()\ncount = {}\norder = []\nfor w in words:\n    if w not in count:\n        count[w] = 0\n        order.append(w)\n    count[w] += 1\nbest = order[0]\nfor w in order:\n    if count[w] > count[best]:\n        best = w\nprint(best)",
                "apple banana apple cherry banana apple",
                "apple",
            ),
            problem(
                "카멜케이스를 스네이크케이스로",
                ["camelCase 형식의 단어가 입력되면 snake_case 형식으로 변환해 출력하세요. 대문자 앞에 _ 를 붙이고 소문자로 바꾸세요."],
                "각 문자를 순회하며 대문자면 '_' + lower() 를 붙이세요.",
                "s = input().strip()\nresult = ''\nfor i, ch in enumerate(s):\n    if ch.isupper() and i != 0:\n        result += '_' + ch.lower()\n    else:\n        result += ch.lower()\nprint(result)",
                "myVariableName",
                "my_variable_name",
            ),
            problem(
                "문자열 압축",
                ["문자열이 입력되면 연속된 같은 문자를 문자+개수로 압축해 출력하세요. 개수가 1이어도 표시하세요."],
                "이전 문자와 현재 문자를 비교하며 count 를 관리하세요.",
                "s = input().strip()\nif not s:\n    print('')\nelse:\n    result = ''\n    count = 1\n    for i in range(1, len(s)):\n        if s[i] == s[i-1]:\n            count += 1\n        else:\n            result += s[i-1] + str(count)\n            count = 1\n    result += s[-1] + str(count)\n    print(result)",
                "aaabbbccddddee",
                "a3b3c2d4e2",
            ),
            problem(
                "특정 접두사로 시작하는 단어 필터",
                ["첫 줄에 단어 여러 개, 둘째 줄에 접두사가 입력됩니다. 해당 접두사로 시작하는 단어만 순서대로 출력하세요."],
                "startswith 메서드를 사용하세요.",
                "words = input().split()\nprefix = input().strip()\nfor w in words:\n    if w.startswith(prefix):\n        print(w)",
                "python programming java pascal perl\np",
                "python\nprogramming\npascal\nperl",
            ),
            problem(
                "이메일 도메인 추출",
                ["이메일 주소가 입력되면 @ 뒤의 도메인 부분만 출력하세요."],
                "split('@')[1] 을 사용하세요.",
                "email = input().strip()\nprint(email.split('@')[1])",
                "user@example.com",
                "example.com",
            ),
            problem(
                "문자열 내 부분 문자열 위치 찾기",
                ["첫 줄에 문자열, 둘째 줄에 찾을 부분 문자열이 입력됩니다. 처음 등장하는 인덱스를 출력하고, 없으면 -1을 출력하세요."],
                "find 메서드를 사용하세요.",
                "s = input()\nsub = input().strip()\nprint(s.find(sub))",
                "hello world\nworld",
                "6",
            ),
            problem(
                "단어 첫 글자 대문자로 변환",
                ["문장이 입력되면 각 단어의 첫 글자를 대문자로 바꿔 출력하세요."],
                "title 메서드 또는 capitalize 를 join 과 함께 사용하세요.",
                "s = input()\nprint(s.title())",
                "hello world python",
                "Hello World Python",
            ),
            problem(
                "문자열을 특정 너비로 정렬",
                ["문자열과 너비가 한 줄씩 입력됩니다. 너비에 맞게 오른쪽 정렬해 출력하세요. 빈 자리는 공백으로 채우세요."],
                "rjust(width) 메서드를 사용하세요.",
                "s = input().strip()\nw = int(input())\nprint(s.rjust(w))",
                "hello\n10",
                "     hello",
            ),
        ],
    })

    # ── 4장: 함수 심화 (재귀·람다·고급) ─────────────────────────────────────
    chapters.append({
        "title": "함수 심화 (재귀·람다·고급)",
        "content": "재귀함수, 람다, map, filter, sorted 의 key 인수, 기본값 인수를 익힙니다.",
        "items": [
            problem(
                "재귀로 팩토리얼",
                ["정수 n이 입력되면 재귀 함수로 n! 을 계산해 출력하세요."],
                "factorial(n) = n * factorial(n-1), 기저 조건은 n <= 1 입니다.",
                "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial(int(input())))",
                "6",
                "720",
            ),
            problem(
                "재귀로 피보나치",
                ["정수 n이 입력되면 피보나치 수열의 n번째 값을 출력하세요. (F(1)=1, F(2)=1)"],
                "fib(n) = fib(n-1) + fib(n-2), 기저 조건은 n <= 2 입니다.",
                "def fib(n):\n    if n <= 2:\n        return 1\n    return fib(n - 1) + fib(n - 2)\n\nprint(fib(int(input())))",
                "7",
                "13",
            ),
            problem(
                "재귀로 거듭제곱",
                ["밑(base)과 지수(exp)가 입력되면 재귀로 base^exp 를 계산해 출력하세요."],
                "power(b, e) = b * power(b, e-1), 기저 조건은 e == 0 입니다.",
                "def power(b, e):\n    if e == 0:\n        return 1\n    return b * power(b, e - 1)\n\nb, e = map(int, input().split())\nprint(power(b, e))",
                "2 10",
                "1024",
            ),
            problem(
                "람다와 sorted 로 튜플 정렬",
                ["이름:점수 쌍 여러 개가 콤마로 구분되어 입력됩니다. 점수 오름차순으로 이름을 출력하세요."],
                "sorted(..., key=lambda x: x[1]) 을 사용하세요.",
                "data = []\nfor item in input().split(','):\n    k, v = item.strip().split(':')\n    data.append((k.strip(), int(v.strip())))\nfor name, _ in sorted(data, key=lambda x: x[1]):\n    print(name)",
                "Alice:85, Bob:92, Chris:78",
                "Chris\nAlice\nBob",
            ),
            problem(
                "map으로 일괄 변환",
                ["정수 여러 개가 입력됩니다. 각 값에 2를 곱한 결과를 공백으로 구분해 출력하세요."],
                "map(lambda x: x*2, nums) 를 사용하세요.",
                "nums = list(map(int, input().split()))\nresult = list(map(lambda x: x * 2, nums))\nprint(*result)",
                "1 2 3 4 5",
                "2 4 6 8 10",
            ),
            problem(
                "filter로 양수만 추출",
                ["정수 여러 개가 입력됩니다. 양수만 추출해 공백으로 구분해 출력하세요."],
                "filter(lambda x: x > 0, nums) 를 사용하세요.",
                "nums = list(map(int, input().split()))\nresult = list(filter(lambda x: x > 0, nums))\nprint(*result)",
                "-3 1 -2 4 0 5",
                "1 4 5",
            ),
            problem(
                "기본값 인수가 있는 함수",
                ["이름과 선택적으로 인삿말이 한 줄에 입력됩니다(인삿말 없으면 이름만). 인삿말이 없으면 안녕하세요를 기본값으로 사용해 인삿말, 이름님! 형식으로 출력하세요."],
                "def greet(name, msg='안녕하세요'): 처럼 기본값을 설정하세요.",
                "def greet(name, msg='안녕하세요'):\n    print(f'{msg}, {name}님!')\n\nparts = input().strip().split()\nif len(parts) == 1:\n    greet(parts[0])\nelse:\n    greet(parts[0], parts[1])",
                "민지 반갑습니다",
                "반갑습니다, 민지님!",
            ),
            problem(
                "재귀로 리스트 합계",
                ["한 줄에 정수 여러 개가 입력됩니다. 재귀 함수로 합계를 계산해 출력하세요."],
                "list_sum(lst) = lst[0] + list_sum(lst[1:]), 기저 조건은 빈 리스트입니다.",
                "def list_sum(lst):\n    if not lst:\n        return 0\n    return lst[0] + list_sum(lst[1:])\n\nnums = list(map(int, input().split()))\nprint(list_sum(nums))",
                "1 2 3 4 5",
                "15",
            ),
            problem(
                "재귀로 최대공약수(GCD)",
                ["두 양의 정수가 입력되면 유클리드 알고리즘(재귀)으로 GCD를 구해 출력하세요."],
                "gcd(a, b) = gcd(b, a%b), gcd(a, 0) = a 입니다.",
                "def gcd(a, b):\n    if b == 0:\n        return a\n    return gcd(b, a % b)\n\na, b = map(int, input().split())\nprint(gcd(a, b))",
                "48 18",
                "6",
            ),
            problem(
                "함수를 인수로 전달",
                ["정수 여러 개와 연산 기호(+, *)가 입력됩니다. + 면 합계, * 면 곱을 출력하세요."],
                "딕셔너리에 lambda 를 저장해 선택하세요.",
                "from functools import reduce\nnums = list(map(int, input().split()))\nop = input().strip()\nops = {'+': lambda a, b: a + b, '*': lambda a, b: a * b}\nprint(reduce(ops[op], nums))",
                "1 2 3 4 5\n+",
                "15",
            ),
        ],
    })

    # ── 5장: 정렬 알고리즘 기초 ──────────────────────────────────────────────
    chapters.append({
        "title": "정렬 알고리즘 기초",
        "content": "버블 정렬, 선택 정렬, 삽입 정렬을 직접 구현하고 이해합니다.",
        "items": [
            problem(
                "버블 정렬 구현",
                ["한 줄에 정수 여러 개가 입력됩니다. 버블 정렬을 직접 구현해 오름차순 결과를 출력하세요."],
                "인접한 두 원소를 비교하며 교환하는 과정을 n-1번 반복하세요.",
                "nums = list(map(int, input().split()))\nn = len(nums)\nfor i in range(n - 1):\n    for j in range(n - 1 - i):\n        if nums[j] > nums[j + 1]:\n            nums[j], nums[j + 1] = nums[j + 1], nums[j]\nprint(*nums)",
                "5 3 8 1 9 2",
                "1 2 3 5 8 9",
            ),
            problem(
                "선택 정렬 구현",
                ["한 줄에 정수 여러 개가 입력됩니다. 선택 정렬을 직접 구현해 오름차순 결과를 출력하세요."],
                "각 위치에서 나머지 중 최솟값을 찾아 교환하세요.",
                "nums = list(map(int, input().split()))\nn = len(nums)\nfor i in range(n):\n    min_idx = i\n    for j in range(i + 1, n):\n        if nums[j] < nums[min_idx]:\n            min_idx = j\n    nums[i], nums[min_idx] = nums[min_idx], nums[i]\nprint(*nums)",
                "5 3 8 1 9 2",
                "1 2 3 5 8 9",
            ),
            problem(
                "삽입 정렬 구현",
                ["한 줄에 정수 여러 개가 입력됩니다. 삽입 정렬을 직접 구현해 오름차순 결과를 출력하세요."],
                "현재 원소를 이미 정렬된 부분의 올바른 위치에 삽입하세요.",
                "nums = list(map(int, input().split()))\nfor i in range(1, len(nums)):\n    key = nums[i]\n    j = i - 1\n    while j >= 0 and nums[j] > key:\n        nums[j + 1] = nums[j]\n        j -= 1\n    nums[j + 1] = key\nprint(*nums)",
                "5 3 8 1 9 2",
                "1 2 3 5 8 9",
            ),
            problem(
                "내림차순 정렬",
                ["한 줄에 정수 여러 개가 입력됩니다. 내림차순으로 정렬해 출력하세요."],
                "sorted(..., reverse=True) 를 사용하세요.",
                "nums = list(map(int, input().split()))\nprint(*sorted(nums, reverse=True))",
                "5 3 8 1 9 2",
                "9 8 5 3 2 1",
            ),
            problem(
                "문자열 길이 기준 정렬",
                ["단어 여러 개가 한 줄에 입력됩니다. 길이 오름차순으로 정렬하고, 길이가 같으면 알파벳 순으로 출력하세요."],
                "sorted(words, key=lambda x: (len(x), x)) 를 사용하세요.",
                "words = input().split()\nresult = sorted(words, key=lambda x: (len(x), x))\nprint(*result)",
                "banana apple kiwi fig cherry",
                "fig kiwi apple banana cherry",
            ),
            problem(
                "k번째로 작은 값",
                ["첫 줄에 정수 여러 개, 둘째 줄에 k가 입력됩니다. k번째로 작은 값을 출력하세요. (k는 1부터 시작)"],
                "정렬 후 인덱스 k-1 을 출력하세요.",
                "nums = list(map(int, input().split()))\nk = int(input())\nnums.sort()\nprint(nums[k - 1])",
                "5 3 8 1 9 2\n3",
                "3",
            ),
            problem(
                "정렬 후 중앙값",
                ["정수 홀수 개가 한 줄에 입력됩니다. 정렬 후 중앙값을 출력하세요."],
                "정렬 후 인덱스 n//2 를 사용하세요.",
                "nums = sorted(map(int, input().split()))\nprint(nums[len(nums) // 2])",
                "3 1 4 1 5 9 2",
                "3",
            ),
            problem(
                "두 리스트 병합 후 정렬",
                ["두 줄에 각각 정수 여러 개가 입력됩니다. 두 리스트를 합쳐 오름차순 정렬해 출력하세요."],
                "리스트를 합친 뒤 sort 를 호출하세요.",
                "a = list(map(int, input().split()))\nb = list(map(int, input().split()))\nresult = sorted(a + b)\nprint(*result)",
                "3 1 5\n4 2 6",
                "1 2 3 4 5 6",
            ),
            problem(
                "안정 정렬: 점수 동률이면 이름순",
                ["이름:점수 쌍 여러 개가 콤마로 구분되어 입력됩니다. 점수 내림차순으로, 동점이면 이름 오름차순으로 출력하세요."],
                "sorted(..., key=lambda x: (-x[1], x[0])) 을 사용하세요.",
                "data = []\nfor item in input().split(','):\n    k, v = item.strip().split(':')\n    data.append((k.strip(), int(v.strip())))\nfor name, score in sorted(data, key=lambda x: (-x[1], x[0])):\n    print(f'{name}:{score}')",
                "Alice:85, Bob:85, Chris:92",
                "Chris:92\nAlice:85\nBob:85",
            ),
            problem(
                "버블 정렬 단계 출력",
                ["한 줄에 정수 네 개가 입력됩니다. 버블 정렬의 각 패스 후 상태를 한 줄씩 출력하세요."],
                "외부 반복 끝마다 현재 리스트를 출력하세요.",
                "nums = list(map(int, input().split()))\nn = len(nums)\nfor i in range(n - 1):\n    for j in range(n - 1 - i):\n        if nums[j] > nums[j + 1]:\n            nums[j], nums[j + 1] = nums[j + 1], nums[j]\n    print(*nums)",
                "4 3 2 1",
                "3 2 1 4\n2 1 3 4\n1 2 3 4",
            ),
        ],
    })

    # ── 6장: 탐색 알고리즘 ───────────────────────────────────────────────────
    chapters.append({
        "title": "탐색 알고리즘",
        "content": "선형 탐색과 이진 탐색을 직접 구현하고 활용합니다.",
        "items": [
            problem(
                "선형 탐색으로 인덱스 찾기",
                ["첫 줄에 정수 여러 개, 둘째 줄에 찾을 값이 입력됩니다. 처음 나오는 인덱스를 출력하고, 없으면 -1을 출력하세요."],
                "enumerate 로 인덱스와 값을 함께 순회하세요.",
                "nums = list(map(int, input().split()))\ntarget = int(input())\nresult = -1\nfor i, n in enumerate(nums):\n    if n == target:\n        result = i\n        break\nprint(result)",
                "3 7 2 9 4\n9",
                "3",
            ),
            problem(
                "이진 탐색 구현",
                ["첫 줄에 오름차순 정수 여러 개, 둘째 줄에 찾을 값이 입력됩니다. 이진 탐색으로 인덱스를 출력하고, 없으면 -1을 출력하세요."],
                "left, right 포인터를 두고 mid = (left+right)//2 로 좁혀가세요.",
                "nums = list(map(int, input().split()))\ntarget = int(input())\nleft, right = 0, len(nums) - 1\nresult = -1\nwhile left <= right:\n    mid = (left + right) // 2\n    if nums[mid] == target:\n        result = mid\n        break\n    elif nums[mid] < target:\n        left = mid + 1\n    else:\n        right = mid - 1\nprint(result)",
                "1 3 5 7 9 11 13\n7",
                "3",
            ),
            problem(
                "특정 값보다 큰 첫 번째 인덱스",
                ["첫 줄에 오름차순 정수 여러 개, 둘째 줄에 기준값이 입력됩니다. 기준값보다 처음으로 큰 값의 인덱스를 출력하세요. 없으면 -1을 출력하세요."],
                "이진 탐색으로 lower bound 를 구하세요.",
                "nums = list(map(int, input().split()))\ntarget = int(input())\nleft, right = 0, len(nums)\nwhile left < right:\n    mid = (left + right) // 2\n    if nums[mid] <= target:\n        left = mid + 1\n    else:\n        right = mid\nprint(left if left < len(nums) else -1)",
                "1 3 5 7 9\n6",
                "3",
            ),
            problem(
                "선형 탐색으로 최솟값 위치",
                ["정수 여러 개가 입력됩니다. 최솟값이 처음 나오는 인덱스를 출력하세요."],
                "현재 최솟값과 인덱스를 저장하며 순회하세요.",
                "nums = list(map(int, input().split()))\nmin_idx = 0\nfor i in range(1, len(nums)):\n    if nums[i] < nums[min_idx]:\n        min_idx = i\nprint(min_idx)",
                "3 7 2 9 4 1 8",
                "5",
            ),
            problem(
                "이진 탐색 반복 횟수",
                ["첫 줄에 오름차순 정수 여러 개, 둘째 줄에 찾을 값이 입력됩니다. 이진 탐색이 몇 번의 비교 끝에 값을 찾는지 출력하세요. 없으면 -1을 출력하세요."],
                "비교할 때마다 count 를 증가시키세요.",
                "nums = list(map(int, input().split()))\ntarget = int(input())\nleft, right = 0, len(nums) - 1\ncount = 0\nresult = -1\nwhile left <= right:\n    mid = (left + right) // 2\n    count += 1\n    if nums[mid] == target:\n        result = count\n        break\n    elif nums[mid] < target:\n        left = mid + 1\n    else:\n        right = mid - 1\nprint(result)",
                "1 3 5 7 9 11 13 15\n7",
                "2",
            ),
            problem(
                "정렬 후 이진 탐색",
                ["첫 줄에 정수 여러 개(정렬 안 됨), 둘째 줄에 찾을 값이 입력됩니다. 정렬 후 이진 탐색으로 값의 존재 여부를 YES/NO로 출력하세요."],
                "정렬 후 이진 탐색을 수행하세요.",
                "nums = sorted(map(int, input().split()))\ntarget = int(input())\nleft, right = 0, len(nums) - 1\nfound = False\nwhile left <= right:\n    mid = (left + right) // 2\n    if nums[mid] == target:\n        found = True\n        break\n    elif nums[mid] < target:\n        left = mid + 1\n    else:\n        right = mid - 1\nprint('YES' if found else 'NO')",
                "5 3 8 1 9 2\n8",
                "YES",
            ),
            problem(
                "두 포인터로 두 수의 합",
                ["첫 줄에 오름차순 정수 여러 개, 둘째 줄에 목표합이 입력됩니다. 합이 목표와 같은 두 수를 출력하세요. 없으면 NONE을 출력하세요."],
                "left=0, right=n-1 에서 시작해 합에 따라 포인터를 이동하세요.",
                "nums = list(map(int, input().split()))\ntarget = int(input())\nleft, right = 0, len(nums) - 1\nresult = 'NONE'\nwhile left < right:\n    s = nums[left] + nums[right]\n    if s == target:\n        result = f'{nums[left]} {nums[right]}'\n        break\n    elif s < target:\n        left += 1\n    else:\n        right -= 1\nprint(result)",
                "1 2 3 4 6 8 9\n10",
                "1 9",
            ),
            problem(
                "선형 탐색으로 조건 만족 요소 모두 찾기",
                ["첫 줄에 정수 여러 개, 둘째 줄에 기준값이 입력됩니다. 기준값보다 큰 수를 모두 출력하세요. 없으면 NONE을 출력하세요."],
                "반복문으로 조건 만족 요소를 result 에 추가하세요.",
                "nums = list(map(int, input().split()))\ntarget = int(input())\nresult = [n for n in nums if n > target]\nif result:\n    print(*result)\nelse:\n    print('NONE')",
                "3 7 2 9 4 6\n5",
                "7 9 6",
            ),
            problem(
                "이진 탐색으로 삽입 위치 찾기",
                ["첫 줄에 오름차순 정수 여러 개, 둘째 줄에 삽입할 값이 입력됩니다. 정렬을 유지하면서 삽입할 인덱스를 출력하세요."],
                "이진 탐색으로 올바른 위치를 찾으세요.",
                "nums = list(map(int, input().split()))\nval = int(input())\nleft, right = 0, len(nums)\nwhile left < right:\n    mid = (left + right) // 2\n    if nums[mid] < val:\n        left = mid + 1\n    else:\n        right = mid\nprint(left)",
                "1 3 5 7 9\n6",
                "3",
            ),
            problem(
                "문자열 탐색: 아나그램 확인",
                ["두 문자열이 한 줄씩 입력됩니다. 두 문자열이 아나그램이면 YES, 아니면 NO를 출력하세요."],
                "sorted 로 정렬해 비교하거나 딕셔너리로 빈도를 비교하세요.",
                "a = input().strip()\nb = input().strip()\nprint('YES' if sorted(a) == sorted(b) else 'NO')",
                "listen\nsilent",
                "YES",
            ),
        ],
    })

    # ── 7장: 클래스와 객체지향 기초 ──────────────────────────────────────────
    chapters.append({
        "title": "클래스와 객체지향 기초",
        "content": "__init__, 메서드, 상속, @property 등 클래스 기초를 익힙니다.",
        "items": [
            problem(
                "간단한 클래스 만들기",
                ["이름과 나이가 한 줄에 입력됩니다. Person 클래스를 만들어 introduce 메서드가 이름: X, 나이: Y 를 출력하게 하세요."],
                "class Person: 안에 __init__ 과 introduce 를 정의하세요.",
                "class Person:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n    def introduce(self):\n        print(f'이름: {self.name}, 나이: {self.age}')\n\nparts = input().split()\np = Person(parts[0], int(parts[1]))\np.introduce()",
                "홍길동 25",
                "이름: 홍길동, 나이: 25",
            ),
            problem(
                "계산기 클래스",
                ["연산자(+ - * /)와 두 정수가 한 줄에 입력됩니다. Calculator 클래스의 compute 메서드로 결과를 출력하세요. 나눗셈은 실수로 출력하세요."],
                "compute(op, a, b) 메서드에서 연산자에 따라 분기하세요.",
                "class Calculator:\n    def compute(self, op, a, b):\n        if op == '+':\n            return a + b\n        elif op == '-':\n            return a - b\n        elif op == '*':\n            return a * b\n        else:\n            return a / b\n\nparts = input().split()\ncalc = Calculator()\nprint(calc.compute(parts[0], int(parts[1]), int(parts[2])))",
                "* 6 7",
                "42",
            ),
            problem(
                "클래스 상속 기초",
                ["동물 이름이 입력됩니다. Animal 을 상속하는 Dog 클래스를 만들어 speak 메서드가 이름: 멍멍! 을 출력하게 하세요."],
                "class Dog(Animal): 처럼 상속하고 메서드를 오버라이드하세요.",
                "class Animal:\n    def __init__(self, name):\n        self.name = name\n    def speak(self):\n        print(f'{self.name}: ...')\n\nclass Dog(Animal):\n    def speak(self):\n        print(f'{self.name}: 멍멍!')\n\nname = input().strip()\nd = Dog(name)\nd.speak()",
                "바둑이",
                "바둑이: 멍멍!",
            ),
            problem(
                "은행 계좌 클래스",
                ["초기 잔액이 입력됩니다. 그 다음 줄부터 deposit 금액 또는 withdraw 금액 형식으로 입력되고 END가 나오면 최종 잔액을 출력하세요. 잔액 부족 시 잔액 부족을 출력하세요."],
                "BankAccount 클래스에 deposit, withdraw 메서드를 구현하세요.",
                "class BankAccount:\n    def __init__(self, balance):\n        self.balance = balance\n    def deposit(self, amount):\n        self.balance += amount\n    def withdraw(self, amount):\n        if amount > self.balance:\n            print('잔액 부족')\n        else:\n            self.balance -= amount\n\naccount = BankAccount(int(input()))\nwhile True:\n    line = input().strip()\n    if line == 'END':\n        break\n    parts = line.split()\n    op, amount = parts[0], int(parts[1])\n    if op == 'deposit':\n        account.deposit(amount)\n    else:\n        account.withdraw(amount)\nprint(account.balance)",
                "1000\ndeposit 500\nwithdraw 200\nEND",
                "1300",
            ),
            problem(
                "클래스 메서드로 객체 개수 세기",
                ["이름들이 한 줄씩 입력되고 END가 나오면 총 생성된 Student 객체 수를 출력하세요."],
                "클래스 변수 count = 0 을 두고 __init__ 마다 증가시키세요.",
                "class Student:\n    count = 0\n    def __init__(self, name):\n        self.name = name\n        Student.count += 1\n\nwhile True:\n    line = input().strip()\n    if line == 'END':\n        break\n    Student(line)\nprint(Student.count)",
                "Alice\nBob\nChris\nEND",
                "3",
            ),
            problem(
                "__str__ 메서드 구현",
                ["상품명과 가격이 한 줄에 입력됩니다. Product 클래스의 __str__ 이 상품명 - 가격원 을 반환하도록 구현해 print로 출력하세요."],
                "def __str__(self): return ... 형태로 문자열을 반환하세요.",
                "class Product:\n    def __init__(self, name, price):\n        self.name = name\n        self.price = price\n    def __str__(self):\n        return f'{self.name} - {self.price}원'\n\nparts = input().split()\np = Product(parts[0], int(parts[1]))\nprint(p)",
                "노트북 1500000",
                "노트북 - 1500000원",
            ),
            problem(
                "상속과 메서드 오버라이딩",
                ["도형 종류(circle 또는 rect)와 치수가 입력됩니다. circle 이면 반지름, rect 이면 가로 세로가 입력됩니다. 넓이를 소수 둘째 자리로 출력하세요. (π=3.14)"],
                "Shape 를 상속한 Circle, Rectangle 에서 area 를 오버라이딩하세요.",
                "class Shape:\n    def area(self):\n        return 0\n\nclass Circle(Shape):\n    def __init__(self, r):\n        self.r = r\n    def area(self):\n        return round(3.14 * self.r ** 2, 2)\n\nclass Rectangle(Shape):\n    def __init__(self, w, h):\n        self.w = w\n        self.h = h\n    def area(self):\n        return round(self.w * self.h, 2)\n\nparts = input().split()\nshape_type = parts[0]\nif shape_type == 'circle':\n    s = Circle(float(parts[1]))\nelse:\n    s = Rectangle(float(parts[1]), float(parts[2]))\nprint(s.area())",
                "circle 5",
                "78.5",
            ),
            problem(
                "@property 로 읽기 전용 속성",
                ["섭씨 온도가 입력됩니다. Temperature 클래스에서 @property 로 fahrenheit 를 계산해 출력하세요."],
                "@property 데코레이터로 fahrenheit 를 정의하세요.",
                "class Temperature:\n    def __init__(self, celsius):\n        self.celsius = celsius\n    @property\n    def fahrenheit(self):\n        return self.celsius * 9 / 5 + 32\n\nt = Temperature(float(input()))\nprint(t.fahrenheit)",
                "100",
                "212.0",
            ),
            problem(
                "클래스로 스택 구현",
                ["push 값 또는 pop 명령이 한 줄씩 입력됩니다. END가 나오면 종료하고 pop 결과를 순서대로 출력하세요. 스택이 비어 있을 때 pop 하면 EMPTY를 출력하세요."],
                "Stack 클래스에 push, pop 메서드를 구현하세요.",
                "class Stack:\n    def __init__(self):\n        self.data = []\n    def push(self, val):\n        self.data.append(val)\n    def pop(self):\n        if not self.data:\n            return 'EMPTY'\n        return self.data.pop()\n\ns = Stack()\nresults = []\nwhile True:\n    line = input().strip()\n    if line == 'END':\n        break\n    parts = line.split()\n    if parts[0] == 'push':\n        s.push(int(parts[1]))\n    else:\n        results.append(str(s.pop()))\nfor r in results:\n    print(r)",
                "push 1\npush 2\npush 3\npop\npop\nEND",
                "3\n2",
            ),
            problem(
                "클래스로 큐 구현",
                ["enqueue 값 또는 dequeue 명령이 한 줄씩 입력됩니다. END가 나오면 종료하고 dequeue 결과를 순서대로 출력하세요. 큐가 비어 있을 때 dequeue 하면 EMPTY를 출력하세요."],
                "Queue 클래스에 enqueue, dequeue 메서드를 구현하세요.",
                "class Queue:\n    def __init__(self):\n        self.data = []\n    def enqueue(self, val):\n        self.data.append(val)\n    def dequeue(self):\n        if not self.data:\n            return 'EMPTY'\n        return self.data.pop(0)\n\nq = Queue()\nresults = []\nwhile True:\n    line = input().strip()\n    if line == 'END':\n        break\n    parts = line.split()\n    if parts[0] == 'enqueue':\n        q.enqueue(int(parts[1]))\n    else:\n        results.append(str(q.dequeue()))\nfor r in results:\n    print(r)",
                "enqueue 1\nenqueue 2\nenqueue 3\ndequeue\ndequeue\nEND",
                "1\n2",
            ),
        ],
    })

    # ── 8장: 예외처리와 실전 코딩 패턴 ──────────────────────────────────────
    chapters.append({
        "title": "예외처리와 실전 코딩 패턴",
        "content": "try-except, raise, 내장 예외 종류와 실전에서 자주 쓰는 코딩 패턴을 익힙니다.",
        "items": [
            problem(
                "정수 변환 예외처리",
                ["문자열이 입력됩니다. 정수로 변환 가능하면 2배 값을, 불가능하면 오류를 출력하세요."],
                "try-except ValueError 를 사용하세요.",
                "s = input().strip()\ntry:\n    n = int(s)\n    print(n * 2)\nexcept ValueError:\n    print('오류')",
                "abc",
                "오류",
            ),
            problem(
                "0으로 나누기 예외처리",
                ["두 정수가 입력됩니다. 두 번째가 0이면 0으로 나눌 수 없습니다를 출력하고, 아니면 나눗셈 결과를 출력하세요."],
                "try-except ZeroDivisionError 를 사용하세요.",
                "a, b = map(int, input().split())\ntry:\n    print(a / b)\nexcept ZeroDivisionError:\n    print('0으로 나눌 수 없습니다')",
                "10 0",
                "0으로 나눌 수 없습니다",
            ),
            problem(
                "리스트 인덱스 예외처리",
                ["정수 여러 개와 인덱스가 한 줄씩 입력됩니다. 해당 인덱스의 값을 출력하고, 범위를 벗어나면 범위 오류를 출력하세요."],
                "try-except IndexError 를 사용하세요.",
                "nums = list(map(int, input().split()))\nidx = int(input())\ntry:\n    print(nums[idx])\nexcept IndexError:\n    print('범위 오류')",
                "1 2 3\n5",
                "범위 오류",
            ),
            problem(
                "여러 예외 처리",
                ["문자열과 인덱스가 한 줄씩 입력됩니다. 인덱스를 정수로 변환해 해당 문자를 출력하세요. 변환 오류면 변환오류, 범위 오류면 범위오류를 출력하세요."],
                "except 절을 여러 개 사용하거나 튜플로 묶으세요.",
                "s = input()\nidx_str = input().strip()\ntry:\n    idx = int(idx_str)\n    print(s[idx])\nexcept ValueError:\n    print('변환오류')\nexcept IndexError:\n    print('범위오류')",
                "hello\n10",
                "범위오류",
            ),
            problem(
                "사용자 정의 예외",
                ["나이가 입력됩니다. 0 미만이면 InvalidAgeError 를 발생시키고 잘못된 나이: 값 을 출력하세요. 아니면 나이: 값 을 출력하세요."],
                "class InvalidAgeError(Exception): 를 정의하고 raise 로 발생시키세요.",
                "class InvalidAgeError(Exception):\n    pass\n\nage = int(input())\ntry:\n    if age < 0:\n        raise InvalidAgeError(age)\n    print(f'나이: {age}')\nexcept InvalidAgeError as e:\n    print(f'잘못된 나이: {e}')",
                "-5",
                "잘못된 나이: -5",
            ),
            problem(
                "finally 활용",
                ["두 정수가 입력됩니다. 나눗셈을 시도하고 결과 또는 오류 메시지를 출력하세요. 성공/실패 여부에 관계없이 작업 종료를 출력하세요."],
                "try-except-finally 구조를 사용하세요.",
                "a, b = map(int, input().split())\ntry:\n    print(a // b)\nexcept ZeroDivisionError:\n    print('0으로 나눌 수 없습니다')\nfinally:\n    print('작업 종료')",
                "10 3",
                "3\n작업 종료",
            ),
            problem(
                "입력값 검증 패턴",
                ["양의 정수가 입력됩니다. 0 이하면 양수를 입력하세요를 출력하고, 맞으면 입력 성공: 값 을 출력하세요."],
                "조건 확인 후 필요시 raise ValueError 를 사용하세요.",
                "n = int(input())\ntry:\n    if n <= 0:\n        raise ValueError(n)\n    print(f'입력 성공: {n}')\nexcept ValueError:\n    print('양수를 입력하세요')",
                "-3",
                "양수를 입력하세요",
            ),
            problem(
                "딕셔너리 키 예외처리",
                ["이름:점수 쌍이 콤마로 구분되어 입력되고 둘째 줄에 찾을 이름이 입력됩니다. 점수를 출력하고, 없으면 이름 없음을 출력하세요."],
                "try-except KeyError 또는 get 메서드를 사용하세요.",
                "d = {}\nfor item in input().split(','):\n    k, v = item.strip().split(':')\n    d[k.strip()] = int(v.strip())\nname = input().strip()\ntry:\n    print(d[name])\nexcept KeyError:\n    print('이름 없음')",
                "Alice:90, Bob:85\nChris",
                "이름 없음",
            ),
            problem(
                "누적 합 with 예외처리",
                ["한 줄에 값들이 공백으로 입력됩니다. 각 값을 정수로 변환해 합산하고, 정수로 변환할 수 없는 값은 건너뜁니다. 최종 합계를 출력하세요."],
                "반복 안에서 try-except 를 사용해 변환 실패를 무시하세요.",
                "total = 0\nfor token in input().split():\n    try:\n        total += int(token)\n    except ValueError:\n        pass\nprint(total)",
                "1 abc 2 def 3",
                "6",
            ),
            problem(
                "assert 로 사전 조건 검사",
                ["두 정수가 입력됩니다. 두 번째 수가 0이 아닌지 assert 로 확인하고 나눗셈 결과를 출력하세요. assert 실패 시 AssertionError 를 잡아 조건 오류를 출력하세요."],
                "assert b != 0, '메시지' 구문을 사용하세요.",
                "a, b = map(int, input().split())\ntry:\n    assert b != 0, '0으로 나눌 수 없음'\n    print(a // b)\nexcept AssertionError as e:\n    print(f'조건 오류: {e}')",
                "10 0",
                "조건 오류: 0으로 나눌 수 없음",
            ),
        ],
    })

    # ── 9장: 실전 모의고사 1 ─────────────────────────────────────────────────
    chapters.append({
        "title": "실전 모의고사 1 (2급 스타일)",
        "content": "COS Pro 2급 출제 유형인 빈칸 채우기·한 줄 수정·함수 작성 스타일의 실전 문제 10문제입니다.",
        "items": [
            problem(
                "[모의1-1] 최고·최저 제외 합계",
                ["정수 다섯 개가 한 줄에 입력됩니다. 최댓값과 최솟값을 각각 하나씩 제외하고 나머지의 합을 출력하세요."],
                "전체 합에서 max와 min을 빼세요.",
                "nums = list(map(int, input().split()))\nprint(sum(nums) - max(nums) - min(nums))",
                "50 35 78 91 85",
                "213",
            ),
            problem(
                "[모의1-2] 거스름돈 계산 함수",
                ["물건 가격과 지불 금액이 한 줄에 입력됩니다. 500원, 100원, 50원, 10원 동전으로 거스름돈을 최소 개수로 주는 각 동전 수를 출력하세요."],
                "change(price, paid) 함수를 구현해 잔돈을 계산하세요.",
                "def change(price, paid):\n    money = paid - price\n    coins = [500, 100, 50, 10]\n    result = []\n    for coin in coins:\n        result.append(money // coin)\n        money %= coin\n    return result\n\nprice, paid = map(int, input().split())\nfor c in change(price, paid):\n    print(c)",
                "1250 2000",
                "1\n2\n0\n0",
            ),
            problem(
                "[모의1-3] 신장 필터링",
                ["키(cm)가 한 줄에 여러 개 입력됩니다. 170 이상인 값만 오름차순으로 출력하세요."],
                "필터링 후 정렬해 출력하세요.",
                "heights = list(map(int, input().split()))\nresult = sorted([h for h in heights if h >= 170])\nprint(*result)",
                "165 175 168 182 170 155 190",
                "170 175 182 190",
            ),
            problem(
                "[모의1-4] 리스트 구간 평균",
                ["정수 여러 개와 구간 시작·끝 인덱스가 두 줄에 입력됩니다. 해당 구간의 평균을 소수 둘째 자리로 출력하세요."],
                "슬라이싱으로 구간을 추출하세요.",
                "nums = list(map(int, input().split()))\nstart, end = map(int, input().split())\nsub = nums[start:end + 1]\nprint(round(sum(sub) / len(sub), 2))",
                "10 20 30 40 50 60\n1 3",
                "30.0",
            ),
            problem(
                "[모의1-5] 단어 길이 기준 분류",
                ["단어 여러 개가 한 줄에 입력됩니다. 길이 4 이하와 5 이상으로 분류해 각각 오름차순으로 출력하세요."],
                "두 리스트로 나눠 각각 정렬하세요.",
                "words = input().split()\nshort = sorted([w for w in words if len(w) <= 4])\nlong_ = sorted([w for w in words if len(w) >= 5])\nprint(*short)\nprint(*long_)",
                "hi python java go programming",
                "go hi java\npython programming",
            ),
            problem(
                "[모의1-6] 두 리스트 공통 원소",
                ["두 줄에 정수 여러 개씩 입력됩니다. 두 리스트에 공통으로 있는 수를 오름차순으로 출력하세요."],
                "set 교집합을 사용하세요.",
                "a = set(map(int, input().split()))\nb = set(map(int, input().split()))\nprint(*sorted(a & b))",
                "1 3 5 7 9\n2 3 4 5 6",
                "3 5",
            ),
            problem(
                "[모의1-7] 재귀로 문자열 뒤집기",
                ["문자열이 입력되면 재귀 함수로 뒤집어 출력하세요."],
                "reverse_str(s) = s[-1] + reverse_str(s[:-1]), 기저 조건은 빈 문자열입니다.",
                "def reverse_str(s):\n    if not s:\n        return ''\n    return s[-1] + reverse_str(s[:-1])\n\nprint(reverse_str(input().strip()))",
                "abcde",
                "edcba",
            ),
            problem(
                "[모의1-8] 행렬 전치",
                ["3행 3열 행렬이 세 줄에 입력됩니다. 전치 행렬을 출력하세요."],
                "zip(*matrix) 를 사용하세요.",
                "matrix = [list(map(int, input().split())) for _ in range(3)]\nfor row in zip(*matrix):\n    print(*row)",
                "1 2 3\n4 5 6\n7 8 9",
                "1 4 7\n2 5 8\n3 6 9",
            ),
            problem(
                "[모의1-9] 중복 없이 조합",
                ["정수 여러 개가 입력됩니다. 두 수의 합이 같은 쌍의 개수를 출력하세요. (중복 쌍 제외, i<j)"],
                "이중 반복문으로 i<j 인 경우만 확인하세요.",
                "nums = list(map(int, input().split()))\ncount = 0\nfor i in range(len(nums)):\n    for j in range(i + 1, len(nums)):\n        if nums[i] + nums[j] == nums[i] + nums[j]:\n            pass  # placeholder\nnums_set = {}\nfor i in range(len(nums)):\n    for j in range(i + 1, len(nums)):\n        nums_set[(i, j)] = nums[i] + nums[j]\nfrom collections import Counter\nprint(max(Counter(nums_set.values()).values()))",
                "1 3 2 4 5",
                "2",
            ),
            problem(
                "[모의1-10] 단어 빈도 상위 k개",
                ["첫 줄에 문장, 둘째 줄에 k가 입력됩니다. 빈도 높은 순으로 k개 단어를 출력하세요. 동률이면 알파벳 순으로 정렬하세요."],
                "딕셔너리로 빈도를 세고 (-빈도, 단어) 로 정렬하세요.",
                "words = input().split()\nk = int(input())\ncount = {}\nfor w in words:\n    count[w] = count.get(w, 0) + 1\nsorted_words = sorted(count.keys(), key=lambda x: (-count[x], x))\nfor w in sorted_words[:k]:\n    print(w)",
                "apple banana apple cherry banana apple\n2",
                "apple\nbanana",
            ),
        ],
    })

    # ── 10장: 실전 모의고사 2 ────────────────────────────────────────────────
    chapters.append({
        "title": "실전 모의고사 2 (2급 스타일)",
        "content": "COS Pro 2급 최종 실전 연습입니다. 50분 안에 10문제를 완성하세요.",
        "items": [
            problem(
                "[모의2-1] 평균 이상 원소 개수",
                ["정수 여러 개가 입력됩니다. 평균 이상인 원소의 개수를 출력하세요."],
                "평균을 먼저 구하고 조건 비교하세요.",
                "nums = list(map(int, input().split()))\navg = sum(nums) / len(nums)\nprint(sum(1 for n in nums if n >= avg))",
                "4 8 6 5 3 2 8 9 2 5",
                "4",
            ),
            problem(
                "[모의2-2] 연속 부분합 최대",
                ["정수 여러 개가 입력됩니다. 연속된 부분 수열의 합이 최대인 값을 출력하세요."],
                "카데인 알고리즘: current = max(n, current+n) 을 사용하세요.",
                "nums = list(map(int, input().split()))\ncurrent = best = nums[0]\nfor n in nums[1:]:\n    current = max(n, current + n)\n    best = max(best, current)\nprint(best)",
                "-2 1 -3 4 -1 2 1 -5 4",
                "6",
            ),
            problem(
                "[모의2-3] 딕셔너리로 성적 통계",
                ["이름:점수 쌍이 콤마로 구분되어 입력됩니다. 최고점 이름, 최저점 이름, 평균을 각각 출력하세요."],
                "딕셔너리를 items() 로 순회하며 최대·최소를 찾으세요.",
                "d = {}\nfor item in input().split(','):\n    k, v = item.strip().split(':')\n    d[k.strip()] = int(v.strip())\nbest = max(d, key=d.get)\nworst = min(d, key=d.get)\navg = round(sum(d.values()) / len(d), 1)\nprint(best)\nprint(worst)\nprint(avg)",
                "Alice:90, Bob:70, Chris:80",
                "Alice\nBob\n80.0",
            ),
            problem(
                "[모의2-4] 2차원 리스트 각 행의 최댓값",
                ["3행 4열 행렬이 세 줄에 입력됩니다. 각 행의 최댓값을 한 줄씩 출력하세요."],
                "max(row) 를 사용하세요.",
                "for _ in range(3):\n    row = list(map(int, input().split()))\n    print(max(row))",
                "3 1 4 1\n5 9 2 6\n5 3 5 8",
                "4\n9\n8",
            ),
            problem(
                "[모의2-5] 재귀로 하노이 탑 이동 횟수",
                ["원판 개수 n이 입력되면 하노이 탑을 옮기는 데 필요한 최소 이동 횟수를 출력하세요."],
                "hanoi(n) = 2 * hanoi(n-1) + 1, hanoi(1) = 1 입니다.",
                "def hanoi(n):\n    if n == 1:\n        return 1\n    return 2 * hanoi(n - 1) + 1\n\nprint(hanoi(int(input())))",
                "4",
                "15",
            ),
            problem(
                "[모의2-6] 문자열 단어 역순 + 대문자",
                ["문장이 입력됩니다. 단어 순서를 뒤집고 각 단어의 첫 글자를 대문자로 변환해 출력하세요."],
                "reverse 후 title 을 적용하세요.",
                "words = input().split()\nresult = [w.capitalize() for w in reversed(words)]\nprint(' '.join(result))",
                "hello world python",
                "Python World Hello",
            ),
            problem(
                "[모의2-7] 이진수 변환",
                ["양의 정수가 입력되면 이진수 문자열(0b 제외)로 변환해 출력하세요."],
                "bin(n)[2:] 를 사용하세요.",
                "n = int(input())\nprint(bin(n)[2:])",
                "42",
                "101010",
            ),
            problem(
                "[모의2-8] 클래스로 학생 관리",
                ["이름과 점수가 공백으로 구분된 줄이 여러 개 입력됩니다. END가 나오면 평균 이상 점수를 받은 학생 이름을 입력 순으로 출력하세요."],
                "Student 클래스로 관리하고 평균 계산 후 필터링하세요.",
                "class Student:\n    def __init__(self, name, score):\n        self.name = name\n        self.score = score\n\nstudents = []\nwhile True:\n    line = input().strip()\n    if line == 'END':\n        break\n    name, score = line.split()\n    students.append(Student(name, int(score)))\navg = sum(s.score for s in students) / len(students)\nfor s in students:\n    if s.score >= avg:\n        print(s.name)",
                "Alice 90\nBob 60\nChris 80\nEND",
                "Alice\nChris",
            ),
            problem(
                "[모의2-9] 소수 목록 출력",
                ["정수 n이 입력되면 2부터 n까지의 소수를 한 줄에 하나씩 출력하세요."],
                "각 수에 대해 2부터 sqrt(i) 까지 나누어 보세요.",
                "import math\nn = int(input())\nfor i in range(2, n + 1):\n    is_prime = True\n    for j in range(2, int(math.sqrt(i)) + 1):\n        if i % j == 0:\n            is_prime = False\n            break\n    if is_prime:\n        print(i)",
                "20",
                "2\n3\n5\n7\n11\n13\n17\n19",
            ),
            problem(
                "[모의2-10] 문자 치환 암호화",
                ["영문 소문자 문자열이 입력됩니다. 각 문자를 알파벳 순서에서 3칸 뒤 문자로 바꿔 출력하세요. z를 넘으면 a로 돌아오세요."],
                "ord, chr 와 % 26 을 활용하세요.",
                "s = input().strip()\nresult = ''\nfor ch in s:\n    if ch.isalpha():\n        result += chr((ord(ch) - ord('a') + 3) % 26 + ord('a'))\n    else:\n        result += ch\nprint(result)",
                "hello",
                "khoor",
            ),
        ],
    })

    total_items = sum(len(chapter["items"]) for chapter in chapters)
    if total_items != 100:
        raise ValueError(f"문항 수가 100개가 아닙니다: {total_items}")
    return chapters


class Command(BaseCommand):
    help = "YBM COS Pro 파이썬 2급 대비 과정(100문제)을 생성합니다."

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
                    "YBM IT COS Pro 파이썬 2급 자격증 취득을 위한 중급 연습 과정입니다. "
                    "리스트 심화·딕셔너리·재귀함수·정렬·탐색·클래스·예외처리를 체계적으로 익히고, "
                    "실전 모의고사 2세트(각 10문제)로 실제 시험을 대비합니다. "
                    "시험: 10문제 / 50분 / 1,000점 만점 / 600점 이상 합격"
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
            "YBM IT COS Pro 파이썬 2급 자격증 취득을 위한 중급 연습 과정입니다. "
            "리스트 심화·딕셔너리·재귀함수·정렬·탐색·클래스·예외처리를 체계적으로 익히고, "
            "실전 모의고사 2세트(각 10문제)로 실제 시험을 대비합니다. "
            "시험: 10문제 / 50분 / 1,000점 만점 / 600점 이상 합격"
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
                    key=f"cos2_{chapter_index:02d}_{item_index:02d}",
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
