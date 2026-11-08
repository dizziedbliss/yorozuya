from pipeline.text import html_to_text


def test_list_items_keep_their_text_on_the_bullet_line():
    html = "<p>Who you are</p><ul>\n<li>\n<p>Ambitious builder: you build things.</p>\n</li>\n<li><p>Rigorous thinker.</p></li></ul>"

    assert html_to_text(html) == "Who you are\n\n• Ambitious builder: you build things.\n• Rigorous thinker."


def test_escaped_greenhouse_html_is_unescaped_first():
    assert html_to_text("&lt;p&gt;Hello &amp;amp; welcome&lt;/p&gt;") == "Hello & welcome"
