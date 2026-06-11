import json
import re
from typing import Any
from PIL import Image, ImageDraw, ImageFont
from google import genai
from openai import OpenAI
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from crewai import Agent
from .config import get_settings
from .models import BrandProfile

settings = get_settings()


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip().replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, flags=re.S)
        if match:
            return json.loads(match.group(0))
    raise ValueError('AI response was not valid JSON')


def _font(size: int, bold: bool = False):
    for name in (('arialbd.ttf' if bold else 'arial.ttf'), 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap(text: str, width: int) -> list[str]:
    import textwrap
    return textwrap.wrap(text, width=width)


def create_branded_image(company: str, title: str, subtitle: str, colors: str) -> str:
    import os
    from datetime import datetime
    os.makedirs('generated_assets', exist_ok=True)
    palette = [c.strip() for c in colors.split(',') if c.strip()]
    bg = palette[0] if len(palette) > 0 else '#0B1220'
    accent = palette[1] if len(palette) > 1 else '#1F6FEB'
    text_color = palette[2] if len(palette) > 2 else '#FFFFFF'

    img = Image.new('RGB', (1200, 627), bg)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((48, 48, 1152, 579), radius=28, outline=accent, width=5)
    draw.text((85, 75), company, fill=text_color, font=_font(32, True))
    draw.text((85, 122), 'AI Marketing Operations • Data • Agentic Workflows', fill='#C9D7E8', font=_font(22))
    y = 210
    for line in _wrap(title, 32)[:3]:
        draw.text((85, y), line, fill=text_color, font=_font(48, True))
        y += 58
    y += 18
    for line in _wrap(subtitle, 58)[:3]:
        draw.text((85, y), line, fill='#D7E4F4', font=_font(28))
        y += 38
    draw.rounded_rectangle((860, 215, 1080, 435), radius=34, outline=accent, width=6)
    draw.line((785, 485, 1080, 485), fill=accent, width=6)
    draw.line((860, 325, 785, 485), fill=accent, width=6)
    path = f"generated_assets/post_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(path, optimize=True)
    return path


def build_prompt(brand: BrandProfile, topic: str, extra_focus: list[str], extra_avoid: list[str]) -> str:
    focus = list(dict.fromkeys((brand.topics_to_focus or []) + extra_focus))
    avoid = list(dict.fromkeys((brand.topics_to_avoid or []) + (brand.forbidden_words or []) + extra_avoid))
    hashtags = brand.preferred_hashtags or []
    return f"""
You are the senior B2B social media marketing engine for {brand.company_name}.

Brand profile:
- Industry: {brand.industry}
- Audience: {brand.target_audience}
- Services: {brand.services}
- Brand voice: {brand.brand_voice}
- Positioning: {brand.positioning_statement}
- Focus topics: {focus}
- Avoid topics / forbidden words: {avoid}
- Preferred hashtags: {hashtags}

Task:
Create a LinkedIn company page post about: {topic}

Rules:
- Respect focus topics and avoid topics strictly.
- Executive-friendly, commercially strong, human, and clear.
- No fake statistics, no exaggerated claims.
- Do not use unsupported markdown formatting.
- 130 to 190 words.
- Use short paragraphs and optional bullets.
- Include a clear CTA.
- Include 4 to 6 relevant hashtags.
- Create a concise image title and subtitle with large readable text.

Return valid JSON only with these keys:
{{
  "title": "...",
  "content": "...",
  "image_title": "...",
  "image_subtitle": "...",
  "quality_notes": "..."
}}
"""


def generate_with_gemini(prompt: str) -> dict[str, Any]:
    if not settings.gemini_api_key:
        raise ValueError('GEMINI_API_KEY is missing')
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
    return _extract_json(response.text)


def review_with_openai(prompt: str, draft: dict[str, Any]) -> dict[str, Any]:
    if not settings.openai_api_key:
        draft['reviewed_by_chatgpt'] = False
        return draft
    client = OpenAI(api_key=settings.openai_api_key)
    review_prompt = f"""
You are a senior content quality reviewer. Improve the JSON draft while preserving meaning and brand constraints.
Original prompt:
{prompt}

Draft JSON:
{json.dumps(draft, ensure_ascii=False)}

Return valid JSON only using the same keys. Make it sharper, less generic, and safer for a B2B LinkedIn company page.
"""
    result = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{'role': 'user', 'content': review_prompt}],
        temperature=0.4,
    )
    data = _extract_json(result.choices[0].message.content or '')
    data['reviewed_by_chatgpt'] = True
    return data


class GenerationState(dict):
    pass


def generate_post_pipeline(brand: BrandProfile, topic: str, extra_focus: list[str], extra_avoid: list[str]) -> dict[str, Any]:
    # CrewAI role objects document the agent responsibilities and make the package ready for future task expansion.
    Agent(role='Content Planner', goal='Plan B2B social content', backstory='Plans topics from brand strategy.', allow_delegation=False)
    Agent(role='Writer', goal='Write strong LinkedIn content', backstory='Writes executive social posts.', allow_delegation=False)
    Agent(role='Reviewer', goal='Review and improve content', backstory='Improves quality with ChatGPT.', allow_delegation=False)

    prompt_template = ChatPromptTemplate.from_template('{prompt}')
    prompt = prompt_template.format_messages(prompt=build_prompt(brand, topic, extra_focus, extra_avoid))[0].content

    def gemini_node(state: dict):
        state['draft'] = generate_with_gemini(prompt)
        return state

    def openai_review_node(state: dict):
        state['final'] = review_with_openai(prompt, state['draft'])
        return state

    def image_node(state: dict):
        final = state['final']
        state['image_path'] = create_branded_image(
            brand.company_name,
            final.get('image_title') or final.get('title') or topic,
            final.get('image_subtitle') or 'Data, AI and business outcomes',
            brand.brand_colors,
        )
        return state

    workflow = StateGraph(dict)
    workflow.add_node('gemini_generation', gemini_node)
    workflow.add_node('chatgpt_review', openai_review_node)
    workflow.add_node('image_generation', image_node)
    workflow.set_entry_point('gemini_generation')
    workflow.add_edge('gemini_generation', 'chatgpt_review')
    workflow.add_edge('chatgpt_review', 'image_generation')
    workflow.add_edge('image_generation', END)
    app = workflow.compile()
    output = app.invoke({})
    final = output['final']
    final['image_path'] = output['image_path']
    final['ai_metadata'] = {
        'gemini_model': settings.gemini_model,
        'openai_model': settings.openai_model,
        'reviewed_by_chatgpt': final.get('reviewed_by_chatgpt', False),
        'frameworks': ['langgraph', 'langchain', 'crewai'],
    }
    return final
