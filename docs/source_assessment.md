# Source Assessment — muasamcong.mpi.gov.vn

**Ticket:** PI-43 · **Ngày khảo sát:** 2026-08-12 · **Phương pháp:** `curl` (HTTP request thô, không chạy JS) + thử headless Selenium (Chrome 151) + 1 URL trang chi tiết thật lấy qua Google index — xem giới hạn phương pháp ở cuối file.

## 1. robots.txt

```
User-Agent: *
Disallow:
```

**Kết luận:** không có path nào bị chặn. Toàn bộ site cho phép crawl theo robots.txt (allow-all).

## 2. Nền tảng kỹ thuật

- Cổng chạy trên **Liferay Portal** (dấu hiệu: `frontend-js-aui-web`, `liferay/...` script paths, cấu trúc URL kiểu `/o/<module>/...`).
- Widget tìm kiếm/nộp hồ sơ dùng **Vue 2** + **Axios**, gọi API backend dạng POST tới namespace `/o/egp-portal-contractor-selection-v2/services/...` (module OSGi riêng cho "contractor selection" = lựa chọn nhà thầu).
- Trang **không phải SPA rỗng** — HTML trả về từ server đã có nội dung thật (~41KB text), các phần tìm kiếm/lọc là Vue "island" nhúng vào trong portal shell, không phải toàn trang render bằng JS.
- **Ý nghĩa cho crawler:** Selenium (đã chọn theo PLAN.md) là lựa chọn an toàn vì trang có phần render động qua Vue + gọi API nội bộ; có khả năng gọi thẳng API POST nếu reverse-engineer được params, nhưng đó là quyết định thuộc Phase 1, không phải Phase 0.

## 3. Trang tìm kiếm gói thầu

**URL:** `https://muasamcong.mpi.gov.vn/contractor-selection?render=search`

- HTTP 200, **không bị redirect** sang trang đăng nhập.
- Form tìm kiếm/lọc (`search`/`filter` class) render sẵn trong HTML trả về — có thể truy cập không cần đăng nhập.
- Phát hiện template lỗi ẩn: `"Phiên đăng nhập của bạn đã hết hạn. Vui lòng đăng nhập lại !!!"` + xử lý response `401 Unauthorized` — đây là modal dùng chung toàn portal cho các **hành động cần tài khoản** (nộp hồ sơ, thanh toán — thấy endpoint `api/epayclaimr/pm-billing/confirm` cùng trang), **không phải** bằng chứng trang search bị khoá.

**Kết luận (độ tin cậy CAO):** xem danh sách/tìm kiếm gói thầu **không yêu cầu đăng nhập**.

## 4. Trang chi tiết giá trúng thầu

**Cấu trúc URL thật (xác nhận qua Google index, không phải suy đoán):**

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

Portlet Liferay (`p_p_id=egpportalcontractorselectionv2...`), `render=detail-v2`, `stepCode=reoffer-price-step-1` map đúng "bước chào lại giá" — đây chính là trang giá chi tiết Jira yêu cầu khảo sát. `id`/`notifyId` là UUID gói thầu cụ thể.

**Lần thử đầu (giữa lúc bị rate-limit — xem mục 5):** bị chặn ở tầng TLS (`Recv failure: Connection reset by peer` ngay lúc TLS handshake, trước khi tới HTTP) — không lấy được nội dung trang. Đây là do rate-limit tạm thời (mục 5), không phải do yêu cầu đăng nhập.

**Sau khi rate-limit hết (~1 giờ sau, retry 1 request duy nhất) — kết quả thật, xác nhận trực tiếp:**

