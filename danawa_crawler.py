import argparse
import csv
import random
import re
import time
from typing import Dict, List, Set, Optional
from playwright.sync_api import Playwright, sync_playwright, Page, BrowserContext


def wait_for_network_idle(page: Page, timeout_ms: int = 3000) -> None:
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except:
        pass


def open_new_context(playwright: Playwright, headless: bool) -> BrowserContext:
    browser = playwright.chromium.launch(headless=headless)
    return browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 800},
        locale="ko-KR",
        timezone_id="Asia/Seoul",
    )


def human_delay(base_delay_ms: int = 500) -> None:
    time.sleep((base_delay_ms + random.randint(0, base_delay_ms)) / 1000.0)


def slow_scroll(page: Page, steps: int = 6, step_px: int = 800, base_delay_ms: int = 300) -> None:
    for _ in range(steps):
        page.evaluate("step => window.scrollBy(0, step)", step_px)
        human_delay(base_delay_ms)


def extract_specs_from_detail(page: Page) -> Dict[str, str]:
    specs: Dict[str, str] = {}
    
    def add_or_append_spec(key: str, value: str):
        if key == value:
            return
        if key in specs:
            if specs[key] == value or value in specs[key] or specs[key] in value:
                return
            existing_values = [v.strip() for v in specs[key].split(',')]
            if value.strip() not in existing_values:
                specs[key] = f"{specs[key]},{value}"
        else:
            specs[key] = value
    
    all_tr_elements = page.locator("tr").all()
    for tr in all_tr_elements:
        ths = tr.locator("th").all()
        tds = tr.locator("td").all()
        
        if len(ths) == 1 and len(tds) > 1:
            parent_key = ths[0].inner_text().strip()
            for td in tds:
                value = td.inner_text().strip()
                if value and value not in ["○", "O", "o", "●"]:
                    add_or_append_spec(parent_key, value)
        
        for i in range(min(len(ths), len(tds))):
            key = ths[i].inner_text().strip()
            value = tds[i].inner_text().strip()
            if key and value:
                value = value.split("인증번호 확인")[0].split("바로가기")[0].strip()
                value = re.sub(r'\s*\([^)]*\)', '', value)
                if value:
                    add_or_append_spec(key, value)
    
    return specs


def click_detail_tab_if_present(page: Page) -> None:
    for label in ["상세정보", "상세 사양", "상세스펙"]:
        try:
            page.get_by_role("button", name=label).first.click(timeout=2000)
            wait_for_network_idle(page)
            return
        except:
            pass


def collect_product_links(page: Page, max_per_page: Optional[int]) -> List[str]:
    links, seen = [], set()
    selectors = ["li.prod_item div.prod_info a.prod_link", "li.prod_item .prod_name a", "div.prod_info a.prod_link", "a[href*='/product/']"]
    
    for selector in selectors:
        if page.locator(selector).count() == 0:
            continue
        for a in page.locator(selector).all():
            href = a.get_attribute("href")
            text = (a.inner_text() or "").strip()
            
            if not href or href.startswith("javascript:"):
                continue
            if "danawa" not in href and not href.startswith("/"):
                continue
            if href in seen:
                continue
            if any(x in text.lower() for x in ["가격", "비교", "옵션", "구성"]):
                continue
            
            seen.add(href)
            links.append(href)
            if max_per_page and len(links) >= max_per_page:
                return links
    return links


def paginate(page: Page, url: str, page_num: int) -> bool:
    try:
        next_url = re.sub(r'page=\d+', f'page={page_num}', url) if "page=" in url else f"{url}{'&' if '?' in url else '?'}page={page_num}"
        page.goto(next_url)
        wait_for_network_idle(page)
        return True
    except:
        return False


