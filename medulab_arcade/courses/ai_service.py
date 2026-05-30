"""
올림피아드 하위문제 AI 평가 서비스
- 손글씨 사진 → OCR (Gemini Vision, 무료)
- 답안 텍스트 → 평가점수 + 보완점 피드백 (Gemini 1.5 Flash, 무료)
"""
import base64
import json
import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)


def _friendly_ai_error(raw: str) -> str:
    """기술적 AI 에러 문자열을 사람이 읽기 쉬운 메시지로 변환"""
    if "429" in raw or "RESOURCE_EXHAUSTED" in raw or "quota" in raw.lower():
        return "오늘의 무료 AI 사용량이 모두 소진되었습니다. 내일 다시 시도하거나 API 키를 추가해 주세요."
    if "401" in raw or "403" in raw or "invalid" in raw.lower() or "API_KEY" in raw.upper():
        return "AI API 키가 유효하지 않습니다. 서버 .env 설정을 확인해 주세요."
    if "500" in raw or "503" in raw or "unavailable" in raw.lower():
        return "AI 서버가 일시적으로 응답하지 않습니다. 잠시 후 다시 시도해 주세요."
    # 너무 긴 에러는 앞 80자만
    return raw[:80] if len(raw) > 80 else raw


def _get_gemini_api_keys() -> list[str]:
    """GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3 ... 순으로 수집"""
    keys = []
    # 기본 키
    k = getattr(settings, 'GEMINI_API_KEY', '').strip()
    if k:
        keys.append(k)
    # 번호 붙은 추가 키 (2~20)
    for i in range(2, 21):
        k = getattr(settings, f'GEMINI_API_KEY_{i}', '').strip()
        if k:
            keys.append(k)
    return keys


def _get_gemini_clients():
    """등록된 모든 Gemini API 키에 대한 클라이언트 리스트 반환"""
    import google.genai as genai
    keys = _get_gemini_api_keys()
    if not keys:
        raise ValueError("GEMINI_API_KEY가 .env에 설정되지 않았습니다.")
    return [genai.Client(api_key=k) for k in keys]


def _get_gemini_client():
    """단일 클라이언트 반환 (하위 호환)"""
    clients = _get_gemini_clients()
    return clients[0]


def _get_anthropic_client():
    import anthropic
    import httpx
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY가 .env에 설정되지 않았습니다.")
    # httpx 클라이언트에 UTF-8 강제 지정 (서버 locale이 ASCII인 경우 대비)
    http_client = httpx.Client(
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=60.0,
    )
    return anthropic.Anthropic(api_key=api_key, http_client=http_client)


def _has_gemini():
    return bool(_get_gemini_api_keys())


def _has_anthropic():
    return bool(getattr(settings, 'ANTHROPIC_API_KEY', ''))


def has_any_ai():
    return _has_gemini() or _has_anthropic()


def _read_image_bytes(image_field) -> tuple[bytes, str]:
    """ImageField → (bytes, mime_type). 실패 시 (b'', '')"""
    if not image_field:
        return b'', ''
    name = getattr(image_field, 'name', '') or ''
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else 'jpeg'
    mime_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
                'gif': 'image/gif', 'webp': 'image/webp'}
    mime_type = mime_map.get(ext, 'image/jpeg')
    # Django default_storage로 읽기 (가장 안전)
    try:
        from django.core.files.storage import default_storage
        with default_storage.open(name, 'rb') as f:
            return f.read(), mime_type
    except Exception as e:
        logger.warning("default_storage.open 실패 (%s): %s", name, e)
    # 폴백: ImageField 직접 읽기
    try:
        image_field.open('rb')
        data = image_field.read()
        image_field.close()
        return data, mime_type
    except Exception as e:
        logger.warning("ImageField 직접 읽기 실패: %s", e)
    return b'', ''


