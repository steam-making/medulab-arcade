import re
import datetime
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from arcade.models import ScheduleEvent


class Command(BaseCommand):
    help = "AICE 공식 홈페이지로부터 자격시험 일정을 동기화하여 학원 일정에 등록합니다."

    def handle(self, *args, **options):
        self.stdout.write("AICE 시험 일정 동기화 작업을 시작합니다...")
        
        # 1. AICE 시험일정 페이지에서 JS chunk 주소 획득
        main_url = "https://aice.study/certi/examSchedule"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://aice.study/"
        }
        
        try:
            res_main = requests.get(main_url, headers=headers, timeout=10)
            if res_main.status_code != 200:
                self.stderr.write(f"메인 페이지 로드 실패 (HTTP {res_main.status_code})")
                return
        except Exception as e:
            self.stderr.write(f"네트워크 오류: {e}")
            return
            
        soup = BeautifulSoup(res_main.text, "html.parser")
        js_url = None
        for s in soup.find_all("script", src=True):
            src = s["src"]
            if "1878." in src:
                js_url = f"https://aice.study{src}" if not src.startswith("http") else src
                break
                
        if not js_url:
            js_url = "https://aice.study/js/1878.6f6116bd23a03337.js"
            self.stdout.write(f"기본 Fallback JS URL을 사용합니다: {js_url}")
            
        # 2. JS 컨텐츠 획득
        try:
            res_js = requests.get(js_url, headers=headers, timeout=10)
            if res_js.status_code != 200:
                self.stderr.write("JS 파일 로드 실패")
                return
        except Exception as e:
            self.stderr.write(f"네트워크 오류: {e}")
            return
            
        js_text = res_js.text
        
        # 3. 정규식을 통한 등급별 시험 일정 추출
        # Vue3 렌더링 코드 내 data-grade="등급" 및 td 텍스트들 파싱
        # 예: class:"schedule-row","data-grade":"future" ...
        raw_rows = re.findall(
            r'class:"schedule-row","data-grade":"([a-zA-Z0-9_-]+)"\},\[(.*?)(?:\]\)\)|\]\,-1\)\))',
            js_text
        )
        
        self.stdout.write(f"총 {len(raw_rows)}개의 일정을 발견했습니다. 파싱 및 DB 반영을 진행합니다.")
        
        current_year = datetime.datetime.now().year
        added_count = 0
        
        for grade, block in raw_rows:
            # td 내부의 텍스트 파싱
            tds = re.findall(r'"td",[^,]+,"([^"]+)"|"td",null,"([^"]+)"', block)
            td_texts = []
            for t1, t2 in tds:
                t = t1 or t2
                if t:
                    td_texts.append(t.strip())
            
            # 유효한 일정 데이터인지 판별 (회차, 날짜 정보 필요)
            # td_texts 예시: ['1회', '12.29(월) ~ 01.24(토)', '비대면', '01.31(토)', ...]
            # or ['2회', '03.30(월) ~ 04.17(금)', '04.25(토)', ...]
            if not td_texts or len(td_texts) < 2:
                continue
                
            # 회차 정보가 들어있는지 검사 (예: 1회, 2회 등)
            round_info = td_texts[0]
            if "회" not in round_info and "호" not in round_info and not re.search(r'\d+ȸ', round_info):
                # 간혹 첫 번째 요소가 회차가 아닌 경우 (Basic 등의 보충 일정 테이블 등)
                continue
            
            # 회차 텍스트 정상화 (예: 1ȸ -> 1회)
            round_clean = re.sub(r'(\d+)ȸ', r'\1회', round_info)
            
            # 접수 일정 및 시험 일정 파싱
            # 보통 td_texts[1]이 접수 일정("12.29(월) ~ 01.24(토)")이고, td_texts[3] 또는 td_texts[2]가 시험일
            # text 내에서 날짜 형식("MM.DD")을 추출
            date_patterns = re.findall(r'(\d{2})\.(\d{2})', "".join(td_texts))
            if len(date_patterns) < 2:
                continue
                
            # date_patterns: [ (start_month, start_day), (end_month, end_day), (exam_month, exam_day) ]
            try:
                # 1) 시험일 파싱 (보통 3번째 매칭되는 날짜가 시험일이나, 전체 리스트의 마지막 부근)
                exam_m, exam_d = date_patterns[-2] if len(date_patterns) > 2 else date_patterns[-1]
                exam_month = int(exam_m)
                exam_day = int(exam_d)
                exam_date = datetime.date(current_year, exam_month, exam_day)
                
                # 2) 접수 기간 파싱
                start_m, start_d = date_patterns[0]
                end_m, end_d = date_patterns[1]
                
                start_month, start_day = int(start_m), int(start_d)
                end_month, end_day = int(end_m), int(end_d)
                
                # 연도 보정 (접수 기간이 전년도 11, 12월에 걸쳐있는 경우)
                start_year = current_year
                if start_month > exam_month:
                    start_year = current_year - 1
                    
                end_year = current_year
                if end_month > exam_month:
                    end_year = current_year - 1
                    
                start_date = datetime.datetime(start_year, start_month, start_day, 9, 0)
                end_date = datetime.datetime(end_year, end_month, end_day, 18, 0)
                
                # 타임존 적용
                exam_datetime = timezone.make_aware(datetime.datetime(current_year, exam_month, exam_day, 10, 0))
                start_date_tz = timezone.make_aware(start_date)
                end_date_tz = timezone.make_aware(end_date)
                
                # 등급 한글화
                grade_map = {
                    "future": "Future",
                    "junior": "Junior",
                    "basic": "Basic",
                    "associate": "Associate",
                    "professional": "Professional"
                }
                grade_kor = grade_map.get(grade.lower(), grade)
                
                event_title = f"AICE 자격시험 [{grade_kor} {round_clean}]"
                event_desc = (
                    f"KT 주관 인공지능 능력시험 AICE ({grade_kor} 등급) {round_clean} 일정 안내입니다.\n\n"
                    f"- 접수 기간: {start_month:02d}월 {start_day:02d}일 ~ {end_month:02d}월 {end_day:02d}일\n"
                    f"- 시험 일시: {exam_month:02d}월 {exam_day:02d}일\n"
                    f"- 시험 형태: 온라인 비대면 시험"
                )
                
                # 중복 등록 방지
                exists = ScheduleEvent.objects.filter(
                    title=event_title,
                    start_date=exam_datetime
                ).exists()
                
                if not exists:
                    ScheduleEvent.objects.create(
                        title=event_title,
                        description=event_desc,
                        start_date=exam_datetime,
                        end_date=exam_datetime + datetime.timedelta(hours=2),
                        event_type=ScheduleEvent.EVENT_TYPE_CERTIFICATION,
                        external_url="https://aice.study/certi/examSchedule",
                        is_active=True
                    )
                    added_count += 1
                    self.stdout.write(self.style.SUCCESS(f"등록 완료: {event_title} ({exam_date})"))
                    
            except Exception as ex:
                self.stderr.write(f"날짜 파싱 실패 (등급: {grade}, 내용: {td_texts}): {ex}")
                continue
                
        self.stdout.write(self.style.SUCCESS(f"AICE 시험 일정 동기화가 끝났습니다. 새로 등록된 일정: {added_count}개"))
