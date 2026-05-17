import json
import re
from typing import Literal, Tuple

import requests
from django.conf import settings

from .models import BlockedKeyword

_WS_RE = re.compile(r"[\s\u2000-\u200f\u2028-\u202f\u205f\u3000]+")
_SEP_RE = re.compile(r"[`~!@#$%^&*()\-_=+\[\]{}|;:'\",.<>/?\\·．．。，、；：？！…—～‖「」『』〈〉《》【】]+")


def _normalize(s: str) -> str:
    result = _SEP_RE.sub("", _WS_RE.sub("", s.lower()))
    return result


def _call_ai(prompt: str) -> str:
    api_key = settings.DEEPSEEK_API_KEY
    url = settings.DEEPSEEK_API_URL
    model = settings.AI_MODEL

    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是内容审核助手。分析用户内容是否违规。"
                        "只输出一个词：拦截 或 审核 或 放过。"
                        "不要输出任何其他内容。不要解释。不要标点。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": 8,
        },
        timeout=15,
    )
    data = resp.json()
    reply = data["choices"][0]["message"]["content"].strip()
    return reply


ModerationAction = Literal["pass", "block", "review"]


def moderate_text(text: str) -> Tuple[ModerationAction, str]:
    if not text:
        return "pass", ""

    # 1) 关键词拦截 —— 归一化后匹配，封堵"吃 shi""吃.shi"类空格/符号绕过
    text_norm = _normalize(text)
    keywords = BlockedKeyword.objects.values_list("keyword", flat=True)
    for kw in keywords:
        kw_norm = _normalize(kw)
        if kw_norm and kw_norm in text_norm:
            return "block", f"包含拦截关键词：{kw}"

    # 2) 身份证 / 银行卡等敏感信息正则
    if re.search(r"[0-9]{15,19}", text):
        sid = 0
        if re.search(r"(身份证|银行卡)", text):
            sid += 1
        if re.search(r"[a-zA-Z]{5,}", text):
            sid += 1
        if sid >= 2:
            return "block", "疑似包含敏感信息"

    # 3) AI 语义审核
    prompt = (
        "请审核以下用户提交的内容。\n\n"
        "拦截（直接禁止，明显违规）：\n"
        "- 露骨脏话、人身攻击、侮辱、仇恨言论\n"
        "- 涉黄、色情、性暗示、约炮等低俗内容\n"
        "- 毒品、赌博、违法信息\n"
        "- 在词间插入空格/符号来绕过审核的违规内容（如把脏话拆成单字加空格）\n\n"
        "审核（不确定，需人工判断）：\n"
        "- 可能带有恶意但不够明显\n"
        "- 边界模糊的低俗/调侃内容\n"
        "- 疑似变体脏话但不确定\n\n"
        "放过（正常内容）：\n"
        "- 普通吐槽、日常聊天\n"
        "- 正常社交用语\n"
        "- 简单的表情、符号\n\n"
        f"待审核内容：{text}\n\n"
        "只输出：拦截 或 审核 或 放过"
    )

    try:
        result = _call_ai(prompt)
        if "拦截" in result and "审核" not in result:
            return "block", "树洞小助手判定为不当内容"
        if "审核" in result:
            return "review", "树洞小助手判定为需人工审核"
        return "pass", ""
    except Exception:
        return "pass", ""


def moderate_nickname(name: str) -> Tuple[ModerationAction, str]:
    """与 moderate_text 相同逻辑，但 prompt 针对昵称优化"""
    if not name:
        return "pass", ""

    text_norm = _normalize(name)
    keywords = BlockedKeyword.objects.values_list("keyword", flat=True)
    for kw in keywords:
        kw_norm = _normalize(kw)
        if kw_norm and kw_norm in text_norm:
            return "block", f"昵称包含拦截关键词：{kw}"

    prompt = (
        "请审核以下用户昵称。\n\n"
        "拦截（直接禁止）：\n"
        "- 露骨脏话、人身攻击\n"
        "- 涉黄、色情暗示\n"
        "- 冒充管理员、官方身份\n"
        "- 在词间插入空格/符号来绕过审核的违规内容\n\n"
        "审核（不确定）：\n"
        "- 边界模糊，可能低俗但不够明显\n\n"
        "放过：正常昵称\n\n"
        f"待审核昵称：{name}\n\n"
        "只输出：拦截 或 审核 或 放过"
    )

    try:
        result = _call_ai(prompt)
        if "拦截" in result and "审核" not in result:
            return "block", "树洞小助手判定昵称不当"
        if "审核" in result:
            return "review", "昵称需人工审核"
        return "pass", ""
    except Exception:
        return "pass", ""