def ocr_from_image(image_field) -> str:
    """손글씨 이미지 → OCR 텍스트 (Gemini Vision 우선, Anthropic 차선)"""
    if not image_field:
        return ""

    image_bytes, mime_type = _read_image_bytes(image_field)
    if not image_bytes:
        logger.warning("OCR: 이미지 바이트 읽기 실패 — name=%s", getattr(image_field, 'name', '?'))
        return ""

    ocr_prompt = (
        "이 이미지는 학생이 손으로 작성한 올림피아드 답안지입니다.\n"
        "이미지에 적힌 모든 한국어 텍스트를 최대한 정확하게 인식하여 그대로 출력해 주세요.\n"
        "표, 그림 설명, 번호 목록이 있으면 구조를 유지하며 텍스트로 변환하세요.\n"
        "인식된 텍스트만 출력하고 다른 설명은 붙이지 마세요."
    )

    # Gemini 우선 — 키별 × 모델별 순환 (429면 다음 키로)
    if _has_gemini():
        from google.genai import types as gtypes
        clients = _get_gemini_clients()
        for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]:
            for idx, client in enumerate(clients):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[
                            gtypes.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                            ocr_prompt,
                        ],
                    )
                    return response.text.strip()
                except Exception as e:
                    err_str = str(e)
                    logger.warning("Gemini OCR(%s) 키%d 실패: %s", model_name, idx + 1, e)
                    is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                    if not is_quota:
                        break  # 할당량 외 오류 → 다음 키로 재시도 불필요

    # Anthropic 차선
    if _has_anthropic():
        try:
            image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
            client = _get_anthropic_client()
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": image_b64}},
                    {"type": "text", "text": ocr_prompt},
                ]}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error("Anthropic OCR 실패: %s", e)

    return ""


_THINKING_TYPE_GUIDES = {
    "정보이해사고력": {
        "설명": "주어진 정보를 정확히 읽고 핵심을 파악하며 의미를 올바르게 해석하는 능력",
        "채점기준": [
            ("정보 파악", 30, "문제에서 주어진 데이터·조건·규칙을 빠짐없이 이해했는가"),
            ("해석 정확성", 40, "정보를 왜곡 없이 올바르게 해석했는가"),
            ("표현 명확성", 30, "이해한 내용을 명확하고 논리적으로 서술했는가"),
        ],
    },
    "창의적문제해결사고력": {
        "설명": "기존 방법에 얽매이지 않고 새로운 아이디어나 방법으로 문제를 해결하는 능력",
        "채점기준": [
            ("독창성", 35, "일반적이지 않은 참신한 아이디어나 접근법을 제시했는가"),
            ("실현 가능성", 35, "제시한 아이디어가 실제로 작동하거나 구현 가능한가"),
            ("완성도", 30, "아이디어를 충분히 발전시켜 구체적으로 서술했는가"),
        ],
    },
    "지식기반사고력": {
        "설명": "컴퓨터 과학·알고리즘·수학 등 관련 지식을 정확히 활용하여 문제를 푸는 능력",
        "채점기준": [
            ("지식 정확성", 40, "사용한 개념·알고리즘·공식이 정확한가"),
            ("적용 적절성", 35, "문제 상황에 맞는 지식을 선택하여 적용했는가"),
            ("논리 전개", 25, "풀이 과정이 단계별로 논리적으로 전개됐는가"),
        ],
    },
    "통합맥락적사고력": {
        "설명": "여러 개념이나 분야를 연결하여 큰 그림 속에서 문제를 이해하고 해결하는 능력",
        "채점기준": [
            ("연결성", 35, "서로 다른 개념·상황·분야를 의미 있게 연결했는가"),
            ("맥락 이해", 35, "문제의 배경·맥락을 파악하고 답안에 반영했는가"),
            ("종합적 서술", 30, "부분이 아닌 전체를 아우르는 답안을 작성했는가"),
        ],
    },
    "협동적사고력": {
        "설명": "협력 상황을 이해하고 역할 분담·소통·조율 방법을 논리적으로 제시하는 능력",
        "채점기준": [
            ("협력 구조 이해", 35, "협력이 필요한 이유와 방식을 올바르게 이해했는가"),
            ("역할 제안", 35, "구체적이고 공정한 역할 분담이나 협력 방법을 제시했는가"),
            ("현실성", 30, "제시한 협력 방안이 실제 상황에서 실행 가능한가"),
        ],
    },
    "윤리적사고력": {
        "설명": "AI·기술·사회 이슈에 대해 다양한 관점을 고려하고 윤리적 판단을 내리는 능력",
        "채점기준": [
            ("다각도 고려", 35, "찬반·장단점·이해관계자 등 여러 관점을 균형 있게 검토했는가"),
            ("윤리적 근거", 40, "판단의 근거가 윤리적 원칙에 부합하고 논리적인가"),
            ("결론 명확성", 25, "자신의 입장을 분명하게 제시했는가"),
        ],
    },
    "표현력": {
        "설명": "생각이나 답안을 글·그림·순서도 등으로 명확하고 효과적으로 전달하는 능력",
        "채점기준": [
            ("명확성", 40, "읽는 사람이 쉽게 이해할 수 있도록 표현했는가"),
            ("구조성", 35, "서론·본론·결론 또는 단계별 구성이 체계적인가"),
            ("풍부함", 25, "예시·비유·그림 묘사 등으로 내용을 풍부하게 전달했는가"),
        ],
    },
}

