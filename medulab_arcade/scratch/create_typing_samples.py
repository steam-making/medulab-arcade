import os
import sys
import django

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
django.setup()

from typing_practice.models import TypingContent

def create_sample_data():
    samples = [
        # 단어연습 - 한글
        ('word', 'ko', '', '파이썬,자바스크립트,변수,리스트,함수,객체,클래스,인공지능,로봇,코딩,알고리즘,데이터,컴퓨터,소프트웨어,루프'),
        # 단어연습 - 영어
        ('word', 'en', '', 'python,javascript,variable,list,function,object,class,ai,robot,coding,algorithm,data,computer,software,loop'),
        
        # 짧은글 - 한글
        ('short', 'ko', '', '천재는 1%의 영감과 99%의 노력으로 만들어진다.\n시작이 반이다.\n끝날 때까지 끝난 게 아니다.\n아는 것이 힘이다.\n세 살 버릇 여든까지 간다.'),
        # 짧은글 - 영어
        ('short', 'en', '', 'Knowledge is power.\nWell begun is half done.\nBetter late than never.\nNo pain, no gain.\nPractice makes perfect.'),
        
        # 긴글 - 한글
        ('long', 'ko', '애국가', '동해 물과 백두산이 마르고 닳도록 하느님이 보우하사 우리나라 만세. 무궁화 삼천리 화려 강산 대한 사람 대한으로 길이 보전하세. 남산 위에 저 소나무 철갑을 두른 듯 바람 서리 불변함은 우리 기상일세.'),
        # 긴글 - 영어
        ('long', 'en', 'About Coding', 'Coding is the language of the future. It allows us to communicate with computers and create amazing things like games, websites, and artificial intelligence programs. Learning to code develops logical thinking and problem-solving skills.'),
    ]

    for c_type, lang, title, text in samples:
        TypingContent.objects.get_or_create(
            content_type=c_type,
            language=lang,
            title=title,
            defaults={'text': text}
        )
    print("Sample data created successfully!")

if __name__ == '__main__':
    create_sample_data()
