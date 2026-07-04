import requests
import datetime
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from arcade.models import Contest

class Command(BaseCommand):
    help = '씽굿(Think Contest) 사이트에서 IT/SW 및 게임/소프트웨어 분야 공모전 데이터를 크롤링하여 DB에 적재합니다.'

    def handle(self, *args, **options):
        self.stdout.write("씽굿 공모전 수집을 시작합니다...")
        added_count = self.crawl_and_save()
        self.stdout.write(self.style.SUCCESS(f"수집 완료: 총 {added_count}개의 신규 공모전이 추가/업데이트되었습니다."))

    def crawl_and_save(self):
        url = "https://www.thinkcontest.com/thinkgood/user/contest/subList.do"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
            "Referer": "https://www.thinkcontest.com/thinkgood/user/contest/index.do",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }
        
        added_count = 0
        
        # 관심 카테고리/검색 키워드 (일반 수집용)
        interest_keywords = [
            '코딩', '알고리즘', '소프트웨어', 'sw', '프로그래밍', '해커톤', 
            '인공지능', 'ai', '로봇', '게임', '앱', '모바일', '메이커', 
            '과학', '경진대회', '올림피아드', '발명', '메카트로닉스'
        ]
        allowed_targets = ['초등', '중등', '고등', '청소년', '어린이', '학생', '제한 없음', '제한없음']

        # ----------------------------------------------------
        # 파이프라인 A: 최근 50개 전체 목록 수집 (키워드 및 대상 필터링)
        # ----------------------------------------------------
        payload_recent = {
            "searchStatus": "Y",
            "recordsPerPage": 50,
            "currentPageNo": 1,
            "sidx": "putup_sdt",
            "sord": "DESC",
            "pagesite": "contest"
        }
        
        try:
            self.stdout.write("[CRAWL] Fetching recent 50 contests from ThinkContest API...")
            response = requests.post(url, headers=headers, json=payload_recent, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in (1, '1'):
                    list_data = data.get("listJsonData", [])
                    self.stdout.write(f"[CRAWL] Retrieved {len(list_data)} recent items.")
                    
                    for item in list_data:
                        title = item.get("program_nm", "").strip()
                        organizer = item.get("host_company", "").strip()
                        field_nm = item.get("contest_field_nm", "").strip()
                        qualified_nm = item.get("enter_qualified_nm", "").strip()
                        contest_id = item.get("id")
                        
                        if not title or not contest_id:
                            continue
                        
                        # 1. 분야 필터링
                        title_lower = title.lower()
                        field_lower = field_nm.lower()
                        is_target_field = any(kw in title_lower or kw in field_lower for kw in interest_keywords)
                        if not is_target_field:
                            continue
                            
                        # 2. 참가 대상 필터링
                        is_allowed_target = any(t in qualified_nm for t in allowed_targets)
                        if not is_allowed_target:
                            continue
                        
                        # 중복 검사
                        if Contest.objects.filter(title=title, organizer=organizer).exists():
                            continue

                        # 적재 처리
                        success = self.save_contest_item(item, headers)
                        if success:
                            added_count += 1
                            self.stdout.write(f"  -> [A-ADDED] {title} ({organizer})")
        except Exception as e:
            self.stderr.write(f"파이프라인 A 실행 에러: {e}")

        # ----------------------------------------------------
        # 파이프라인 B: 게임/소프트웨어 (CCFD002) 접수중/접수예정 공모전 전체 수집
        # ----------------------------------------------------
        payload_game = {
            "searchStatus": "Y",
            "recordsPerPage": 100,
            "currentPageNo": 1,
            "sidx": "putup_sdt",
            "sord": "DESC",
            "pagesite": "contest",
            "contest_field": "CCFD002"
        }
        
        try:
            self.stdout.write("[CRAWL] Fetching Game/Software field (CCFD002) contests...")
            response = requests.post(url, headers=headers, json=payload_game, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in (1, '1'):
                    list_data = data.get("listJsonData", [])
                    self.stdout.write(f"[CRAWL] Retrieved {len(list_data)} Game/Software items.")
                    
                    for item in list_data:
                        title = item.get("program_nm", "").strip()
                        organizer = item.get("host_company", "").strip()
                        contest_id = item.get("id")
                        process_status = item.get("process", "")  # 'ING' (접수중), 'YET' (접수예정), 'INGEND' (마감임박), 'END' (마감)
                        
                        if not title or not contest_id:
                            continue
                        
                        # 접수 마감된 것은 제외
                        if process_status == 'END':
                            continue
                        
                        # 중복 검사
                        if Contest.objects.filter(title=title, organizer=organizer).exists():
                            continue

                        # 키워드/대상 필터링 없이 접수중/접수예정이면 무조건 수집
                        success = self.save_contest_item(item, headers)
                        if success:
                            added_count += 1
                            self.stdout.write(f"  -> [B-ADDED] {title} ({organizer}) [Process: {process_status}]")
        except Exception as e:
            self.stderr.write(f"파이프라인 B 실행 에러: {e}")

        return added_count

    def save_contest_item(self, item, headers):
        """씽굿 아이템 상세 요강을 크롤링하여 DB에 최종 적재합니다."""
        title = item.get("program_nm", "").strip()
        organizer = item.get("host_company", "").strip()
        field_nm = item.get("contest_field_nm", "").strip()
        qualified_nm = item.get("enter_qualified_nm", "").strip()
        contest_id = item.get("id")
        
        # 1. 상세 정보 크롤링 (요강 상세 설명)
        detail_url = f"https://www.thinkcontest.com/thinkgood/user/contest/view.do?contest_pk={contest_id}"
        description = ""
        try:
            detail_res = requests.get(detail_url, headers=headers, timeout=10)
            if detail_res.status_code == 200:
                soup = BeautifulSoup(detail_res.text, 'html.parser')
                content_div = soup.select_one('#contest_content')
                if content_div:
                    description = content_div.get_text('\n', strip=True)
        except Exception as detail_err:
            self.stdout.write(f"상세 정보 파싱 에러 ({title}): {detail_err}")
        
        if not description:
            description = item.get("text", "") # 기본 텍스트
        
        # 2. 접수 기간 파싱
        start_date = None
        end_date = None
        receive_period = item.get("receive_period", "")
        
        date_parts = [p.strip() for p in receive_period.split('~')]
        if len(date_parts) == 2:
            try:
                s_str = date_parts[0].split()[0]
                start_date = datetime.datetime.strptime(s_str, "%Y-%m-%d").date()
            except ValueError:
                pass
            
            try:
                e_str = date_parts[1].split()[0]
                end_date = datetime.datetime.strptime(e_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        # 3. 대표 이미지/포스터 획득 및 미디어 파일 적재
        image_file = None
        poster_path = item.get("poster_path")
        poster_name = item.get("poster_name")
        if poster_path and poster_name:
            thumbnail_url = f"https://www.thinkcontest.com/thinkgood/common/display.do?filepath={poster_path}&filename={poster_name}"
            try:
                img_res = requests.get(thumbnail_url, headers=headers, timeout=10)
                if img_res.status_code == 200:
                    image_file = ContentFile(img_res.content, name=poster_name)
            except Exception as img_err:
                self.stdout.write(f"이미지 다운로드 에러 ({title}): {img_err}")

        # 4. 카테고리 태그 정리
        interest_keywords = [
            '코딩', '알고리즘', '소프트웨어', 'sw', '프로그래밍', '해커톤', 
            '인공지능', 'ai', '로봇', '게임', '앱', '모바일', '메이커', 
            '과학', '경진대회', '올림피아드', '발명', '메카트로닉스'
        ]
        title_lower = title.lower()
        field_lower = field_nm.lower()
        
        category_tags = []
        for kw in interest_keywords:
            if kw in title_lower or kw in field_lower:
                category_tags.append(kw.upper())
        category_str = ", ".join(list(set(category_tags)))
        
        # 5. DB 저장
        try:
            contest = Contest(
                title=title,
                organizer=organizer,
                category=category_str or field_nm,
                target_audience=qualified_nm,
                start_date=start_date,
                end_date=end_date,
                link=detail_url,
                description=description,
                is_active=True
            )
            if image_file:
                contest.thumbnail.save(poster_name, image_file, save=False)
            
            contest.save()
            return True
        except Exception as save_err:
            self.stdout.write(f"DB 저장 에러 ({title}): {save_err}")
            return False
