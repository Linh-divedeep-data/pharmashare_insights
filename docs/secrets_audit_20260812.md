# Secrets Management Audit — 2026-08-12

**Ticket:** PI-42 · **Người thực hiện audit:** Claude Code (theo yêu cầu user, verify bằng lệnh thật)

## Phạm vi kiểm tra

Xác nhận toàn bộ secret dự án (DB connection string, `ANTHROPIC_API_KEY`) chỉ nằm trong `.env` cục bộ, không bị commit vào git — kể cả trong lịch sử cũ.

## Kết quả

| # | Kiểm tra | Lệnh | Kết quả |
|---|---|---|---|
| 1 | `.gitignore` chặn `.env` | `git check-ignore -v .env` | ✅ Chặn, rule tại `.gitignore:12` |
| 2 | `.env` chưa từng commit (toàn bộ history, toàn bộ branch) | `git rev-list --all \| xargs git ls-tree -r --name-only \| grep -x '\.env'` | ✅ Không xuất hiện trong bất kỳ commit tree nào |
| 3 | `.env.example` không chứa giá trị thật | đọc trực tiếp file | ✅ Chỉ có tên biến (`DATABASE_URL=`, `ANTHROPIC_API_KEY=`), rỗng |
| 4 (bổ sung) | Secret thật (password Supabase, hostname) chưa từng lọt vào history | `git log --all -p -S"<secret-string>"` (pickaxe search) | ✅ 0 kết quả cho cả password và hostname |

## Ghi chú

Kiểm tra #4 xác nhận cụ thể: trong lúc code PI-40, 1 test fixture ban đầu vô tình dùng đúng password thật (`Tryyourbest%40123`) làm dữ liệu mẫu. Lỗi này được phát hiện và sửa **trước khi commit** (grep `git diff --cached` trước mỗi lần commit — quy trình đã áp dụng từ PI-40 trở đi). Pickaxe search xác nhận chuỗi này chưa bao giờ thực sự đi vào git history ở bất kỳ commit nào.

## Kết luận

Không có secret nào bị lộ trên git (local hoặc remote). `.env`/`.env.example`/`.gitignore` đúng chuẩn.
