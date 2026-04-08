# 🚀 메듀랩 Student Arcade - Vultr 배포 가이드

## 📁 프로젝트 구조

```
medulab_arcade/
├── manage.py                    # Django 관리 명령어
├── requirements.txt             # 패키지 목록
├── medulab_arcade/              # 프로젝트 설정
│   ├── settings.py              # ⚙️ 설정 (DB, 시크릿키 등)
│   ├── urls.py
│   └── wsgi.py
├── arcade/                      # 메인 앱
│   ├── models.py                # 📊 DB 모델 (Project, Like, Bookmark)
│   ├── views.py                 # 🖥️ 뷰 로직
│   ├── forms.py                 # 📝 업로드/회원가입 폼
│   ├── urls.py                  # 🔗 URL 라우팅
│   ├── admin.py                 # 👨‍🏫 관리자 페이지 설정
│   └── fixtures/
│       └── initial_categories.json  # 기본 카테고리 데이터
├── templates/                   # 🎨 HTML 템플릿
│   ├── arcade/
│   │   ├── base.html            # 기본 레이아웃
│   │   ├── home.html            # 메인 페이지
│   │   ├── play.html            # 게임 플레이 페이지
│   │   ├── upload.html          # 업로드 페이지
│   │   ├── my_projects.html     # 내 작품 페이지
│   │   └── signup.html          # 회원가입
│   └── registration/
│       └── login.html           # 로그인
├── media/                       # 업로드된 파일 저장소
│   ├── projects/                # 학생 작품 (ZIP 해제)
│   ├── thumbnails/              # 썸네일 이미지
│   └── uploads/                 # 원본 ZIP 파일
└── deploy/                      # 배포 설정
    ├── nginx.conf               # Nginx 설정
    └── medulab.service          # Gunicorn 서비스
```

---

## 1️⃣ Vultr 서버 초기 세팅

```bash
# 서버 접속
ssh root@YOUR_SERVER_IP

# 시스템 업데이트
apt update && apt upgrade -y

# 필수 패키지 설치
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib

# 배포용 계정 생성
adduser deploy
usermod -aG sudo deploy
su - deploy
```

---

## 2️⃣ PostgreSQL 설정

```bash
# postgres 계정으로 전환
sudo -u postgres psql

# DB 및 유저 생성
CREATE DATABASE medulab_arcade;
CREATE USER medulab_user WITH PASSWORD '여기에_강력한_비밀번호';
ALTER ROLE medulab_user SET client_encoding TO 'utf8';
ALTER ROLE medulab_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE medulab_user SET timezone TO 'Asia/Seoul';
GRANT ALL PRIVILEGES ON DATABASE medulab_arcade TO medulab_user;
\q
```

---

## 3️⃣ 프로젝트 배포

```bash
# deploy 계정으로
su - deploy

# 프로젝트 폴더에 파일 업로드 (SCP, Git 등)
cd /home/deploy/medulab_arcade

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

---

## 4️⃣ settings.py 수정 (배포용)

`medulab_arcade/settings.py`에서 아래 항목들을 수정:

```python
# 시크릿키 변경 (터미널에서 생성)
# python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = '생성된_시크릿키'

# 디버그 끄기
DEBUG = False

# 도메인 설정
ALLOWED_HOSTS = ['your-domain.com', 'YOUR_SERVER_IP']

# PostgreSQL 연결
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'medulab_arcade',
        'USER': 'medulab_user',
        'PASSWORD': '여기에_강력한_비밀번호',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 5️⃣ Django 초기화

```bash
source venv/bin/activate

# DB 마이그레이션
python manage.py makemigrations arcade
python manage.py migrate

# 기본 카테고리 데이터 로드
python manage.py loaddata initial_categories

# 정적 파일 수집
python manage.py collectstatic --noinput

# 관리자(선생님) 계정 생성
python manage.py createsuperuser
# → 아이디, 이메일, 비밀번호 입력
```

---

## 6️⃣ Nginx + Gunicorn 설정

```bash
# Nginx 설정 복사
sudo cp deploy/nginx.conf /etc/nginx/sites-available/medulab_arcade
sudo ln -s /etc/nginx/sites-available/medulab_arcade /etc/nginx/sites-enabled/

# ⚠️ nginx.conf에서 도메인명 수정!
sudo nano /etc/nginx/sites-available/medulab_arcade

# default 사이트 비활성화
sudo rm /etc/nginx/sites-enabled/default

# 설정 테스트 및 재시작
sudo nginx -t
sudo systemctl restart nginx

# Gunicorn 서비스 등록
sudo cp deploy/medulab.service /etc/systemd/system/medulab.service
sudo systemctl daemon-reload
sudo systemctl enable medulab
sudo systemctl start medulab
```

---

## 7️⃣ 동작 확인

```bash
# Gunicorn 상태 확인
sudo systemctl status medulab

# 로그 확인
sudo journalctl -u medulab -f

# 브라우저에서 접속
# http://YOUR_SERVER_IP 또는 http://your-domain.com
```

---

## 🔧 주요 기능 사용법

### 관리자(선생님) 페이지
- `http://도메인/admin/` 접속
- 학생 작품 **승인/반려** 가능
- 카테고리 관리, 추천 작품 설정
- 일괄 승인 액션 지원

### 학생 작품 업로드 방법
1. 회원가입 → 로그인
2. **📤 업로드** 클릭
3. 작품 파일을 **ZIP으로 압축** (index.html이 메인 파일)
4. 제목, 설명, 카테고리 등 입력 후 제출
5. 선생님이 `/admin/`에서 **승인** 하면 공개

### ZIP 파일 구조 예시
```
my_game.zip
├── index.html      ← 시작 파일
├── style.css
├── script.js
└── images/
    ├── player.png
    └── bg.jpg
```

---

## 🔒 보안 체크리스트

- [ ] `SECRET_KEY` 변경
- [ ] `DEBUG = False` 설정
- [ ] `ALLOWED_HOSTS` 도메인만 허용
- [ ] PostgreSQL 비밀번호 강력하게 설정
- [ ] HTTPS 적용 (Let's Encrypt)

### HTTPS 적용 (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## ❓ 문제 해결

| 문제 | 해결 |
|------|------|
| 502 Bad Gateway | `sudo systemctl restart medulab` |
| 정적 파일 안 보임 | `python manage.py collectstatic` |
| 업로드 실패 | media 폴더 권한 확인: `chmod -R 775 media/` |
| ZIP 압축 해제 안 됨 | `project_path` 필드 확인, 로그 확인 |
| iframe 안 뜸 | Nginx 설정에서 X-Frame-Options 확인 |
