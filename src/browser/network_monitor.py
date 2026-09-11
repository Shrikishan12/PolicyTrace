from urllib.parse import urlparse
import time


def create_request_record(request):
    parsed_url = urlparse(request.url)

    return {
        "method": request.method,
        "url": request.url,
        "domain": parsed_url.netloc.lower(),
        "resource_type": request.resource_type,
        "timestamp": time.time()
    }