from html import escape

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Chapter, Item, LearningProgram, ProgramType


COURSE_NAME = "COS Pro 파이썬 1급 대비"
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

    # ── 1장: 재귀 알고리즘 심화 ──────────────────────────────────────────────
    chapters.append({
        "title": "재귀 알고리즘 심화",
        "content": "분할정복, 메모이제이션, 복잡한 재귀 패턴을 익힙니다.",
        "items": [
            problem(
                "메모이제이션 피보나치",
                ["정수 n이 입력되면 메모이제이션을 활용한 재귀로 피보나치 수열의 n번째 값을 출력하세요. (F(1)=1, F(2)=1)"],
                "딕셔너리 memo 를 두고 계산된 값을 저장하세요.",
                "memo = {}\ndef fib(n):\n    if n <= 2:\n        return 1\n    if n in memo:\n        return memo[n]\n    memo[n] = fib(n-1) + fib(n-2)\n    return memo[n]\n\nprint(fib(int(input())))",
                "10",
                "55",
            ),
            problem(
                "분할정복 거듭제곱",
                ["밑(base)과 지수(exp)가 입력됩니다. 분할정복 방식으로 base^exp 를 계산해 출력하세요."],
                "exp가 짝수면 (base^(exp//2))^2, 홀수면 base * base^(exp-1) 으로 분기하세요.",
                "def power(b, e):\n    if e == 0:\n        return 1\n    if e % 2 == 0:\n        half = power(b, e // 2)\n        return half * half\n    return b * power(b, e - 1)\n\nb, e = map(int, input().split())\nprint(power(b, e))",
                "2 10",
                "1024",
            ),
            problem(
                "재귀로 순열 생성",
                ["정수 n이 입력되면 1부터 n까지의 숫자로 만들 수 있는 모든 순열을 사전 순으로 한 줄씩 출력하세요."],
                "백트래킹으로 used 배열을 관리하며 경로를 쌓으세요.",
                "n = int(input())\nresult = []\ndef permute(path, used):\n    if len(path) == n:\n        result.append(path[:])\n        return\n    for i in range(1, n+1):\n        if not used[i]:\n            used[i] = True\n            path.append(i)\n            permute(path, used)\n            path.pop()\n            used[i] = False\nused = [False] * (n+1)\npermute([], used)\nfor p in result:\n    print(*p)",
                "3",
                "1 2 3\n1 3 2\n2 1 3\n2 3 1\n3 1 2\n3 2 1",
            ),
            problem(
                "재귀로 조합 생성",
                ["n과 k가 입력됩니다. 1부터 n까지에서 k개를 고르는 모든 조합을 사전 순으로 출력하세요."],
                "start 인덱스를 전달해 중복 없이 고르세요.",
                "n, k = map(int, input().split())\nresult = []\ndef combine(start, path):\n    if len(path) == k:\n        result.append(path[:])\n        return\n    for i in range(start, n+1):\n        path.append(i)\n        combine(i+1, path)\n        path.pop()\ncombine(1, [])\nfor c in result:\n    print(*c)",
                "4 2",
                "1 2\n1 3\n1 4\n2 3\n2 4\n3 4",
            ),
            problem(
                "재귀로 하노이 탑 출력",
                ["원판 수 n이 입력됩니다. 하노이 탑 이동 과정을 A→C (B 보조) 순서로 출력하세요."],
                "hanoi(n, from, to, via) 재귀를 사용하세요.",
                "def hanoi(n, frm, to, via):\n    if n == 1:\n        print(f'{frm} -> {to}')\n        return\n    hanoi(n-1, frm, via, to)\n    print(f'{frm} -> {to}')\n    hanoi(n-1, via, to, frm)\n\nhanoi(int(input()), 'A', 'C', 'B')",
                "3",
                "A -> C\nA -> B\nC -> B\nA -> C\nB -> A\nB -> C\nA -> C",
            ),
            problem(
                "재귀로 부분 집합 합",
                ["정수 리스트와 목표 합이 한 줄씩 입력됩니다. 부분 집합의 합이 목표와 일치하는 부분 집합의 수를 출력하세요."],
                "각 원소를 포함/제외하는 두 가지 경우를 재귀로 탐색하세요.",
                "nums = list(map(int, input().split()))\ntarget = int(input())\ncount = [0]\ndef dfs(idx, current):\n    if idx == len(nums):\n        if current == target:\n            count[0] += 1\n        return\n    dfs(idx+1, current + nums[idx])\n    dfs(idx+1, current)\ndfs(0, 0)\nprint(count[0])",
                "1 2 3 4 5\n5",
                "3",
            ),
            problem(
                "메모이제이션 최소 동전 수",
                ["동전 종류가 한 줄에, 목표 금액이 둘째 줄에 입력됩니다. 목표 금액을 만드는 최소 동전 수를 출력하세요. 불가능하면 -1을 출력하세요."],
                "memo[amount] 에 최솟값을 저장하며 재귀하세요.",
                "coins = list(map(int, input().split()))\namount = int(input())\nmemo = {}\ndef min_coins(n):\n    if n == 0:\n        return 0\n    if n < 0:\n        return float('inf')\n    if n in memo:\n        return memo[n]\n    res = min(min_coins(n - c) for c in coins) + 1\n    memo[n] = res\n    return res\nresult = min_coins(amount)\nprint(result if result != float('inf') else -1)",
                "1 5 6 9\n11",
                "2",
            ),
            problem(
                "재귀로 팰린드롬 분할 수",
                ["문자열이 입력됩니다. 모든 부분 문자열이 팰린드롬이 되도록 분할하는 방법의 수를 출력하세요."],
                "is_palindrome 확인 후 재귀로 분할 경로를 탐색하세요.",
                "s = input().strip()\ncount = [0]\ndef is_pal(t):\n    return t == t[::-1]\ndef dfs(start):\n    if start == len(s):\n        count[0] += 1\n        return\n    for end in range(start+1, len(s)+1):\n        if is_pal(s[start:end]):\n            dfs(end)\ndfs(0)\nprint(count[0])",
                "aab",
                "2",
            ),
            problem(
                "재귀로 N-Queen 해의 수",
                ["정수 n이 입력되면 n×n 체스판에서 n개의 퀸이 서로 공격하지 않도록 놓는 경우의 수를 출력하세요."],
                "행마다 퀸을 놓고 열·대각선 충돌을 확인하세요.",
                "n = int(input())\ncount = [0]\ndef is_safe(queens, row, col):\n    for r, c in enumerate(queens):\n        if c == col or abs(r - row) == abs(c - col):\n            return False\n    return True\ndef solve(queens):\n    row = len(queens)\n    if row == n:\n        count[0] += 1\n        return\n    for col in range(n):\n        if is_safe(queens, row, col):\n            solve(queens + [col])\nsolve([])\nprint(count[0])",
                "6",
                "4",
            ),
            problem(
                "재귀로 계단 오르기 경우의 수",
                ["계단 수 n이 입력됩니다. 한 번에 1칸 또는 2칸을 오를 수 있을 때 n개의 계단을 오르는 경우의 수를 메모이제이션 재귀로 출력하세요."],
                "stairs(n) = stairs(n-1) + stairs(n-2), 기저 조건: stairs(1)=1, stairs(2)=2 입니다.",
                "memo = {}\ndef stairs(n):\n    if n == 1:\n        return 1\n    if n == 2:\n        return 2\n    if n in memo:\n        return memo[n]\n    memo[n] = stairs(n-1) + stairs(n-2)\n    return memo[n]\n\nprint(stairs(int(input())))",
                "5",
                "8",
            ),
        ],
    })

    # ── 2장: 정렬 알고리즘 심화 ──────────────────────────────────────────────
    chapters.append({
        "title": "정렬 알고리즘 심화",
        "content": "병합 정렬, 퀵 정렬, 힙 정렬과 정렬 응용 문제를 익힙니다.",
        "items": [
            problem(
                "병합 정렬 구현",
                ["정수 여러 개가 입력됩니다. 병합 정렬로 오름차순 정렬해 출력하세요."],
                "divide: 반으로 나누고, conquer: 정렬된 두 부분을 병합하세요.",
                "def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i])\n            i += 1\n        else:\n            result.append(b[j])\n            j += 1\n    return result + a[i:] + b[j:]\n\nnums = list(map(int, input().split()))\nprint(*merge_sort(nums))",
                "5 3 8 1 9 2 7 4 6",
                "1 2 3 4 5 6 7 8 9",
            ),
            problem(
                "퀵 정렬 구현",
                ["정수 여러 개가 입력됩니다. 퀵 정렬로 오름차순 정렬해 출력하세요."],
                "피벗을 기준으로 작은 값, 같은 값, 큰 값으로 분리해 재귀하세요.",
                "def quick_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + mid + quick_sort(right)\n\nnums = list(map(int, input().split()))\nprint(*quick_sort(nums))",
                "5 3 8 1 9 2 7 4 6",
                "1 2 3 4 5 6 7 8 9",
            ),
            problem(
                "병합 정렬로 역전쌍 개수",
                ["정수 여러 개가 입력됩니다. 역전쌍(i<j 이고 a[i]>a[j])의 수를 출력하세요."],
                "병합 과정에서 오른쪽 원소가 먼저 선택될 때 왼쪽 남은 수만큼 역전쌍이 발생합니다.",
                "count = [0]\ndef merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\ndef merge(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i])\n            i += 1\n        else:\n            count[0] += len(a) - i\n            result.append(b[j])\n            j += 1\n    return result + a[i:] + b[j:]\n\nnums = list(map(int, input().split()))\nmerge_sort(nums)\nprint(count[0])",
                "3 1 2 5 4",
                "3",
            ),
            problem(
                "heapq로 k번째 최솟값",
                ["정수 여러 개와 k가 한 줄씩 입력됩니다. k번째로 작은 값을 힙으로 구해 출력하세요."],
                "heapq.nsmallest(k, nums)[-1] 을 사용하세요.",
                "import heapq\nnums = list(map(int, input().split()))\nk = int(input())\nprint(heapq.nsmallest(k, nums)[-1])",
                "5 3 8 1 9 2\n3",
                "3",
            ),
            problem(
                "카운팅 정렬",
                ["0 이상 100 이하 정수 여러 개가 입력됩니다. 카운팅 정렬로 오름차순 출력하세요."],
                "각 값의 빈도를 세고 순서대로 출력하세요.",
                "nums = list(map(int, input().split()))\ncount = [0] * 101\nfor n in nums:\n    count[n] += 1\nresult = []\nfor i, c in enumerate(count):\n    result.extend([i] * c)\nprint(*result)",
                "5 3 8 1 3 2",
                "1 2 3 3 5 8",
            ),
            problem(
                "위상 정렬",
                ["노드 수 n과 간선 수 m이 첫 줄에, 이후 m개의 간선(u v: u→v)이 입력됩니다. 위상 정렬 결과를 출력하세요."],
                "진입차수가 0인 노드부터 큐에 넣고 처리하세요.",
                "from collections import deque\nn, m = map(int, input().split())\ngraph = [[] for _ in range(n+1)]\nindegree = [0] * (n+1)\nfor _ in range(m):\n    u, v = map(int, input().split())\n    graph[u].append(v)\n    indegree[v] += 1\nq = deque([i for i in range(1, n+1) if indegree[i] == 0])\nresult = []\nwhile q:\n    node = q.popleft()\n    result.append(node)\n    for nxt in graph[node]:\n        indegree[nxt] -= 1\n        if indegree[nxt] == 0:\n            q.append(nxt)\nprint(*result)",
                "4 4\n1 2\n1 3\n2 4\n3 4",
                "1 2 3 4",
            ),
            problem(
                "정렬로 회의실 배정",
                ["회의 수 n이 첫 줄에, 이후 시작·종료 시간이 n줄 입력됩니다. 겹치지 않게 최대한 많은 회의를 배정할 때 회의 수를 출력하세요."],
                "종료 시간 기준 정렬 후 그리디하게 선택하세요.",
                "n = int(input())\nmeetings = [tuple(map(int, input().split())) for _ in range(n)]\nmeetings.sort(key=lambda x: (x[1], x[0]))\ncount = 0\nend = 0\nfor start, finish in meetings:\n    if start >= end:\n        count += 1\n        end = finish\nprint(count)",
                "5\n1 4\n3 5\n0 6\n5 7\n3 8",
                "2",
            ),
            problem(
                "정렬 후 배낭 그리디",
                ["물건 수 n과 배낭 무게 W가 첫 줄에, 이후 무게:가치 쌍이 n줄 입력됩니다. 단위 무게당 가치가 높은 것부터 넣어 최대 가치를 소수 첫째 자리로 출력하세요. (물건은 쪼갤 수 있습니다)"],
                "가치/무게 기준 내림차순 정렬 후 넣을 수 있는 만큼 넣으세요.",
                "n, W = map(int, input().split())\nitems = []\nfor _ in range(n):\n    w, v = map(int, input().split())\n    items.append((w, v))\nitems.sort(key=lambda x: x[1]/x[0], reverse=True)\ntotal = 0.0\nfor w, v in items:\n    if W <= 0:\n        break\n    take = min(w, W)\n    total += take * v / w\n    W -= take\nprint(round(total, 1))",
                "4 50\n10 60\n20 100\n30 120\n15 90",
                "240.0",
            ),
            problem(
                "외부 파일 없이 계수 정렬 응용",
                ["정수 여러 개가 입력됩니다. 중앙값을 출력하세요. (정렬 후 가운데 값, 짝수 개면 가운데 두 값의 평균)"],
                "정렬 후 n//2 인덱스로 중앙값을 구하세요.",
                "nums = sorted(map(int, input().split()))\nn = len(nums)\nif n % 2 == 1:\n    print(nums[n//2])\nelse:\n    print((nums[n//2-1] + nums[n//2]) / 2)",
                "3 1 4 1 5 9 2 6",
                "3.5",
            ),
            problem(
                "정렬과 슬라이딩 윈도우 최대합",
                ["정수 여러 개와 윈도우 크기 k가 한 줄씩 입력됩니다. 크기 k의 연속 부분 배열 중 합이 가장 큰 값을 출력하세요."],
                "첫 윈도우 합을 구한 뒤 슬라이딩하며 갱신하세요.",
                "nums = list(map(int, input().split()))\nk = int(input())\ncurrent = sum(nums[:k])\nbest = current\nfor i in range(k, len(nums)):\n    current += nums[i] - nums[i-k]\n    best = max(best, current)\nprint(best)",
                "1 3 -1 -3 5 3 6 7\n3",
                "16",
            ),
        ],
    })

    # ── 3장: 스택과 큐 ───────────────────────────────────────────────────────
    chapters.append({
        "title": "스택과 큐",
        "content": "스택·큐를 활용한 알고리즘 문제(괄호, BFS, 모노스택 등)를 익힙니다.",
        "items": [
            problem(
                "괄호 유효성 검사",
                ["괄호 문자열이 입력됩니다. 올바른 괄호 문자열이면 YES, 아니면 NO를 출력하세요."],
                "스택으로 여는 괄호를 쌓고, 닫는 괄호가 나오면 팝 하세요.",
                "s = input().strip()\nstack = []\nvalid = True\nfor ch in s:\n    if ch == '(':\n        stack.append(ch)\n    elif ch == ')':\n        if not stack:\n            valid = False\n            break\n        stack.pop()\nif stack:\n    valid = False\nprint('YES' if valid else 'NO')",
                "((())())",
                "YES",
            ),
            problem(
                "후위 표기식 계산",
                ["후위 표기식이 입력됩니다. 계산 결과를 출력하세요. (피연산자는 정수, 연산자는 + - * /)"],
                "숫자는 push, 연산자는 두 값을 pop해 계산 후 push하세요.",
                "tokens = input().split()\nstack = []\nfor t in tokens:\n    if t in '+-*/':\n        b = stack.pop()\n        a = stack.pop()\n        if t == '+':\n            stack.append(a + b)\n        elif t == '-':\n            stack.append(a - b)\n        elif t == '*':\n            stack.append(a * b)\n        else:\n            stack.append(int(a / b))\n    else:\n        stack.append(int(t))\nprint(stack[0])",
                "3 4 + 2 *",
                "14",
            ),
            problem(
                "BFS로 최단 거리",
                ["미로 크기 n m이 첫 줄에, 이후 n줄에 0(이동가능) 1(벽) 형태의 미로가 입력됩니다. (0,0)에서 (n-1,m-1)까지 최단 거리를 출력하세요. 도달 불가면 -1을 출력하세요."],
                "deque 를 이용한 BFS로 탐색하세요.",
                "from collections import deque\nn, m = map(int, input().split())\ngrid = [list(map(int, input().split())) for _ in range(n)]\nvisited = [[False]*m for _ in range(n)]\nq = deque([(0, 0, 0)])\nvisited[0][0] = True\nresult = -1\nwhile q:\n    r, c, dist = q.popleft()\n    if r == n-1 and c == m-1:\n        result = dist\n        break\n    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:\n        nr, nc = r+dr, c+dc\n        if 0 <= nr < n and 0 <= nc < m and not visited[nr][nc] and grid[nr][nc] == 0:\n            visited[nr][nc] = True\n            q.append((nr, nc, dist+1))\nprint(result)",
                "3 3\n0 0 0\n1 1 0\n0 0 0",
                "4",
            ),
            problem(
                "스택으로 다음 큰 수",
                ["정수 여러 개가 입력됩니다. 각 원소에 대해 오른쪽에서 처음 만나는 큰 수를 출력하세요. 없으면 -1을 출력하세요."],
                "모노 스택: 스택에 인덱스를 쌓고 현재 값이 크면 팝하며 정답을 기록하세요.",
                "nums = list(map(int, input().split()))\nn = len(nums)\nresult = [-1] * n\nstack = []\nfor i in range(n):\n    while stack and nums[stack[-1]] < nums[i]:\n        result[stack.pop()] = nums[i]\n    stack.append(i)\nprint(*result)",
                "4 5 2 10 8",
                "5 10 10 -1 -1",
            ),
            problem(
                "큐로 프린터 우선순위",
                ["첫 줄에 대기 중인 문서 우선순위, 둘째 줄에 확인할 문서 인덱스가 입력됩니다. 해당 문서가 몇 번째로 출력되는지 출력하세요."],
                "deque 로 시뮬레이션하며 순서를 세세요.",
                "from collections import deque\nprior = list(map(int, input().split()))\ntarget = int(input())\nq = deque(enumerate(prior))\norder = 0\nwhile q:\n    idx, p = q.popleft()\n    if any(x[1] > p for x in q):\n        q.append((idx, p))\n    else:\n        order += 1\n        if idx == target:\n            print(order)\n            break",
                "1 1 9 1 1 1\n0",
                "5",
            ),
            problem(
                "스택으로 히스토그램 최대 직사각형",
                ["히스토그램의 각 막대 높이가 입력됩니다. 만들 수 있는 최대 직사각형 넓이를 출력하세요."],
                "모노 증가 스택으로 각 막대가 오른쪽 경계일 때 넓이를 계산하세요.",
                "heights = list(map(int, input().split()))\nheights.append(0)\nstack = []\nmax_area = 0\nfor i, h in enumerate(heights):\n    while stack and heights[stack[-1]] > h:\n        top = stack.pop()\n        width = i if not stack else i - stack[-1] - 1\n        max_area = max(max_area, heights[top] * width)\n    stack.append(i)\nprint(max_area)",
                "2 1 5 6 2 3",
                "10",
            ),
            problem(
                "BFS로 연결 요소 개수",
                ["n m이 첫 줄에, 이후 n줄에 0과 1로 이루어진 격자가 입력됩니다. 1로 연결된 영역의 개수를 출력하세요."],
                "방문하지 않은 1을 만날 때마다 BFS로 탐색하고 count를 증가시키세요.",
                "from collections import deque\nn, m = map(int, input().split())\ngrid = [list(map(int, input().split())) for _ in range(n)]\nvisited = [[False]*m for _ in range(n)]\ncount = 0\nfor r in range(n):\n    for c in range(m):\n        if grid[r][c] == 1 and not visited[r][c]:\n            count += 1\n            q = deque([(r, c)])\n            visited[r][c] = True\n            while q:\n                cr, cc = q.popleft()\n                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:\n                    nr, nc = cr+dr, cc+dc\n                    if 0<=nr<n and 0<=nc<m and not visited[nr][nc] and grid[nr][nc]==1:\n                        visited[nr][nc] = True\n                        q.append((nr, nc))\nprint(count)",
                "4 5\n1 1 0 0 0\n1 1 0 0 0\n0 0 1 0 0\n0 0 0 1 1",
                "3",
            ),
            problem(
                "스택으로 올바른 괄호 쌍 수",
                ["괄호 문자열이 입력됩니다. 제거해야 할 최소 괄호 수를 출력하세요."],
                "스택으로 매칭되지 않은 괄호 수를 세세요.",
                "s = input().strip()\nstack = []\nfor ch in s:\n    if ch == '(':\n        stack.append(ch)\n    elif ch == ')':\n        if stack and stack[-1] == '(':\n            stack.pop()\n        else:\n            stack.append(ch)\nprint(len(stack))",
                "())((",
                "3",
            ),
            problem(
                "deque로 슬라이딩 윈도우 최댓값",
                ["정수 여러 개와 윈도우 크기 k가 한 줄씩 입력됩니다. 크기 k의 윈도우를 이동하며 각 윈도우의 최댓값을 출력하세요."],
                "단조 감소 deque 를 유지하세요.",
                "from collections import deque\nnums = list(map(int, input().split()))\nk = int(input())\ndq = deque()\nresult = []\nfor i, n in enumerate(nums):\n    while dq and nums[dq[-1]] <= n:\n        dq.pop()\n    dq.append(i)\n    if dq[0] == i - k:\n        dq.popleft()\n    if i >= k - 1:\n        result.append(nums[dq[0]])\nprint(*result)",
                "1 3 -1 -3 5 3 6 7\n3",
                "3 3 5 5 6 7",
            ),
            problem(
                "큐 시뮬레이션: 요세푸스 문제",
                ["n과 k가 입력됩니다. n명이 원형으로 서서 k번째마다 한 명씩 나올 때 나오는 순서를 출력하세요."],
                "deque 에 1~n을 넣고 k-1번 rotate 후 popleft 를 반복하세요.",
                "from collections import deque\nn, k = map(int, input().split())\nq = deque(range(1, n+1))\nresult = []\nwhile q:\n    q.rotate(-(k-1))\n    result.append(q.popleft())\nprint(*result)",
                "7 3",
                "3 6 2 7 5 1 4",
            ),
        ],
    })

    # ── 4장: 동적 프로그래밍 ────────────────────────────────────────────────
    chapters.append({
        "title": "동적 프로그래밍 (DP)",
        "content": "1차원·2차원 DP 테이블로 최적 부분 구조 문제를 해결합니다.",
        "items": [
            problem(
                "DP: 계단 오르기",
                ["계단 수 n이 첫 줄에, 각 계단의 점수가 둘째 줄에 입력됩니다. 연속 3칸 규칙 없이 얻을 수 있는 최고 점수를 출력하세요."],
                "dp[i] = max(dp[i-2]+s[i], dp[i-3]+s[i-1]+s[i]) 점화식을 사용하세요.",
                "n = int(input())\ns = list(map(int, input().split()))\nif n == 1:\n    print(s[0])\nelif n == 2:\n    print(s[0]+s[1])\nelse:\n    dp = [0]*n\n    dp[0] = s[0]\n    dp[1] = s[0]+s[1]\n    dp[2] = max(s[0]+s[2], s[1]+s[2])\n    for i in range(3, n):\n        dp[i] = max(dp[i-2]+s[i], dp[i-3]+s[i-1]+s[i])\n    print(dp[n-1])",
                "6\n10 20 15 25 10 20",
                "75",
            ),
            problem(
                "DP: 0-1 배낭 문제",
                ["물건 수 n과 배낭 무게 W가 첫 줄에, 이후 무게와 가치가 n줄 입력됩니다. 최대 가치를 출력하세요."],
                "dp[i][w] = max(dp[i-1][w], dp[i-1][w-wt]+val) 점화식을 사용하세요.",
                "n, W = map(int, input().split())\nitems = [tuple(map(int, input().split())) for _ in range(n)]\ndp = [0] * (W+1)\nfor wt, val in items:\n    for w in range(W, wt-1, -1):\n        dp[w] = max(dp[w], dp[w-wt]+val)\nprint(dp[W])",
                "4 7\n2 3\n3 4\n4 5\n5 6",
                "9",
            ),
            problem(
                "DP: 최장 증가 부분수열 (LIS) 길이",
                ["정수 여러 개가 입력됩니다. LIS의 길이를 출력하세요."],
                "dp[i] = i번째 원소로 끝나는 LIS 길이, max(dp[j]+1 where j<i and a[j]<a[i]) 를 사용하세요.",
                "nums = list(map(int, input().split()))\nn = len(nums)\ndp = [1]*n\nfor i in range(1, n):\n    for j in range(i):\n        if nums[j] < nums[i]:\n            dp[i] = max(dp[i], dp[j]+1)\nprint(max(dp))",
                "3 1 4 1 5 9 2 6 5 3",
                "4",
            ),
            problem(
                "DP: 최장 공통 부분수열 (LCS) 길이",
                ["두 문자열이 한 줄씩 입력됩니다. LCS의 길이를 출력하세요."],
                "dp[i][j]: a[:i], b[:j]의 LCS 길이. 같으면 dp[i-1][j-1]+1, 다르면 max(dp[i-1][j], dp[i][j-1]) 입니다.",
                "a = input().strip()\nb = input().strip()\nm, n = len(a), len(b)\ndp = [[0]*(n+1) for _ in range(m+1)]\nfor i in range(1, m+1):\n    for j in range(1, n+1):\n        if a[i-1] == b[j-1]:\n            dp[i][j] = dp[i-1][j-1]+1\n        else:\n            dp[i][j] = max(dp[i-1][j], dp[i][j-1])\nprint(dp[m][n])",
                "ABCBDAB\nBDCAB",
                "4",
            ),
            problem(
                "DP: 동전 교환 경우의 수",
                ["동전 종류와 목표 금액이 한 줄씩 입력됩니다. 목표 금액을 만드는 방법의 수를 출력하세요."],
                "dp[i] += dp[i-coin] 점화식을 사용하세요.",
                "coins = list(map(int, input().split()))\ntarget = int(input())\ndp = [0]*(target+1)\ndp[0] = 1\nfor coin in coins:\n    for i in range(coin, target+1):\n        dp[i] += dp[i-coin]\nprint(dp[target])",
                "1 2 3\n4",
                "7",
            ),
            problem(
                "DP: 편집 거리",
                ["두 문자열이 한 줄씩 입력됩니다. 첫 번째 문자열을 두 번째로 바꾸기 위한 최소 편집 거리를 출력하세요. (삽입·삭제·교체 각 1회)"],
                "dp[i][j]: a[:i]→b[:j] 최소 연산 수. 같으면 dp[i-1][j-1], 다르면 min(삽입, 삭제, 교체)+1 입니다.",
                "a = input().strip()\nb = input().strip()\nm, n = len(a), len(b)\ndp = [[0]*(n+1) for _ in range(m+1)]\nfor i in range(m+1):\n    dp[i][0] = i\nfor j in range(n+1):\n    dp[0][j] = j\nfor i in range(1, m+1):\n    for j in range(1, n+1):\n        if a[i-1] == b[j-1]:\n            dp[i][j] = dp[i-1][j-1]\n        else:\n            dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])\nprint(dp[m][n])",
                "kitten\nsitting",
                "3",
            ),
            problem(
                "DP: 최대 정사각형 넓이",
                ["n m이 첫 줄에, 이후 n줄에 0과 1로 이루어진 행렬이 입력됩니다. 1로만 이루어진 최대 정사각형의 넓이를 출력하세요."],
                "dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1 (grid[i][j]==1일 때) 입니다.",
                "n, m = map(int, input().split())\ngrid = [list(map(int, input().split())) for _ in range(n)]\ndp = [[0]*m for _ in range(n)]\nmax_sq = 0\nfor i in range(n):\n    for j in range(m):\n        if grid[i][j] == 1:\n            if i == 0 or j == 0:\n                dp[i][j] = 1\n            else:\n                dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1\n            max_sq = max(max_sq, dp[i][j])\nprint(max_sq ** 2)",
                "4 5\n1 0 1 0 0\n1 0 1 1 1\n1 1 1 1 1\n1 0 0 1 0",
                "4",
            ),
            problem(
                "DP: 팰린드롬 최소 분할",
                ["문자열이 입력됩니다. 모든 부분 문자열이 팰린드롬이 되도록 분할할 때 최소 컷 수를 출력하세요."],
                "is_pal[i][j] 를 미리 계산하고 dp[i] = min(dp[j]+1) for j where is_pal[j+1][i] 를 사용하세요.",
                "s = input().strip()\nn = len(s)\nis_pal = [[False]*n for _ in range(n)]\nfor i in range(n):\n    is_pal[i][i] = True\nfor length in range(2, n+1):\n    for i in range(n-length+1):\n        j = i+length-1\n        if s[i] == s[j]:\n            is_pal[i][j] = (length == 2) or is_pal[i+1][j-1]\ndp = [float('inf')] * n\nfor i in range(n):\n    if is_pal[0][i]:\n        dp[i] = 0\n    else:\n        for j in range(1, i+1):\n            if is_pal[j][i]:\n                dp[i] = min(dp[i], dp[j-1]+1)\nprint(dp[n-1])",
                "aab",
                "1",
            ),
            problem(
                "DP: 연속 부분합 최대 (카데인)",
                ["정수 여러 개가 입력됩니다. 연속 부분 배열의 합이 최대인 값을 DP로 출력하세요."],
                "dp[i] = max(nums[i], dp[i-1]+nums[i]) 입니다.",
                "nums = list(map(int, input().split()))\ndp = nums[:]\nfor i in range(1, len(nums)):\n    dp[i] = max(nums[i], dp[i-1]+nums[i])\nprint(max(dp))",
                "-2 1 -3 4 -1 2 1 -5 4",
                "6",
            ),
            problem(
                "DP: 격자 최소 경로합",
                ["n m이 첫 줄에, 이후 n줄에 정수로 된 격자가 입력됩니다. 좌상단에서 우하단까지 이동(오른쪽·아래)하며 최소 합을 출력하세요."],
                "dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1]) 입니다.",
                "n, m = map(int, input().split())\ngrid = [list(map(int, input().split())) for _ in range(n)]\ndp = [[0]*m for _ in range(n)]\ndp[0][0] = grid[0][0]\nfor j in range(1, m):\n    dp[0][j] = dp[0][j-1] + grid[0][j]\nfor i in range(1, n):\n    dp[i][0] = dp[i-1][0] + grid[i][0]\nfor i in range(1, n):\n    for j in range(1, m):\n        dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])\nprint(dp[n-1][m-1])",
                "3 3\n1 3 1\n1 5 1\n4 2 1",
                "7",
            ),
        ],
    })

    # ── 5장: 그래프 알고리즘 ─────────────────────────────────────────────────
    chapters.append({
        "title": "그래프 알고리즘",
        "content": "DFS, BFS, 다익스트라, 유니온-파인드 등 그래프 알고리즘을 익힙니다.",
        "items": [
            problem(
                "DFS로 연결 요소 수",
                ["n m이 첫 줄에, 이후 m개의 간선(u v)이 입력됩니다. 연결 요소의 수를 출력하세요."],
                "방문하지 않은 노드에서 DFS를 시작할 때마다 count를 늘리세요.",
                "import sys\nsys.setrecursionlimit(10000)\nn, m = map(int, input().split())\ngraph = [[] for _ in range(n+1)]\nfor _ in range(m):\n    u, v = map(int, input().split())\n    graph[u].append(v)\n    graph[v].append(u)\nvisited = [False]*(n+1)\ndef dfs(node):\n    visited[node] = True\n    for nxt in graph[node]:\n        if not visited[nxt]:\n            dfs(nxt)\ncount = 0\nfor i in range(1, n+1):\n    if not visited[i]:\n        dfs(i)\n        count += 1\nprint(count)",
                "5 3\n1 2\n1 3\n4 5",
                "2",
            ),
            problem(
                "다익스트라 최단 경로",
                ["n m이 첫 줄에, 이후 m개의 간선(u v w)이 입력됩니다. 1번 노드에서 각 노드까지 최단 거리를 출력하세요. 도달 불가는 INF로 출력하세요."],
                "heapq 로 최소 힙을 사용하세요.",
                "import heapq\nn, m = map(int, input().split())\ngraph = [[] for _ in range(n+1)]\nfor _ in range(m):\n    u, v, w = map(int, input().split())\n    graph[u].append((v, w))\ndist = [float('inf')]*(n+1)\ndist[1] = 0\nheap = [(0, 1)]\nwhile heap:\n    d, node = heapq.heappop(heap)\n    if d > dist[node]:\n        continue\n    for nxt, w in graph[node]:\n        nd = d + w\n        if nd < dist[nxt]:\n            dist[nxt] = nd\n            heapq.heappush(heap, (nd, nxt))\nfor i in range(1, n+1):\n    print(dist[i] if dist[i] != float('inf') else 'INF')",
                "4 5\n1 2 2\n1 3 5\n2 3 1\n2 4 4\n3 4 1",
                "0\n2\n3\n4",
            ),
            problem(
                "유니온-파인드: 사이클 탐지",
                ["n m이 첫 줄에, 이후 m개의 간선(u v)이 입력됩니다. 사이클이 존재하면 YES, 없으면 NO를 출력하세요."],
                "union-find 로 같은 집합이면 사이클이 발생합니다.",
                "n, m = map(int, input().split())\nparent = list(range(n+1))\ndef find(x):\n    if parent[x] != x:\n        parent[x] = find(parent[x])\n    return parent[x]\ndef union(x, y):\n    px, py = find(x), find(y)\n    if px == py:\n        return False\n    parent[px] = py\n    return True\ncycle = False\nfor _ in range(m):\n    u, v = map(int, input().split())\n    if not union(u, v):\n        cycle = True\nprint('YES' if cycle else 'NO')",
                "3 3\n1 2\n2 3\n3 1",
                "YES",
            ),
            problem(
                "BFS: 단어 사다리 최소 변환",
                ["시작 단어, 끝 단어, 단어 목록이 입력됩니다. 한 번에 한 글자씩 바꿔 끝 단어에 도달하는 최소 단계를 출력하세요. 불가능하면 0을 출력하세요."],
                "BFS로 현재 단어에서 한 글자 다른 단어로 이동하세요.",
                "from collections import deque\nstart = input().strip()\nend = input().strip()\nword_list = set(input().split())\nif end not in word_list:\n    print(0)\nelse:\n    q = deque([(start, 1)])\n    visited = {start}\n    result = 0\n    while q:\n        word, step = q.popleft()\n        if word == end:\n            result = step\n            break\n        for i in range(len(word)):\n            for c in 'abcdefghijklmnopqrstuvwxyz':\n                nw = word[:i] + c + word[i+1:]\n                if nw in word_list and nw not in visited:\n                    visited.add(nw)\n                    q.append((nw, step+1))\n    print(result)",
                "hit\ncog\nhot dot dog lot log cog",
                "5",
            ),
            problem(
                "플로이드-워셜",
                ["n m이 첫 줄에, 이후 m개의 간선(u v w)이 입력됩니다. 모든 쌍의 최단 거리 행렬을 출력하세요. 도달 불가는 INF로 출력하세요."],
                "3중 for 문으로 dp[i][j] = min(dp[i][j], dp[i][k]+dp[k][j]) 를 갱신하세요.",
                "INF = float('inf')\nn, m = map(int, input().split())\ndp = [[INF]*(n+1) for _ in range(n+1)]\nfor i in range(n+1):\n    dp[i][i] = 0\nfor _ in range(m):\n    u, v, w = map(int, input().split())\n    dp[u][v] = min(dp[u][v], w)\n    dp[v][u] = min(dp[v][u], w)\nfor k in range(1, n+1):\n    for i in range(1, n+1):\n        for j in range(1, n+1):\n            dp[i][j] = min(dp[i][j], dp[i][k]+dp[k][j])\nfor i in range(1, n+1):\n    row = [str(dp[i][j]) if dp[i][j] != INF else 'INF' for j in range(1, n+1)]\n    print(' '.join(row))",
                "3 3\n1 2 3\n2 3 1\n1 3 7",
                "0 3 4\n3 0 1\n4 1 0",
            ),
            problem(
                "MST: 크루스칼 알고리즘",
                ["n m이 첫 줄에, 이후 m개의 간선(u v w)이 입력됩니다. 최소 신장 트리의 총 비용을 출력하세요."],
                "간선을 가중치 오름차순으로 정렬하고 유니온-파인드로 선택하세요.",
                "n, m = map(int, input().split())\nedges = [tuple(map(int, input().split())) for _ in range(m)]\nedges.sort(key=lambda x: x[2])\nparent = list(range(n+1))\ndef find(x):\n    if parent[x] != x:\n        parent[x] = find(parent[x])\n    return parent[x]\ndef union(x, y):\n    px, py = find(x), find(y)\n    if px == py:\n        return False\n    parent[px] = py\n    return True\ntotal = 0\nfor u, v, w in edges:\n    if union(u, v):\n        total += w\nprint(total)",
                "4 5\n1 2 1\n1 3 4\n2 3 2\n2 4 5\n3 4 3",
                "6",
            ),
            problem(
                "DFS: 사이클 길이",
                ["방향 그래프 n m과 m개의 간선이 입력됩니다. 가장 짧은 사이클의 길이를 출력하세요. 없으면 -1을 출력하세요."],
                "각 노드를 시작점으로 BFS/DFS로 자기 자신으로 돌아오는 최소 경로를 찾으세요.",
                "from collections import deque\nn, m = map(int, input().split())\ngraph = [[] for _ in range(n+1)]\nfor _ in range(m):\n    u, v = map(int, input().split())\n    graph[u].append(v)\nmin_cycle = float('inf')\nfor start in range(1, n+1):\n    dist = [-1]*(n+1)\n    dist[start] = 0\n    q = deque([start])\n    while q:\n        node = q.popleft()\n        for nxt in graph[node]:\n            if dist[nxt] == -1:\n                dist[nxt] = dist[node]+1\n                q.append(nxt)\n            elif nxt == start:\n                min_cycle = min(min_cycle, dist[node]+1)\nprint(min_cycle if min_cycle != float('inf') else -1)",
                "4 4\n1 2\n2 3\n3 4\n4 2",
                "3",
            ),
            problem(
                "BFS: 탈출 가능 여부",
                ["n m과 미로가 입력됩니다. S는 시작, E는 출구, #은 벽, .은 통로입니다. 탈출 가능하면 YES와 최단 경로 길이, 불가능하면 NO를 출력하세요."],
                "S를 찾아 BFS를 시작하고 E에 도달하면 거리를 출력하세요.",
                "from collections import deque\nn, m = map(int, input().split())\ngrid = [input() for _ in range(n)]\nstart = None\nfor r in range(n):\n    for c in range(m):\n        if grid[r][c] == 'S':\n            start = (r, c)\nvisited = [[False]*m for _ in range(n)]\nq = deque([(*start, 0)])\nvisited[start[0]][start[1]] = True\nresult = -1\nwhile q:\n    r, c, d = q.popleft()\n    if grid[r][c] == 'E':\n        result = d\n        break\n    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:\n        nr, nc = r+dr, c+dc\n        if 0<=nr<n and 0<=nc<m and not visited[nr][nc] and grid[nr][nc] != '#':\n            visited[nr][nc] = True\n            q.append((nr, nc, d+1))\nif result == -1:\n    print('NO')\nelse:\n    print('YES')\n    print(result)",
                "4 5\nS....\n###.#\n....#\n....E",
                "YES\n9",
            ),
            problem(
                "위상정렬: 선수과목",
                ["과목 수 n과 선수 관계 m이 첫 줄에, 이후 m개의 관계(a b: a 먼저)가 입력됩니다. 위상 정렬로 수강 순서를 출력하세요. 사이클이 있으면 CYCLE을 출력하세요."],
                "진입차수 0인 노드를 큐에 넣고 처리하세요. 결과 수가 n보다 적으면 사이클입니다.",
                "from collections import deque\nn, m = map(int, input().split())\ngraph = [[] for _ in range(n+1)]\nindeg = [0]*(n+1)\nfor _ in range(m):\n    a, b = map(int, input().split())\n    graph[a].append(b)\n    indeg[b] += 1\nq = deque(sorted([i for i in range(1, n+1) if indeg[i] == 0]))\nresult = []\nwhile q:\n    node = q.popleft()\n    result.append(node)\n    candidates = []\n    for nxt in graph[node]:\n        indeg[nxt] -= 1\n        if indeg[nxt] == 0:\n            candidates.append(nxt)\n    for c in sorted(candidates):\n        q.append(c)\nif len(result) == n:\n    print(*result)\nelse:\n    print('CYCLE')",
                "4 4\n1 2\n1 3\n2 4\n3 4",
                "1 2 3 4",
            ),
            problem(
                "이분 탐색: 파라메트릭 서치",
                ["n과 목표값 m이 첫 줄에, n개의 높이가 둘째 줄에 입력됩니다. 절단기를 H로 설정할 때 H 이상인 부분을 잘라 얻는 합이 m 이상이 되는 최대 H를 출력하세요."],
                "이분 탐색으로 H를 정하고 조건을 확인하세요.",
                "n, m = map(int, input().split())\nheights = list(map(int, input().split()))\nleft, right = 0, max(heights)\nresult = 0\nwhile left <= right:\n    mid = (left + right) // 2\n    total = sum(max(0, h - mid) for h in heights)\n    if total >= m:\n        result = mid\n        left = mid + 1\n    else:\n        right = mid - 1\nprint(result)",
                "4 6\n19 15 10 17",
                "15",
            ),
        ],
    })

    # ── 6장: 클래스 심화 (상속·다형성·매직메서드) ────────────────────────────
    chapters.append({
        "title": "클래스 심화 (상속·다형성·매직메서드)",
        "content": "추상 클래스, 다중 상속, __repr__, __eq__, __lt__, __add__ 등을 익힙니다.",
        "items": [
            problem(
                "추상 클래스로 도형 구현",
                ["도형 종류(circle/rect/triangle)와 치수가 입력됩니다. 각 도형의 넓이를 소수 둘째 자리로 출력하세요. (π=3.14)"],
                "abc.ABC 와 @abstractmethod 로 Shape 를 정의하고 각 도형에서 구현하세요.",
                "from abc import ABC, abstractmethod\nclass Shape(ABC):\n    @abstractmethod\n    def area(self): pass\nclass Circle(Shape):\n    def __init__(self, r): self.r = r\n    def area(self): return round(3.14*self.r**2, 2)\nclass Rect(Shape):\n    def __init__(self, w, h): self.w=w; self.h=h\n    def area(self): return round(self.w*self.h, 2)\nclass Triangle(Shape):\n    def __init__(self, b, h): self.b=b; self.h=h\n    def area(self): return round(0.5*self.b*self.h, 2)\nparts = input().split()\nif parts[0]=='circle': s=Circle(float(parts[1]))\nelif parts[0]=='rect': s=Rect(float(parts[1]), float(parts[2]))\nelse: s=Triangle(float(parts[1]), float(parts[2]))\nprint(s.area())",
                "triangle 6 4",
                "12.0",
            ),
            problem(
                "__eq__와 __lt__ 구현",
                ["학생 이름과 점수가 여러 줄 입력됩니다. END 가 나오면 점수 기준 오름차순으로 정렬해 출력하세요."],
                "Student 에 __lt__ 를 구현하고 sorted 로 정렬하세요.",
                "class Student:\n    def __init__(self, name, score):\n        self.name=name; self.score=score\n    def __lt__(self, other):\n        return self.score < other.score\n    def __repr__(self):\n        return f'{self.name}:{self.score}'\nstudents=[]\nwhile True:\n    line=input().strip()\n    if line=='END': break\n    name,score=line.split()\n    students.append(Student(name,int(score)))\nfor s in sorted(students):\n    print(s)",
                "Bob 85\nAlice 92\nChris 78\nEND",
                "Chris:78\nBob:85\nAlice:92",
            ),
            problem(
                "__add__로 벡터 덧셈",
                ["두 벡터가 한 줄씩 입력됩니다(x y 형식). 두 벡터의 합을 출력하세요."],
                "Vector 클래스에 __add__ 를 구현하세요.",
                "class Vector:\n    def __init__(self, x, y): self.x=x; self.y=y\n    def __add__(self, other): return Vector(self.x+other.x, self.y+other.y)\n    def __repr__(self): return f'{self.x} {self.y}'\nax,ay=map(int,input().split())\nbx,by=map(int,input().split())\nprint(Vector(ax,ay)+Vector(bx,by))",
                "1 2\n3 4",
                "4 6",
            ),
            problem(
                "다중 상속",
                ["비행기 정보가 입력됩니다. FlyingVehicle 과 Vehicle 을 다중 상속한 Airplane 클래스를 구현해 info() 가 이름 비행 가능 출력하도록 하세요."],
                "class Airplane(FlyingVehicle, Vehicle): 처럼 다중 상속하세요.",
                "class Vehicle:\n    def __init__(self, name): self.name=name\nclass FlyingVehicle:\n    def fly(self): return '비행 가능'\nclass Airplane(FlyingVehicle, Vehicle):\n    def info(self): print(f'{self.name} {self.fly()}')\nname=input().strip()\na=Airplane(name)\na.info()",
                "보잉747",
                "보잉747 비행 가능",
            ),
            problem(
                "__iter__와 __next__로 커스텀 이터레이터",
                ["시작값 s와 끝값 e가 입력됩니다. EvenIterator 클래스로 s부터 e까지의 짝수를 한 줄씩 출력하세요."],
                "__iter__는 self를 반환하고, __next__는 다음 짝수를 반환하세요.",
                "class EvenIterator:\n    def __init__(self, s, e):\n        self.current=s if s%2==0 else s+1\n        self.end=e\n    def __iter__(self): return self\n    def __next__(self):\n        if self.current>self.end: raise StopIteration\n        val=self.current; self.current+=2; return val\ns,e=map(int,input().split())\nfor n in EvenIterator(s,e):\n    print(n)",
                "3 10",
                "4\n6\n8\n10",
            ),
            problem(
                "@classmethod와 @staticmethod",
                ["온도와 변환 방향(CtoF/FtoC)이 입력됩니다. Temperature 클래스의 클래스 메서드로 변환해 소수 둘째 자리로 출력하세요."],
                "@classmethod 로 변환 메서드를 정의하세요.",
                "class Temperature:\n    @classmethod\n    def to_fahrenheit(cls, c): return round(c*9/5+32, 2)\n    @classmethod\n    def to_celsius(cls, f): return round((f-32)*5/9, 2)\nval, direction=input().split()\nval=float(val)\nif direction=='CtoF': print(Temperature.to_fahrenheit(val))\nelse: print(Temperature.to_celsius(val))",
                "100 CtoF",
                "212.0",
            ),
            problem(
                "믹스인 패턴",
                ["이름이 입력됩니다. LogMixin 과 SaveMixin 을 상속한 Service 클래스를 구현해 process() 호출 시 [LOG] 처리: 이름, [SAVE] 저장: 이름 을 출력하세요."],
                "Mixin 클래스에 각 메서드를 정의하고 Service 에서 super() 를 활용하세요.",
                "class LogMixin:\n    def log(self, name): print(f'[LOG] 처리: {name}')\nclass SaveMixin:\n    def save(self, name): print(f'[SAVE] 저장: {name}')\nclass Service(LogMixin, SaveMixin):\n    def process(self, name):\n        self.log(name)\n        self.save(name)\nname=input().strip()\nService().process(name)",
                "홍길동",
                "[LOG] 처리: 홍길동\n[SAVE] 저장: 홍길동",
            ),
            problem(
                "__slots__로 메모리 최적화 클래스",
                ["이름과 나이가 입력됩니다. __slots__ 를 사용한 Person 클래스로 이름: 이름, 나이: 나이 를 출력하세요."],
                "__slots__ = ['name', 'age'] 를 클래스 변수로 정의하세요.",
                "class Person:\n    __slots__=['name','age']\n    def __init__(self,name,age): self.name=name; self.age=age\n    def info(self): print(f'이름: {self.name}, 나이: {self.age}')\nname,age=input().split()\nPerson(name,int(age)).info()",
                "홍길동 30",
                "이름: 홍길동, 나이: 30",
            ),
            problem(
                "컨텍스트 매니저 클래스",
                ["파일명이 입력됩니다. __enter__와 __exit__가 구현된 FileManager 클래스를 with 문으로 사용해 열기: 파일명, 닫기: 파일명 을 출력하세요."],
                "__enter__는 self를, __exit__는 None을 반환하도록 하세요.",
                "class FileManager:\n    def __init__(self, name): self.name=name\n    def __enter__(self): print(f'열기: {self.name}'); return self\n    def __exit__(self, *args): print(f'닫기: {self.name}')\nname=input().strip()\nwith FileManager(name): pass",
                "data.txt",
                "열기: data.txt\n닫기: data.txt",
            ),
            problem(
                "데코레이터 구현",
                ["정수가 입력됩니다. 실행 시간을 측정하는 timer 데코레이터를 구현하고, 적용된 함수를 실행해 함수이름 실행완료 를 출력하세요."],
                "wraps 없이 단순히 wrapper 함수에서 원본 함수를 호출하고 메시지를 출력하세요.",
                "def timer(func):\n    def wrapper(*args, **kwargs):\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} 실행완료')\n        return result\n    return wrapper\n\n@timer\ndef compute(n):\n    return sum(range(n))\n\nn=int(input())\ncompute(n)",
                "100",
                "compute 실행완료",
            ),
        ],
    })

    # ── 7장: 문자열 알고리즘 ─────────────────────────────────────────────────
    chapters.append({
        "title": "문자열 알고리즘",
        "content": "KMP, 라빈-카프, 정규식 기초, 문자열 처리 고급 알고리즘을 익힙니다.",
        "items": [
            problem(
                "KMP 부분 문자열 검색",
                ["텍스트와 패턴이 한 줄씩 입력됩니다. 패턴이 처음 등장하는 인덱스를 출력하세요. 없으면 -1을 출력하세요."],
                "KMP 알고리즘의 실패 함수(failure function)를 먼저 구하세요.",
                "def kmp(text, pattern):\n    n,m=len(text),len(pattern)\n    fail=[0]*m\n    j=0\n    for i in range(1,m):\n        while j>0 and pattern[i]!=pattern[j]: j=fail[j-1]\n        if pattern[i]==pattern[j]: j+=1; fail[i]=j\n    j=0\n    for i in range(n):\n        while j>0 and text[i]!=pattern[j]: j=fail[j-1]\n        if text[i]==pattern[j]: j+=1\n        if j==m: return i-m+1\n    return -1\ntext=input()\npattern=input().strip()\nprint(kmp(text, pattern))",
                "ababcabcacbab\nabcac",
                "6",
            ),
            problem(
                "정규식으로 이메일 유효성 검사",
                ["문자열이 입력됩니다. 이메일 형식(영숫자@영숫자.영숫자)이면 VALID, 아니면 INVALID를 출력하세요."],
                "re.match(r'^[\\w.]+@[\\w]+\\.[\\w]+$', s) 를 사용하세요.",
                "import re\ns=input().strip()\nif re.match(r'^[\\w.]+@[\\w]+\\.[\\w]+$', s):\n    print('VALID')\nelse:\n    print('INVALID')",
                "user@example.com",
                "VALID",
            ),
            problem(
                "아나그램 그룹화",
                ["단어 여러 개가 한 줄에 입력됩니다. 아나그램끼리 묶어 각 그룹을 사전 순 첫 단어 기준으로 오름차순 출력하세요."],
                "sorted(word) 를 키로 딕셔너리에 그룹화하세요.",
                "words=input().split()\ngroups={}\nfor w in words:\n    key=tuple(sorted(w))\n    groups.setdefault(key,[]).append(w)\nfor key in sorted(groups, key=lambda k: sorted(groups[k])[0]):\n    print(' '.join(sorted(groups[key])))",
                "eat tea tan ate nat bat",
                "ate eat tea\nbat\nnat tan",
            ),
            problem(
                "최장 팰린드롬 부분 문자열",
                ["문자열이 입력됩니다. 가장 긴 팰린드롬 부분 문자열을 출력하세요. 여러 개면 먼저 나오는 것을 출력하세요."],
                "각 위치를 중심으로 홀수/짝수 팰린드롬을 확장하세요.",
                "s=input().strip()\nbest=''\ndef expand(l,r):\n    while l>=0 and r<len(s) and s[l]==s[r]: l-=1; r+=1\n    return s[l+1:r]\nfor i in range(len(s)):\n    for p in [expand(i,i), expand(i,i+1)]:\n        if len(p)>len(best): best=p\nprint(best)",
                "babad",
                "bab",
            ),
            problem(
                "문자열 패턴 매칭 개수",
                ["텍스트와 패턴이 한 줄씩 입력됩니다. 패턴이 텍스트에 몇 번 등장하는지 출력하세요. (중복 허용)"],
                "KMP 또는 단순 슬라이딩으로 모든 등장 위치를 찾으세요.",
                "text=input()\npattern=input().strip()\ncount=0\nstart=0\nwhile True:\n    idx=text.find(pattern, start)\n    if idx==-1: break\n    count+=1\n    start=idx+1\nprint(count)",
                "aababab\nab",
                "3",
            ),
            problem(
                "정규식으로 숫자 추출",
                ["문자열이 입력됩니다. 모든 정수(연속 숫자)를 추출해 합계를 출력하세요."],
                "re.findall(r'\\d+', s) 로 숫자를 추출하세요.",
                "import re\ns=input()\nnums=list(map(int, re.findall(r'\\d+', s)))\nprint(sum(nums))",
                "abc12def34ghi56",
                "102",
            ),
            problem(
                "Z 알고리즘으로 패턴 등장 위치",
                ["텍스트와 패턴이 한 줄씩 입력됩니다. 패턴이 등장하는 모든 시작 인덱스를 오름차순으로 출력하세요."],
                "s = pattern + '#' + text 로 Z 배열을 구하세요.",
                "def z_array(s):\n    n=len(s); z=[0]*n; z[0]=n; l=r=0\n    for i in range(1,n):\n        if i<r: z[i]=min(r-i, z[i-l])\n        while i+z[i]<n and s[z[i]]==s[i+z[i]]: z[i]+=1\n        if i+z[i]>r: l=i; r=i+z[i]\n    return z\ntext=input()\npattern=input().strip()\ns=pattern+'#'+text\nz=z_array(s)\nm=len(pattern)\nresult=[i-m-1 for i in range(m+1,len(s)) if z[i]==m]\nprint(*result) if result else print(-1)",
                "ababcababab\nab",
                "0 2 5 7 9",
            ),
            problem(
                "문자열 압축 후 최소 길이",
                ["문자열이 입력됩니다. 앞에서부터 일정 단위로 잘라 압축(반복되면 횟수+문자열)할 때 가장 짧은 압축 결과의 길이를 출력하세요."],
                "1부터 len(s)//2 까지 단위 길이를 시도하세요.",
                "s=input().strip()\ndef compress(s, unit):\n    result=''\n    i=0\n    while i<len(s):\n        chunk=s[i:i+unit]\n        count=1\n        while s[i+unit:i+unit+unit]==chunk:\n            count+=1; i+=unit\n        result+=(str(count) if count>1 else '')+chunk\n        i+=unit\n    return len(result)\nif len(s)==1:\n    print(1)\nelse:\n    print(min(compress(s,u) for u in range(1,len(s)//2+1)))",
                "aabbaccc",
                "7",
            ),
            problem(
                "롤링 해시로 중복 부분 문자열",
                ["문자열과 길이 k가 한 줄씩 입력됩니다. 길이 k의 부분 문자열 중 중복이 있으면 YES와 중복 문자열을, 없으면 NO를 출력하세요."],
                "set 으로 이미 본 부분 문자열을 관리하세요.",
                "s=input().strip()\nk=int(input())\nseen=set()\nresult=None\nfor i in range(len(s)-k+1):\n    sub=s[i:i+k]\n    if sub in seen:\n        result=sub; break\n    seen.add(sub)\nif result:\n    print('YES')\n    print(result)\nelse:\n    print('NO')",
                "abcabc\n3",
                "YES\nabc",
            ),
            problem(
                "문자열 순열 포함 여부",
                ["두 문자열이 한 줄씩 입력됩니다. 첫 번째 문자열의 순열이 두 번째 문자열의 부분 문자열로 포함되면 YES, 아니면 NO를 출력하세요."],
                "슬라이딩 윈도우로 각 구간의 문자 빈도를 관리하세요.",
                "from collections import Counter\np=input().strip()\ns=input().strip()\nm=len(p)\nif m>len(s):\n    print('NO')\nelse:\n    need=Counter(p)\n    window=Counter(s[:m])\n    found=window==need\n    for i in range(m, len(s)):\n        window[s[i]]+=1\n        window[s[i-m]]-=1\n        if window[s[i-m]]==0: del window[s[i-m]]\n        if window==need: found=True; break\n    print('YES' if found else 'NO')",
                "ab\neidbaooo",
                "YES",
            ),
        ],
    })

    # ── 8장: 실전 모의고사 1 ─────────────────────────────────────────────────
    chapters.append({
        "title": "실전 모의고사 1 (1급 스타일)",
        "content": "COS Pro 1급 완성형·부분완성형 스타일의 종합 실전 문제 10문제입니다. 90분 안에 도전하세요.",
        "items": [
            problem(
                "[모의1-1] 피자 가게 주문 관리",
                ["첫 줄에 메뉴:가격 쌍(콤마 구분), 이후 order 메뉴 또는 total 명령이 입력됩니다. order면 해당 메뉴 가격을 누적하고, total이면 총 금액을 출력하세요. END 로 종료하세요."],
                "PizzaStore 클래스에 order, total 메서드를 구현하세요.",
                "class PizzaStore:\n    def __init__(self, menu):\n        self.menu=menu; self.total_price=0\n    def order(self, item):\n        if item in self.menu: self.total_price+=self.menu[item]\n    def total(self): return self.total_price\n\nmenu={}\nfor item in input().split(','):\n    k,v=item.strip().split(':')\n    menu[k.strip()]=int(v.strip())\nstore=PizzaStore(menu)\nwhile True:\n    line=input().strip()\n    if line=='END': break\n    cmd=line.split()\n    if cmd[0]=='order': store.order(cmd[1])\n    elif cmd[0]=='total': print(store.total())",
                "피자:15000, 파스타:12000, 샐러드:8000\norder 피자\norder 파스타\ntotal\nEND",
                "27000",
            ),
            problem(
                "[모의1-2] 두 스택으로 큐 구현",
                ["enqueue 값 또는 dequeue 명령이 입력됩니다. END가 나오면 dequeue 결과를 순서대로 출력하세요."],
                "스택 두 개(in_stack, out_stack)로 큐를 구현하세요. dequeue 시 out_stack이 비어 있으면 in_stack을 옮기세요.",
                "class QueueWithStacks:\n    def __init__(self): self.in_s=[]; self.out_s=[]\n    def enqueue(self, v): self.in_s.append(v)\n    def dequeue(self):\n        if not self.out_s:\n            while self.in_s: self.out_s.append(self.in_s.pop())\n        return self.out_s.pop() if self.out_s else 'EMPTY'\n\nq=QueueWithStacks(); results=[]\nwhile True:\n    line=input().strip()\n    if line=='END': break\n    parts=line.split()\n    if parts[0]=='enqueue': q.enqueue(int(parts[1]))\n    else: results.append(str(q.dequeue()))\nfor r in results: print(r)",
                "enqueue 1\nenqueue 2\nenqueue 3\ndequeue\ndequeue\nEND",
                "1\n2",
            ),
            problem(
                "[모의1-3] 해밍 거리",
                ["두 이진 문자열이 한 줄씩 입력됩니다. 두 문자열의 해밍 거리(다른 위치의 수)를 출력하세요. 길이가 다르면 -1을 출력하세요."],
                "같은 위치에서 문자가 다른 경우를 세세요.",
                "a=input().strip()\nb=input().strip()\nif len(a)!=len(b): print(-1)\nelse: print(sum(x!=y for x,y in zip(a,b)))",
                "10101\n10010",
                "2",
            ),
            problem(
                "[모의1-4] DP로 최소 비용 경로",
                ["n m과 비용 격자가 입력됩니다. 좌상단에서 우하단까지 오른쪽·아래로만 이동할 때 최소 비용을 출력하세요."],
                "dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1]) 를 사용하세요.",
                "n,m=map(int,input().split())\ng=[list(map(int,input().split())) for _ in range(n)]\ndp=[[0]*m for _ in range(n)]\ndp[0][0]=g[0][0]\nfor j in range(1,m): dp[0][j]=dp[0][j-1]+g[0][j]\nfor i in range(1,n): dp[i][0]=dp[i-1][0]+g[i][0]\nfor i in range(1,n):\n    for j in range(1,m): dp[i][j]=g[i][j]+min(dp[i-1][j],dp[i][j-1])\nprint(dp[n-1][m-1])",
                "3 3\n1 3 1\n1 5 1\n4 2 1",
                "7",
            ),
            problem(
                "[모의1-5] 그리디: 활동 선택",
                ["활동 수 n이 첫 줄에, 이후 시작·종료 시간이 n줄 입력됩니다. 최대한 많은 활동을 선택할 때 수를 출력하세요."],
                "종료 시간 기준 오름차순 정렬 후 겹치지 않는 것을 선택하세요.",
                "n=int(input())\nacts=[tuple(map(int,input().split())) for _ in range(n)]\nacts.sort(key=lambda x:x[1])\ncount=0; end=0\nfor s,e in acts:\n    if s>=end: count+=1; end=e\nprint(count)",
                "6\n1 3\n2 5\n4 7\n1 8\n5 9\n8 10",
                "3",
            ),
            problem(
                "[모의1-6] 트리 순회 (전위)",
                ["노드 수 n과 각 노드의 왼쪽·오른쪽 자식(없으면 -1)이 입력됩니다. 루트는 1번이며 전위 순회 결과를 출력하세요."],
                "preorder(node): print(node) → left → right 를 재귀로 구현하세요.",
                "import sys\nsys.setrecursionlimit(10000)\nn=int(input())\ntree={}\nfor _ in range(n):\n    parts=list(map(int,input().split()))\n    tree[parts[0]]=(parts[1],parts[2])\nresult=[]\ndef preorder(node):\n    if node==-1: return\n    result.append(node)\n    preorder(tree[node][0])\n    preorder(tree[node][1])\npreorder(1)\nprint(*result)",
                "5\n1 2 3\n2 4 5\n3 -1 -1\n4 -1 -1\n5 -1 -1",
                "1 2 4 5 3",
            ),
            problem(
                "[모의1-7] 투 포인터로 세 수의 합",
                ["정수 여러 개가 입력됩니다. 세 수의 합이 0인 경우의 수를 출력하세요. (중복 조합 제외)"],
                "정렬 후 첫 번째 수를 고정하고 나머지 두 수를 투 포인터로 찾으세요.",
                "nums=sorted(map(int,input().split()))\nn=len(nums); count=0\nfor i in range(n-2):\n    if i>0 and nums[i]==nums[i-1]: continue\n    l,r=i+1,n-1\n    while l<r:\n        s=nums[i]+nums[l]+nums[r]\n        if s==0:\n            count+=1\n            while l<r and nums[l]==nums[l+1]: l+=1\n            while l<r and nums[r]==nums[r-1]: r-=1\n            l+=1; r-=1\n        elif s<0: l+=1\n        else: r-=1\nprint(count)",
                "-1 0 1 2 -1 -4",
                "2",
            ),
            problem(
                "[모의1-8] BFS 최단 경로 복원",
                ["n m과 m개 간선(u v)이 입력됩니다. 1번에서 n번까지 최단 경로를 출력하세요. 없으면 NONE을 출력하세요."],
                "prev 배열로 이전 노드를 기록하고 역추적하세요.",
                "from collections import deque\nn,m=map(int,input().split())\ngraph=[[] for _ in range(n+1)]\nfor _ in range(m):\n    u,v=map(int,input().split())\n    graph[u].append(v); graph[v].append(u)\nprev=[-1]*(n+1); visited=[False]*(n+1)\nq=deque([1]); visited[1]=True\nwhile q:\n    node=q.popleft()\n    for nxt in graph[node]:\n        if not visited[nxt]:\n            visited[nxt]=True; prev[nxt]=node; q.append(nxt)\nif not visited[n]: print('NONE')\nelse:\n    path=[]\n    cur=n\n    while cur!=-1: path.append(cur); cur=prev[cur]\n    print(*path[::-1])",
                "5 5\n1 2\n1 3\n2 4\n3 4\n4 5",
                "1 2 4 5",
            ),
            problem(
                "[모의1-9] 구간 합 쿼리",
                ["정수 n과 q가 첫 줄에, 정수 n개가 둘째 줄에, 이후 q개의 쿼리(l r)가 입력됩니다. 각 쿼리에서 l~r 구간 합(1-indexed)을 출력하세요."],
                "prefix sum 배열로 O(1) 쿼리를 지원하세요.",
                "n,q=map(int,input().split())\nnums=list(map(int,input().split()))\nprefix=[0]*(n+1)\nfor i in range(n): prefix[i+1]=prefix[i]+nums[i]\nfor _ in range(q):\n    l,r=map(int,input().split())\n    print(prefix[r]-prefix[l-1])",
                "5 3\n1 2 3 4 5\n1 3\n2 4\n1 5",
                "6\n9\n15",
            ),
            problem(
                "[모의1-10] 클래스로 LRU 캐시",
                ["용량 c가 첫 줄에, get 키 또는 put 키 값 명령이 입력됩니다. END가 나오면 종료. get은 캐시에 있으면 값을, 없으면 -1을 출력하세요."],
                "OrderedDict 로 LRU를 구현하세요. get/put 시 해당 키를 가장 최근으로 이동하세요.",
                "from collections import OrderedDict\nclass LRUCache:\n    def __init__(self, capacity):\n        self.cap=capacity; self.cache=OrderedDict()\n    def get(self, key):\n        if key not in self.cache: return -1\n        self.cache.move_to_end(key); return self.cache[key]\n    def put(self, key, value):\n        if key in self.cache: self.cache.move_to_end(key)\n        self.cache[key]=value\n        if len(self.cache)>self.cap: self.cache.popitem(last=False)\n\nc=int(input()); lru=LRUCache(c)\nwhile True:\n    line=input().strip()\n    if line=='END': break\n    parts=line.split()\n    if parts[0]=='get': print(lru.get(int(parts[1])))\n    else: lru.put(int(parts[1]),int(parts[2]))",
                "2\nput 1 1\nput 2 2\nget 1\nput 3 3\nget 2\nget 3\nEND",
                "1\n-1\n3",
            ),
        ],
    })

    # ── 9장: 실전 모의고사 2 ─────────────────────────────────────────────────
    chapters.append({
        "title": "실전 모의고사 2 (1급 스타일)",
        "content": "COS Pro 1급 최종 실전 연습입니다. 90분 안에 10문제를 완성하세요.",
        "items": [
            problem(
                "[모의2-1] 트라이(Trie) 자료구조",
                ["단어 목록이 첫 줄에(공백 구분), 검색할 접두사가 둘째 줄에 입력됩니다. 해당 접두사로 시작하는 단어 수를 출력하세요."],
                "딕셔너리로 트라이를 구현하고 접두사를 따라가 카운트 합계를 구하세요.",
                "words=input().split()\nprefix=input().strip()\nprint(sum(1 for w in words if w.startswith(prefix)))",
                "apple application apply banana band\napp",
                "3",
            ),
            problem(
                "[모의2-2] 세그먼트 트리 범위 합",
                ["n q가 첫 줄에, 정수 n개가 둘째 줄에, 이후 쿼리(sum l r 또는 update i v)가 입력됩니다. sum 쿼리 결과를 출력하세요."],
                "prefix sum 배열로 O(1) sum, O(n) update 로 구현하세요.",
                "n,q=map(int,input().split())\nnums=list(map(int,input().split()))\nfor _ in range(q):\n    parts=input().split()\n    if parts[0]=='sum':\n        l,r=int(parts[1])-1,int(parts[2])-1\n        print(sum(nums[l:r+1]))\n    else:\n        i,v=int(parts[1])-1,int(parts[2])\n        nums[i]=v",
                "5 4\n1 2 3 4 5\nsum 1 3\nupdate 2 10\nsum 1 3\nsum 2 5",
                "6\n14\n22",
            ),
            problem(
                "[모의2-3] 그래프 최단 경로 복원",
                ["n m과 m개 간선(u v w)이 입력됩니다. 1번에서 n번까지 최단 경로와 비용을 출력하세요."],
                "다익스트라로 prev 배열을 채우고 역추적하세요.",
                "import heapq\nn,m=map(int,input().split())\ng=[[] for _ in range(n+1)]\nfor _ in range(m):\n    u,v,w=map(int,input().split())\n    g[u].append((v,w)); g[v].append((u,w))\ndist=[float('inf')]*(n+1); dist[1]=0; prev=[-1]*(n+1)\nhp=[(0,1)]\nwhile hp:\n    d,node=heapq.heappop(hp)\n    if d>dist[node]: continue\n    for nxt,w in g[node]:\n        nd=d+w\n        if nd<dist[nxt]: dist[nxt]=nd; prev[nxt]=node; heapq.heappush(hp,(nd,nxt))\npath=[]; cur=n\nwhile cur!=-1: path.append(cur); cur=prev[cur]\nprint(*path[::-1])\nprint(dist[n])",
                "4 5\n1 2 2\n1 3 5\n2 3 1\n2 4 4\n3 4 1",
                "1 2 3 4\n4",
            ),
            problem(
                "[모의2-4] DP: 배낭 경로 복원",
                ["물건 수 n과 용량 W가 첫 줄에, 이후 무게와 가치가 n줄 입력됩니다. 최대 가치와 선택한 물건 번호(1-indexed)를 출력하세요."],
                "dp 테이블을 채운 후 역추적으로 선택한 물건을 찾으세요.",
                "n,W=map(int,input().split())\nitems=[tuple(map(int,input().split())) for _ in range(n)]\ndp=[[0]*(W+1) for _ in range(n+1)]\nfor i,(wt,val) in enumerate(items,1):\n    for w in range(W+1):\n        dp[i][w]=dp[i-1][w]\n        if w>=wt: dp[i][w]=max(dp[i][w], dp[i-1][w-wt]+val)\nprint(dp[n][W])\nw=W; selected=[]\nfor i in range(n,0,-1):\n    if dp[i][w]!=dp[i-1][w]:\n        selected.append(i); w-=items[i-1][0]\nprint(*sorted(selected))",
                "4 7\n2 3\n3 4\n4 5\n5 6",
                "9\n2 3",
            ),
            problem(
                "[모의2-5] 문자열 복호화",
                ["k[encoded_string] 형식의 인코딩된 문자열이 입력됩니다. 디코딩해 출력하세요. (k: 반복 횟수, 중첩 가능)"],
                "스택으로 숫자와 문자열을 관리하며 ] 를 만나면 팝해 반복하세요.",
                "s=input().strip()\nstack=[]; cur=''; num=0\nfor ch in s:\n    if ch.isdigit(): num=num*10+int(ch)\n    elif ch=='[': stack.append((cur,num)); cur=''; num=0\n    elif ch==']':\n        prev,k=stack.pop(); cur=prev+cur*k\n    else: cur+=ch\nprint(cur)",
                "3[a2[bc]]",
                "abcbcabcbcabcbc",
            ),
            problem(
                "[모의2-6] 최소 힙으로 K 합계",
                ["정수 여러 개와 k가 한 줄씩 입력됩니다. 가장 작은 k개의 합을 출력하세요."],
                "heapq.nsmallest 를 사용하세요.",
                "import heapq\nnums=list(map(int,input().split()))\nk=int(input())\nprint(sum(heapq.nsmallest(k,nums)))",
                "5 3 8 1 9 2 7\n3",
                "6",
            ),
            problem(
                "[모의2-7] 연속 부분 배열 경우의 수",
                ["정수 여러 개와 목표합 target이 한 줄씩 입력됩니다. 연속 부분 배열의 합이 target 인 경우의 수를 출력하세요."],
                "prefix sum + 딕셔너리로 O(n) 에 해결하세요.",
                "from collections import defaultdict\nnums=list(map(int,input().split()))\ntarget=int(input())\ncount=defaultdict(int); count[0]=1\ncurrent=0; result=0\nfor n in nums:\n    current+=n\n    result+=count[current-target]\n    count[current]+=1\nprint(result)",
                "1 1 1\n2",
                "2",
            ),
            problem(
                "[모의2-8] 유니온-파인드: 친구 관계",
                ["n m이 첫 줄에, m개의 친구 관계(a b)가 입력됩니다. 이후 q개의 질문(a b: 같은 그룹?)이 입력됩니다. YES/NO로 출력하세요."],
                "유니온-파인드로 같은 집합인지 확인하세요.",
                "n,m=map(int,input().split())\nparent=list(range(n+1))\ndef find(x):\n    if parent[x]!=x: parent[x]=find(parent[x])\n    return parent[x]\ndef union(x,y): parent[find(x)]=find(y)\nfor _ in range(m):\n    a,b=map(int,input().split()); union(a,b)\nq=int(input())\nfor _ in range(q):\n    a,b=map(int,input().split())\n    print('YES' if find(a)==find(b) else 'NO')",
                "5 3\n1 2\n2 3\n4 5\n2\n1 3\n1 4",
                "YES\nNO",
            ),
            problem(
                "[모의2-9] 재고 관리 시뮬레이션",
                ["초기 재고(상품:수량, 콤마 구분)가 첫 줄에, 이후 sell 상품 수량 또는 restock 상품 수량 명령이 입력됩니다. END가 나오면 재고가 0인 상품 이름을 사전 순으로 출력하세요."],
                "딕셔너리로 재고를 관리하고 sell 시 부족하면 재고 부족을 출력하세요.",
                "stock={}\nfor item in input().split(','):\n    k,v=item.strip().split(':')\n    stock[k.strip()]=int(v.strip())\nwhile True:\n    line=input().strip()\n    if line=='END': break\n    parts=line.split()\n    cmd,name,qty=parts[0],parts[1],int(parts[2])\n    if cmd=='sell':\n        if stock.get(name,0)<qty: print('재고 부족')\n        else: stock[name]-=qty\n    else: stock[name]=stock.get(name,0)+qty\nfor name in sorted(stock):\n    if stock[name]==0: print(name)",
                "사과:5, 바나나:3, 포도:2\nsell 사과 5\nsell 바나나 1\nrestock 포도 0\nEND",
                "사과\n포도",
            ),
            problem(
                "[모의2-10] 종합: 학사 관리 시스템",
                ["학생 수 n이 첫 줄에, 이름과 과목:점수 목록이 n줄 입력됩니다. 이후 rank 과목 명령이 입력되면 해당 과목 점수 내림차순 순위를 출력하세요. END로 종료하세요."],
                "학생 딕셔너리에 과목별 점수를 저장하고 정렬해 출력하세요.",
                "n=int(input())\nstudents={}\nfor _ in range(n):\n    parts=input().split()\n    name=parts[0]\n    scores={}\n    for pair in parts[1:]:\n        subj,score=pair.split(':')\n        scores[subj]=int(score)\n    students[name]=scores\nwhile True:\n    line=input().strip()\n    if line=='END': break\n    _,subj=line.split()\n    ranking=[(name, students[name].get(subj,0)) for name in students]\n    ranking.sort(key=lambda x:(-x[1],x[0]))\n    for i,(name,score) in enumerate(ranking,1):\n        print(f'{i}. {name}: {score}')",
                "3\nAlice math:90 english:85\nBob math:75 english:92\nChris math:90 english:78\nrank math\nEND",
                "1. Alice: 90\n1. Chris: 90\n3. Bob: 75",
            ),
        ],
    })

    # ── 10장: 실전 모의고사 3 ────────────────────────────────────────────────
    chapters.append({
        "title": "실전 모의고사 3 (1급 종합)",
        "content": "자료구조·알고리즘·클래스를 종합한 최고 난이도 실전 문제입니다. 90분 안에 도전하세요.",
        "items": [
            problem(
                "[모의3-1] 최소 비용 신장 트리 (프림)",
                ["n m이 첫 줄에, m개의 간선(u v w)이 입력됩니다. 프림 알고리즘으로 MST 비용을 출력하세요."],
                "방문하지 않은 노드 중 최소 비용 간선을 선택하며 확장하세요.",
                "import heapq\nn,m=map(int,input().split())\ng=[[] for _ in range(n+1)]\nfor _ in range(m):\n    u,v,w=map(int,input().split())\n    g[u].append((w,v)); g[v].append((w,u))\nvisited=[False]*(n+1)\nhp=[(0,1)]; total=0\nwhile hp:\n    cost,node=heapq.heappop(hp)\n    if visited[node]: continue\n    visited[node]=True; total+=cost\n    for w,nxt in g[node]:\n        if not visited[nxt]: heapq.heappush(hp,(w,nxt))\nprint(total)",
                "4 5\n1 2 1\n1 3 4\n2 3 2\n2 4 5\n3 4 3",
                "6",
            ),
            problem(
                "[모의3-2] 최장 증가 부분수열 실제 출력",
                ["정수 여러 개가 입력됩니다. LIS를 구성하는 수열 중 하나를 출력하세요."],
                "dp와 prev 배열로 역추적하세요.",
                "nums=list(map(int,input().split()))\nn=len(nums)\ndp=[1]*n; prev=[-1]*n\nfor i in range(1,n):\n    for j in range(i):\n        if nums[j]<nums[i] and dp[j]+1>dp[i]:\n            dp[i]=dp[j]+1; prev[i]=j\nmax_len=max(dp); idx=dp.index(max_len)\npath=[]\nwhile idx!=-1: path.append(nums[idx]); idx=prev[idx]\nprint(*path[::-1])",
                "3 1 4 1 5 9 2 6",
                "1 4 5 9",
            ),
            problem(
                "[모의3-3] 구간 트리: 범위 최솟값",
                ["n q가 첫 줄에, n개의 정수가 둘째 줄에, 이후 min l r 쿼리가 입력됩니다. 각 구간 최솟값을 출력하세요."],
                "간단하게 슬라이싱 후 min 을 사용하세요.",
                "n,q=map(int,input().split())\nnums=list(map(int,input().split()))\nfor _ in range(q):\n    _,l,r=input().split()\n    print(min(nums[int(l)-1:int(r)]))",
                "6 3\n1 3 2 7 9 4\nmin 1 3\nmin 2 5\nmin 4 6",
                "1\n2\n4",
            ),
            problem(
                "[모의3-4] 완전탐색: 전력망 분할",
                ["n과 n-1개의 간선이 입력됩니다. 간선 하나를 끊었을 때 두 영역 크기 차이의 최솟값을 출력하세요."],
                "각 간선을 하나씩 제거하며 BFS로 크기를 재세요.",
                "from collections import deque\nn=int(input())\ngraph=[[] for _ in range(n+1)]\nfor _ in range(n-1):\n    u,v=map(int,input().split())\n    graph[u].append(v); graph[v].append(u)\ndef bfs(start, blocked_u, blocked_v):\n    visited={start}; q=deque([start])\n    while q:\n        node=q.popleft()\n        for nxt in graph[node]:\n            if nxt not in visited and not (node==blocked_u and nxt==blocked_v) and not (node==blocked_v and nxt==blocked_u):\n                visited.add(nxt); q.append(nxt)\n    return len(visited)\nresult=float('inf')\nfor u in range(1,n+1):\n    for v in graph[u]:\n        if u<v:\n            sz=bfs(u,u,v)\n            result=min(result, abs(sz-(n-sz)))\nprint(result)",
                "9\n1 3\n2 3\n3 4\n4 5\n4 6\n4 7\n7 8\n7 9",
                "3",
            ),
            problem(
                "[모의3-5] DP: 팰린드롬 분할 최솟값 경로",
                ["문자열이 입력됩니다. 팰린드롬으로 분할하는 최소 컷 수와 한 가지 분할 결과를 출력하세요."],
                "is_pal 테이블과 dp를 구한 후 역추적하세요.",
                "s=input().strip()\nn=len(s)\nis_pal=[[False]*n for _ in range(n)]\nfor i in range(n): is_pal[i][i]=True\nfor l in range(2,n+1):\n    for i in range(n-l+1):\n        j=i+l-1\n        if s[i]==s[j]: is_pal[i][j]=(l==2) or is_pal[i+1][j-1]\ndp=[float('inf')]*n; cut=[0]*n\nfor i in range(n):\n    if is_pal[0][i]: dp[i]=0; cut[i]=-1\n    else:\n        for j in range(1,i+1):\n            if is_pal[j][i] and dp[j-1]+1<dp[i]:\n                dp[i]=dp[j-1]+1; cut[i]=j\nparts=[]; end=n-1\nwhile end>=0:\n    if cut[end]==-1: parts.append(s[0:end+1]); break\n    parts.append(s[cut[end]:end+1]); end=cut[end]-1\nprint(dp[n-1])\nprint('|'.join(parts[::-1]))",
                "aab",
                "1\na|ab",
            ),
            problem(
                "[모의3-6] 클래스: 이벤트 스케줄러",
                ["이벤트 수 n이 첫 줄에, 이름 시작시간 종료시간이 n줄 입력됩니다. 겹치지 않게 최대 이벤트를 선택해 이름을 출력하세요."],
                "Event 클래스로 관리하고 종료시간 기준 정렬 후 그리디하게 선택하세요.",
                "class Event:\n    def __init__(self,name,start,end): self.name=name;self.start=start;self.end=end\n    def __lt__(self,other): return self.end<other.end\nn=int(input())\nevents=sorted([Event(*input().split()[:1]+list(map(int,input().split()[1:]))) for _ in range(n)])\nselected=[]; cur_end=0\nfor e in sorted(events):\n    if e.start>=cur_end: selected.append(e.name); cur_end=e.end\nfor name in selected: print(name)",
                "4\nA 1 3\nB 2 5\nC 4 7\nD 6 8",
                "A\nC\nD",
            ),
            problem(
                "[모의3-7] 두 큐의 합 균등화",
                ["두 줄에 각각 정수 여러 개가 입력됩니다. 두 큐의 합이 같아지도록 원소를 이동할 때 최소 이동 횟수를 출력하세요. 불가능하면 -1을 출력하세요."],
                "전체 합이 홀수면 -1. 한쪽에서 dequeue해 다른 쪽에 enqueue하며 목표합을 맞추세요.",
                "from collections import deque\na=list(map(int,input().split()))\nb=list(map(int,input().split()))\ntotal=sum(a)+sum(b)\nif total%2!=0: print(-1)\nelse:\n    target=total//2\n    qa=deque(a); qb=deque(b)\n    sa=sum(a); sb=sum(b); count=0\n    limit=(len(a)+len(b))*3\n    while sa!=sb and count<=limit:\n        if sa>target: v=qa.popleft(); sa-=v; qb.append(v); sb+=v\n        else: v=qb.popleft(); sb-=v; qa.append(v); sa+=v\n        count+=1\n    print(count if sa==sb else -1)",
                "3 2 7 2\n1 5 1 2 3 2",
                "2",
            ),
            problem(
                "[모의3-8] 재귀: 모든 부분집합 출력",
                ["정수 여러 개가 입력됩니다. 공집합을 포함한 모든 부분집합을 사전 순으로 출력하세요."],
                "재귀로 각 원소를 포함/제외하는 두 경우를 탐색하세요.",
                "nums=sorted(map(int,input().split()))\nresult=[]\ndef dfs(idx,path):\n    result.append(path[:])\n    for i in range(idx,len(nums)):\n        path.append(nums[i])\n        dfs(i+1,path)\n        path.pop()\ndfs(0,[])\nfor r in result: print(*r) if r else print('{}')",
                "1 2 3",
                "{}\n1\n1 2\n1 2 3\n1 3\n2\n2 3\n3",
            ),
            problem(
                "[모의3-9] 문자열 편집 거리 경로",
                ["두 문자열이 한 줄씩 입력됩니다. 최소 편집 거리를 출력하고 변환 과정을 출력하세요. (삽입 I, 삭제 D, 교체 R)"],
                "DP 테이블을 채운 후 역추적으로 연산 경로를 복원하세요.",
                "a=input().strip(); b=input().strip()\nm,n=len(a),len(b)\ndp=[[0]*(n+1) for _ in range(m+1)]\nfor i in range(m+1): dp[i][0]=i\nfor j in range(n+1): dp[0][j]=j\nfor i in range(1,m+1):\n    for j in range(1,n+1):\n        if a[i-1]==b[j-1]: dp[i][j]=dp[i-1][j-1]\n        else: dp[i][j]=1+min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1])\nprint(dp[m][n])\nops=[]; i,j=m,n\nwhile i>0 or j>0:\n    if i>0 and j>0 and a[i-1]==b[j-1]: i-=1;j-=1\n    elif i>0 and j>0 and dp[i][j]==dp[i-1][j-1]+1: ops.append(f'R:{a[i-1]}->{b[j-1]}');i-=1;j-=1\n    elif j>0 and dp[i][j]==dp[i][j-1]+1: ops.append(f'I:{b[j-1]}');j-=1\n    else: ops.append(f'D:{a[i-1]}');i-=1\nfor op in ops[::-1]: print(op)",
                "cat\ncut",
                "1\nR:a->u",
            ),
            problem(
                "[모의3-10] 종합: 소셜 네트워크 분석",
                ["n m이 첫 줄에, m개의 친구 관계(u v)가 입력됩니다. 이후 가장 많은 친구를 가진 사람과 수, 친구 수가 같으면 번호 작은 순으로 출력하세요. 그 다음 줄에 모든 사람과 연결된 사람(허브) 번호를 오름차순으로 출력하세요."],
                "인접 리스트로 각 노드의 차수를 세고 BFS로 연결성을 확인하세요.",
                "from collections import deque\nn,m=map(int,input().split())\ngraph=[[] for _ in range(n+1)]\nfor _ in range(m):\n    u,v=map(int,input().split())\n    graph[u].append(v); graph[v].append(u)\ndeg=[len(graph[i]) for i in range(n+1)]\nmax_deg=max(deg[1:])\nmost=[i for i in range(1,n+1) if deg[i]==max_deg]\nprint(*most, max_deg)\nhubs=[]\nfor node in range(1,n+1):\n    visited=set([node]); q=deque([node])\n    while q:\n        cur=q.popleft()\n        for nxt in graph[cur]:\n            if nxt not in visited: visited.add(nxt); q.append(nxt)\n    if len(visited)==n: hubs.append(node)\nprint(*hubs) if hubs else print('없음')",
                "5 5\n1 2\n1 3\n1 4\n1 5\n2 3",
                "1 4\n1 2 3 4 5",
            ),
        ],
    })

    total_items = sum(len(chapter["items"]) for chapter in chapters)
    if total_items != 100:
        raise ValueError(f"문항 수가 100개가 아닙니다: {total_items}")
    return chapters


class Command(BaseCommand):
    help = "YBM COS Pro 파이썬 1급 대비 과정(100문제)을 생성합니다."

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
                    "YBM IT COS Pro 파이썬 1급 자격증 취득을 위한 고급 연습 과정입니다. "
                    "재귀·분할정복, 정렬 알고리즘, 스택·큐, 동적 프로그래밍, 그래프, "
                    "클래스 심화, 문자열 알고리즘을 체계적으로 익히고 실전 모의고사 2세트로 시험을 대비합니다. "
                    "시험: 10문제 / 90분 / 1,000점 만점 / 600점 이상 합격"
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
            "YBM IT COS Pro 파이썬 1급 자격증 취득을 위한 고급 연습 과정입니다. "
            "재귀·분할정복, 정렬 알고리즘, 스택·큐, 동적 프로그래밍, 그래프, "
            "클래스 심화, 문자열 알고리즘을 체계적으로 익히고 실전 모의고사 2세트로 시험을 대비합니다. "
            "시험: 10문제 / 90분 / 1,000점 만점 / 600점 이상 합격"
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
                    key=f"cos1_{chapter_index:02d}_{item_index:02d}",
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