_GRADE_GUIDE = {
    "초등3~4": "초등학교 3~4학년 수준으로 평가합니다. 완벽한 문장보다 핵심 아이디어 파악 여부를 중시하고, 맞춤법 오류는 감점하지 않습니다.",
    "초등5~6": "초등학교 5~6학년 수준으로 평가합니다. 논리적 흐름과 근거 제시를 중시하되, 전문 용어 미사용은 감점하지 않습니다.",
    "중학": "중학교 1~3학년 수준으로 평가합니다. 개념의 정확한 사용, 논리적 전개, 근거의 타당성을 중점적으로 봅니다.",
}


def _get_grade_hint(sub_question) -> str:
    """하위문제가 속한 프로그램 이름에서 학년 힌트 추출"""
    try:
        name = sub_question.item.chapter.program.name
        if "3~4" in name or "3·4" in name:
            return _GRADE_GUIDE["초등3~4"]
        if "5~6" in name or "5·6" in name:
            return _GRADE_GUIDE["초등5~6"]
        if "중" in name or "중학" in name:
            return _GRADE_GUIDE["중학"]
    except Exception:
        pass
    return ""


def evaluate_sub_answer(sub_question, answer_text: str, ocr_text: str = "") -> dict:
    """답안 → AI 평가점수 + 피드백 (Gemini 우선, Anthropic 차선)"""
    combined = answer_text.strip() or ocr_text.strip()
    if not combined:
        return {"score": 0, "feedback": json.dumps({"score": 0, "strengths": [], "improvements": ["답안이 없습니다."], "summary": "답안 미제출"}, ensure_ascii=False)}

    thinking_type = getattr(sub_question, 'thinking_type', '') or ''
    example = (sub_question.example_answer or '').strip()
    grade_hint = _get_grade_hint(sub_question)
    tg = _THINKING_TYPE_GUIDES.get(thinking_type)

    # 채점 기준 텍스트 생성
    if tg:
        criteria_lines = "\n".join(
            f"  - {name}({weight}점): {desc}"
            for name, weight, desc in tg["채점기준"]
        )
        thinking_section = f"""[사고력 유형: {thinking_type}]
{tg['설명']}

[항목별 채점 기준 - 합계 100점]
{criteria_lines}"""
    else:
        thinking_section = "[사고력 유형]\n미지정 — 논리성(40점), 완성도(35점), 표현력(25점)으로 평가하세요."

    example_section = f"[예시 답안]\n{example}" if example else "[예시 답안]\n없음 — 문제의 의도에 맞게 자체적으로 채점하세요."
    grade_section = f"\n[학년 수준 안내]\n{grade_hint}" if grade_hint else ""

    prompt = f"""당신은 AI SW 사고력 올림피아드 전문 채점관입니다.
아래 정보를 바탕으로 학생 답안을 꼼꼼하고 공정하게 평가해 주세요.

[문제]
{sub_question.question_text}

{thinking_section}

{example_section}{grade_section}

[학생 답안]
{combined}

━━━ 평가 지침 ━━━
1. 채점 기준의 각 항목을 개별적으로 검토한 뒤 총점(0~100)을 산출하세요.
2. strengths: 답안에서 실제로 잘된 구체적인 부분을 2~3개 서술하세요. "잘 썼어요" 같은 막연한 칭찬은 금지입니다.
3. improvements: 점수를 올리려면 무엇을 어떻게 보완해야 하는지 2~3개 구체적으로 서술하세요.
4. summary: 이 답안의 핵심 강점과 핵심 약점을 한 문장에 담아주세요.
5. 예시 답안이 있으면 비교하여 누락된 핵심 내용을 improvements에 포함하세요.
6. 반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

{{
  "score": <0~100 정수>,
  "strengths": ["구체적 잘한점1", "구체적 잘한점2"],
  "improvements": ["구체적 보완점1", "구체적 보완점2"],
  "summary": "핵심 강점과 약점을 담은 한 문장 총평"
}}"""

    def _parse(raw: str) -> dict | None:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
            score = max(0, min(100, int(data.get("score", 0))))
            return {"score": score, "feedback": json.dumps({
                "score": score,
                "strengths": data.get("strengths", []),
                "improvements": data.get("improvements", []),
                "summary": data.get("summary", ""),
            }, ensure_ascii=False)}
        except Exception:
            return None

    last_error = ""

    # Gemini 우선 — 키별 × 모델별 순환 (429면 다음 키로)
    if _has_gemini():
        clients = _get_gemini_clients()
        for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]:
            for idx, client in enumerate(clients):
                try:
                    response = client.models.generate_content(model=model_name, contents=prompt)
                    result = _parse(response.text)
                    if result:
                        return result
                    logger.warning("Gemini(%s) 키%d 평가 JSON 파싱 실패", model_name, idx + 1)
                    last_error = f"Gemini({model_name}) 응답 파싱 실패"
                    break  # 파싱 실패는 같은 모델 다른 키로 재시도 불필요
                except Exception as e:
                    err_str = str(e)
                    last_error = f"Gemini({model_name}) 키{idx + 1}: {err_str}"
                    logger.warning("Gemini(%s) 키%d 평가 실패: %s", model_name, idx + 1, e)
                    is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                    if not is_quota:
                        break  # 할당량 외 오류는 다음 키로 재시도 불필요
            else:
                continue  # 이 모델의 모든 키가 할당량 소진 → 다음 모델 시도
            break  # 파싱 실패 또는 비할당량 오류 → 다음 모델 불필요

    # Anthropic 차선
    if _has_anthropic():
        try:
            client = _get_anthropic_client()
            # content를 bytes로 강제 인코딩 후 디코딩 → locale ASCII 문제 우회
            safe_prompt = prompt.encode("utf-8").decode("utf-8")
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": [{"type": "text", "text": safe_prompt}]}],
            )
            result = _parse(response.content[0].text)
            if result:
                return result
        except Exception as e:
            last_error = f"Anthropic: {e}"
            logger.error("Anthropic 평가 실패: %s", e)

    return {"score": 0, "feedback": json.dumps({"error": last_error or "AI 분석 실패"}, ensure_ascii=False)}


