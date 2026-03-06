"""
Configuration: loads environment variables, provides DB connection, shared constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ─────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# ── OpenAI ───────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ── Scraping defaults ────────────────────────────────────
SCRAPE_DELAY_SECONDS = float(os.environ.get("SCRAPE_DELAY_SECONDS", "2"))
HTTP_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# ── LLM defaults ────────────────────────────────────────
LLM_BATCH_SIZE = int(os.environ.get("LLM_BATCH_SIZE", "10"))
LLM_MODEL = "gpt-4o-mini"  # cheap and fast for translation/tagging

# ── Prefectures (canonical romanized names) ──────────────
PREFECTURES = [
    "Hokkaido", "Aomori", "Iwate", "Miyagi", "Akita", "Yamagata", "Fukushima",
    "Ibaraki", "Tochigi", "Gunma", "Saitama", "Chiba", "Tokyo", "Kanagawa",
    "Niigata", "Toyama", "Ishikawa", "Fukui", "Yamanashi", "Nagano",
    "Gifu", "Shizuoka", "Aichi", "Mie",
    "Shiga", "Kyoto", "Osaka", "Hyogo", "Nara", "Wakayama",
    "Tottori", "Shimane", "Okayama", "Hiroshima", "Yamaguchi",
    "Tokushima", "Kagawa", "Ehime", "Kochi",
    "Fukuoka", "Saga", "Nagasaki", "Kumamoto", "Oita", "Miyazaki", "Kagoshima", "Okinawa",
]

# ── Prefecture aliases (kanji → romanized) ──────────────
PREFECTURE_MAP = {
    "北海道": "Hokkaido", "青森県": "Aomori", "岩手県": "Iwate", "宮城県": "Miyagi",
    "秋田県": "Akita", "山形県": "Yamagata", "福島県": "Fukushima",
    "茨城県": "Ibaraki", "栃木県": "Tochigi", "群馬県": "Gunma",
    "埼玉県": "Saitama", "千葉県": "Chiba", "東京都": "Tokyo", "神奈川県": "Kanagawa",
    "新潟県": "Niigata", "富山県": "Toyama", "石川県": "Ishikawa", "福井県": "Fukui",
    "山梨県": "Yamanashi", "長野県": "Nagano",
    "岐阜県": "Gifu", "静岡県": "Shizuoka", "愛知県": "Aichi", "三重県": "Mie",
    "滋賀県": "Shiga", "京都府": "Kyoto", "大阪府": "Osaka", "兵庫県": "Hyogo",
    "奈良県": "Nara", "和歌山県": "Wakayama",
    "鳥取県": "Tottori", "島根県": "Shimane", "岡山県": "Okayama", "広島県": "Hiroshima",
    "山口県": "Yamaguchi",
    "徳島県": "Tokushima", "香川県": "Kagawa", "愛媛県": "Ehime", "高知県": "Kochi",
    "福岡県": "Fukuoka", "佐賀県": "Saga", "長崎県": "Nagasaki", "熊本県": "Kumamoto",
    "大分県": "Oita", "宮崎県": "Miyazaki", "鹿児島県": "Kagoshima", "沖縄県": "Okinawa",
    # Without 県/府/都 suffix
    "青森": "Aomori", "岩手": "Iwate", "宮城": "Miyagi", "秋田": "Akita",
    "山形": "Yamagata", "福島": "Fukushima", "茨城": "Ibaraki", "栃木": "Tochigi",
    "群馬": "Gunma", "埼玉": "Saitama", "千葉": "Chiba", "東京": "Tokyo",
    "神奈川": "Kanagawa", "新潟": "Niigata", "富山": "Toyama", "石川": "Ishikawa",
    "福井": "Fukui", "山梨": "Yamanashi", "長野": "Nagano", "岐阜": "Gifu",
    "静岡": "Shizuoka", "愛知": "Aichi", "三重": "Mie", "滋賀": "Shiga",
    "京都": "Kyoto", "大阪": "Osaka", "兵庫": "Hyogo", "奈良": "Nara",
    "和歌山": "Wakayama", "鳥取": "Tottori", "島根": "Shimane", "岡山": "Okayama",
    "広島": "Hiroshima", "山口": "Yamaguchi", "徳島": "Tokushima", "香川": "Kagawa",
    "愛媛": "Ehime", "高知": "Kochi", "福岡": "Fukuoka", "佐賀": "Saga",
    "長崎": "Nagasaki", "熊本": "Kumamoto", "大分": "Oita", "宮崎": "Miyazaki",
    "鹿児島": "Kagoshima", "沖縄": "Okinawa",
}

# ── Regions ──────────────────────────────────────────────
REGION_MAP = {
    "Hokkaido": "Hokkaido",
    "Aomori": "Tohoku", "Iwate": "Tohoku", "Miyagi": "Tohoku",
    "Akita": "Tohoku", "Yamagata": "Tohoku", "Fukushima": "Tohoku",
    "Ibaraki": "Kanto", "Tochigi": "Kanto", "Gunma": "Kanto",
    "Saitama": "Kanto", "Chiba": "Kanto", "Tokyo": "Kanto", "Kanagawa": "Kanto",
    "Niigata": "Chubu", "Toyama": "Chubu", "Ishikawa": "Chubu", "Fukui": "Chubu",
    "Yamanashi": "Chubu", "Nagano": "Chubu", "Gifu": "Chubu", "Shizuoka": "Chubu", "Aichi": "Chubu",
    "Mie": "Kansai", "Shiga": "Kansai", "Kyoto": "Kansai", "Osaka": "Kansai",
    "Hyogo": "Kansai", "Nara": "Kansai", "Wakayama": "Kansai",
    "Tottori": "Chugoku", "Shimane": "Chugoku", "Okayama": "Chugoku",
    "Hiroshima": "Chugoku", "Yamaguchi": "Chugoku",
    "Tokushima": "Shikoku", "Kagawa": "Shikoku", "Ehime": "Shikoku", "Kochi": "Shikoku",
    "Fukuoka": "Kyushu", "Saga": "Kyushu", "Nagasaki": "Kyushu", "Kumamoto": "Kyushu",
    "Oita": "Kyushu", "Miyazaki": "Kyushu", "Kagoshima": "Kyushu", "Okinawa": "Okinawa",
}
