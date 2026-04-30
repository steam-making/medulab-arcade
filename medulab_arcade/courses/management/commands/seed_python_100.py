from html import escape

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Chapter, Item, LearningProgram, ProgramType


COURSE_NAME = "파이썬 100문제"
PROGRAM_TYPE_NAME = "파이썬 문제풀이"


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

    chapters.append({
        "title": "출력과 기본 문법",
        "content": "print 함수와 기본 문자열 출력을 연습합니다.",
        "items": [
            problem("Hello, Python! 출력하기", ["문자열 Hello, Python!을 그대로 출력하세요."], "print 함수 안에 문자열을 넣어보세요.", """print("Hello, Python!")""", "", "Hello, Python!"),
            problem("두 줄 문장 출력하기", ["첫째 줄에는 파이썬 공부 중, 둘째 줄에는 오늘도 한 걸음을 출력하세요."], "print를 두 번 사용하면 됩니다.", """print("파이썬 공부 중")\nprint("오늘도 한 걸음")""", "", "파이썬 공부 중\n오늘도 한 걸음"),
            problem("이름과 학교 출력하기", ["첫째 줄에 자신의 이름, 둘째 줄에 메듀랩을 출력하는 코드를 작성하세요."], "문자열 두 개를 줄바꿈해서 출력하세요.", """print("홍길동")\nprint("메듀랩")""", "", "홍길동\n메듀랩"),
            problem("따옴표 포함 출력하기", ['문장 안에 "파이썬"이라는 말을 포함해 출력하세요.'], "큰따옴표를 문자열 안에 넣을 때는 작은따옴표 문자열을 써도 됩니다.", """print('"파이썬"은 재미있다')""", "", '"파이썬"은 재미있다'),
            problem("별표 한 줄 출력하기", ["별표 다섯 개를 한 줄에 출력하세요."], "***** 문자열을 그대로 출력하면 됩니다.", """print("*****")""", "", "*****"),
            problem("세 줄 자기소개 출력하기", ["첫째 줄은 안녕하세요, 둘째 줄은 저는 코딩을 좋아합니다, 셋째 줄은 잘 부탁드립니다를 출력하세요."], "print를 세 번 써서 순서대로 출력해보세요.", """print("안녕하세요")\nprint("저는 코딩을 좋아합니다")\nprint("잘 부탁드립니다")""", "", "안녕하세요\n저는 코딩을 좋아합니다\n잘 부탁드립니다"),
            problem("탭 느낌으로 출력하기", ["사과 3개를 출력하세요."], "문자열 사이에 공백을 넣어도 됩니다.", """print("사과", "3개")""", "", "사과 3개"),
            problem("경로 문자열 출력하기", [r"C:\python\study 경로를 그대로 출력하세요."], "역슬래시는 두 번 써야 그대로 보입니다.", """print("C:\\\\python\\\\study")""", "", r"C:\python\study"),
            problem("오늘의 목표 출력하기", ["첫째 줄에 오늘의 목표, 둘째 줄에 파이썬 3문제 해결을 출력하세요."], "문장 두 개를 줄바꿈해서 출력하세요.", """print("오늘의 목표")\nprint("파이썬 3문제 해결")""", "", "오늘의 목표\n파이썬 3문제 해결"),
            problem("라벨과 값 출력하기", ["이름: 민수 와 목표: 완주 를 두 줄로 출력하세요."], "각 줄마다 라벨과 값을 함께 출력하세요.", """print("이름: 민수")\nprint("목표: 완주")""", "", "이름: 민수\n목표: 완주"),
        ],
    })

    chapters.append({
        "title": "입력과 사칙연산",
        "content": "input 함수와 숫자 연산을 연습합니다.",
        "items": [
            problem("두 수의 합", ["한 줄에 정수 두 개가 입력됩니다. 두 수의 합을 출력하세요."], "split으로 나눈 뒤 int로 바꿔 더해보세요.", """nums = input().split()\na = int(nums[0])\nb = int(nums[1])\nprint(a + b)""", "3 5", "8"),
            problem("두 수의 차", ["한 줄에 정수 두 개가 입력됩니다. 앞의 수에서 뒤의 수를 뺀 값을 출력하세요."], "a - b 형태를 생각해보세요.", """nums = input().split()\na = int(nums[0])\nb = int(nums[1])\nprint(a - b)""", "10 4", "6"),
            problem("두 수의 곱", ["한 줄에 정수 두 개가 입력됩니다. 두 수의 곱을 출력하세요."], "곱셈 연산자를 사용하세요.", """nums = input().split()\na = int(nums[0])\nb = int(nums[1])\nprint(a * b)""", "7 8", "56"),
            problem("몫과 나머지", ["한 줄에 정수 두 개가 입력됩니다. 몫과 나머지를 한 줄에 공백으로 구분해 출력하세요."], "// 와 % 연산자를 함께 사용하세요.", """nums = input().split()\na = int(nums[0])\nb = int(nums[1])\nprint(a // b, a % b)""", "17 5", "3 2"),
            problem("직사각형 넓이", ["가로와 세로 길이가 입력되면 직사각형의 넓이를 출력하세요."], "넓이는 가로 곱하기 세로입니다.", """nums = input().split()\nwidth = int(nums[0])\nheight = int(nums[1])\nprint(width * height)""", "6 9", "54"),
            problem("섭씨를 화씨로", ["섭씨 온도가 입력되면 화씨 온도를 소수 첫째 자리까지 출력하세요."], "화씨 = 섭씨 * 9 / 5 + 32 입니다.", """c = float(input())\nf = c * 9 / 5 + 32\nprint(round(f, 1))""", "25", "77.0"),
            problem("초를 분과 초로 바꾸기", ["초가 입력되면 몇 분 몇 초인지 공백으로 구분해 출력하세요."], "분은 // 60, 초는 % 60 입니다.", """seconds = int(input())\nprint(seconds // 60, seconds % 60)""", "125", "2 5"),
            problem("세 수의 평균", ["한 줄에 정수 세 개가 입력됩니다. 세 수의 평균을 출력하세요."], "합을 3으로 나누세요.", """nums = input().split()\na = int(nums[0])\nb = int(nums[1])\nc = int(nums[2])\nprint((a + b + c) / 3)""", "10 20 30", "20.0"),
            problem("두 수 자리 바꾸기", ["한 줄에 정수 두 개가 입력됩니다. 두 수의 순서를 바꿔 출력하세요."], "출력 순서만 바꾸면 됩니다.", """nums = input().split()\na = nums[0]\nb = nums[1]\nprint(b, a)""", "12 34", "34 12"),
            problem("두 자리 수의 각 자리 합", ["두 자리 수가 입력되면 십의 자리와 일의 자리의 합을 출력하세요."], "문자열로 받아 각 자리를 나눠도 됩니다.", """n = input().strip()\nprint(int(n[0]) + int(n[1]))""", "47", "11"),
        ],
    })

    chapters.append({
        "title": "문자열 다루기",
        "content": "문자열의 길이, 슬라이싱, 메서드를 연습합니다.",
        "items": [
            problem("이름 이어 붙이기", ["이름과 성이 한 줄에 공백으로 입력됩니다. 성이름 순서로 붙여 출력하세요."], "split으로 나눈 뒤 순서를 바꿔 붙여보세요.", """parts = input().split()\nfirst = parts[0]\nlast = parts[1]\nprint(last + first)""", "길동 홍", "홍길동"),
            problem("환영 문장 만들기", ["이름이 입력되면 안녕하세요, 이름님! 을 출력하세요."], "문자열 더하기로 문장을 만들 수 있습니다.", """name = input().strip()\nprint("안녕하세요, " + name + "님!")""", "민지", "안녕하세요, 민지님!"),
            problem("문자열 길이 구하기", ["문자열이 입력되면 글자 수를 출력하세요."], "len 함수를 사용해보세요.", """text = input()\nprint(len(text))""", "python", "6"),
            problem("첫 글자와 마지막 글자", ["문자열이 입력되면 첫 글자와 마지막 글자를 공백으로 구분해 출력하세요."], "인덱스 0과 -1을 사용해보세요.", """text = input().strip()\nprint(text[0], text[-1])""", "coding", "c g"),
            problem("모두 대문자로", ["영문 문자열이 입력되면 모두 대문자로 바꿔 출력하세요."], "upper 메서드를 사용해보세요.", """text = input().strip()\nprint(text.upper())""", "python", "PYTHON"),
            problem("공백을 밑줄로", ["문장이 입력되면 공백을 모두 밑줄(_)로 바꿔 출력하세요."], "replace 메서드를 떠올려보세요.", """text = input()\nprint(text.replace(" ", "_"))""", "hello world python", "hello_world_python"),
            problem("문자 개수 세기", ["문장과 찾을 문자가 한 줄씩 입력됩니다. 문장 안에 해당 문자가 몇 번 나오는지 출력하세요."], "count 메서드를 사용해도 됩니다.", """text = input()\ntarget = input().strip()\nprint(text.count(target))""", "banana\na", "3"),
            problem("문자열 뒤집기", ["문자열이 입력되면 거꾸로 뒤집어 출력하세요."], "슬라이싱 [::-1] 을 써보세요.", """text = input().strip()\nprint(text[::-1])""", "level", "level"),
            problem("공백 없이 붙이기", ["문장이 입력되면 모든 공백을 제거하고 출력하세요."], "replace로 공백을 빈 문자열로 바꾸세요.", """text = input()\nprint(text.replace(" ", ""))""", "a b c d", "abcd"),
            problem("날짜 나누기", ["YYYY-MM-DD 형식의 날짜가 입력됩니다. 연 월 일을 공백으로 구분해 출력하세요."], "split('-')을 활용해보세요.", """parts = input().strip().split("-")\nprint(parts[0], parts[1], parts[2])""", "2026-04-27", "2026 04 27"),
        ],
    })

    chapters.append({
        "title": "조건문",
        "content": "if, elif, else를 사용해 다양한 판단 문제를 해결합니다.",
        "items": [
            problem("더 큰 수 찾기", ["정수 두 개가 입력되면 더 큰 수를 출력하세요."], "두 수를 비교하는 if 문을 써보세요.", """nums = input().split()\na = int(nums[0])\nb = int(nums[1])\nif a > b:\n    print(a)\nelse:\n    print(b)""", "8 13", "13"),
            problem("짝수와 홀수", ["정수가 입력되면 짝수면 짝수, 홀수면 홀수를 출력하세요."], "% 2 결과를 비교하세요.", """n = int(input())\nif n % 2 == 0:\n    print("짝수")\nelse:\n    print("홀수")""", "9", "홀수"),
            problem("양수 음수 0", ["정수가 입력되면 양수, 음수, 0 중 하나를 출력하세요."], "세 경우를 나눠보세요.", """n = int(input())\nif n > 0:\n    print("양수")\nelif n < 0:\n    print("음수")\nelse:\n    print("0")""", "-3", "음수"),
            problem("점수 등급", ["점수가 입력되면 90 이상 A, 80 이상 B, 70 이상 C, 그 외 D를 출력하세요."], "큰 점수부터 차례대로 비교하세요.", """score = int(input())\nif score >= 90:\n    print("A")\nelif score >= 80:\n    print("B")\nelif score >= 70:\n    print("C")\nelse:\n    print("D")""", "85", "B"),
            problem("세 수 중 최댓값", ["정수 세 개가 입력되면 가장 큰 수를 출력하세요."], "비교 대상을 하나씩 넓혀보세요.", """nums = input().split()\na = int(nums[0])\nb = int(nums[1])\nc = int(nums[2])\nmax_value = a\nif b > max_value:\n    max_value = b\nif c > max_value:\n    max_value = c\nprint(max_value)""", "4 12 7", "12"),
            problem("통과 여부", ["점수가 입력되면 60 이상이면 통과, 아니면 재도전을 출력하세요."], "조건 한 개만 판단하면 됩니다.", """score = int(input())\nif score >= 60:\n    print("통과")\nelse:\n    print("재도전")""", "59", "재도전"),
            problem("절댓값 출력", ["정수가 입력되면 절댓값을 출력하세요."], "음수면 -1을 곱하면 됩니다.", """n = int(input())\nif n < 0:\n    print(-n)\nelse:\n    print(n)""", "-25", "25"),
            problem("신호등 행동", ["신호등 색이 입력되면 빨강은 멈춤, 노랑은 준비, 초록은 출발을 출력하세요."], "문자열을 그대로 비교하면 됩니다.", """color = input().strip()\nif color == "빨강":\n    print("멈춤")\nelif color == "노랑":\n    print("준비")\nelse:\n    print("출발")""", "노랑", "준비"),
            problem("연령 구분", ["나이가 입력되면 13세 미만은 어린이, 19세 미만은 청소년, 그 외는 성인을 출력하세요."], "작은 나이 구간부터 판단하세요.", """age = int(input())\nif age < 13:\n    print("어린이")\nelif age < 19:\n    print("청소년")\nelse:\n    print("성인")""", "16", "청소년"),
            problem("배수 판별", ["정수가 입력되면 3과 5의 공배수면 YES, 아니면 NO를 출력하세요."], "두 조건을 모두 만족하는지 보세요.", """n = int(input())\nif n % 3 == 0 and n % 5 == 0:\n    print("YES")\nelse:\n    print("NO")""", "30", "YES"),
        ],
    })

    chapters.append({
        "title": "반복문",
        "content": "for와 while 반복문으로 규칙적인 처리를 연습합니다.",
        "items": [
            problem("1부터 5까지 출력", ["1부터 5까지 한 줄에 하나씩 출력하세요."], "range(1, 6)을 사용해보세요.", """for i in range(1, 6):\n    print(i)""", "", "1\n2\n3\n4\n5"),
            problem("1부터 n까지 합", ["정수 n이 입력되면 1부터 n까지의 합을 출력하세요."], "합계를 저장할 변수를 하나 만드세요.", """n = int(input())\ntotal = 0\nfor i in range(1, n + 1):\n    total += i\nprint(total)""", "5", "15"),
            problem("구구단 한 단", ["정수 n이 입력되면 n단을 1부터 9까지 출력하세요."], "반복문 안에서 n * i 를 출력하세요.", """n = int(input())\nfor i in range(1, 10):\n    print(n * i)""", "3", "3\n6\n9\n12\n15\n18\n21\n24\n27"),
            problem("거꾸로 세기", ["정수 n이 입력되면 n부터 1까지 출력하세요."], "range의 감소 값을 사용하세요.", """n = int(input())\nfor i in range(n, 0, -1):\n    print(i)""", "4", "4\n3\n2\n1"),
            problem("짝수 합 구하기", ["정수 n이 입력되면 1부터 n까지 짝수의 합을 출력하세요."], "짝수일 때만 더해보세요.", """n = int(input())\ntotal = 0\nfor i in range(1, n + 1):\n    if i % 2 == 0:\n        total += i\nprint(total)""", "10", "30"),
            problem("별 사각형", ["정수 n이 입력되면 가로 세로가 n인 별 사각형을 출력하세요."], "같은 줄을 n번 반복해서 출력해보세요.", """n = int(input())\nfor i in range(n):\n    print("*" * n)""", "3", "***\n***\n***"),
            problem("왼쪽 삼각형", ["정수 n이 입력되면 높이가 n인 왼쪽 정렬 삼각형을 출력하세요."], "별 개수를 하나씩 늘려보세요.", """n = int(input())\nfor i in range(1, n + 1):\n    print("*" * i)""", "4", "*\n**\n***\n****"),
            problem("홀수만 출력", ["정수 n이 입력되면 1부터 n까지의 홀수를 한 줄에 하나씩 출력하세요."], "i % 2 == 1 인지 확인하세요.", """n = int(input())\nfor i in range(1, n + 1):\n    if i % 2 == 1:\n        print(i)""", "7", "1\n3\n5\n7"),
            problem("팩토리얼 구하기", ["정수 n이 입력되면 n! 값을 출력하세요."], "곱셈 누적 변수를 사용하세요.", """n = int(input())\nresult = 1\nfor i in range(1, n + 1):\n    result *= i\nprint(result)""", "5", "120"),
            problem("숫자 각 자리 출력", ["정수 문자열이 입력되면 각 숫자를 한 줄에 하나씩 출력하세요."], "문자열을 하나씩 순회해보세요.", """text = input().strip()\nfor ch in text:\n    print(ch)""", "5027", "5\n0\n2\n7"),
        ],
    })

    chapters.append({
        "title": "리스트",
        "content": "리스트 생성, 수정, 순회, 정렬을 연습합니다.",
        "items": [
            problem("세 수의 합 리스트 버전", ["한 줄에 정수 세 개가 입력됩니다. 리스트로 저장한 뒤 합을 출력하세요."], "split으로 받은 값을 하나씩 int로 바꾸세요.", """parts = input().split()\nnums = [int(parts[0]), int(parts[1]), int(parts[2])]\nprint(sum(nums))""", "3 6 9", "18"),
            problem("다섯 수의 평균", ["한 줄에 정수 다섯 개가 입력됩니다. 평균을 출력하세요."], "합계를 5로 나누세요.", """parts = input().split()\nnums = [int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])]\nprint(sum(nums) / 5)""", "10 20 30 40 50", "30.0"),
            problem("첫 값과 마지막 값", ["한 줄에 숫자 네 개가 입력됩니다. 첫 번째와 마지막 값을 공백으로 구분해 출력하세요."], "리스트 인덱스 0과 -1을 사용하세요.", """parts = input().split()\nprint(parts[0], parts[-1])""", "8 3 5 2", "8 2"),
            problem("리스트 뒤집어 출력", ["한 줄에 단어 네 개가 입력됩니다. 순서를 뒤집어 한 줄에 공백으로 구분해 출력하세요."], "reverse 메서드를 사용해도 됩니다.", """words = input().split()\nwords.reverse()\nprint(" ".join(words))""", "red blue green yellow", "yellow green blue red"),
            problem("50보다 큰 수 개수", ["한 줄에 정수 다섯 개가 입력됩니다. 50보다 큰 수가 몇 개인지 출력하세요."], "조건을 만족할 때마다 개수를 늘리세요.", """parts = input().split()\ncount = 0\nfor value in parts:\n    if int(value) > 50:\n        count += 1\nprint(count)""", "30 55 80 42 61", "3"),
            problem("세 수 오름차순", ["한 줄에 정수 세 개가 입력됩니다. 오름차순으로 정렬해 출력하세요."], "리스트 sort 메서드를 사용해보세요.", """parts = input().split()\nnums = [int(parts[0]), int(parts[1]), int(parts[2])]\nnums.sort()\nprint(nums[0], nums[1], nums[2])""", "9 2 5", "2 5 9"),
            problem("마지막 값 제거 후 길이", ["한 줄에 단어 네 개가 입력됩니다. 마지막 단어를 제거한 뒤 리스트의 길이를 출력하세요."], "pop으로 마지막 값을 뺄 수 있습니다.", """words = input().split()\nwords.pop()\nprint(len(words))""", "하나 둘 셋 넷", "3"),
            problem("값 추가해서 출력", ["한 줄에 단어 세 개와 다음 줄에 단어 한 개가 입력됩니다. 마지막 단어를 리스트에 추가한 뒤 모두 출력하세요."], "append 메서드를 사용하세요.", """words = input().split()\nnew_word = input().strip()\nwords.append(new_word)\nprint(" ".join(words))""", "봄 여름 가을\n겨울", "봄 여름 가을 겨울"),
            problem("가장 큰 수 찾기", ["한 줄에 정수 네 개가 입력됩니다. 가장 큰 수를 출력하세요."], "반복하면서 최대값을 비교하세요.", """parts = input().split()\nnums = [int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])]\nmax_value = nums[0]\nfor n in nums:\n    if n > max_value:\n        max_value = n\nprint(max_value)""", "14 3 27 18", "27"),
            problem("두 리스트 이어 붙이기", ["첫 줄과 둘째 줄에 단어 두 개씩 입력됩니다. 두 줄의 단어를 이어 붙여 한 줄에 출력하세요."], "리스트끼리 더할 수 있습니다.", """first = input().split()\nsecond = input().split()\nmerged = first + second\nprint(" ".join(merged))""", "a b\nc d", "a b c d"),
        ],
    })

    chapters.append({
        "title": "딕셔너리와 데이터 정리",
        "content": "딕셔너리와 문자열 분해를 활용해 데이터를 정리합니다.",
        "items": [
            problem("고정 전화번호 찾기", ["이름이 입력되면 미리 준비된 연락처에서 전화번호를 찾아 출력하세요. 민수는 010-1111-1111, 지수는 010-2222-2222, 하늘은 010-3333-3333 입니다."], "딕셔너리에 이름과 번호를 저장하세요.", """phone_book = {\n    "민수": "010-1111-1111",\n    "지수": "010-2222-2222",\n    "하늘": "010-3333-3333"\n}\nname = input().strip()\nprint(phone_book[name])""", "지수", "010-2222-2222"),
            problem("과일 개수 세기", ["첫 줄에 과일 세 개가 공백으로 구분되어 입력됩니다. 각 과일이 몇 번 나왔는지 fruit:count 형태로 한 줄씩 출력하세요. 출력 순서는 입력 순서를 따릅니다."], "딕셔너리에 개수를 누적해보세요.", """fruits = input().split()\ncounts = {}\norder = []\nfor fruit in fruits:\n    if fruit not in counts:\n        counts[fruit] = 0\n        order.append(fruit)\n    counts[fruit] += 1\nfor fruit in order:\n    print(fruit + ":" + str(counts[fruit]))""", "사과 바나나 사과", "사과:2\n바나나:1"),
            problem("문장 단어 수 세기", ["문장이 입력되면 공백으로 나뉜 단어 개수를 출력하세요."], "split 결과의 길이를 구하면 됩니다.", """words = input().split()\nprint(len(words))""", "파이썬 문제 풀이 연습", "4"),
            problem("키 존재 확인", ["딕셔너리에 사과, 바나나, 포도가 있습니다. 과일 이름이 입력되면 있으면 YES, 없으면 NO를 출력하세요."], "in 연산자를 사용하세요.", """fruits = {"사과": 3, "바나나": 5, "포도": 2}\nname = input().strip()\nif name in fruits:\n    print("YES")\nelse:\n    print("NO")""", "딸기", "NO"),
            problem("점수 갱신하기", ["영어 점수와 추가 점수가 한 줄에 입력됩니다. 기본 점수 70에 추가 점수를 더한 값을 출력하세요."], "딕셔너리에 들어 있는 값을 더해보세요.", """parts = input().split()\nbase_scores = {"영어": 70}\nbase_scores["영어"] = base_scores["영어"] + int(parts[1])\nprint(base_scores["영어"])""", "영어 8", "78"),
            problem("딕셔너리 값의 합", ["국어 80, 영어 90, 수학 100 이 저장된 딕셔너리의 총합을 출력하세요."], "딕셔너리 값을 하나씩 더해보세요.", """scores = {"국어": 80, "영어": 90, "수학": 100}\ntotal = 0\nfor key in scores:\n    total += scores[key]\nprint(total)""", "", "270"),
            problem("문자별 개수 세기", ["문자열이 입력되면 각 문자가 몇 번 나왔는지 문자:개수 형태로 한 줄씩 출력하세요. 출력 순서는 처음 등장한 순서를 따릅니다."], "처음 본 문자는 순서 목록에 함께 저장하세요.", """text = input().strip()\ncounts = {}\norder = []\nfor ch in text:\n    if ch not in counts:\n        counts[ch] = 0\n        order.append(ch)\n    counts[ch] += 1\nfor ch in order:\n    print(ch + ":" + str(counts[ch]))""", "level", "l:2\ne:2\nv:1"),
            problem("메뉴 가격 찾기", ["메뉴 이름이 입력되면 가격을 출력하세요. 김밥 3000, 라면 4000, 우동 5000 입니다."], "메뉴와 가격을 딕셔너리로 만드세요.", """menu = {"김밥": 3000, "라면": 4000, "우동": 5000}\nname = input().strip()\nprint(menu[name])""", "우동", "5000"),
            problem("단어 길이 사전 만들기", ["단어 세 개가 한 줄에 입력됩니다. 각 단어의 길이를 단어:길이 형태로 한 줄씩 출력하세요."], "단어를 순회하면서 len을 구하세요.", """words = input().split()\nfor word in words:\n    print(word + ":" + str(len(word)))""", "code python loop", "code:4\npython:6\nloop:4"),
            problem("앞글자 개수 세기", ["단어 세 개가 한 줄에 입력됩니다. 각 단어의 첫 글자가 몇 번 나왔는지 첫글자:개수 형태로 출력하세요."], "word[0]을 키로 삼아 개수를 세어보세요.", """words = input().split()\ncounts = {}\norder = []\nfor word in words:\n    key = word[0]\n    if key not in counts:\n        counts[key] = 0\n        order.append(key)\n    counts[key] += 1\nfor key in order:\n    print(key + ":" + str(counts[key]))""", "apple art banana", "a:2\nb:1"),
        ],
    })

    chapters.append({
        "title": "함수",
        "content": "함수를 정의하고 호출하는 연습을 합니다.",
        "items": [
            problem("더하기 함수 만들기", ["정수 두 개가 입력되면 add 함수를 만들어 두 수의 합을 출력하세요."], "def add(a, b): 형태를 떠올려보세요.", """def add(a, b):\n    return a + b\n\nparts = input().split()\na = int(parts[0])\nb = int(parts[1])\nprint(add(a, b))""", "7 9", "16"),
            problem("제곱 함수 만들기", ["정수가 입력되면 square 함수를 이용해 제곱값을 출력하세요."], "return x * x 를 사용하세요.", """def square(x):\n    return x * x\n\nn = int(input())\nprint(square(n))""", "6", "36"),
            problem("인사 함수 만들기", ["이름이 입력되면 greet 함수로 안녕, 이름! 을 출력하세요."], "함수 안에서 print를 해도 됩니다.", """def greet(name):\n    print("안녕, " + name + "!")\n\nname = input().strip()\ngreet(name)""", "수아", "안녕, 수아!"),
            problem("짝수 판별 함수", ["정수가 입력되면 is_even 함수로 짝수 또는 홀수를 출력하세요."], "함수에서 True/False 대신 문자열을 반환해도 됩니다.", """def is_even(n):\n    if n % 2 == 0:\n        return "짝수"\n    return "홀수"\n\nn = int(input())\nprint(is_even(n))""", "14", "짝수"),
            problem("더 큰 값 반환 함수", ["정수 두 개가 입력되면 bigger 함수로 더 큰 값을 출력하세요."], "if 문으로 비교해서 return 하세요.", """def bigger(a, b):\n    if a > b:\n        return a\n    return b\n\nparts = input().split()\na = int(parts[0])\nb = int(parts[1])\nprint(bigger(a, b))""", "4 19", "19"),
            problem("모음 개수 함수", ["영문 단어가 입력되면 count_vowels 함수로 모음 개수를 출력하세요."], "a, e, i, o, u 중 하나인지 확인하세요.", """def count_vowels(word):\n    count = 0\n    for ch in word:\n        if ch in "aeiouAEIOU":\n            count += 1\n    return count\n\nword = input().strip()\nprint(count_vowels(word))""", "banana", "3"),
            problem("문자 반복 함수", ["문자열과 반복 횟수가 한 줄에 입력됩니다. repeat_text 함수로 문자열을 여러 번 이어 붙여 출력하세요."], "문자열 곱셈을 사용할 수 있습니다.", """def repeat_text(text, n):\n    return text * n\n\nparts = input().split()\ntext = parts[0]\ncount = int(parts[1])\nprint(repeat_text(text, count))""", "ha 3", "hahaha"),
            problem("리스트 총합 함수", ["한 줄에 정수 네 개가 입력됩니다. total_list 함수로 총합을 출력하세요."], "리스트를 함수에 전달해보세요.", """def total_list(nums):\n    return sum(nums)\n\nparts = input().split()\nnums = [int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])]\nprint(total_list(nums))""", "1 2 3 4", "10"),
            problem("할인 가격 함수", ["가격과 할인율이 한 줄에 입력됩니다. discount_price 함수로 할인 후 가격을 출력하세요."], "가격 * (100 - 할인율) // 100 형태를 생각해보세요.", """def discount_price(price, percent):\n    return price * (100 - percent) // 100\n\nparts = input().split()\nprice = int(parts[0])\npercent = int(parts[1])\nprint(discount_price(price, percent))""", "12000 25", "9000"),
            problem("별 줄 함수", ["정수 n이 입력되면 make_stars 함수로 별 n개를 출력하세요."], "함수에서 '*' * n 을 반환하면 됩니다.", """def make_stars(n):\n    return "*" * n\n\nn = int(input())\nprint(make_stars(n))""", "5", "*****"),
        ],
    })

    chapters.append({
        "title": "기초 문제 풀이",
        "content": "여러 개념을 함께 사용하는 짧은 종합 문제를 연습합니다.",
        "items": [
            problem("BMI 구하기", ["몸무게(kg)와 키(cm)가 한 줄에 입력됩니다. BMI를 소수 첫째 자리까지 출력하세요."], "키는 미터로 바꾼 뒤 몸무게를 키의 제곱으로 나누세요.", """parts = input().split()\nweight = float(parts[0])\nheight_cm = float(parts[1])\nheight_m = height_cm / 100\nbmi = weight / (height_m * height_m)\nprint(round(bmi, 1))""", "60 165", "22.0"),
            problem("동전 개수 구하기", ["금액이 입력되면 500원, 100원, 50원, 10원 동전이 각각 몇 개인지 순서대로 출력하세요."], "큰 단위부터 나누고 남은 금액을 갱신하세요.", """money = int(input())\ncoin500 = money // 500\nmoney = money % 500\ncoin100 = money // 100\nmoney = money % 100\ncoin50 = money // 50\nmoney = money % 50\ncoin10 = money // 10\nprint(coin500, coin100, coin50, coin10)""", "1260", "2 2 1 1"),
            problem("시분초로 바꾸기", ["초가 입력되면 시 분 초를 공백으로 구분해 출력하세요."], "3600초와 60초 기준으로 나눠보세요.", """seconds = int(input())\nhour = seconds // 3600\nseconds = seconds % 3600\nminute = seconds // 60\nsecond = seconds % 60\nprint(hour, minute, second)""", "3672", "1 1 12"),
            problem("회문 판별", ["문자열이 입력되면 앞뒤가 같으면 YES, 아니면 NO를 출력하세요."], "원본과 뒤집은 문자열을 비교하세요.", """text = input().strip()\nif text == text[::-1]:\n    print("YES")\nelse:\n    print("NO")""", "radar", "YES"),
            problem("전화번호 마스킹", ["전화번호가 입력되면 마지막 네 자리를 제외한 앞부분을 *로 바꿔 출력하세요."], "길이를 이용해 별표 개수를 만들 수 있습니다.", """phone = input().strip()\nmask = "*" * (len(phone) - 4)\nprint(mask + phone[-4:])""", "01012345678", "*******5678"),
            problem("구구단 묶음 합", ["정수 n이 입력되면 n단의 결과를 모두 더한 값을 출력하세요."], "n * 1부터 n * 9까지 누적합을 구하세요.", """n = int(input())\ntotal = 0\nfor i in range(1, 10):\n    total += n * i\nprint(total)""", "2", "90"),
            problem("긴 단어 개수", ["문장이 입력되면 길이가 4 이상인 단어가 몇 개인지 출력하세요."], "split 후 각 단어의 길이를 검사하세요.", """words = input().split()\ncount = 0\nfor word in words:\n    if len(word) >= 4:\n        count += 1\nprint(count)""", "I like coding every day", "3"),
            problem("중복 제거 목록", ["한 줄에 단어 다섯 개가 입력됩니다. 처음 나온 순서대로 중복 없이 출력하세요."], "결과 리스트에 없을 때만 추가하세요.", """words = input().split()\nresult = []\nfor word in words:\n    if word not in result:\n        result.append(word)\nprint(" ".join(result))""", "a b a c b", "a b c"),
            problem("번갈아 대문자 만들기", ["영문 문자열이 입력되면 짝수 인덱스는 대문자, 홀수 인덱스는 소문자로 바꿔 출력하세요."], "인덱스를 사용해 한 글자씩 처리하세요.", """text = input().strip()\nresult = ""\nfor i in range(len(text)):\n    if i % 2 == 0:\n        result += text[i].upper()\n    else:\n        result += text[i].lower()\nprint(result)""", "python", "PyThOn"),
            problem("누적 합 출력", ["한 줄에 정수 다섯 개가 입력됩니다. 앞에서부터 누적 합을 한 줄에 하나씩 출력하세요."], "합계를 저장하며 반복하세요.", """parts = input().split()\ntotal = 0\nfor value in parts:\n    total += int(value)\n    print(total)""", "1 2 3 4 5", "1\n3\n6\n10\n15"),
        ],
    })

    chapters.append({
        "title": "응용 문제 풀이 1",
        "content": "실생활 느낌의 계산 문제와 조건 판단 문제를 연습합니다.",
        "items": [
            problem("영수증 총액", ["상품 가격과 수량이 한 줄에 두 번 입력됩니다. 총 지불 금액을 출력하세요."], "각 상품의 가격*수량을 더하세요.", """first = input().split()\nsecond = input().split()\nprice1 = int(first[0])\nqty1 = int(first[1])\nprice2 = int(second[0])\nqty2 = int(second[1])\nprint(price1 * qty1 + price2 * qty2)""", "1200 2\n800 3", "4800"),
            problem("버스 요금 구하기", ["나이가 입력되면 8세 미만 무료, 20세 미만 900, 그 외 1300을 출력하세요."], "나이 구간을 조건문으로 나누세요.", """age = int(input())\nif age < 8:\n    print(0)\nelif age < 20:\n    print(900)\nelse:\n    print(1300)""", "15", "900"),
            problem("주차 요금 계산", ["주차 시간이 분으로 입력됩니다. 기본 30분 1000원, 이후 10분마다 500원을 더해 총 요금을 출력하세요."], "추가 시간은 0보다 클 때만 계산하세요.", """minutes = int(input())\nfee = 1000\nif minutes > 30:\n    extra = minutes - 30\n    blocks = extra // 10\n    if extra % 10 != 0:\n        blocks += 1\n    fee += blocks * 500\nprint(fee)""", "52", "2500"),
            problem("세 과목 평균과 결과", ["국어, 영어, 수학 점수가 한 줄에 입력됩니다. 평균이 70 이상이고 모든 과목이 50 이상이면 PASS, 아니면 FAIL을 출력하세요."], "평균과 과락 여부를 함께 확인하세요.", """parts = input().split()\na = int(parts[0])\nb = int(parts[1])\nc = int(parts[2])\navg = (a + b + c) / 3\nif avg >= 70 and a >= 50 and b >= 50 and c >= 50:\n    print("PASS")\nelse:\n    print("FAIL")""", "80 75 60", "PASS"),
            problem("주사위 합 판정", ["주사위 눈 두 개가 입력됩니다. 합이 7 이상이면 WIN, 아니면 TRY를 출력하세요."], "합계를 먼저 계산하세요.", """parts = input().split()\na = int(parts[0])\nb = int(parts[1])\nif a + b >= 7:\n    print("WIN")\nelse:\n    print("TRY")""", "3 4", "WIN"),
            problem("단어 액자 만들기", ["단어가 입력되면 위아래는 별표로 감싼 줄, 가운데는 *단어* 형태로 출력하세요."], "단어 길이에 맞춰 별표 개수를 정하세요.", """word = input().strip()\nline = "*" * (len(word) + 2)\nprint(line)\nprint("*" + word + "*")\nprint(line)""", "CODE", "******\n*CODE*\n******"),
            problem("단어 순서 뒤집기", ["세 단어가 한 줄에 입력되면 순서를 거꾸로 출력하세요."], "split 후 reverse를 사용해보세요.", """words = input().split()\nwords.reverse()\nprint(" ".join(words))""", "하나 둘 셋", "셋 둘 하나"),
            problem("가장 긴 단어 찾기", ["세 단어가 한 줄에 입력되면 가장 긴 단어를 출력하세요. 길이가 같다면 먼저 나온 단어를 출력하세요."], "현재 최장 단어를 저장하며 비교하세요.", """words = input().split()\nlongest = words[0]\nfor word in words:\n    if len(word) > len(longest):\n        longest = word\nprint(longest)""", "code python ai", "python"),
            problem("퀴즈 점수 합계", ["한 줄에 정수 다섯 개가 입력됩니다. 0점은 제외하고 합계를 출력하세요."], "0이 아닐 때만 더하세요.", """parts = input().split()\ntotal = 0\nfor value in parts:\n    score = int(value)\n    if score != 0:\n        total += score\nprint(total)""", "10 0 20 30 0", "60"),
            problem("세 점수 등수 매기기", ["정수 세 개가 입력됩니다. 가장 큰 점수를 1등, 다음을 2등, 마지막을 3등으로 보며 첫 번째 점수의 등수를 출력하세요."], "점수보다 큰 값이 몇 개인지 세면 등수가 됩니다.", """parts = input().split()\na = int(parts[0])\nb = int(parts[1])\nc = int(parts[2])\nrank = 1\nif b > a:\n    rank += 1\nif c > a:\n    rank += 1\nprint(rank)""", "70 90 80", "3"),
        ],
    })

    chapters.append({
        "title": "응용 문제 풀이 2",
        "content": "반복문, 문자열, 리스트를 함께 활용하는 문제를 연습합니다.",
        "items": [
            problem("문자 등장 위치 출력", ["문자열과 찾을 문자가 한 줄씩 입력됩니다. 찾는 문자가 등장하는 위치를 한 줄에 하나씩 출력하세요."], "인덱스를 반복하면서 같은지 비교하세요.", """text = input().strip()\ntarget = input().strip()\nfor i in range(len(text)):\n    if text[i] == target:\n        print(i)""", "banana\na", "1\n3\n5"),
            problem("연속 합이 10 이상인 개수", ["한 줄에 정수 다섯 개가 입력됩니다. 앞에서부터 누적 합이 10 이상이 되는 순간의 개수를 출력하세요."], "누적 합을 만들며 기준을 넘는지 확인하세요.", """parts = input().split()\ntotal = 0\ncount = 0\nfor value in parts:\n    total += int(value)\n    if total >= 10:\n        count += 1\nprint(count)""", "1 2 7 3 1", "3"),
            problem("모음만 이어 붙이기", ["영문 문자열이 입력되면 모음만 모아 출력하세요."], "모음이면 결과 문자열에 더하세요.", """text = input().strip()\nresult = ""\nfor ch in text:\n    if ch in "aeiouAEIOU":\n        result += ch\nprint(result)""", "education", "euaio"),
            problem("숫자 중 가장 작은 값", ["한 줄에 정수 네 개가 입력됩니다. 가장 작은 값을 출력하세요."], "현재 최소값을 저장해보세요.", """parts = input().split()\nnums = [int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])]\nmin_value = nums[0]\nfor n in nums:\n    if n < min_value:\n        min_value = n\nprint(min_value)""", "8 3 11 5", "3"),
            problem("문장 끝의 마침표 확인", ["문장이 입력되면 마지막 글자가 마침표면 YES, 아니면 NO를 출력하세요."], "문자열의 마지막 글자를 확인하세요.", """text = input().rstrip()\nif text[-1] == ".":\n    print("YES")\nelse:\n    print("NO")""", "파이썬은 재미있다.", "YES"),
            problem("숫자 문자열 합", ["숫자로만 이루어진 문자열이 입력되면 각 자리 숫자의 합을 출력하세요."], "문자 하나씩 int로 바꿔 더하세요.", """text = input().strip()\ntotal = 0\nfor ch in text:\n    total += int(ch)\nprint(total)""", "50231", "11"),
            problem("문자열 압축 기초", ["문자열이 입력되면 같은 문자가 연속해서 나올 때 문자와 개수를 붙여 출력하세요."], "이전 문자와 현재 문자를 비교하세요.", """text = input().strip()\nresult = ""\ncount = 1\nfor i in range(1, len(text)):\n    if text[i] == text[i - 1]:\n        count += 1\n    else:\n        result += text[i - 1] + str(count)\n        count = 1\nresult += text[-1] + str(count)\nprint(result)""", "aaabbc", "a3b2c1"),
            problem("세 수 중 가운데 값", ["정수 세 개가 입력됩니다. 크기순으로 정렬했을 때 가운데 값을 출력하세요."], "리스트를 정렬한 뒤 인덱스 1을 출력하세요.", """parts = input().split()\nnums = [int(parts[0]), int(parts[1]), int(parts[2])]\nnums.sort()\nprint(nums[1])""", "9 2 5", "5"),
            problem("줄바꿈 없이 누적 출력", ["정수 n이 입력되면 1부터 n까지를 공백으로 구분해 한 줄에 출력하세요."], "print의 end 옵션을 사용해보세요.", """n = int(input())\nfor i in range(1, n + 1):\n    if i == n:\n        print(i)\n    else:\n        print(i, end=" ")""", "5", "1 2 3 4 5"),
            problem("문자열 회전", ["문자열이 입력되면 맨 앞 글자를 맨 뒤로 보낸 결과를 출력하세요."], "슬라이싱으로 앞과 뒤를 나눌 수 있습니다.", """text = input().strip()\nprint(text[1:] + text[0])""", "python", "ythonp"),
        ],
    })

    chapters.append({
        "title": "실전형 10문제",
        "content": "입력, 조건, 반복, 문자열, 함수 개념을 함께 사용하는 마무리 문제입니다.",
        "items": [
            problem("간단한 암호 만들기", ["문자열이 입력되면 각 글자 사이에 *를 넣어 출력하세요."], "반복문으로 한 글자씩 이어 붙이세요.", """text = input().strip()\nresult = ""\nfor i in range(len(text)):\n    result += text[i]\n    if i != len(text) - 1:\n        result += "*"\nprint(result)""", "code", "c*o*d*e"),
            problem("시험 최고점과 평균", ["한 줄에 점수 네 개가 입력됩니다. 첫 줄에 최고점, 둘째 줄에 평균을 출력하세요."], "최고점은 비교하며 찾고 평균은 합계를 나누세요.", """parts = input().split()\nnums = [int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])]\nmax_value = nums[0]\nfor n in nums:\n    if n > max_value:\n        max_value = n\nprint(max_value)\nprint(sum(nums) / len(nums))""", "80 95 70 88", "95\n83.25"),
            problem("반 번호 만들기", ["학년과 반이 한 줄에 입력되면 학년-반 형식으로 출력하세요."], "문자열끼리 이어 붙이면 됩니다.", """parts = input().split()\ngrade = parts[0]\nroom = parts[1]\nprint(grade + "-" + room)""", "3 2", "3-2"),
            problem("박수 게임 숫자 세기", ["정수 n이 입력되면 1부터 n까지 숫자 중 3, 6, 9가 하나라도 들어간 수의 개수를 출력하세요."], "숫자를 문자열로 바꿔 확인하세요.", """n = int(input())\ncount = 0\nfor i in range(1, n + 1):\n    text = str(i)\n    if "3" in text or "6" in text or "9" in text:\n        count += 1\nprint(count)""", "20", "4"),
            problem("과목명과 점수 출력", ["첫 줄에 과목명, 둘째 줄에 점수가 입력됩니다. 과목명: 점수점 형식으로 출력하세요."], "문자열을 차례대로 이어 붙여보세요.", """subject = input().strip()\nscore = input().strip()\nprint(subject + ": " + score + "점")""", "수학\n95", "수학: 95점"),
            problem("줄 번호 붙이기", ["한 줄에 단어 세 개가 입력됩니다. 1:단어 형태로 한 줄씩 출력하세요."], "인덱스를 1부터 사용하세요.", """words = input().split()\nfor i in range(len(words)):\n    print(str(i + 1) + ":" + words[i])""", "red blue green", "1:red\n2:blue\n3:green"),
            problem("문자열 중앙 글자", ["문자열이 입력되면 길이가 홀수일 때 중앙 글자를 출력하세요."], "길이를 2로 나눈 몫을 인덱스로 사용하세요.", """text = input().strip()\nmid = len(text) // 2\nprint(text[mid])""", "robot", "b"),
            problem("출석 점수 계산", ["출석 횟수와 지각 횟수가 한 줄에 입력됩니다. 출석 1회당 5점, 지각 1회당 2점 감점일 때 최종 점수를 출력하세요. 시작 점수는 100점입니다."], "100에서 감점 값을 빼세요.", """parts = input().split()\nattendance = int(parts[0])\nlate = int(parts[1])\nscore = 100 + attendance * 5 - late * 2\nprint(score)""", "10 3", "144"),
            problem("가장 많이 나온 문자", ["문자열이 입력되면 가장 많이 나온 문자를 출력하세요. 개수가 같으면 먼저 등장한 문자를 출력하세요."], "개수 딕셔너리와 순서 목록을 함께 쓰면 편합니다.", """text = input().strip()\ncounts = {}\norder = []\nfor ch in text:\n    if ch not in counts:\n        counts[ch] = 0\n        order.append(ch)\n    counts[ch] += 1\nbest = order[0]\nfor ch in order:\n    if counts[ch] > counts[best]:\n        best = ch\nprint(best)""", "banana", "a"),
            problem("반복 없는 합계", ["한 줄에 정수 다섯 개가 입력됩니다. 같은 숫자는 한 번만 더해 합계를 출력하세요."], "이미 더한 숫자는 결과 목록에 기록하세요.", """parts = input().split()\nused = []\ntotal = 0\nfor value in parts:\n    number = int(value)\n    if number not in used:\n        used.append(number)\n        total += number\nprint(total)""", "1 2 2 3 1", "6"),
        ],
    })

    chapters = chapters[:10]
    total_items = sum(len(chapter["items"]) for chapter in chapters)
    if total_items != 100:
        raise ValueError(f"문항 수가 100개가 아닙니다: {total_items}")
    return chapters


