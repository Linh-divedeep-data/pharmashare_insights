# Source Assessment — muasamcong.mpi.gov.vn

**Ticket:** PI-43 · **Ngày khảo sát:** 2026-08-12 · **Phương pháp:** `curl` (HTTP request thô, không chạy JS) — xem giới hạn phương pháp ở cuối file.

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

**Chưa verify trực tiếp được bằng `curl`** — trang chi tiết cần 1 `id` gói thầu cụ thể, lấy được qua kết quả tìm kiếm (gọi API POST động, `curl` tĩnh không thực thi được form search). Đây là giới hạn thật của phương pháp dùng trong khảo sát này.

**Độ tin cậy TRUNG BÌNH (suy luận, chưa xác nhận trực tiếp):** dựa trên việc trang search truy cập tự do + robots.txt allow-all + đây là dữ liệu đấu thầu công khai theo luật Việt Nam (Luật Đấu thầu yêu cầu công khai kết quả), khả năng cao trang chi tiết cũng không yêu cầu đăng nhập. Cần xác nhận trực tiếp bằng Selenium/DevTools ở đầu Phase 1 trước khi code crawler dựa hẳn vào giả định này (đúng theo R-02 trong PLAN.md — verify sớm, không giả định).

## 5. Captcha

Không phát hiện dấu hiệu captcha (`recaptcha`, `captcha`) trong HTML trang chủ và trang search. Không loại trừ khả năng captcha xuất hiện khi tần suất request cao (anti-bot phía sau) — cần theo dõi khi crawl thật ở Phase 1, đúng R-01 trong PLAN.md (rate-limit, dừng ngay khi bị chặn).

## Giới hạn phương pháp

Khảo sát này dùng `curl` (HTTP request thô, không chạy JavaScript) thay vì DevTools trình duyệt như Jira đề xuất ban đầu, do môi trường không có UI trình duyệt tương tác được. Ưu điểm: nhanh, khách quan (xem đúng response server trả về, không lẫn state của trình duyệt cá nhân). Giới hạn: không thấy được nội dung render bởi Vue sau khi gọi API (VD kết quả tìm kiếm thật, trang chi tiết), không test được luồng tương tác (bấm nút tìm kiếm, phân trang). Mục 3 kết luận CAO vì kiểm tra được response HTTP trực tiếp; mục 4 chỉ TRUNG BÌNH vì suy luận, chưa test trực tiếp — cần verify lại bằng Selenium khi bắt đầu code Phase 1.
