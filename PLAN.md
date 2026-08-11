# PharmaShare Insights — Implementation Plan

**Mã tài liệu:** PTI-PLAN-001 · **Rev:** 1.0 · **Ngày lập:** 11/08/2026
**Mục đích:** Portfolio phỏng vấn Data Analyst — STADA Pymepharco
**Ngôn ngữ:** Python 3.11+ · **Thời lượng dự kiến:** ~7–8 tuần (buổi tối/cuối tuần)
**Trạng thái:** Draft — chờ Phase 0

---

## 00. Deal-breaker — spec nhà tuyển dụng vs. bằng chứng dự án

| Chỉ tiêu | Yêu cầu (spec) | Bằng chứng dự án tạo ra | Đạt |
|---|---|---|---|
| **#1 Crawl bằng Python** | Selenium + Pandas thật, chạy được | `crawler/` (Selenium, pagination, retry/backoff, rate-limit) + `etl/` (Pandas clean/normalize/validate) + QA report có số liệu thật. Demo chạy trực tiếp khi phỏng vấn nếu được yêu cầu. | ĐẠT |
| **#2 Power BI quy mô lớn** | Từng build với vài triệu dòng Excel | Star schema chuẩn, fact ở **mức line-item** (không phải mức gói thầu), partition theo năm, surrogate key, aggregation table, DAX measure thay calculated column — tài liệu hoá rõ "kỹ thuật dùng khi data đến triệu dòng". | ĐẠT* |
| **#3 Làm việc Sales/Ops** | Từng phối hợp Sales Force/Operations | 2 persona nghiệp vụ (Regional Sales Manager, Tender KAE) + yêu cầu nghiệp vụ dạng user story tự soạn + dashboard trả lời trực tiếp từng câu hỏi persona. | ĐẠT |

> **Ghi chú trung thực — dùng khi trả lời phỏng vấn:** đừng khẳng định dataset thật có "triệu dòng". Câu trả lời an toàn hơn: *"Dataset demo ở scale [X] dòng vì giới hạn nguồn công khai, nhưng em thiết kế model — partition, surrogate key, aggregation table, DAX — theo đúng nguyên tắc sẽ áp dụng khi data lên triệu dòng, đây là lý do tại sao…"*. Trung thực + tư duy kỹ thuật ăn điểm hơn phóng đại.

---

## 01. Bối cảnh & mục tiêu kinh doanh

**Mục tiêu**
- Theo dõi vị thế cạnh tranh STADA/Pymepharco theo nhóm hoạt chất & khu vực
- Hỗ trợ Tender/KAE định giá thầu cạnh tranh
- Cảnh báo sớm xu hướng giảm giá trúng thầu (price erosion)
- Xác định tỉnh đang mất thị phần vào tay đối thủ
- Tự động hoá quy trình theo dõi đấu thầu đang làm thủ công

**Vấn đề hiện tại**
- Dữ liệu phân tán trên nhiều cổng, không có điểm tổng hợp
- Nhập tay Excel — chậm, dễ sai, không kịp cập nhật
- Tên thuốc/hoạt chất không chuẩn hoá, khó so sánh giá
- Thiếu công cụ trực quan cho Commercial/Tender KAE
- Không có cảnh báo khi đối thủ thắng thầu giá bất thường

---

## 02. Quyết định đã chốt

| Hạng mục | Quyết định | Lý do |
|---|---|---|
| Nguồn dữ liệu chính | **muasamcong.mpi.gov.vn** (cổng đấu thầu quốc gia, công khai, miễn phí) | Chỉ có tài khoản DauThau.info tier free — giá trúng thầu chi tiết nhiều khả năng bị khoá sau paywall. DauThau.info giữ vai trò nguồn đối chiếu/bổ sung. |
| LLM chuẩn hoá hoạt chất/ATC | **Claude API — model Haiku** | Chi phí thấp với volume dự án, độ chính xác tiếng Việt tốt, sẵn workflow Claude Code. |
| Phạm vi năm crawl | **2022–2026** (~5 năm) | Cân bằng volume (nhiều năm × nhiều hoạt chất × nhiều dòng hàng) và thời gian crawl khả thi ngoài giờ. |
| PostgreSQL hosting | **Supabase/Neon free tier** (cloud) | Có URL sống, Power BI connect trực tiếp, demo được khi phỏng vấn mà không cần máy cá nhân bật. |

---

## 03. Kiến trúc pipeline