class Command(BaseCommand):
    help = "메듀랩용 자체 제작 '파이썬 100문제' 과정을 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="같은 이름의 기존 과정이 있으면 문항을 모두 지우고 다시 생성합니다.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        program_type, _ = ProgramType.objects.get_or_create(
            name=PROGRAM_TYPE_NAME,
            defaults={"order": 50},
        )

        program, created = LearningProgram.objects.get_or_create(
            name=COURSE_NAME,
            defaults={
                "description": "메듀랩 자체 제작 파이썬 문제 100선입니다. 출력, 입력, 조건문, 반복문, 문자열, 리스트, 함수, 응용 문제를 단계적으로 연습합니다.",
                "program_type": program_type,
                "is_active": True,
            },
        )

        if not created and not options["replace"] and program.chapters.exists():
            self.stdout.write(self.style.WARNING("이미 같은 이름의 과정이 있습니다. 다시 넣으려면 --replace 옵션을 사용하세요."))
            return

        program.description = "메듀랩 자체 제작 파이썬 문제 100선입니다. 출력, 입력, 조건문, 반복문, 문자열, 리스트, 함수, 응용 문제를 단계적으로 연습합니다."
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
                    key=f"py100_{chapter_index:02d}_{item_index:02d}",
                    title=item_data["title"],
                    item_type="problem",
                    explain_html=item_data["explain_html"],
                    hint=item_data["hint"],
                    answer_code=item_data["answer_code"],
                    example_input=item_data["example_input"],
                    expected_output=item_data["expected_output"],
                )

        self.stdout.write(self.style.SUCCESS(f"'{COURSE_NAME}' 과정이 생성되었습니다."))
        self.stdout.write(self.style.SUCCESS(f"총 {len(chapters)}개 챕터, {item_total}개 문항을 등록했습니다."))
