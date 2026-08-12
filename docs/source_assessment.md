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

**Thử truy cập trực tiếp bằng `curl` (không đăng nhập) — kết quả thật:** bị chặn ở tầng TLS (`Recv failure: Connection reset by peer` ngay lúc TLS handshake, trước khi tới HTTP) — không lấy được nội dung trang. Không phải do yêu cầu đăng nhập (đó là lỗi ở tầng ứng dụng/HTTP, không phải TLS) — xem mục 5 để biết nguyên nhân thật (rate-limit/WAF).

**Độ tin cậy TRUNG BÌNH (vẫn là suy luận, không phải "kết quả thật" như Jira yêu cầu):** nội dung trang chi tiết KHÔNG verify được trực tiếp trong khảo sát này (do bị chặn tầng TLS, xem mục 5) — đây là gap còn lại, không phải do lựa chọn phương pháp. Suy luận dựa trên: trang search truy cập tự do + robots.txt allow-all + dữ liệu đấu thầu công khai theo luật Việt Nam (Luật Đấu thầu yêu cầu công khai kết quả). **Bắt buộc verify trực tiếp bằng Selenium ở đầu Phase 1** (cách chờ rate-limit hết + dùng URL thật ở trên) trước khi code crawler dựa vào giả định này (R-02, PLAN.md).

## 5. Captcha / Anti-bot

- Không phát hiện widget captcha tĩnh (`recaptcha`, `captcha`) trong HTML trang chủ và trang search.
- **Phát hiện thật (khảo sát này, không phải suy luận):** thử headless Chrome (Selenium 4.47, `--headless=new`) vào trang search → server trả HTML lỗi generic (`<title>Error</title>`, "This page can't be displayed. Contact support...", 637 byte) thay vì nội dung trang thật mà `curl` với cùng URL nhận được — có dấu hiệu fingerprint/chặn trình duyệt tự động ở tầng ứng dụng/WAF, khác hành vi so với `curl` thường.
- **Phát hiện thật quan trọng nhất:** sau khoảng 6-8 request trong vài phút (mix `curl` + headless Chrome, không cố tình dồn dập), server bắt đầu **reset kết nối TLS ngay ở bước Client Hello** (`Recv failure: Connection reset by peer`) cho MỌI request tiếp theo — kể cả `/robots.txt` vốn đã pass trước đó. Trạng thái này còn nguyên sau 15s cooldown (chưa thử chờ lâu hơn để tránh làm phiền hệ thống production của cơ quan nhà nước).
- **Kết luận:** không có captcha hiển thị, nhưng có tầng **anti-bot/rate-limit chặn ở mức TLS/network**, kích hoạt rất sớm (số request thấp) và không phân biệt path (chặn cả path an toàn như robots.txt). Đây là input quan trọng cho crawler Phase 1: cần rate-limit rất bảo thủ (vài request/phút, không phải giây) + cơ chế backoff dài + phát hiện sớm tình trạng bị chặn (connection reset, không phải HTTP 4xx/5xx) — đúng R-01 trong PLAN.md nhưng cụ thể hơn: ngưỡng chặn thấp hơn dự kiến ban đầu.

## Giới hạn phương pháp

Khảo sát này dùng `curl` + thử headless Selenium thay vì DevTools trình duyệt tương tác như Jira đề xuất ban đầu (môi trường không có UI trình duyệt tương tác, và headless Chrome ở đây bị WAF/anti-bot chặn — xem mục 5). Ưu điểm `curl`: nhanh, khách quan. Giới hạn: không thấy nội dung render bởi Vue sau khi gọi API. Mục 3 kết luận CAO vì kiểm tra được response HTTP trực tiếp trước khi bị rate-limit. Mục 4 (trang chi tiết) vẫn TRUNG BÌNH — đây là gap thật của khảo sát này, chưa đạt yêu cầu "ghi lại kết quả thật" của Jira PI-43 cho riêng trang chi tiết; đã xác nhận được URL/params thật (mục 4) nhưng bị chặn TLS trước khi lấy được nội dung. **Cần làm lại bước verify trang chi tiết đầu Phase 1**, chờ rate-limit hết, dùng URL thật đã tìm được ở mục 4, qua Selenium không headless nếu có thể (headless bị chặn riêng — mục 5).