def process_specs(specs: Dict[str, str]) -> str:
    spec_parts = []
    cert_items, cert_info_items = [], []
    registration_date = ""
    
    key_simplification = {"재료 종류": "재료", "반찬종류": "종류"}
    category_mapping = {
        "국내산": "원산지", "레토르트이유식": "품목", "파우치": "포장용기", "플라스틱병": "포장용기",
        "6개월~": "최소연령", "7개월~": "최소연령", "9개월~": "최소연령", "10개월~": "최소연령",
        "12개월~": "최소연령", "13개월~": "최소연령", "15개월~": "최소연령", "4개월~": "최소연령",
        "상온": "보관방식", "냉장": "보관방식", "냉동": "보관방식",
        "양념": "품목", "반찬": "품목", "아기국": "품목", "수제이유식": "품목",
        "미음": "형태", "죽": "형태", "진밥": "형태", "아기밥": "형태", "액상": "형태",
        "국물조림용": "용도", "비빔무침용": "용도", "무항생제인증": "인증",
    }
    
    for key, value in specs.items():
        if not value or not value.strip():
            continue
        
        original_key = key
        key = key_simplification.get(key, key).replace('[', '').replace(']', '')
        
        if key == value or original_key == value:
            continue
        
        clean_value = value.strip()
        clean_value = clean_value.split("인증번호 확인")[0].split("바로가기")[0].strip()
        clean_value = re.sub(r'\s*\([^)]*\)', '', clean_value)
        clean_value = re.sub(r'\s*\([^)]*$', '', clean_value)
        clean_value = re.sub(r'\s*\([^)]*', '', clean_value)
        clean_value = clean_value.replace("제조사 웹사이트", "").replace("웹사이트", "").strip()
        clean_value = re.sub(r'\s+', ' ', clean_value).strip()
        
        if not clean_value:
            continue
        
        if "등록년월" in key or "등록일" in key:
            registration_date = clean_value
            continue
        
        if key == "인증정보" or ("인증" in key and clean_value in ["○", "O", "o", "●"]):
            if "HACCP" in key or key == "HACCP인증":
                if key not in cert_info_items:
                    cert_info_items.append(key)
                continue
        
        if "인증번호" in key:
            if clean_value not in cert_info_items:
                cert_info_items.append(clean_value)
            continue
        
        additive_keys = ["합성보존료", "합성착색료", "합성감미료", "보존료", "착색료", "감미료"]
        if key in additive_keys and clean_value not in ["○", "O", "o", "●", "무첨가", "없음"]:
            key = "無첨가"
        
        meaningless_values = ["상세설명 / 판매 사이트 문의", "상세설명", "판매 사이트 문의", "인증번호 확인"]
        is_meaningless = clean_value in meaningless_values or any(mv in clean_value for mv in meaningless_values)
        
        check_marks = ["○", "O", "o", "●"]
        if clean_value in check_marks:
            if "HACCP" in key or key == "HACCP인증":
                if key not in cert_info_items:
                    cert_info_items.append(key)
            elif "인증" in key:
                if key not in cert_items:
                    cert_items.append(key)
            else:
                if key in category_mapping:
                    category = category_mapping[key]
                    existing = next((p for p in spec_parts if p.startswith(f"{category}:")), None)
                    if existing:
                        existing_value = existing.split(":", 1)[1]
                        spec_parts.remove(existing)
                        spec_parts.append(f"{category}:{existing_value},{key}")
                    else:
                        spec_parts.append(f"{category}:{key}")
        elif "인증" in key and "HACCP" not in key:
            if key not in cert_items:
                cert_items.append(key)
        else:
            if not is_meaningless:
                if key == clean_value and key in category_mapping:
                    category = category_mapping[key]
                    existing = next((p for p in spec_parts if p.startswith(f"{category}:")), None)
                    if existing:
                        existing_value = existing.split(":", 1)[1]
                        spec_parts.remove(existing)
                        spec_parts.append(f"{category}:{existing_value},{key}")
                    else:
                        spec_parts.append(f"{category}:{key}")
                else:
                    spec_parts.append(f"{key}:{clean_value}")
    
    if cert_items:
        spec_parts.append(f"인증:{','.join(cert_items)}")
    if cert_info_items:
        spec_parts.append(f"인증정보:{','.join(cert_info_items)}")
    if registration_date:
        spec_parts.append(f"등록년월일:{registration_date}")
    
    return "/".join(spec_parts)


def crawl_category(category_url: str, output_csv: str, max_pages: int, max_items_per_page: Optional[int],
                   headless: bool, max_total_items: Optional[int] = None, base_delay_ms: int = 500) -> None:
    with sync_playwright() as p:
        context = open_new_context(p, headless)
        page = context.new_page()
        page.set_default_timeout(10000)
        page.goto(category_url)
        wait_for_network_idle(page)
        slow_scroll(page)
        human_delay(base_delay_ms)

        all_rows = []

        for page_index in range(max_pages):
            print(f"페이지 {page_index + 1}/{max_pages} 크롤링 중...")
            product_links = collect_product_links(page, max_items_per_page)
            print(f"  - {len(product_links)}개 링크 발견")
            
            if not product_links:
                break
            
            for link in product_links:
                if max_total_items and len(all_rows) >= max_total_items:
                    print(f"최대 아이템 수({max_total_items})에 도달했습니다.")
                    break
                
                print(f"  [{len(all_rows) + 1}] 크롤링 중...")
                detail_page = context.new_page()
                detail_page.set_default_timeout(15000)
                
                try:
                    detail_page.goto(link, wait_until="domcontentloaded", timeout=15000)
                    wait_for_network_idle(detail_page)
                    slow_scroll(detail_page, steps=4, step_px=900, base_delay_ms=base_delay_ms)
                    click_detail_tab_if_present(detail_page)
                    
                    specs = extract_specs_from_detail(detail_page)
                    title = detail_page.title() or ""
                    detail_info = process_specs(specs)
                    
                    all_rows.append({"상품명": title, "URL": link, "상세정보": detail_info})
                    print(f"    완료! (총 {len(all_rows)}개 수집)")
                except Exception as e:
                    print(f"    오류: {e}")
                finally:
                    try:
                        detail_page.close()
                    except:
                        pass
                
                human_delay(base_delay_ms)
            
            if max_total_items and len(all_rows) >= max_total_items:
                break
            
            if page_index < max_pages - 1:
                if not paginate(page, category_url, page_index + 2):
                    break
                slow_scroll(page)
                human_delay(base_delay_ms)

        with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["상품명", "URL", "상세정보"])
            writer.writeheader()
            writer.writerows(all_rows)

        context.browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Danawa crawler")
    parser.add_argument("--category-url", required=True)
    parser.add_argument("--output", default="danawa_output.csv")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--items-per-page", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--max-total-items", type=int, default=0)
    parser.add_argument("--delay-ms", type=int, default=600)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    crawl_category(
        args.category_url, args.output, args.pages,
        args.items_per_page or None, args.headless,
        args.max_total_items or None, args.delay_ms
    )


if __name__ == "__main__":
    main()

