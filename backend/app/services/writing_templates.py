"""IELTS Task 2 essay templates.

Five standard templates with skeletons, placeholders, and worked examples.
Templates share the writing_lessons table; their slugs are prefixed `tmpl-`.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.anthropic_client import claude_complete


@dataclass(frozen=True)
class TemplateSpec:
    slug: str
    title: str
    summary: str
    brief: str


TEMPLATES: tuple[TemplateSpec, ...] = (
    TemplateSpec(
        slug="tmpl-opinion",
        title="Шаблон 1. Opinion (Agree / Disagree)",
        summary="«To what extent do you agree?» — 4 абзаца с готовыми фразами.",
        brief=(
            "Полный шаблон эссе Opinion (To what extent do you agree or disagree / Do you agree...). "
            "1) Покажи как распознать opinion-вопрос (маркеры: 'do you agree', 'to what extent', 'is it a positive or negative development'). "
            "2) Скелет из 4 абзацев с [ПЛЕЙСХОЛДЕРАМИ] и под каждым плейсхолдером 1-2 строки на русском, ЧТО туда писать и ПОЧЕМУ. "
            "3) Раздел '## Готовые фразы' с подборкой для каждой части (введение / opinion-statement / topic sentence / example intro / conclusion). "
            "4) Раздел '## Полный пример' — реальная IELTS question + полностью развернутое эссе ~270 слов где плейсхолдеры заполнены, с пометками в скобках какая это часть скелета. "
            "Помни: шаблон, а не лекция — больше структуры, меньше воды."
        ),
    ),
    TemplateSpec(
        slug="tmpl-discussion",
        title="Шаблон 2. Discussion (обсудить обе точки зрения)",
        summary="«Discuss both views and give your own opinion» — баланс + позиция.",
        brief=(
            "Шаблон эссе Discussion (Discuss both views and give your own opinion). "
            "1) Маркеры вопроса: 'discuss both views', 'compare the views', 'some people think X while others think Y'. "
            "2) Скелет: Intro (перефраз + 'this essay will discuss both views before giving my opinion'), "
            "Body 1 = первая точка зрения (+аргументы), Body 2 = вторая точка зрения (+аргументы), Conclusion = твоя позиция. "
            "Под каждым [ПЛЕЙСХОЛДЕРОМ] — что туда писать и зачем. "
            "3) Раздел '## Готовые фразы' для представления каждой точки зрения и для собственной позиции. "
            "4) Раздел '## Полный пример' с реальной IELTS question и эссе ~280 слов с пометками."
        ),
    ),
    TemplateSpec(
        slug="tmpl-problem-solution",
        title="Шаблон 3. Problem & Solution",
        summary="«What are the causes and what can be done?» — диагностика + действия.",
        brief=(
            "Шаблон Problem & Solution (или Causes & Solutions / Causes & Effects). "
            "1) Маркеры: 'what are the causes', 'what problems does this cause', 'what can be done', 'how can this be solved'. "
            "2) Скелет: Intro (перефраз + 'this essay will examine the causes/problems and propose solutions'), "
            "Body 1 = причины/проблемы (2 главные с примерами), Body 2 = решения (2 главные с примерами), Conclusion. "
            "Под каждым [ПЛЕЙСХОЛДЕРОМ] — что и почему. "
            "3) Раздел '## Готовые фразы' для введения проблемы, причинно-следственных связей, предложения решений. "
            "4) Раздел '## Полный пример' — реальная question (например про urban traffic) и эссе ~280 слов с пометками."
        ),
    ),
    TemplateSpec(
        slug="tmpl-adv-disadv",
        title="Шаблон 4. Advantages & Disadvantages",
        summary="«Do the advantages outweigh the disadvantages?» — взвесить, дать оценку.",
        brief=(
            "Шаблон Advantages & Disadvantages. ВАЖНО: есть две подварианта — нейтральный 'discuss advantages and disadvantages' "
            "и оценочный 'do the advantages outweigh the disadvantages'. Объясни разницу и как менять заключение. "
            "1) Маркеры: 'advantages and disadvantages', 'outweigh', 'benefits and drawbacks'. "
            "2) Скелет: Intro (перефраз + thesis), Body 1 = преимущества (2 главных с примерами), Body 2 = недостатки (2 главных с примерами), "
            "Conclusion = взвешенный вывод (если 'outweigh', обязательно дать однозначный ответ). Под каждым [ПЛЕЙСХОЛДЕРОМ] — что и почему. "
            "3) Раздел '## Готовые фразы' для перечисления и оценки. "
            "4) Раздел '## Полный пример' — реальная question и эссе ~280 слов с пометками."
        ),
    ),
    TemplateSpec(
        slug="tmpl-two-part",
        title="Шаблон 5. Two-Part Question",
        summary="Два вопроса в одной задаче — отвечай на оба, по абзацу на каждый.",
        brief=(
            "Шаблон Two-Part Question (Direct Question). Часто это два связанных вопроса: 'Why is this happening? Is it a positive development?' "
            "1) Маркеры: ДВА явных вопросительных предложения, обычно один описательный + один оценочный. "
            "2) Скелет: Intro (перефраз контекста + thesis который коротко отвечает на оба вопроса), "
            "Body 1 = развёрнутый ответ на первый вопрос (с примерами), Body 2 = развёрнутый ответ на второй вопрос (с примерами), Conclusion. "
            "Под каждым [ПЛЕЙСХОЛДЕРОМ] — что и почему. "
            "3) Раздел '## Готовые фразы' для прямых ответов и оценок. "
            "4) Раздел '## Полный пример' — реальная two-part question и эссе ~280 слов с пометками."
        ),
    ),
)


def get_template_spec(slug: str) -> TemplateSpec | None:
    return next((t for t in TEMPLATES if t.slug == slug), None)


TEMPLATE_SYSTEM = (
    "You produce IELTS Writing Task 2 templates for a Russian-speaking learner. "
    "Output is Markdown only, in Russian (English examples stay in English). "
    "Be a SKELETON-FIRST template, not a long lecture: show the structure with "
    "[PLACEHOLDERS], a short why-line under each, ready-made phrases, and one "
    "fully worked example. 600-1000 words is the right length."
)


async def generate_template_body(spec: TemplateSpec) -> str:
    user = (
        f"Build the template '{spec.title}'.\n\n"
        f"Brief:\n{spec.brief}\n\n"
        "Output structure (Markdown, in Russian):\n"
        "## Как распознать этот тип вопроса\n"
        "## Скелет эссе  (use markdown code blocks for the skeleton, with [PLACEHOLDERS])\n"
        "## Готовые фразы\n"
        "## Полный пример\n"
        "Markdown only. No commentary outside the template."
    )
    reply = await claude_complete(system_prompt=TEMPLATE_SYSTEM, user_message=user)
    return reply.strip().strip("`").strip()
