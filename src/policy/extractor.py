from bs4 import BeautifulSoup


def extract_policy_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "noscript",
        "nav",
        "header",
        "footer"
    ]):
        element.decompose()

    main_content = soup.find("main")

    if main_content:
        text = main_content.get_text(" ", strip=True)
    else:
        text = soup.get_text(" ", strip=True)

    return text