import tldextract


def get_registered_domain(url):
    extracted = tldextract.extract(url)

    if not extracted.domain or not extracted.suffix:
        return extracted.domain

    return f"{extracted.domain}.{extracted.suffix}"


def is_first_party(request_domain, website_domain):
    return get_registered_domain(request_domain) == get_registered_domain(website_domain)


def classify_requests(requests, website_url):
    website_domain = get_registered_domain(website_url)

    first_party = []
    third_party = []

    for request in requests:
        if is_first_party(request["domain"], website_domain):
            first_party.append(request)
        else:
            third_party.append(request)

    return first_party, third_party