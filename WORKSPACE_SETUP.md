# Workspace Setup — thứ tự cài đặt tools & skills

> File này để Claude (hoặc cậu) chạy lại toàn bộ setup khi init một workspace mới.
> Cứ nói với Claude: **"làm theo WORKSPACE_SETUP.md"**.

Có 2 nhóm:
- **A. Global (1 lần / máy)** — cài đặt cấp máy, dùng cho mọi workspace.
- **B. Per-workspace (mỗi project)** — chạy bên trong thư mục project mới.

---

## Yêu cầu trước (prerequisites)

| Tool | Kiểm tra | Cài |
|------|----------|-----|
| Homebrew | `brew --version` | https://brew.sh |
| Node ≥ 20.19 | `node -v` | `brew install node` |
| pipx | `pipx --version` | `brew install pipx && pipx ensurepath` |
| Claude Code CLI | `claude --version` | đã có |

---

## A. Global — cài 1 lần cho máy

Các bước này an toàn khi chạy lại (đã cài thì báo "already installed").

```bash
# 1) beads — issue tracker (bd) + dependency dolt
brew install beads

# 2) code-review-graph — MCP review graph
pipx install code-review-graph            # hoặc: pipx upgrade code-review-graph

# 3) OpenSpec — spec-driven workflow (cli: openspec)
npm install -g @fission-ai/openspec@latest

# 4) caveman — plugin trả lời ngắn, tiết kiệm output token (scope: user)
npx -y github:JuliusBrussee/caveman -- --only claude --non-interactive

# 5) karpathy-guidelines — plugin nguyên tắc coding (scope: user)
claude plugin marketplace add multica-ai/andrej-karpathy-skills
claude plugin install andrej-karpathy-skills@karpathy-skills
```

> Plugin caveman + karpathy cài scope **user** → tự động có ở mọi workspace,
> không cần lặp lại ở bước B.

---

## B. Per-workspace — chạy trong project mới

Đứng ở **thư mục gốc project**, chạy theo thứ tự:

```bash
# 1) beads — khởi tạo issue tracker cho project (tạo .beads/)
bd init

# 2) superpowers — bộ skills (writing-plans, TDD, systematic-debugging,
#    git-worktrees, code-review, ...) → cài vào .agents/skills/, symlink Claude Code
npx --yes skills add obra/superpowers

# 3) code-review-graph — cấu hình cho Claude Code (.mcp.json, hooks,
#    skills, chèn hướng dẫn vào CLAUDE.md, git pre-commit hook)
code-review-graph install --platform claude-code
code-review-graph build          # build knowledge graph

# 4) OpenSpec — khởi tạo spec workspace (tạo openspec/, skills, commands
#    cho Claude Code + Codex)
openspec init
```

### 5) .gitignore — bỏ qua file local

Đảm bảo `.gitignore` có các mục sau (một số bước ở trên tự thêm):

```gitignore
# macOS
.DS_Store

# Logs
*.log

# Local machine-specific config
.claude/settings.local.json
.codex/config.local.toml

# Beads / Dolt
.dolt/
*.db
.beads-credential-key
.beads/proxieddb/

# code-review-graph
.code-review-graph/
```

---

## C. GitHub CLI (`gh`) — review PR bằng `/review`

```bash
# Cài (macOS)
brew install gh

# Đăng nhập — scope tối thiểu "repo" (đọc/ghi PR, review, comment), "workflow" nếu cần xem CI
gh auth login

# Verify
gh auth status
```

Sau khi login: `/review <PR number|URL>` — Claude tự `gh pr diff` lấy nội dung, review, và **post comment thật lên GitHub PR**. Phân biệt với `/code-review`: review diff local/branch hiện tại theo checklist riêng của repo, **không** post lên GitHub — dùng khi tự kiểm tra trước khi mở PR.

---

## D. Jira ↔ bd sync — bắt buộc mỗi session

**Nguyên tắc: 1 task không bao giờ chỉ đóng ở 1 tracker.** bd và Jira phải luôn khớp trạng thái — task xong = Jira tick (chuyển Done/status tương ứng) **và** bd close, làm cùng lúc, không tách rời.

### D.1 Đầu mỗi session — bắt buộc verify kết nối Jira trước khi nhận task

Trước khi bắt đầu làm việc trên bất kỳ task nào chạm Jira/bd, kiểm tra Jira MCP đã kết nối:

```
getAccessibleAtlassianResources
```

Nếu lỗi/rỗng → **dừng lại**, báo cho user: "Jira MCP chưa authorize, vào claude.ai → Settings → Connectors để kết nối trước." Không tự đoán trạng thái Jira hay làm việc "mù" (chỉ dựa vào bd) khi chưa xác nhận kết nối được.

### D.2 Setup credential cho CLI (khi cần thao tác Jira ngoài MCP)

```bash
cp jira.env.example jira.env
# Điền JIRA_URL, JIRA_EMAIL, JIRA_TOKEN thật (Atlassian API token: id.atlassian.com/manage-profile/security/api-tokens)
```

`jira.env` **không commit** — thêm vào `.gitignore` nếu chưa có.

### D.3 Đóng 1 task — 2 cách, chọn 1

**Cách A — trong session tương tác (mặc định):** Claude dùng MCP tool `transitionJiraIssue` (chuyển Jira) + lệnh `bd close <id>` (đóng bd) trong cùng 1 turn, không hỏi lại xác nhận riêng lẻ cho từng bước — coi như 1 hành động.

**Cách B — CLI (script, non-interactive hoặc muốn double-check 2 tracker khớp nhau):**

```bash
uv run python bin/jira/sync_task.py <bd-id> [--jira-status "Done"] [--reason "..."]
```

Script tự lấy `external_ref` (link Jira) từ bd issue, transition Jira, rồi `bd close` — nếu bước Jira lỗi thì **dừng ngay, không đóng bd** (tránh 2 tracker lệch nhau). Nếu `bd close` lỗi sau khi Jira đã tick, script báo rõ để xử lý tay — không tự động retry mù.

### D.4 Nếu bd không có external_ref (task tạo mới trong bd, chưa có trên Jira)

Không tự suy đoán — hỏi user có cần tạo issue Jira tương ứng (`createJiraIssue`) trước không, hay task này chỉ track nội bộ ở bd (không cần đẩy lên Jira).

---

## Sau khi xong

1. **Khởi động lại Claude Code / IDE** để nhận plugins, skills, MCP, slash commands.
2. Kiểm tra nhanh:
   ```bash
   bd version
   openspec --version
   code-review-graph --help
   claude plugin list        # thấy caveman@caveman, andrej-karpathy-skills@karpathy-skills
   ```
3. Slash commands có thể dùng: `/caveman`, `/opsx:propose "..."`.

---

## Ghi chú
- Thứ tự B quan trọng: `bd init` và `code-review-graph install` đều đụng vào
  `CLAUDE.md` / `.gitignore` — chạy đúng thứ tự để không xung đột.
- Muốn gỡ caveman: `npx -y github:JuliusBrussee/caveman -- --uninstall`.
- `code-review-graph build` cần chạy lại khi codebase đổi nhiều để cập nhật graph.