```
Nguồn công khai (muasamcong / dauthau.info)
        │  Selenium crawler (rate-limit 2–5s, retry/backoff)
        ▼
Raw JSONL, versioned theo ngày  (data/raw/YYYY-MM-DD/)
        │  Pandas ETL (clean, normalize, validate)
        ├──▶ QA report (null%, dup%, outlier)
        ▼
PostgreSQL Star Schema — Supabase  (partition theo năm, upsert idempotent)
        │◀─▶ Claude Haiku (đọc/phân loại hoạt chất → ATC, ghi lại dim_drug)
        ▼
Power BI — 2 dashboard (Regional Sales Manager / Tender KAE)
```

---

## 04. Cấu trúc thư mục đề xuất

```
pharmashare-insights/
├── README.md
├── docs/
│   ├── data_dictionary.md
│   ├── star_schema.md
│   ├── source_assessment.md        # kết quả khảo sát Phase 0
│   ├── qa_report_YYYYMMDD.md       # số liệu thật, tự sinh
│   └── interview_story.md          # mapping deal-breaker → bằng chứng
├── config/
│   ├── keywords.yaml               # danh mục hoạt chất/từ khóa crawl
│   ├── province_mapping.yaml       # chuẩn hóa 63 tỉnh/thành
│   └── settings.yaml               # rate limit, retry, DB conn (.env)
├── crawler/
│   ├── muasamcong/
│   │   ├── search.py
│   │   ├── detail.py
│   │   └── selectors.py
│   ├── dauthau_info/
│   │   ├── search.py
│   │   └── detail.py
│   ├── base_crawler.py             # retry/backoff/logging dùng chung
│   └── run_crawl.py                # entrypoint, checkpoint idempotent
├── data/
│   ├── raw/2026-08-11/*.jsonl      # versioned theo ngày crawl
│   ├── bronze/                     # sau parse cơ bản
│   ├── silver/                     # sau clean + validate
│   └── gold/                       # sẵn sàng nạp star schema
├── etl/
│   ├── clean.py
│   ├── normalize_drug_name.py
│   ├── normalize_province.py
│   ├── validate.py                 # pandera schema check
│   └── qa_report.py
├── ai/
│   ├── classify_drug.py            # gọi Claude Haiku, batch + cache
│   ├── prompts/atc_classification.md
│   └── cache/                      # tránh gọi lại API trùng tên thuốc
├── db/
│   ├── schema.sql                  # DDL star schema, partition, index
│   ├── load.py                     # upsert idempotent vào Postgres
│   └── migrations/
├── powerbi/
│   ├── pharmashare_insights.pbix
│   └── dax_measures.md
├── tests/
│   └── test_normalize.py
├── .env.example
└── requirements.txt
```

---

## 05. Phase & tiêu chí Done

7 phase, mỗi phase gói gọn 1–2 tuần buổi tối/cuối tuần. Tổng ~7–8 tuần.

| Phase | Nội dung | Tiêu chí "Done" | Thời lượng |
|---|---|---|---|
| 0 | **Khảo sát nguồn** — cấu trúc HTML muasamcong & dauthau.info, robots.txt, có đăng nhập/captcha không, chốt danh mục hoạt chất STADA/Pymepharco cần crawl | `source_assessment.md` + 5 sample HTML/nguồn đã lưu + danh sách field xác nhận | 3–5 tối (~1 tuần) |
| 1 | **Crawler MVP** — Selenium search + pagination + detail page, rate-limit, retry/backoff, checkpoint resume, config-driven keyword | Chạy hết 5–10 hoạt chất, ra `data/raw/` vài nghìn dòng, rerun không trùng lặp | 1–2 tuần |
| 2 | **ETL Pandas** — parse số/tiền VNĐ, chuẩn hóa tên thuốc/tỉnh/bệnh viện, dedupe, schema validation (pandera), QA report tự sinh | `qa_report` có số liệu thật (tỷ lệ null/dup/outlier), data dictionary v1 | 1 tuần |
| 3 | **Data model + load** — tạo star schema trên Supabase, partition theo năm, surrogate key, aggregation table, load script upsert idempotent | Schema deploy xong, row count clean = row count DB, ER diagram tài liệu hóa | 1 tuần |
| 4 | **AI enrichment** — Claude Haiku phân loại hoạt chất/ATC, batch + cache tránh gọi trùng, ghi field confidence | >95% `dim_drug` được phân loại, spot-check tay 50 dòng, ghi nhận % đúng + chi phí API | 3–5 tối |
| 5 | **Power BI** — import star schema, DAX measures, 2 dashboard theo persona, tài liệu kỹ thuật scale (aggregation, incremental refresh dự kiến) | 2 dashboard hoàn chỉnh + `dax_measures.md` + ghi chú hiệu năng | 1–1.5 tuần |
| 6 | **Tài liệu & câu chuyện phỏng vấn** — README, data dictionary, `interview_story.md` map deal-breaker → bằng chứng, dọn repo | README đầy đủ, repo trình bày được, kịch bản nói ~3 phút cho từng deal-breaker | 3–5 tối |

