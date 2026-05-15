import io
import os
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medulab_arcade.settings")

import django

django.setup()

from courses.models import LearningProgram


PROGRAM_ID = 2


SPECIAL_INPUTS = {
    12: "철수",
    13: "초밥\n콜라",
    15: "3\n5",
    16: "2010",
    17: "강아지",
    18: "홍길동\n13",
    19: "3\n5",
    20: "파이썬\n짱",
    21: "수학\n영어\n과학",
    22: "150\n42",
    23: "저는 파이썬을 좋아합니다!",
    24: "열심히 공부하기!",
    54: "chulsoo",
    55: "철수\n6",
    56: "python@gmail.com",
    58: "너는 바보",
    77: "15",
    78: "4",
    79: "75",
    80: "5",
    81: "비",
    82: "admin",
    83: "150",
    102: "3",
    111: "1",
    113: "철수",
    114: "3",
    116: "1",
    117: "4",
    119: "1234",
}


MANUAL_CODE = {
    21: 'sub1 = input("과목1: ")\nsub2 = input("과목2: ")\nsub3 = input("과목3: ")\nprint(sub1, sub2, sub3)',
    22: 'height = input("키: ")\nweight = input("몸무게: ")\nprint(height + "cm", weight + "kg")',
    23: 'intro = input("자기소개: ")\nprint(intro)',
    24: 'goal = input("목표: ")\nprint(goal)',
    38: 'def add(x, y):\n    return x + y\n\nprint(add(3, 5))',
    42: 'def subtract(x, y):\n    return x - y\n\nprint(subtract(10, 3))',
    43: 'print(20 // 4)',
    54: 'name = input()\nprint(name.upper())',
    55: 'name = input()\ngrade = input()\nprint(f"{name}은 {grade}학년입니다")',
    56: 'email = input()\nprint(email.split("@")[0])',
    58: 'msg = input()\nprint(msg.replace("바보", "***"))',
    77: 'age = int(input("나이: "))\nif age >= 20:\n    print("성인")\nelse:\n    print("미성년자")',
    78: 'num = int(input())\nif num % 2 == 0:\n    print("짝수")\nelse:\n    print("홀수")',
    79: 'score = int(input())\nif score >= 60:\n    print("합격")\nelse:\n    print("불합격")',
    80: 'grade = int(input())\nif grade <= 3:\n    print("저학년")\nelse:\n    print("고학년")',
    81: 'weather = input()\nif weather == "비":\n    print("우산 챙기기")\nelse:\n    print("산책하기")',
    82: 'user = input()\nif user == "admin":\n    print("관리자")\nelse:\n    print("일반 사용자")',
    83: 'height = int(input())\nif height >= 140:\n    print("탑승 가능")\nelse:\n    print("탑승 불가")',
    89: 'for i in range(10):\n    if i == 5:\n        break\n    print(i)',
    90: 'for i in range(5):\n    if i == 2:\n        continue\n    print(i)',
    95: 'for i in range(1, 11):\n    if i % 2 == 0:\n        print(i)',
    97: 'def hello():\n    print("안녕하세요")\n\nhello()',
    98: 'def clap():\n    print("짝!")\n\nclap()\nclap()',
    99: 'def greet(name):\n    print("안녕,", name)\n\ngreet("철수")',
    100: 'def add(a, b):\n    print(a + b)\n\nadd(3, 5)',
    101: 'def add(a, b):\n    return a + b\n\nprint(add(2, 4))',
    102: 'def square(n):\n    return n * n\n\nnum = int(input())\nprint(square(num))',
    103: 'def show():\n    print("====")\n    print("메뉴")\n    print("====")\n\nshow()',
    104: 'def hello():\n    print("안녕하세요")\n\nhello()',
    105: 'def add(a, b):\n    return a + b\n\nprint(add(3, 4))',
    106: 'def is_even(n):\n    return n % 2 == 0\n\nprint(is_even(4))',
    107: 'def square(n):\n    return n * n\n\nprint(square(5))',
    108: 'def intro(name):\n    print("안녕하세요", name)\n\nintro("철수")',
    109: 'def calc(a, b):\n    return a + b\n\nprint(calc(10, 20))',
    110: 'def show_menu():\n    print("1. 인사하기")\n    print("2. 종료")\n\nshow_menu()',
    111: 'choice = input()\nif choice == "1":\n    print("안녕하세요!")\nelse:\n    print("종료합니다")',
    112: 'while True:\n    print("메뉴")\n    break',
    113: 'def greet(name):\n    print("안녕하세요", name)\n\nname = input()\ngreet(name)',
    114: 'answer = 3\nnum = int(input())\nif num == answer:\n    print("정답")\nelse:\n    print("틀림")',
    115: 'def add(a, b):\n    return a + b\n\nprint(add(3, 5))',
    116: 'choice = input()\nif choice == "1":\n    print("게임 시작")\nelse:\n    print("종료")',
    117: 'num = int(input())\nif num % 2 == 0:\n    print("성공")\nelse:\n    print("실패")',
    118: 'for i in range(3):\n    print("안녕하세요")',
    119: 'pwd = input()\nif pwd == "1234":\n    print("통과")\nelse:\n    print("실패")',
    120: 'total = 0\nfor i in range(1, 6):\n    total += i\nprint(total)',
    121: 'while True:\n    print("실행")\n    break',
}


class MockInput:
    def __init__(self, data: str):
        self.lines = data.splitlines() if data else []
        self.index = 0

    def __call__(self, prompt: str = "") -> str:
        if self.index < len(self.lines):
            value = self.lines[self.index]
            self.index += 1
            return value
        return ""


def execute(code: str, input_str: str) -> str:
    allowed_builtins = {
        "print": print,
        "range": range,
        "len": len,
        "int": int,
        "str": str,
        "float": float,
        "list": list,
        "dict": dict,
        "sum": sum,
        "abs": abs,
        "round": round,
        "input": MockInput(input_str),
        "type": type,
    }

    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    try:
        exec(code, {"__builtins__": allowed_builtins})
        return captured.getvalue().replace("\r\n", "\n").rstrip("\n")
    finally:
        sys.stdout = old_stdout


def clean_code(code: str) -> str:
    code = (code or "").replace("\r\n", "\n")
    code = code.replace('\\"', '"').replace("\\'", "'")

    lines = []
    in_block = False
    prev_colon = False

    for raw in code.split("\n"):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.endswith(";"):
            stripped = stripped[:-1]

        if stripped.startswith(("elif ", "else:", "except", "finally:")):
            indent = ""
            in_block = stripped.endswith(":")
        elif prev_colon:
            indent = "    "
            in_block = True
        elif raw[:1].isspace():
            indent = "    " if in_block else ""
            in_block = stripped.endswith(":") or in_block
        else:
            indent = ""
            in_block = stripped.endswith(":")

        lines.append(f"{indent}{stripped}")
        prev_colon = stripped.endswith(":")

    return "\n".join(lines)


def main():
    program = LearningProgram.objects.get(id=PROGRAM_ID)
    updated = 0

    for chapter in program.chapters.all().order_by("number", "id"):
        for index, item in enumerate(chapter.items.all().order_by("id"), start=1):
            code = MANUAL_CODE.get(item.id, clean_code(item.answer_code or ""))
            item.answer_code = code
            item.number = index

            if item.id in SPECIAL_INPUTS:
                item.example_input = SPECIAL_INPUTS[item.id]

            if code:
                item.expected_output = execute(code, item.example_input or "")

            item.save()
            updated += 1

    print(f"updated {updated} items in {program.name}")


if __name__ == "__main__":
    main()
