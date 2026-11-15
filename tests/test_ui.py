from ui.theme import safe_color, build_css
from ui.components import e, multiline, risk_class, _card_html


def test_safe_color_accepts_only_hex():
    assert safe_color('#3B82F6') == '#3b82f6'
    assert safe_color('red;} body{display:none') == '#3b82f6'
    assert safe_color(None) == '#3b82f6'


def test_css_generation_never_emits_unsafe_values():
    css = build_css([{'id': 3, 'color': 'url(javascript:alert(1))'}, {'id': 4, 'color': '#a78bfa'}])
    assert 'javascript' not in css
    assert 'st-key-card_c4_' in css and '--accent:#a78bfa' in css


def test_html_is_escaped():
    assert '<script>' not in e('<script>alert(1)</script>')
    assert '\n' not in multiline('a\nb') and '&#10;' in multiline('a\nb')


def test_risk_class_whitelist():
    assert risk_class('High') == 'risk-High'
    assert risk_class('x" onmouseover="evil') == 'risk-None'


def test_card_html_escapes_command_and_notes():
    html = _card_html({'title': '<b>t</b>', 'command_text': '"$_" <img src=x onerror=1>', 'notes': '<i>n</i>',
                       'risk_level': 'High', 'usage_type': 'Admin', 'category': 'Net'}, 1)
    assert '<img' not in html and '<b>t' not in html and '<i>n' not in html