---

## 06. Star Schema

Fact ở **mức dòng hàng trong gói thầu** (line-item), không phải mức gói — một gói thầu thuốc ở Việt Nam thường có 50–200 mặt hàng, nên volume tăng tự nhiên và đúng thực tế nghiệp vụ, không phải số liệu giả lập.

```
                     dim_date
                        │
dim_drug ── fact_tender_result ── dim_company
                        │
                  dim_province ── dim_buyer

fact_tender_result: PARTITION BY year(date_key)
agg_monthly_drug_province  (bảng tổng hợp, tăng tốc Power BI, join dim_province + dim_drug + dim_date)
```

| Bảng | Vai trò & cột chính | Ghi chú scale |
|---|---|---|
| `fact_tender_result` | PK `tender_result_id` (surrogate) · natural key `tender_package_id` để upsert idempotent · FK tới 5 dim · `quantity`, `unit_price_vnd`, `total_value_vnd`, `is_stada_related` | Line-item level → volume tự nhiên cao hơn 50–200 lần so với mức gói |
| `dim_drug` | `raw_drug_name`, `standardized_active_ingredient`, `atc_code/therapeutic_group` (từ LLM), `dosage_form`, `is_stada_product`, `classification_confidence` | Surrogate integer key, không dùng chuỗi làm khóa join → giảm cost join |
| `dim_company` | `company_name_normalized`, `is_stada_group`, `competitor_tier` | — |
| `dim_province` | `province_name` (chuẩn 63 tỉnh/thành), `region` (Bắc/Trung/Nam) | Rollup theo `region` hỗ trợ aggregation table |
| `dim_buyer` | `buyer_name`, `buyer_type` (bệnh viện TW/tỉnh/huyện, Sở Y tế), FK `province_key` | Tách riêng khỏi `dim_province` để phân tích cấp bệnh viện khi cần |
| `dim_date` | `date_key` (int yyyymmdd), `full_date`, `year`, `quarter`, `month` | Dùng làm partition key cho `fact_tender_result` |

**Kỹ thuật scale sẽ áp dụng** (ghi rõ trong README, không cần chờ data lớn mới làm): Postgres declarative partitioning theo năm trên fact table · index composite `(drug_key, date_key)` và `(province_key, date_key)` · aggregation table `agg_monthly_drug_province` cho Power BI Import mode · DAX measure thay calculated column · ghi chú cấu hình incremental refresh (RangeStart/RangeEnd) dù demo hiện tại refresh thủ công.

---

## 07. Persona nghiệp vụ

### Regional Sales Manager — Quản lý Kinh doanh Khu vực
Chịu trách nhiệm doanh số & thị phần một vùng (VD: Miền Bắc), cần biết tỉnh nào đang thắng/thua trước khi họp phân bổ nguồn lực quý tới.

- Tỉnh nào đang mất thị phần vào tay đối thủ, theo nhóm thuốc nào?
- Xu hướng thị phần theo quý tại từng tỉnh trọng điểm ra sao?
- Đối thủ nào tăng trưởng nhanh nhất trong khu vực mình phụ trách?
- Quý tới nên ưu tiên nguồn lực (rep, promotion) vào tỉnh nào?

*Dashboard trả lời:* bản đồ/thanh thị phần theo tỉnh, xu hướng theo quý, xếp hạng đối thủ theo tốc độ tăng trưởng.

### Tender KAE — Key Account Executive, Đấu thầu
Chuẩn bị hồ sơ dự thầu, cần định giá cạnh tranh trước khi nộp giá cho gói thầu sắp mở.

- Giá trúng thầu trung bình/thấp nhất/cao nhất của hoạt chất X, 12 tháng gần nhất, theo khu vực?
- Giá nhóm thuốc X đang giảm (price erosion) qua các năm — có nên hạ giá đấu tới không?
- Đối thủ nào hay thắng ở khu vực/bệnh viện mục tiêu, với giá nào?
- Gói thầu gần nhất cùng hoạt chất + hàm lượng trúng giá bao nhiêu, ai trúng?

*Dashboard trả lời:* benchmark giá theo hoạt chất/khu vực, line chart xu hướng giá kèm cảnh báo erosion, bảng gói thầu tương tự gần nhất.

---

## 08. Cần bạn xác nhận thêm trước khi code

