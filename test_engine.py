from db import init_db, save_endpoint, get_endpoint, search_endpoints
from executor import execute_scraper

def test_full_pipeline():
    init_db()
    html_sample = "<div class='price'>1500</div>"
    code = """
from bs4 import BeautifulSoup
def extract(html: str, base_url: str = "") -> dict:
    soup = BeautifulSoup(html, "html.parser")
    val = int(soup.find("div", class_="price").text)
    return {"price": val}
"""
    result = execute_scraper(code, html_sample)
    assert result == {"price": 1500}, f"Expected price 1500, got {result}"

    save_endpoint(
        slug="test-price",
        name="Test Price",
        url="http://example.com",
        task="get price",
        category="finance",
        tags=["test"],
        scraper_code=code,
        schema={"price": "integer"},
        sample_output=result
    )
    ep = get_endpoint("test-price")
    assert ep is not None
    assert ep["schema"]["price"] == "integer"

    search_res = search_endpoints("price")
    assert any(x["slug"] == "test-price" for x in search_res)
    print("ALL TESTS PASSED ✓")

if __name__ == "__main__":
    test_full_pipeline()
