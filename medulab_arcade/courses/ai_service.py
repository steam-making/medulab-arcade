"""
올림피아드 하위문제 AI 평가 서비스
- 손글씨 사진 → OCR (Claude Vision)
- 답안 텍스트 → 평가점수 + 보완점 피드백 생성
"""
import base64
import json
import re
from django.conf import settings


def _get_client():
    import anthropic
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY가 settings에 설정되지 않았습니다.")
    return anthropic.Anthropic(api_key=api_key)


def ocr_from_image(image_field) -> str:
    """
    Django ImageField → Claude Vision으로 손글씨 OCR.
    반환: 인식된 텍스트 문자열
    """
    if not image_field:
        return ""
    try:
        client = _get_client()
        image_field.seek(0)
        image_data = base64.standard_b64encode(image_field.read()).decode("utf-8")
        name = getattr(image_field, 'name', '') or ''
        ext = name.rsplit('.', 1)[-1].lower() if '.' in name else 'jpeg'
        media_type_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp'}
        media_type = media_type_map.get(ext, 'image/jpeg')

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_data},
                    },
                    {
                        "type": "text",
                        "text": (
                            "이 이미지는 학생이 손으로 작성한 올림피아드 답안지입니다.\n"
                            "이미지에 적힌 모든 한국어 텍스트를 최대한 정확하게 인식하여 그대로 출력해 주세요.\n"
                            "표, 그림 설명, 번호 목록 등이 있으면 구조를 유지하며 텍스트로 변환하세요.\n"
                            "인식된 텍스트만 출력하고 다른 설명은 붙이지 마세요."
                        ),
                    },
                ],
            }],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"[OCR 오류: {e}]"


def evaluate_sub_answer(sub_question, answer_text: str, ocr_text: str = "") -> dict:
    """
    하위문제 + 답안 텍스트 → AI 평가.
    반환: {"score": int, "feedback": str}
    """
    if not answer_text.strip() and not ocr_text.strip():
        return {"score": 0, "feedback": "답안이 없습니다."}

    combined = answer_text.strip() or ocr_text.strip()
    thinking_type = getattr(sub_question, 'thinking_type', '') or ''
    q_text = sub_question.question_text
    example = (sub_question.example_answer or '').strip()

    prompt = f"""당신은 AI SW 사고력 올림피아드 채점 전문가입니다.

[문제]
{q_text}

[사고력 유형]
{thinking_type if thinking_type else '미지정'}

[예시 답안]
{example if example else '없음'}

[학생 답안]
{combined}

위 답안을 다음 기준으로 평가하세요:

1. **점수 (0~100)**: 문제 조건 충족도, 논리적 구성, 구체성, 사고력 유형 반영도를 고려하세요.
2. **잘한 점** (2~3가지): 구체적으로 기술
3. **보완할 점** (2~3가지): 어떻게 보완하면 좋은지 친절하게 안내
4. **한 줄 총평**

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "score": <0~100 정수>,
  "strengths": ["잘한점1", "잘한점2"],
  "improvements": ["보완점1", "보완점2"],
  "summary": "한 줄 총평"
}}"""

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # JSON 추출
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            score = max(0, min(100, int(data.get("score", 0))))
            strengths = data.get("strengths", [])
            improvements = data.get("improvements", [])
            summary = data.get("summary", "")
            feedback = json.dumps({
                "score": score,
                "strengths": strengths,
                "improvements": improvements,
                "summary": summary,
            }, ensure_ascii=False)
            return {"score": score, "feedback": feedback}
    except Exception as e:
        return {"score": 0, "feedback": json.dumps({"error": str(e)}, ensure_ascii=False)}

    return {"score": 0, "feedback": ""}


def run_ai_analysis(sub_answer) -> None:
    """
    OlympiadSubAnswer 인스턴스를 받아 OCR + AI 평가 실행 후 저장.
    뷰에서 저장 직후 호출 (동기).
    """
    from django.utils import timezone

    ocr_text = ""
    if sub_answer.photo:
        try:
            sub_answer.photo.open('rb')
            ocr_text = ocr_from_image(sub_answer.photo)
        except Exception:
            ocr_text = ""
        finally:
            try:
                sub_answer.photo.close()
            except Exception:
                pass

    if ocr_text and not ocr_text.startswith("[OCR 오류"):
        sub_answer.ocr_text = ocr_text
        if not sub_answer.text_answer.strip():
            sub_answer.text_answer = ocr_text

    result = evaluate_sub_answer(
        sub_answer.sub_question,
        sub_answer.text_answer,
        ocr_text,
    )
    sub_answer.ai_score = result["score"]
    sub_answer.ai_feedback = result["feedback"]
    sub_answer.ai_analyzed_at = timezone.now()
    sub_answer.save(update_fields=["ocr_text", "text_answer", "ai_score", "ai_feedback", "ai_analyzed_at"])
