from bs4 import BeautifulSoup
import html2text

def clean_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')

    for tag in soup.find_all(style=True):
        del tag['style']

    for style_tag in soup.find_all('style'):
        style_tag.decompose()

    for script_tag in soup.find_all('script'):
        script_tag.decompose()

    for link_tag in soup.find_all('link', rel='stylesheet'):
        link_tag.decompose()

    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
        comment.extract()

    for tag in soup.find_all():
        for attr in ['aria-', 'role', 'class', 'id']:
            if attr in tag.attrs:
                del tag[attr]

    for div in soup.find_all('div'):
        if div.get_text(strip=True).isdigit():
            div.decompose()
        elif not div.get_text(strip=True):
            div.decompose()

    for svg in soup.find_all('svg'):
        svg.decompose()

    return soup.prettify()

def html_to_markdown(html_content: str) -> str:
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    return h.handle(html_content)