def run_ai_analysis(sub_answer, skip_ocr: bool = False, force: bool = False) -> None:
    """OlympiadSubAnswer 저장 후 OCR + 평가 실행"""
    from django.utils import timezone

    # 1) 사진 OCR (이미 confirmed_ocr이 저장됐으면 생략)
    ocr_text = ""
    if sub_answer.photo and not skip_ocr:
        ocr_text = ocr_from_image(sub_answer.photo)
        # 오류 문구면 무시
        if ocr_text.startswith("[") and "오류" in ocr_text:
            ocr_text = ""
    elif skip_ocr and sub_answer.ocr_text:
        ocr_text = sub_answer.ocr_text

    # 2) OCR 결과 저장 + 서술형 자동 채움
    if ocr_text and not skip_ocr:
        sub_answer.ocr_text = ocr_text
        if not sub_answer.text_answer.strip():
            sub_answer.text_answer = ocr_text

    # 3) 답안이 하나도 없으면 평가 불가
    has_content = bool(sub_answer.text_answer.strip() or ocr_text)
    if not has_content:
        sub_answer.ai_score = 0
        sub_answer.ai_feedback = json.dumps({
            "score": 0, "strengths": [],
            "improvements": ["사진에서 글씨를 인식하지 못했습니다. 밝고 선명하게 다시 찍어 업로드해 주세요."],
            "summary": "OCR 인식 실패 — 사진을 다시 제출해 주세요."
        }, ensure_ascii=False)
        sub_answer.ai_analyzed_at = timezone.now()
        sub_answer.save(update_fields=["ocr_text", "text_answer", "ai_score", "ai_feedback", "ai_analyzed_at"])
        return

    # 4) AI 평가
    result = evaluate_sub_answer(sub_answer.sub_question, sub_answer.text_answer, ocr_text)
    # force=True(답안 변경)면 무조건 덮어씀; 아니면 기존 좋은 결과 보호
    is_failure = result["score"] == 0 and "error" in result.get("feedback", "")
    if is_failure and not force and sub_answer.ai_score and sub_answer.ai_score > 0:
        sub_answer.save(update_fields=["ocr_text", "text_answer"])
        return
    if is_failure:
        fb = result.get("feedback", "{}")
        try:
            raw_err = json.loads(fb).get("error", "AI 분석 실패")
        except Exception:
            raw_err = fb
        raise RuntimeError(_friendly_ai_error(raw_err))
    sub_answer.ai_score = result["score"]
    sub_answer.ai_feedback = result["feedback"]
    sub_answer.ai_analyzed_at = timezone.now()
    sub_answer.save(update_fields=["ocr_text", "text_answer", "ai_score", "ai_feedback", "ai_analyzed_at"])
