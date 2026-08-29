from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """템플릿에서 변수 키로 딕셔너리 값을 조회 (예: {{ some_dict|get_item:loop_var }})"""
    if not dictionary:
        return None
    return dictionary.get(key)