- `HTTP 200`, `curl` không mang cookie/session, **không redirect** sang trang login, response 454KB (không phải trang lỗi/login wall).
- Response chứa đúng `notifyNo=IB2500633776` / `planNo=PL2500351299` (giá trị query mình gửi được server phản ánh lại trong nội dung) — xác nhận server có xử lý theo `id`/`notifyId` thật, không phải trang tĩnh chung chung.
- Response chứa các label/template giá thật: `Giá dự thầu`, `Giá dự thầu cuối cùng (M)`, `{{item?.reofferPrice | currency}}`, `{{listContractorKq?.[0]?.reofferPriceFinal | currency}} VND` — đây là template Vue binding (giá trị số thật populate lúc client gọi API, giống kiến trúc trang search ở mục 2), không phải nội dung bị che/khoá.
- Chuỗi modal "Phiên đăng nhập của bạn đã hết hạn..." vẫn xuất hiện (1 lần, trong 1 ternary JS) — cùng pattern shared-modal đã xác nhận ở mục 3, không phải login wall chặn trang.

**Kết luận (độ tin cậy CAO — xác nhận trực tiếp bằng kết quả thật, không còn suy luận):** trang chi tiết giá trúng thầu **không yêu cầu đăng nhập** để load — cùng pattern với trang search. Giá trị số cụ thể (số tiền) render qua Vue sau khi gọi API POST client-side (giới hạn kiến trúc chung, mục 2), không phải do chặn đăng nhập — muốn lấy số liệu thật cần Selenium/gọi thẳng API, đây là quyết định kỹ thuật Phase 1, không phải câu hỏi "có cần login" nữa (AC này đã trả lời xong).

## 5. Captcha / Anti-bot

- Không phát hiện widget captcha tĩnh (`recaptcha`, `captcha`) trong HTML trang chủ và trang search.
- **Phát hiện thật (khảo sát này, không phải suy luận):** thử headless Chrome (Selenium 4.47, `--headless=new`) vào trang search → server trả HTML lỗi generic (`<title>Error</title>`, "This page can't be displayed. Contact support...", 637 byte) thay vì nội dung trang thật mà `curl` với cùng URL nhận được — có dấu hiệu fingerprint/chặn trình duyệt tự động ở tầng ứng dụng/WAF, khác hành vi so với `curl` thường.
- **Phát hiện thật quan trọng nhất:** sau khoảng 6-8 request trong vài phút (mix `curl` + headless Chrome, không cố tình dồn dập), server bắt đầu **reset kết nối TLS ngay ở bước Client Hello** (`Recv failure: Connection reset by peer`) cho MỌI request tiếp theo — kể cả `/robots.txt` vốn đã pass trước đó. Trạng thái này còn nguyên sau 15s cooldown (chưa thử chờ lâu hơn để tránh làm phiền hệ thống production của cơ quan nhà nước).
- **Kết luận:** không có captcha hiển thị, nhưng có tầng **anti-bot/rate-limit chặn ở mức TLS/network**, kích hoạt rất sớm (số request thấp) và không phân biệt path (chặn cả path an toàn như robots.txt). Đây là input quan trọng cho crawler Phase 1: cần rate-limit rất bảo thủ (vài request/phút, không phải giây) + cơ chế backoff dài + phát hiện sớm tình trạng bị chặn (connection reset, không phải HTTP 4xx/5xx) — đúng R-01 trong PLAN.md nhưng cụ thể hơn: ngưỡng chặn thấp hơn dự kiến ban đầu.

## Giới hạn phương pháp

Khảo sát này dùng `curl` + thử headless Selenium thay vì DevTools trình duyệt tương tác như Jira đề xuất ban đầu (môi trường không có UI trình duyệt tương tác, và headless Chrome ở đây bị WAF/anti-bot chặn — xem mục 5). Ưu điểm `curl`: nhanh, khách quan. Giới hạn: không thấy giá trị số thật render bởi Vue sau khi gọi API (search lẫn detail) — nhưng câu hỏi trọng tâm của PI-43 ("có/không yêu cầu đăng nhập") đã trả lời được cho cả 2 trang bằng kết quả HTTP thật (mục 3, mục 4), độ tin cậy CAO. Việc lấy số liệu giá thật (không phải câu hỏi đăng nhập) thuộc phạm vi kỹ thuật crawler Phase 1.
