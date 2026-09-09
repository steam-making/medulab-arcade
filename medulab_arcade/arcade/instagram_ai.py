"""인스타 AI 업로드용 Gemini 연동 헬퍼.
- 사진 분석(얼굴감지 + 내용 설명): google.generativeai (구 SDK, GenerativeModel)
- 이미지 스타일 변환 / 캡션 생성: google.genai (신 SDK, Client)
전부 GEMINI_API_KEY(+ _2~_20) 로테이션을 사용해 무료 할당량 안에서 처리한다.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

MODEL_NAMES_TEXT = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite']
MODEL_NAME_IMAGE = 'gemini-2.5-flash-image'


def _friendly_ai_error(raw: str) -> str:
    if "429" in raw or "RESOURCE_EXHAUSTED" in raw or "quota" in raw.lower():
        return "오늘의 무료 AI 사용량이 모두 소진되었습니다. 내일 다시 시도하거나 API 키를 추가해 주세요."
    if "401" in raw or "403" in raw or "invalid" in raw.lower() or "API_KEY" in raw.upper():
        return "AI API 키가 유효하지 않습니다. 서버 .env 설정을 확인해 주세요."
    if "500" in raw or "503" in raw or "unavailable" in raw.lower():
        return "AI 서버가 일시적으로 응답하지 않습니다. 잠시 후 다시 시도해 주세요."
    return raw[:120] if len(raw) > 120 else raw


def _get_gemini_api_keys():
    keys = []
    k = os.environ.get('GEMINI_API_KEY', '').strip()
    if k:
        keys.append(k)
    for i in range(2, 21):
        k = os.environ.get(f'GEMINI_API_KEY_{i}', '').strip()
        if k:
            keys.append(k)
    return keys


def has_gemini():
    return bool(_get_gemini_api_keys())


def analyze_photo(image_bytes: bytes, mime_type: str) -> dict:
    """사진 → {"has_face": bool, "description": str}. 실패 시 has_face=False, description=''"""
    try:
        import google.genai as genai
        from google.genai import types as gtypes
    except ImportError:
        return {'has_face': False, 'description': '', 'error': 'google-genai 패키지가 설치되지 않았습니다.'}

    api_keys = _get_gemini_api_keys()
    if not api_keys:
        return {'has_face': False, 'description': '', 'error': 'GEMINI_API_KEY가 설정되지 않았습니다.'}

    prompt = """이 사진을 분석해서 JSON으로만 답변하세요. 다른 텍스트는 절대 포함하지 마세요.

- has_face: 사람의 얼굴(실루엣이 아닌 인식 가능한 얼굴)이 사진에 나오면 true, 아니면 false
- description: 사진에 무엇이 나오는지 1~2문장으로 한국어 설명 (인스타그램 게시글 문구를 만들 때 참고할 용도)

응답 예시: {"has_face": true, "description": "학생들이 로봇 키트를 조립하며 웃고 있는 수업 장면"}"""

    last_error = None
    for api_key in api_keys:
        for model_name in MODEL_NAMES_TEXT:
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=[gtypes.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt],
                )
                raw = (response.text or '').strip()
                if raw.startswith('```'):
                    lines = [l for l in raw.split('\n') if not l.startswith('```')]
                    raw = '\n'.join(lines).strip()
                data = json.loads(raw)
                return {'has_face': bool(data.get('has_face')), 'description': data.get('description', '')}
            except Exception as e:
                last_error = str(e)
                err_str = str(e)
                if '429' in err_str or '404' in err_str or 'not found' in err_str.lower() or 'quota' in err_str.lower():
                    continue
                break

    logger.warning("사진 분석 실패: %s", last_error)
    return {'has_face': False, 'description': '', 'error': _friendly_ai_error(last_error or '알 수 없는 오류')}


def stylize_photo(image_bytes: bytes, mime_type: str, style: str = 'ghibli') -> bytes:
    """얼굴이 나온 사진 → 애니메이션/지브리풍 이미지로 변환. 실패 시 b'' 반환(호출측에서 원본 사용)"""
    try:
        import google.genai as genai
        from google.genai import types as gtypes
    except ImportError:
        logger.warning("google-genai 패키지가 설치되지 않았습니다.")
        return b''

    api_keys = _get_gemini_api_keys()
    if not api_keys:
        return b''

    style_prompts = {
        'ghibli': '이 사진을 스튜디오 지브리풍 애니메이션 일러스트로 변환해 주세요. 인물 수, 구도, 배경, 옷차림은 최대한 유지하되 '
                   '사실적인 얼굴 특징은 애니메이션 캐릭터처럼 부드럽게 각색해서 특정 인물을 알아볼 수 없게 해 주세요.',
        'anime': '이 사진을 일본 애니메이션 스타일 일러스트로 변환해 주세요. 인물 수, 구도, 배경은 유지하되 '
                  '얼굴은 애니메이션 캐릭터처럼 각색해서 실제 인물을 알아볼 수 없게 해 주세요.',
    }
    prompt = style_prompts.get(style, style_prompts['ghibli'])

    last_error = None
    for api_key in api_keys:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=MODEL_NAME_IMAGE,
                contents=[gtypes.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt],
            )
            for part in response.candidates[0].content.parts:
                if getattr(part, 'inline_data', None) and part.inline_data.data:
                    return part.inline_data.data
            last_error = '응답에 이미지 데이터가 없습니다.'
        except Exception as e:
            last_error = str(e)
            err_str = str(e)
            logger.warning("이미지 스타일 변환 실패: %s", e)
            if '429' in err_str or 'quota' in err_str.lower():
                continue
            break

    logger.warning("이미지 스타일 변환 최종 실패: %s", last_error)
    return b''


def generate_caption(descriptions: list, user_context: str) -> str:
    """사진 설명 목록 + 사용자 참고 내용 → 인스타그램 캡션(해시태그 포함)"""
    try:
        import google.genai as genai
    except ImportError:
        return ''

    api_keys = _get_gemini_api_keys()
    if not api_keys:
        return ''

    desc_text = '\n'.join(f'- {d}' for d in descriptions if d) or '(사진 설명 없음)'
    context_text = user_context.strip() or '(추가 참고 내용 없음)'

    prompt = f"""당신은 'AI로봇코딩 학원 메듀랩'의 SNS 담당자입니다. 아래 정보를 참고해서 인스타그램 게시글 문구를 작성해 주세요.

[사진/영상 내용]
{desc_text}

[담당자가 남긴 참고 내용]
{context_text}

━━━ 작성 지침 ━━━
1. 친근하고 밝은 톤의 한국어로 2~4문장 작성
2. 학원 홍보 느낌이 과하지 않게, 학생들의 즐거운 학습 순간을 자연스럽게 담기
3. 마지막 줄에 관련 해시태그 5~8개 추가 (예: #메듀랩 #AI로봇코딩 #코딩학원 등 사진 내용에 맞게)
4. 캡션 텍스트만 출력하고 다른 설명은 붙이지 마세요."""

    last_error = None
    for api_key in api_keys:
        for model_name in MODEL_NAMES_TEXT:
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(model=model_name, contents=prompt)
                text = (response.text or '').strip()
                if text:
                    return text
            except Exception as e:
                last_error = str(e)
                err_str = str(e)
                if '429' in err_str or 'quota' in err_str.lower():
                    continue
                break

    logger.warning("캡션 생성 실패: %s", last_error)
    return ''
