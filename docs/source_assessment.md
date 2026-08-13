# Source Assessment — muasamcong.mpi.gov.vn

**Ticket:** PI-43 · **Ngày khảo sát:** 2026-08-12 → 2026-08-13 · **Người thực hiện:** khảo sát kỹ thuật, không tương tác UI trực tiếp (xem [Phương pháp](#phương-pháp--giới-hạn))

---

## Tóm tắt điều hành

**Câu hỏi Jira đặt ra:** site muasamcong.mpi.gov.vn có crawl được không, độ khó thế nào, cần chuẩn bị gì trước khi build crawler?

**Trả lời ngắn gọn:** Crawl được, độ khó **Medium** (có thể lên Medium–High nếu captcha bắt buộc ở ô tìm kiếm chính — chưa xác nhận). Không cần tài khoản đăng nhập để đọc dữ liệu. Rủi ro chính không nằm ở access control mà ở **anti-bot** (rate-limit theo IP, chặn headless browser, reCAPTCHA v3 xuất hiện ít nhất ở 1 tính năng).

| Câu hỏi | Trả lời | Độ tin cậy |
|---|---|:---:|
| Cần đăng nhập để xem danh sách/chi tiết gói thầu? | Không | 🟢 CAO |
| Có captcha? | Có, ít nhất ở 1 tính năng phụ — chưa rõ có áp dụng cho ô tìm kiếm chính không | 🟢 CAO (tồn tại) / 🔴 THẤP (phạm vi áp dụng) |
| Có bị chặn tốc độ (rate-limit)? | Có, theo IP là giả thuyết khớp nhất, ngưỡng ước lượng ~6-8 request/~3-4 phút | 🟡 TRUNG BÌNH |
| Có API nội bộ dùng được thay vì trình duyệt? | Có 6 endpoint xác định được từ source code, chưa gọi thử response thật | 🟢 CAO (path/payload) / 🟡 (response) |
| Biết được tổng khối lượng dữ liệu (số gói thầu)? | Chưa — gap cần lấp đầu Phase 1 | — |

**Khuyến nghị:** đi theo 2 giai đoạn — Phase 1 dùng Selenium (không headless) với tần suất request thấp để vừa lấy dữ liệu vừa trả lời các câu hỏi còn mở; Phase 2 chuyển dần các bước không cần captcha sang gọi thẳng HTTP API để tăng tốc. Chi tiết ở mục [Chiến lược Crawl](#chiến-lược-crawl) và [Kết luận](#kết-luận).

---

## Phương pháp & Giới hạn

**Cách khảo sát:** `curl` (HTTP request thô, không chạy JS) + đọc trực tiếp inline Vue component source có sẵn trong HTML server-render + thử headless Selenium (Chrome 151, không ổn định ở môi trường này) + 1 URL trang chi tiết thật lấy qua Google index.

Lý do không dùng DevTools trình duyệt tương tác như đề xuất ban đầu trong Jira: môi trường khảo sát không có UI trình duyệt tương tác, và headless Chrome vừa bị WAF chặn vừa render không ổn định (xem mục [Anti-bot](#anti-bot--captcha)). Ưu điểm của cách đã dùng: lấy được endpoint/payload/pagination **thật từ source code**, không suy đoán, không cần chạy JS.

**Giới hạn còn lại (thật, cần biết trước khi dùng báo cáo này):**

1. Chưa gọi trực tiếp được endpoint POST nào (cần token reCAPTCHA hợp lệ; gọi sai có rủi ro ăn thêm rate-limit) → Content-Type response, cấu trúc `page.totalElements`, và toàn bộ field response đầy đủ đều **suy ra từ code, chưa xác nhận bằng response thật**.
2. Chưa xác nhận được ô tìm kiếm **chính** (trên `?render=search`) có dùng đúng endpoint `smart/search` hay không — endpoint này trích từ 1 tính năng phụ (tra cứu theo `contractCode`) ở trang chi tiết. Cùng dùng chung index Elasticsearch nên khả năng cao là dùng chung, nhưng chưa quan sát trực tiếp.
3. Data volume và `pageSize` mặc định của UI chính chưa xác định được.

**Việc cần làm đầu Phase 1** (bắt buộc, không phải "cho có"): dùng Selenium không-headless (Xvfb), quan sát Network tab thật khi bấm nút search chính, để xác nhận (1) đúng endpoint `smart/search`, (2) response thật có `totalElements` không, (3) `pageSize` mặc định UI, (4) lấy token reCAPTCHA v3 hợp lệ qua hành vi trình duyệt thật để gọi thử endpoint chi tiết và xác nhận field response khớp với suy luận ở mục [Data Fields](#data-fields).

**Chú giải Confidence Level (áp dụng toàn bộ báo cáo):**

| Ký hiệu | Ý nghĩa |
|---|---|
| 🟢 **CAO** | Thực nghiệm trực tiếp trong khảo sát này — tự gửi request thật, tự đọc response/header thật, hoặc quan sát hành vi thật. |
| 🟡 **TRUNG BÌNH** | Đọc trực tiếp source code thật (JS/HTML server trả về) — endpoint/tên biến là thật, nhưng chưa gọi thử để xác nhận hành vi runtime. |
| 🔴 **THẤP** | Suy luận có cơ sở (pattern chung, kinh nghiệm hệ thống tương tự) — chưa có bằng chứng trực tiếp, coi là giả thuyết. |

---

## 1. Khả năng truy cập (không cần login)

### 1.1 robots.txt

```
User-Agent: *
Disallow:
```

Không path nào bị chặn — allow-all. 🟢 CAO.

### 1.2 Trang tìm kiếm gói thầu

**URL:** `https://muasamcong.mpi.gov.vn/contractor-selection?render=search`

- HTTP 200, không redirect sang trang đăng nhập.
- Form tìm kiếm/lọc render sẵn trong HTML — truy cập được không cần đăng nhập.
- Có phát hiện 1 template lỗi ẩn ("Phiên đăng nhập của bạn đã hết hạn...") + xử lý `401 Unauthorized`, nhưng đây là modal dùng chung toàn portal cho các hành động **cần tài khoản** (nộp hồ sơ, thanh toán), **không phải** bằng chứng trang search bị khoá.

**Kết luận: không yêu cầu đăng nhập.** 🟢 CAO.

### 1.3 Trang chi tiết giá trúng thầu

**URL thật (xác nhận qua Google index):**

```
/en/web/guest/contractor-selection
  ?p_p_id=egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2
  &_egpportalcontractorselectionv2_WAR_egpportalcontractorselectionv2_render=detail-v2
  &type=es-notify-contractor
  &stepCode=reoffer-price-step-1
  &id=<uuid>&notifyId=<uuid>
  &processApply=LDT&bidMode=1_MTHS
  &notifyNo=IB2500633776&planNo=PL2500351299
  &step=tbmt&isInternet=1&bidForm=CGTTRG
```

`render=detail-v2` + `stepCode=reoffer-price-step-1` map đúng "bước chào lại giá" — đây chính là trang giá chi tiết Jira yêu cầu khảo sát.

Lần thử đầu bị chặn ở tầng TLS (đúng lúc site đang rate-limit khảo sát — xem [mục Rate Limit](#3-rate-limit)), không phải do thiếu đăng nhập. Sau khi rate-limit hết, retry lại 1 lần và lấy được kết quả thật:

- `HTTP 200`, không mang cookie/session, không redirect login, response 454KB.
- Response phản ánh lại đúng `notifyNo=IB2500633776`/`planNo=PL2500351299` mà mình gửi — xác nhận server xử lý theo `id`/`notifyId` thật, không phải trang tĩnh chung chung.
- Có label/template giá thật (`Giá dự thầu`, `{{item?.reofferPrice | currency}}`...) — đây là Vue template binding, giá trị số thật populate lúc client gọi API (cùng kiến trúc mục 2.1), không phải bị che.
- Modal "hết phiên đăng nhập" vẫn xuất hiện 1 lần trong code (ternary JS) — cùng pattern shared-modal ở mục 1.2, không phải login wall.

**Kết luận: trang chi tiết cũng không yêu cầu đăng nhập để load.** 🟢 CAO. Giá trị số cụ thể chỉ render sau khi Vue gọi API POST client-side — muốn lấy số liệu thật cần Selenium hoặc gọi thẳng API (mục [Chiến lược Crawl](#chiến-lược-crawl)), đây là quyết định kỹ thuật riêng, không còn liên quan câu hỏi "có cần login".

### 1.4 Cơ chế xác thực (Session, không phải login)

Header response thật (`curl -D -`):

```
Set-Cookie: COOKIE_SUPPORT=true; HttpOnly
Set-Cookie: GUEST_LANGUAGE_ID=vi_VN; domain=.mpi.gov.vn; HttpOnly
Set-Cookie: JSESSIONID=<session-id>.dc-app1-02
Set-Cookie: NSC_WT_QSE_QPSUBM_NTD_NQJ=<opaque>; secure; httponly
```

- `JSESSIONID` — cookie session chuẩn Liferay, cấp ngay cả khi không đăng nhập (guest session). Không có `Authorization: Bearer`/JWT ở header. 🟢 CAO.
- `NSC_WT_QSE_QPSUBM_NTD_NQJ` — dạng cookie NetScaler/F5 persistence (load-balancer sticky session). Khả năng liên quan tới lớp WAF/anti-bot ở mục 3 là hợp lý nhưng chưa chứng minh trực tiếp 2 thứ là cùng 1 hệ thống. 🟡 TRUNG BÌNH.
- Endpoint `smart/search` có thêm lớp reCAPTCHA v3 token theo từng request (mục 2.3) — không phải cookie-based, mà theo từng lần gọi.

**Kết luận: không cần login, nhưng có session (JSESSIONID + LB cookie) cấp cho guest.** 🟢 CAO.

**Khuyến nghị (chưa phải kết luận đã kiểm chứng):** crawler nên duy trì cookie jar xuyên suốt phiên (giống `requests.Session()`) — đây là thực hành chuẩn cho site Liferay nói chung. Khảo sát này gọi `curl` không giữ cookie giữa các lần và sau đó bị rate-limit; có thể việc thiếu cookie nhất quán góp phần khiến hành vi trông khả nghi hơn, nhưng chưa tách biệt được nguyên nhân (rate-limit có thể xảy ra thuần theo IP). 🔴 THẤP — xem [Open Questions #10](#open-questions).

---

## 2. Kiến trúc kỹ thuật

### 2.1 Nền tảng

- Cổng chạy trên **Liferay Portal** (`frontend-js-aui-web`, `liferay/...` script paths, URL kiểu `/o/<module>/...`).
- Widget tìm kiếm/nộp hồ sơ dùng **Vue 2 + Axios**, gọi API backend POST tới namespace `/o/egp-portal-contractor-selection-v2/services/...`.
- Trang **không phải SPA rỗng** — HTML trả về từ server đã có nội dung thật (~41KB text); phần tìm kiếm/lọc là Vue "island" nhúng vào portal shell, không phải toàn trang render bằng JS.
- **Ý nghĩa cho crawler:** Selenium là lựa chọn an toàn vì có phần render động qua Vue + gọi API nội bộ. Có khả năng gọi thẳng API POST nếu reverse-engineer được params — quyết định này thuộc Phase 1/2, xem [Chiến lược Crawl](#chiến-lược-crawl).

### 2.2 Endpoint API thật (trích từ source code)

Tất cả endpoint dưới đây trích trực tiếp từ inline `<script>` Vue component có trong HTML server-render của trang chi tiết — `curl` thường lấy được, không cần chạy JS. Base: `https://muasamcong.mpi.gov.vn`.

**Cách đọc bảng:** cột Path/Payload là 🟢 CAO (đọc nguyên văn từ code thật). Cột Response là 🟡 TRUNG BÌNH (suy luận từ cách code dùng biến — **không endpoint nào trong bảng đã được gọi thử trực tiếp**, vì cần token reCAPTCHA + session/CSRF đúng, và gọi sai có rủi ro ăn thêm rate-limit). Coi cột Response là "dự đoán có căn cứ", không phải "đã xác nhận".

| # | Endpoint | Method | Payload thật | Auth thêm | Response (suy luận, chưa gọi thử) |
|---|---|---|---|---|---|
| 1 | `/o/egp-portal-contractor-selection-v2/services/smart/search` | POST | `[{"pageSize":N,"pageNumber":N,"query":[{"index":"es-contractor-selection","keyWord":"...","matchType":"exact\|...","matchFields":["contractCode",...],"filters":[{"fieldName":"type","searchType":"in","fieldValues":[...]}]}]}]` | Query param `?token=<reCAPTCHA v3 token>` — gọi kèm token này (🟢), bắt buộc/enforce ở backend hay không chưa rõ (🔴, mục 3.1) | `response.data.page.content[]`, item có `id, notifyId, inputResultId, bidOpenId, techReqId, stepCode, isInternet, processApply, bidMode, notifyNo, planNo, pno, contractCode` — nếu đúng, đây là nguồn ID để build URL trang chi tiết |
| 2 | `/o/egp-portal-contractor-selection-v2/services/contractor-input-result/get` | POST | `{"id": inputResultId}` | Không thấy trong code đã đọc (không có nghĩa chắc chắn không cần) | Suy luận từ tên field template Vue (`bideContractorInputResultDTO.reofferPriceFinal`...): nhiều khả năng chứa giá trúng thầu. **Ứng viên endpoint quan trọng nhất** — cần xác nhận Phase 1 |
| 3 | `/o/egp-portal-contractor-selection-v2/services/lcnt_tbmcgtt_hsmt` | POST | `{"id": notifyId, "processApply": "LDT"}` | Không thấy | Chưa map field chi tiết — suy luận: hồ sơ mời/chào giá gói thầu (từ tên endpoint) |
| 4 | `/o/egp-portal-contractor-selection-v2/services/lcnt_tbmt_kn` | POST | `{"notifyNo": ..., "processApply": ..., "type": "CGTTRG"}` | Không thấy | Suy luận: field `biduPetitionContractorVersionDTOList` (danh sách kiến nghị) |
| 5 | `/o/egp-portal-contractor-selection-v2/services/econsign/contract-info/list-contract-for-po` | POST (`?token=<token riêng>`) | `{"notifyNo": ...}` | Có `?token=` — chưa rõ cùng loại reCAPTCHA hay token khác | Suy luận: thông tin hợp đồng |
| 6 | `/o/egp-portal-contractor-selection-v2/services/check-mail`, `/services/sub` | POST | Chưa trích được payload cụ thể | — | — |

**Content-Type:** suy ra là JSON từ cách code dùng (`response.data.page.content`, `response.data?.field`), nhưng chưa xem trực tiếp response thật nào. 🟡 TRUNG BÌNH — cần xác nhận Phase 1.

### 2.3 Pagination

```json
{"pageSize": 1, "pageNumber": 0, "query": [...]}
```

- Param **`pageSize`** + **`pageNumber`** (0-indexed, không phải `page=1`) — tên param đọc nguyên văn từ code thật. 🟢 CAO.
- Code dùng `response.data.page.content`, pattern giống Spring Data `Pageable`/Elasticsearch wrapper. Suy đoán response cũng kèm `page.totalElements`/`page.totalPages`, nhưng code đã đọc **không tham chiếu trực tiếp 2 field này** — có thể sai, cần xác nhận response thật ở Phase 1. 🔴 THẤP.
- Ví dụ trong code dùng `pageSize: 1` cho tra cứu 1 kết quả cụ thể (theo `contractCode`, exact match) — **không phải** giá trị dùng khi crawl toàn bộ. Giá trị thật ở ô tìm kiếm chính chưa xác nhận được (component đó không nằm trong HTML tĩnh đã tải).

---

## 3. Anti-bot & Captcha

Đây là rủi ro chính của dự án — không phải access control. Quan sát được **ít nhất 3 dấu hiệu phòng thủ khác nhau**; chưa chứng minh được đây là 3 hệ thống độc lập hay cùng 1 WAF chỉ khác kiểu phát hiện.

### 3.1 reCAPTCHA v3

Trang chi tiết nhúng script `https://www.google.com/recaptcha/api.js?render=<siteKey>` (siteKey thật `6LeQH9gpAAAAAPpzhkvYzd8QCrP-QyLVRSw_SD9U`) và gọi `grecaptcha.execute(siteKey, {action:'submit'}).then(token => axios.post(elasticSearch+"?token="+token, ...))`.

**Sự tồn tại của đoạn code này là chắc chắn** — đọc nguyên văn trong response HTML. 🟢 CAO. Hai điều sau vẫn là giả thuyết chưa kiểm chứng:

1. Server backend có thực sự **enforce/reject** request thiếu token hay không — code frontend gọi captcha không chứng minh backend validate nghiêm ngặt. 🔴 THẤP.
2. Đoạn code này nằm trong 1 tính năng phụ (tra cứu nhanh theo `contractCode`) — chưa quan sát được ô tìm kiếm **chính** có gọi cùng cơ chế hay không, vì component đó không nằm trong HTML tĩnh đã tải. 🔴 THẤP.

Không phát hiện widget captcha tĩnh trên HTML shell của trang chủ/trang search — bản thân trang search không nhúng recaptcha trực tiếp. 🟢 CAO.

### 3.2 Chặn theo fingerprint trình duyệt tự động

Headless Chrome (Selenium 4.47, `--headless=new`) vào trang search → server trả HTML lỗi generic (`<title>Error</title>`, "This page can't be displayed...", 637 byte) thay vì nội dung thật mà `curl` cùng URL nhận được cùng lúc. Hiện tượng quan sát trực tiếp. 🟢 CAO. Cơ chế nội bộ (rule WAF cụ thể nào) là suy luận, chỉ biết kết quả chứ không biết nguyên nhân chính xác. 🔴 THẤP.

### 3.3 Rate limit (reset kết nối)

**⚠️ n=1** — một lần bị chặn duy nhất, quan sát trong lúc khảo sát, không phải thí nghiệm lặp lại có kiểm soát. Không lặp lại thêm để tránh làm phiền hệ thống production của cơ quan nhà nước. Coi số liệu dưới đây là 1 điểm dữ liệu quan sát được, không phải ngưỡng đã đo chính xác.

**Hiện tượng:** sau ~6-8 request (mix `curl` + headless Chrome) trong ~3-4 phút, server reset kết nối TLS ngay ở Client Hello (`Recv failure: Connection reset by peer`) cho mọi request tiếp theo, kể cả `/robots.txt` đã pass trước đó. Hết block sau khoảng ~1 giờ. 🟢 CAO cho hiện tượng.

**Theo IP, Connection, hay Session?** Suy luận loại trừ (🟡 TRUNG BÌNH — logic hợp lý nhưng dựa trên 1 lần quan sát):

- Mỗi lần `curl` là 1 TCP/TLS connection mới, stateless — vẫn bị chặn sau khi tích lũy đủ request → loại trừ "theo 1 connection".
- Không cookie/session nào được thiết lập trước khi bắt đầu bị chặn → loại trừ "theo session/cookie".
- `/robots.txt` (không liên quan search/detail) cũng bị chặn cùng lúc, cùng nguồn → **theo IP nguồn** là cách giải thích khớp nhất.
- **Giới hạn:** không loại trừ được khả năng WAF dùng kết hợp nhiều tín hiệu (IP + TLS/JA3 fingerprint + User-Agent + tốc độ) — `curl` và headless Chrome có fingerprint khác nhau nhưng chạy cùng IP, nên không tách biệt được 2 giả thuyết bằng dữ liệu đã có.

**Con số quan sát được (🔴 THẤP về độ chính xác):**
- ~6-8 request trong ~3-4 phút → bắt đầu bị chặn (đếm gần đúng theo nhật ký thao tác, không phải log server).
- Thời gian chặn: ≥15 giây vẫn còn chặn, ~1 giờ sau đã hết (2 mốc đo được thật). Ngưỡng chính xác nằm đâu đó trong khoảng (15s, ~1h).
- Khuyến nghị vận hành (không phải số đã đo): ≤ 2 request/phút/IP là điểm khởi đầu thận trọng, cần tinh chỉnh bằng dữ liệu thật khi crawler chạy Phase 1.

### 3.4 Retry Strategy đề xuất

Dựa trên 1 điểm dữ liệu ở mục 3.3 — coi đây là điểm khởi đầu để tinh chỉnh, không phải cấu hình cuối cùng.

- **Phát hiện bị chặn:** connection reset ở tầng TLS, không phải HTTP 4xx/5xx — retry logic phải bắt exception ở tầng network/TLS, không chỉ check status code.
- **Backoff — dài hơn chuẩn thông thường** vì thời gian chặn đo được (~1 giờ) lớn hơn nhiều so với backoff giây/phút hay dùng:
  1. Lần 1: dừng 5 phút
  2. Lần 2: dừng 15 phút
  3. Lần 3: dừng 30 phút
  4. Lần 4 trở đi: dừng 60 phút, lặp lại mức này (không tăng vô hạn) + log/cảnh báo cho người vận hành
- **Circuit breaker:** sau 2 lần bị chặn liên tiếp trong cùng phiên, tạm dừng toàn bộ crawler (không chỉ request lỗi), cần xác nhận thủ công hoặc lịch chạy lại thay vì auto-retry vô hạn.
- **Rate limit chủ động (phòng ngừa):** giữ ≤ 2 request/phút/IP, có jitter ngẫu nhiên giữa các request để tránh pattern dễ nhận diện.

---

## 4. Data Volume & Data Fields

### 4.1 Data Volume — chưa xác định (gap thật)

- Không tìm thấy counter/thống kê tổng số gói thầu công khai trên trang chủ hay trang search (HTML tĩnh không có).
- Cách lấy được ở Phase 1 (đề xuất, chưa thực hiện): gọi 1 lần endpoint `smart/search` với `pageSize` nhỏ + filter rỗng/rộng nhất, đọc `page.totalElements` (nếu tồn tại) trong response thật — nhưng cần giải quyết reCAPTCHA token trước, nên ngoài scope khảo sát tĩnh PI-43.
- **Chưa có input để estimate crawl time** — follow-up bắt buộc đầu Phase 1.

### 4.2 Data Fields (nguồn: endpoint #2 — `contractor-input-result/get`)

| Field | Nguồn (object.field trong response) | Ghi chú |
|---|---|---|
| Mã thông báo (notifyNo) | `bideContractorInputResultDTO.notifyNo` | Định danh gói thầu |
| Tên gói thầu (bidName) | `bideContractorInputResultDTO.bidName` | |
| Thời gian thực hiện (cperiod) | `bideContractorInputResultDTO.cperiod` | |
| Giá dự thầu (reofferPrice) | `item.reofferPrice` (mảng contractor) | Giá trước khi finalize |
| Giá trúng thầu cuối cùng (reofferPriceFinal) | `contractorsResultAll[0].reofferPriceFinal` / `listContractorKq[0].reofferPriceFinal` | **Field quan trọng nhất — giá trúng thầu thật** |
| Tên nhà thầu (contractorName) | `con.contractorName` / `item.contractorName` | |
| Mã nhà thầu (contractorCode) | `con.contractorCode` / `item.contractorCode` | |
| Mã phần/lô (lotNo, lotName) | `con.lotNo`, `con.lotName` | Gói thầu chia nhiều lô |
| Đơn vị tính giá (bidPriceUnit) | `bidpPlanDetailDTO.bidPriceUnit` | |
| Kế hoạch (planNo) | query param, echo lại trong response | Liên kết ngược về kế hoạch lựa chọn nhà thầu |

Bảng chưa đầy đủ 100% field (response thật đầy đủ chỉ thấy được khi gọi API trực tiếp), nhưng đủ để Phase 1 định hình schema DB ban đầu.

---

## 5. Chiến lược Crawl

**Option A — Gọi thẳng HTTP API đã reverse-engineer (mục 2.2)**
- Ưu điểm: nhanh, ít RAM/CPU, dễ scale song song có kiểm soát, không bị lớp chặn headless-fingerprint (mục 3.2) vì không dùng trình duyệt.
- Nhược điểm: cần giải reCAPTCHA v3 cho endpoint search (2Captcha/Anti-Captcha, hoặc tự tính token qua trình duyệt thật rồi tái sử dụng), cần duy trì cookie/session đúng, dễ vỡ nếu backend đổi payload/endpoint (không có hợp đồng API chính thức).

**Option B — Selenium (browser thật, có UI hoặc Xvfb, KHÔNG headless)**
- Ưu điểm: tự chạy JS + tự giải reCAPTCHA v3 qua hành vi thật (score cao hơn, giống người dùng thật), né được lớp chặn headless-fingerprint vì không bật cờ headless.
- Nhược điểm: chậm hơn Option A nhiều, tốn RAM/CPU hơn, khó scale song song lớn, môi trường server cần Xvfb.

**Đề xuất theo giai đoạn** (khác với giả định ban đầu trong PLAN.md — Selenium-only):

- **Phase 1 (khởi động, ưu tiên ổn định):** Selenium không-headless, tần suất request rất thấp (theo mục 3.3-3.4), vừa lấy dữ liệu vừa quan sát thêm hành vi anti-bot thật, xác nhận lại pagination/volume ở mục 2.3/4.1.
- **Phase 2 (khi đã hiểu rõ luồng captcha + đo lại rate-limit chính xác hơn):** chuyển dần sang Option A cho phần không cần captcha (endpoint #2-6: lấy chi tiết theo ID đã biết) — chỉ dùng Selenium/giải captcha riêng cho bước search/lấy danh sách ID (endpoint #1). Mô hình lai: Selenium để "mở khóa" ID, HTTP API để lấy chi tiết hàng loạt.

### Risk Assessment

| Risk | Impact | Mitigation |
|---|---|---|
| TLS reset (rate-limit theo IP, mục 3.3) | Crawler dừng đột ngột, mất session giữa chừng | Circuit breaker + backoff dài (mục 3.4), theo dõi request/phút chủ động |
| reCAPTCHA v3 có khả năng bắt buộc cho search (🟡, mục 3.1 — chưa xác nhận áp dụng cho search chính) | Nếu đúng: không lấy được danh sách ID gói thầu mới nếu không giải được captcha | Selenium không-headless cho bước search, hoặc dịch vụ giải captcha trả phí; xác nhận [Open Questions #2-3](#open-questions) trước khi đầu tư hạ tầng giải captcha |
| Headless-fingerprint block (mục 3.2) | Selenium headless bị chặn ngay, khác hẳn hành vi mong đợi khi test local | Luôn dùng Selenium không-headless (Xvfb) trong production, không dùng `--headless` |
| Payload/endpoint API thay đổi (không có hợp đồng chính thức, mục 2.2) | Crawler HTTP API (Option A) vỡ đột ngột không báo trước | Theo dõi lỗi phân loại theo response shape, có test smoke chạy định kỳ phát hiện sớm |
| Chưa biết data volume thật (mục 4.1) | Không estimate được thời gian crawl toàn bộ, dễ lên kế hoạch sai | Đo `page.totalElements` ngay đầu Phase 1 trước khi commit timeline |
| Session/cookie hết hạn giữa phiên dài (JSESSIONID, mục 1.4) | Request giữa chừng bị lỗi vì session cũ | Refresh session định kỳ (GET lại trang gốc) trước khi hết hạn, không đợi lỗi mới refresh |

### Crawlability Score

Bảng tóm tắt để đọc nhanh — **cột Confidence là phần quan trọng nhất**, đừng chỉ đọc cột Đánh giá.

| Tiêu chí | Đánh giá | Confidence | Ghi chú |
|---|---|:---:|---|
| Login | Không | 🟢 CAO | Xác nhận thật cho cả search + detail (mục 1.2, 1.3) |
| JS bắt buộc để xem dữ liệu số thật | Có | 🟢 CAO | Giá trị số qua Vue/API POST, HTML tĩnh chỉ có template rỗng |
| API nội bộ | 6 endpoint path/payload thật (mục 2.2) | 🟢 CAO (path/payload) 🟡 (response) | Path/payload đọc từ code thật; response là suy luận, chưa gọi thử. Không có hợp đồng API chính thức/docs công khai |
| Pagination | `pageSize`/`pageNumber`, 0-indexed | 🟢 CAO (tên param) 🔴 (totalElements) | Tên param thật; có `totalElements`/`totalPages` hay không là suy đoán |
| Captcha | reCAPTCHA v3 tồn tại trong code (1 tính năng phụ) | 🟢 CAO (code tồn tại) 🔴 (bắt buộc/enforce, áp dụng ô search chính) | Xem mục 3.1 + Open Questions — đừng đọc thành "search chính chắc chắn có captcha" |
| Anti-bot khác | Có ≥2 dấu hiệu (headless-block, connection reset) | 🟢 CAO (hiện tượng) 🟡 (nguyên nhân/cơ chế) | Xem mục 3.2, 3.3 |
| Session/Auth | Cookie-based (JSESSIONID), không cần login | 🟢 CAO | Header thật (mục 1.4) |
| Data volume | Chưa xác định | — | Gap thật, chưa có dữ liệu (mục 4.1) |
| Rate limit ngưỡng cụ thể | ~6-8 req/~3-4 phút (n=1) | 🔴 THẤP | 1 lần quan sát, không phải đo lặp lại (mục 3.3) |
| Khả thi bằng Selenium | Được, khuyến nghị không-headless | 🟡 TRUNG BÌNH | Headless bị chặn 1 lần quan sát; chưa test non-headless thật ở site này |
| Khả thi bằng HTTP API thuần | Có khả năng cho phần chi tiết; search cần giải captcha | 🟡 TRUNG BÌNH | Dựa trên suy luận từ code, chưa test runtime |
| **Crawl Difficulty tổng thể** | **Medium** (có thể lên Medium–High tùy mức độ enforce captcha thật) | 🟡 TRUNG BÌNH | Cao hơn đánh giá "Medium" thuần trước đó vì có dấu hiệu captcha + anti-bot, nhưng chưa đủ dữ liệu runtime để khẳng định chắc "High" |

---

## 6. Nguồn đối chiếu — dauthau.info (PI-44)

**Ticket:** PI-44 · **Ngày khảo sát:** 2026-08-13 · **Phương pháp:** đăng nhập thủ công tài khoản free tier (nền tảng "Hệ sinh thái Đấu Thầu" — DauThau.info / DauThau.Net / DauGia.Net dùng chung 1 tài khoản), duyệt UI qua trình duyệt thật, không dùng `curl`/API trực tiếp.

**Mục đích khảo sát:** xác định dauthau.info có dùng được làm phương án dự phòng (R-02, PLAN.md) nếu muasamcong.mpi.gov.vn bị chặn hoặc yêu cầu login giữa chừng Phase 1 hay không.

### 6.1 Field mở với tài khoản free tier

Xem tại trang chi tiết 1 gói thầu (`Mã TBMT: IB2600229367-00`, "Kiểm toán Báo cáo quyết toán dự án hoàn thành"):

| Field | Trạng thái |
|---|---|
| Mã TBMT, Số KHLCNT | Mở |
| Tên gói thầu | Mở |
| Chủ đầu tư | Mở |
| Hình thức đấu thầu | Mở |
| **Giá gói thầu** (số VND cụ thể) | Mở |
| Ngày đăng tải | Mở |
| Loại hợp đồng, số lượng túi hồ sơ | Mở |
| Lĩnh vực | Mở |
| Số quyết định phê duyệt + nội dung quyết định | Mở |

**Kết luận (🟢 CAO — quan sát trực tiếp, tài khoản free tier thật):** toàn bộ thông tin **mô tả gói thầu** (trước khi có kết quả) xem được đầy đủ, không bị khoá.

### 6.2 Field khoá sau paywall

Kiểm tra ở 2 danh mục kết quả riêng biệt trong menu "ĐẤU THẦU":

- **"Kết quả lựa chọn nhà thầu"** (mua sắm hàng hoá/dịch vụ — cùng nhóm với muasamcong) — toàn bộ danh sách nhiều dòng, cột **"Trúng thầu"** hiện dòng cố định: *"Thông tin chỉ hiển thị cho tài khoản trả phí!"* thay vì tên nhà thầu/giá trúng thầu. Khoá ngay ở list view, không cần mở chi tiết mới thấy khoá.
- **"Kết quả lựa chọn nhà đầu tư"** (dự án PPP/đầu tư) — cùng pattern y hệt, cùng dòng chữ khoá.

**Kết luận (🟢 CAO — quan sát trực tiếp, 2 danh mục riêng, nhiều dòng khác nhau, cùng pattern):** **kết quả trúng thầu (tên nhà thầu + giá trúng thầu) bị khoá hoàn toàn với tài khoản free tier** — đây đúng là field quan trọng nhất mà PI-43 xác định là mục tiêu chính của crawler (`reofferPriceFinal`, mục 4.2).

**Ghi chú thêm (🟡 TRUNG BÌNH — quan sát 1 lần, chưa test hết mọi loại gói thầu):** trang **"Kết quả sơ tuyển nhà thầu"** (vòng sơ tuyển, khác với kết quả trúng thầu cuối) lại **không bị khoá** — tên nhà thầu qua sơ tuyển hiện đầy đủ. Gợi ý paywall chỉ chặn đúng bước "kết quả cuối/giá trúng thầu", không chặn toàn bộ dữ liệu đấu thầu.

### 6.3 Vai trò của dauthau.info cho crawler

**Kết luận:** dauthau.info dùng được với vai trò **đối chiếu** (cross-reference), **không dùng được** với vai trò **phương án dự phòng thay thế** cho mục tiêu chính của crawler.

- **Dùng tốt để đối chiếu:** thông tin mô tả gói thầu (tên, chủ đầu tư, giá gói thầu dự toán, ngày đăng, hình thức, quyết định phê duyệt) — có thể dùng validate chéo dữ liệu crawl được từ muasamcong, hoặc bổ sung field mà muasamcong không có sẵn ở dạng dễ đọc.
- **Không dùng được làm dự phòng cho phần quan trọng nhất:** field mục tiêu chính của toàn bộ dự án — **giá trúng thầu cụ thể (`reofferPriceFinal`)** — bị khoá sau paywall trên dauthau.info với free tier. Nếu muasamcong bị chặn giữa chừng Phase 1, dauthau.info **không thể** thay thế để lấy được số liệu giá trúng thầu; chỉ nâng cấp tài khoản trả phí (chưa rõ chi phí/gói nào đủ) mới mở được, nằm ngoài scope kỹ thuật của crawler.
- **Ý nghĩa cho R-02 (PLAN.md):** rủi ro "muasamcong bị chặn/yêu cầu login" **vẫn chưa có phương án dự phòng đã xác nhận** cho phần giá trúng thầu — cần note lại R-02 là gap còn mở, không nên coi dauthau.info là giải pháp an toàn đã kiểm chứng.

---

## Open Questions

Câu hỏi **chưa trả lời được** trong khảo sát này — liệt kê rõ để Phase 1 biết cần verify gì trước khi dựa vào báo cáo này để thiết kế crawler.

| # | Câu hỏi mở | Vì sao chưa trả lời được | Mức ảnh hưởng nếu sai |
|---|---|---|---|
| 1 | Endpoint #2 (`contractor-input-result/get`) có thật sự trả về field `reofferPriceFinal` như suy luận không? | Chưa gọi thử trực tiếp (cần session/CSRF đúng) | Cao — endpoint "quan trọng nhất"; nếu sai, toàn bộ Data Fields (mục 4.2) phải viết lại |
| 2 | reCAPTCHA v3 có bắt buộc cho MỌI lần gọi `smart/search`, kể cả từ ô tìm kiếm chính, hay chỉ riêng tính năng tra cứu theo `contractCode`? | Code reCAPTCHA chỉ thấy trong 1 component phụ; component search chính không nằm trong HTML tĩnh đã tải | Cao — quyết định trực tiếp Chiến lược Crawl (mục 5): nếu search chính không cần captcha, Option A khả thi hơn nhiều |
| 3 | Server backend có thật sự reject request thiếu/sai token reCAPTCHA không, hay chỉ là biện pháp phòng ngừa phía frontend? | Chưa thử gọi thiếu token để xem response | Trung bình — ảnh hưởng độ ưu tiên đầu tư giải captcha |
| 4 | Ngưỡng rate-limit chính xác (request/phút) là bao nhiêu? | Chỉ 1 lần quan sát (n=1), không lặp lại để tránh làm phiền site | Cao — ảnh hưởng trực tiếp tốc độ crawl và Retry Strategy (mục 3.4) |
| 5 | Rate-limit theo thuần IP, hay kết hợp thêm TLS/JA3 fingerprint, User-Agent, tốc độ request? | `curl` và headless Chrome có fingerprint khác nhau nhưng cùng IP, không tách biệt được 2 giả thuyết | Trung bình — nếu fingerprint-based, đổi User-Agent/client có thể né được; nếu thuần IP thì không |
| 6 | Response của `smart/search` có field `page.totalElements`/`page.totalPages` không? | Code đã đọc không tham chiếu trực tiếp 2 field này | Cao — cần thiết để estimate Data Volume (mục 4.1) và crawl time |
| 7 | `pageSize` mặc định UI chính (không phải giá trị `1` dùng cho tra cứu phụ) là bao nhiêu? | Component UI chính không nằm trong HTML tĩnh | Trung bình — ảnh hưởng thiết kế batch size khi crawl |
| 8 | Component search chính có gọi đúng endpoint `smart/search` hay 1 endpoint khác chưa phát hiện? | Cùng lý do câu 2 | Cao — giả định nền tảng cho toàn bộ Network Analysis liên quan tới search |
| 9 | Content-Type thật của response các endpoint POST có đúng là JSON như suy luận không? | Chưa gọi thử endpoint nào | Thấp-Trung bình — nhiều khả năng đúng (pattern code rõ ràng), nhưng chưa xác nhận |
| 10 | Việc `curl` không giữ cookie giữa các lần gọi có phải là 1 nguyên nhân góp phần bị rate-limit không? | Không có thí nghiệm đối chứng (gọi có giữ cookie vs không) | Thấp — chỉ ảnh hưởng cách diễn giải nguyên nhân, không ảnh hưởng khuyến nghị (vẫn nên giữ cookie dù lý do gì) |

**Cách giải quyết đề xuất cho cả 10 câu hỏi:** 1 buổi làm việc đầu Phase 1 với Selenium không-headless (Xvfb), quan sát tab Network thật khi thao tác trực tiếp trên UI (search, xem chi tiết) — xem mục [Phương pháp & Giới hạn](#phương-pháp--giới-hạn).

---

## Kết luận

**1. Site crawl được, và không cần vượt qua rào cản đăng nhập.** Cả trang tìm kiếm lẫn trang chi tiết giá trúng thầu đều trả dữ liệu cho khách vãng lai (guest session qua `JSESSIONID`, không cần tài khoản). Đây là kết luận có độ tin cậy cao nhất trong toàn báo cáo — xác nhận bằng request thật, không suy đoán.

**2. Rào cản thật sự không phải access control, mà là anti-bot.** Ba lớp phòng thủ độc lập hoặc liên quan tới nhau đã quan sát được: reCAPTCHA v3 (ít nhất ở 1 tính năng), chặn theo fingerprint trình duyệt tự động (headless Chrome bị từ chối ngay), và reset kết nối theo IP sau ~6-8 request/vài phút. Mức độ nghiêm trọng thật của rào cản này phụ thuộc vào 1 câu hỏi chưa trả lời: **captcha có bắt buộc cho ô tìm kiếm chính hay không** — đây là câu hỏi quan trọng nhất cần giải trước khi commit hạ tầng.

**3. Kiến trúc kỹ thuật đã đủ rõ để thiết kế crawler.** 6 endpoint API nội bộ, cấu trúc pagination, và field dữ liệu cần lấy (đặc biệt `reofferPriceFinal` — giá trúng thầu) đều đã xác định từ source code thật. Phần chưa xác nhận (response thật, `totalElements`, Content-Type) là rủi ro thấp — thường đúng như suy luận theo pattern code, chỉ cần 1 lần gọi thử thật để chốt.

**4. Data volume là gap duy nhất chưa có hướng giải quyết rõ ràng trong khảo sát tĩnh** — cần gọi API thật (có captcha) mới đo được, nên nằm ngoài scope PI-43.

**5. Không có phương án dự phòng đã kiểm chứng cho rủi ro R-02 (muasamcong bị chặn).** Khảo sát dauthau.info (PI-44, mục 6) cho thấy nguồn này chỉ dùng được để đối chiếu thông tin mô tả gói thầu (giá gói thầu, chủ đầu tư, ngày đăng...), **không thay thế được** cho phần dữ liệu quan trọng nhất — giá trúng thầu cụ thể bị khoá sau paywall trả phí ngay cả ở tài khoản free tier. Nếu muasamcong gặp sự cố giữa Phase 1, dự án chưa có nguồn thay thế đã xác nhận cho `reofferPriceFinal`.

**Quyết định cần stakeholder xác nhận trước khi vào Phase 1:**
- Đồng ý đầu tư 1 buổi Selenium không-headless (Xvfb) đầu Phase 1 để trả lời 10 Open Questions, thay vì code crawler dựa hoàn toàn trên suy luận từ source code tĩnh.
- Nếu Open Questions #2 xác nhận captcha bắt buộc cho search chính: cần duyệt ngân sách/thời gian cho dịch vụ giải captcha (2Captcha/Anti-Captcha) hoặc chấp nhận tốc độ crawl chậm hơn với Selenium thuần.
- Timeline nên tính theo backoff dài (tới 60 phút/lần bị chặn) và rate ≤ 2 request/phút/IP làm giả định ban đầu — không nên cam kết mốc thời gian cụ thể cho tới khi đo được data volume thật.

**Độ tin cậy tổng thể của báo cáo:** hỗn hợp — phần "có crawl được không, có cần login không" ở mức CAO (đã kiểm chứng thật); phần "captcha có chặn không, ngưỡng rate-limit chính xác bao nhiêu, response API thật trả gì" ở mức THẤP–TRUNG BÌNH (suy luận từ code hoặc quan sát 1 lần). Không nên dùng báo cáo này để cam kết deadline cứng với bên ngoài trước khi hoàn thành buổi khảo sát Phase 1 nêu trên.