- **Danh mục hoạt chất crawl** — soạn draft `keywords.yaml` từ danh mục sản phẩm công khai STADA Việt Nam/Pymepharco, review trước khi chạy Phase 1.
- **muasamcong.mpi.gov.vn có yêu cầu đăng nhập để xem chi tiết giá không** — Phase 0 trả lời bằng khảo sát thực tế, không giả định trước.
- **Máy có Power BI Desktop (Windows) sẵn sàng chưa** — cần cho Phase 5; nếu dùng macOS cần xác nhận phương án (VM/Windows máy khác).
- **Ngân sách Claude API cho Phase 4** — ước tính thấp (vài USD với volume dự kiến) nhưng cần API key sẵn sàng trước khi bắt đầu.

---

## 09. Rủi ro & biện pháp giảm thiểu

| ID | Rủi ro | Mức độ | Biện pháp giảm thiểu |
|---|---|---|---|
| R-01 | Bị chặn IP/anti-bot khi crawl liên tục | Cao | Rate-limit 2–5s, chạy off-peak, header hợp lệ, dừng ngay khi bị chặn thay vì cố lách |
| R-02 | muasamcong yêu cầu đăng nhập mới xem được giá chi tiết | Cao | Verify sớm ở Phase 0; phương án B: dauthau.info free tier + bổ sung thủ công |
| R-03 | Cấu trúc trang đổi làm hỏng selector | Trung bình | Selector tách file riêng, lưu snapshot HTML mẫu, log lỗi rõ ràng để debug nhanh |
| R-04 | Volume thật nhỏ hơn nhiều "triệu dòng" kỳ vọng | Trung bình | Crawl ở mức line-item, gộp nhiều năm/hoạt chất; khi phỏng vấn nói trung thực về scale + nhấn tư duy thiết kế |
| R-05 | Tên thuốc viết tắt/sai chính tả khiến LLM phân loại sai | Trung bình | Spot-check tay ~50 dòng ngẫu nhiên, ghi nhận % đúng, giữ field `confidence` |
| R-06 | Rủi ro pháp lý/ToS khi crawl dữ liệu công khai | Thấp | Chỉ crawl dữ liệu công khai, phi thương mại, tôn trọng robots.txt, disclaimer rõ trong README |

---

## 10. Insight / dashboard cho câu chuyện phỏng vấn

**1. Market Share Erosion Map** — *Objective: mất thị phần theo tỉnh · Persona: RSM · Deal-breaker #3*
% giá trị trúng thầu STADA/Pymepharco vs. top 3 đối thủ theo tỉnh, theo quý — chỉ ra ngay tỉnh nào đang mất thị phần để ưu tiên nguồn lực. Câu chuyện phỏng vấn: "em tự đặt câu hỏi như một Regional Sales Manager sẽ hỏi, rồi thiết kế ngược ra dashboard."

**2. Price Erosion Trend theo nhóm điều trị** — *Objective: cảnh báo price erosion · Persona: Tender KAE · Deal-breaker #2*
Line chart giá trúng thầu trung bình theo nhóm ATC qua thời gian, cảnh báo khi giảm >X% YoY. Đây cũng là nơi thể hiện rõ nhất kỹ thuật xử lý scale (DAX time-intelligence trên fact partition theo năm).

**3. Competitive Bid Benchmark** — *Objective: định giá thầu cạnh tranh · Persona: Tender KAE · Deal-breaker #1 & #3*
Bảng/scatter so giá trúng thầu gần nhất cùng hoạt chất + hàm lượng giữa STADA và đối thủ theo khu vực — công cụ Tender KAE dùng ngay trước khi chốt giá bỏ thầu. Gắn trực tiếp với dữ liệu crawler tạo ra (deal-breaker #1).

---

## 11. Cấu trúc README / tài liệu

1. Tổng quan & động lực dự án (1 đoạn, tóm tắt business objectives)
2. Sơ đồ kiến trúc
3. Tech stack
4. Cấu trúc repo
5. Hướng dẫn chạy từng stage (crawler → etl → ai → db), nhấn idempotent
6. Data dictionary (liên kết `docs/data_dictionary.md`)
7. Star schema + lý do thiết kế (ghi chú scale)
8. Tóm tắt QA/validation report — số liệu thật
9. Screenshot 2 dashboard + mapping persona → business question
10. Giới hạn & rủi ro đã biết (trung thực về volume, về nguồn dữ liệu)
11. Roadmap — sẽ làm gì tiếp nếu có thêm thời gian
12. Ghi chú đạo đức/pháp lý khi crawl dữ liệu công khai

---

*Không có code nào được viết ở bước này — plan thuần túy, chờ xác nhận mục 08 trước khi bắt đầu Phase 0.*
