# Playbooks theo pattern (định tính + định lượng)

Mục tiêu: Khi đã biết driver (CTR/CTI/CPM) và cluster (Hook mạnh–intent yếu, ...), đưa ra khuyến nghị sửa creative *cụ thể*.

## 1) CTR là driver chính (hook/visual thắng)
Dấu hiệu:
- CTR cao vượt median/benchmark, CTI không nhất thiết cao.

Playbook:
- Tối ưu **2 giây đầu**: pattern interrupt + hook rõ (pain/curiosity/benefit).
- Ưu tiên:
  - `has_person=yes` + `selfie_facecam` (UGC) hoặc `hands_only` demo.
  - pacing nhanh, ít chữ, claim “1 câu” ngay đầu.
- Test biến thể:
  - Same concept, đổi 3 hook đầu (pain vs curiosity vs benefit).
  - Same footage, đổi thumbnail/frame đầu.

## 2) CTI là driver chính (intent/expectation matching thắng)
Dấu hiệu:
- CTI cao, CTR không quá nổi bật.

Playbook:
- Làm rõ “đây là app gì” và “mình nhận được gì sau khi cài”:
  - `shows_product_ui=yes` sớm.
  - claim cụ thể hơn (`claim_specificity=high`).
  - thêm social proof (rating/review) nếu phù hợp.
- Tránh misleading hook (CTR cao nhưng CTI thấp).

## 3) CPM là vấn đề (auction đắt / creative bị đánh giá kém)
Dấu hiệu:
- CPM cao bất thường trong khi CTR/CTI không bù được.

Playbook:
- Nâng chất lượng visual (ánh sáng, độ nét, bố cục), giảm cảm giác “spam”.
- Giảm text overlay quá dày (`text_overlay_density=high`).
- Tránh nội dung dễ bị hạn chế phân phối.

## 4) Cluster: Hook mạnh – intent yếu
- Thường CTR cao nhưng CTI thấp.
- Hướng xử lý: giữ hook nhưng sửa phần “đúng kỳ vọng” (show UI/app, claim rõ, social proof, offer rõ).

## 5) Cluster: Hook yếu – intent mạnh
- CTR thấp nhưng CTI cao.
- Hướng xử lý: giữ message/offer nhưng sửa 2s đầu + thumbnail + pacing.

## 6) Cluster: Auction đắt nhưng convert tốt
- CPM cao, CTR & CTI cao.
- Hướng xử lý: scale có kiểm soát; test thêm variant visual để kéo CPM xuống (b-roll khác, giảm text, thay opening frame).

