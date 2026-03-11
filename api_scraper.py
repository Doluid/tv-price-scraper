import requests
import pandas as pd
import time
from datetime import datetime
import gspread  # ☁️ 구글 스프레드시트 연동 라이브러리


# --- 🧠 카테고리 자동 분류 함수 ---
def categorize_tv(name):
    name_upper = str(name).upper()
    if "NEO QLED" in name_upper:
        return "Neo QLED"
    elif "OLED" in name_upper:
        return "OLED"
    elif "QLED" in name_upper:
        return "QLED"
    elif "CRYSTAL" in name_upper:
        return "Crystal UHD"
    elif "FRAME" in name_upper or "SERIF" in name_upper or "SERO" in name_upper:
        return "Lifestyle TV"
    else:
        return "Standard TV"


# --- 🚀 메인 크롤링 함수 ---
def fetch_all_tvs_multi_country():
    api_url = "https://searchapi.samsung.com/v6/front/b2c/product/finder/newhybris"
    num_per_page = 12

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }

    extracted_date = datetime.now().strftime("%Y-%m-%d")
    brand_name = "Samsung"
    division_name = "TV"

    # 수집할 국가 목록 (독일, 영국)
    target_countries = [
        {"code": "de", "name": "Germany"},
        {"code": "uk", "name": "UK"}
    ]

    all_extracted_data = []

    print(f"🚀 [{extracted_date}] 글로벌 {brand_name} {division_name} 데이터 수집을 시작합니다...\n")

    for country in target_countries:
        site_code = country["code"]
        country_name = country["name"]
        start_index = 1

        print(f"🌍 === {country_name} ({site_code}) 데이터 수집 시작 === 🌍")

        while True:
            print(f"📡 {country_name}: {start_index}번째 제품부터 {num_per_page}개 요청 중...")
            params = {
                "type": "04010000",
                "siteCode": site_code,
                "start": str(start_index),
                "num": str(num_per_page),
                "sort": "recommended",
                "onlyFilterInfoYN": "N",
                "keySummaryYN": "Y",
                "onlyReasonToBuyYN": "N"
            }

            response = requests.get(api_url, params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                product_list = data.get("response", {}).get("resultData", {}).get("productList", [])

                if not product_list:
                    print(f"✅ {country_name} 데이터 스크롤 끝(수집 완료)!\n")
                    break

                for product in product_list:
                    models = product.get("modelList", [])
                    for model in models:
                        display_name = model.get("displayName", "N/A")

                        all_extracted_data.append({
                            "Date": extracted_date,
                            "Country": country_name,
                            "Brand": brand_name,
                            "Division": division_name,
                            "Category": categorize_tv(display_name),
                            "Family_Name": model.get("fmyEngName", "N/A"),
                            "Model_Code": model.get("modelCode", "N/A"),
                            "Name": display_name,
                            "Price_Raw": model.get("price", "N/A"),
                            "Price_Display": model.get("priceDisplay", "N/A"),
                            "Promo_Price_Raw": model.get("promotionPrice", "N/A"),
                            "Promo_Price_Display": model.get("promotionPriceDisplay", "N/A"),
                            "Ratings": model.get("ratings", "N/A"),
                            "Review_Count": model.get("reviewCount", "N/A"),
                            "URL": f"https://www.samsung.com{model.get('pdpUrl', '')}" if model.get("pdpUrl") else "N/A"
                        })

                start_index += num_per_page
                time.sleep(1)
            else:
                print(f"❌ 요청 실패 (상태 코드: {response.status_code}). 반복을 중단합니다.")
                break

    # --- ☁️ 수집 완료 후 구글 스프레드시트에 저장 ---
    if all_extracted_data:
        df = pd.DataFrame(all_extracted_data)

        print("☁️ 구글 스프레드시트에 데이터를 전송합니다...")
        try:
            gc = gspread.service_account(filename='secrets.json')
            sh = gc.open("Samsung_TV_Data")  # 시트 이름이 정확히 일치해야 합니다.
            worksheet = sh.sheet1

            existing_data = worksheet.get_all_values()

            # 빈 시트일 경우 헤더(열 이름) 먼저 추가
            if not existing_data:
                worksheet.append_row(df.columns.tolist())

            # 데이터를 시트 맨 아래에 누적(Append)
            values_to_append = df.fillna("").values.tolist()
            worksheet.append_rows(values_to_append)

            print(f"💾 대성공! 총 {len(df)}개의 데이터가 구글 시트에 안전하게 누적되었습니다! 🚀")

            # 백업용 로컬 저장
            df.to_csv("samsung_global_tvs_backup.csv", index=False, encoding="utf-8-sig")

        except Exception as e:
            print(f"❌ 구글 시트 저장 중 에러가 발생했습니다: {e}")
            print("💡 확인: secrets.json 파일 존재 여부, 시트 이름(Samsung_TV_Data), 서비스 계정 공유 여부")
    else:
        print("수집된 데이터가 없습니다.")


if __name__ == "__main__":
    fetch_all_tvs_multi_country()
