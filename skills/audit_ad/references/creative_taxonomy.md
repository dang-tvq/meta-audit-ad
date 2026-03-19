# Creative Taxonomy (định tính)

Mục tiêu: Chuẩn hoá cách “tag” các yếu tố của creative (hình ảnh/âm thanh/cấu trúc/thông điệp) để có thể so sánh giữa các creative và đối chiếu với chỉ số định lượng (CPM/CTR/CTI/CPI).

## 1) Quy ước chung
- Mỗi creative = 1 hàng trong **Creative Feature Sheet**.
- Mỗi feature nên là:
  - **binary** (0/1) hoặc **categorical** (một trong các giá trị chuẩn).
  - có định nghĩa rõ ràng để tránh tag lệch.
- Nếu không đủ thông tin để tag (video mờ, không có audio, không thấy caption...) → để `unknown` (không suy đoán).

## 2) Nhóm feature đề xuất

### A. Visual / Content
- `format`: `video` | `static` | `carousel` | `unknown`
- `has_person`: `yes` | `no` | `unknown`
- `person_type` (nếu has_person=yes): `ugc_creator` | `actor` | `hands_only` | `multiple_people` | `unknown`
- `camera_style`: `selfie_facecam` | `tripod` | `screen_record` | `mixed` | `unknown`
- `shows_product_ui`: `yes` | `no` | `unknown` (có hiển thị UI/app thật không)
- `before_after`: `yes` | `no` | `unknown`
- `demo_clarity`: `high` | `med` | `low` | `unknown` (mức dễ hiểu của demo)
- `text_overlay_density`: `low` | `med` | `high` | `unknown` (lượng chữ overlay trên video)
- `visual_quality`: `high` | `med` | `low` | `unknown` (ánh sáng, độ nét, bố cục)
- `branding_early`: `yes` | `no` | `unknown` (logo/brand xuất hiện trong ~3s đầu)

### B. Hook & structure (đặc biệt quan trọng cho CTR)
- `hook_first_2s`: `pain` | `curiosity` | `benefit` | `shock` | `social_proof` | `offer` | `question` | `unknown`
- `pattern_interrupt_first_2s`: `yes` | `no` | `unknown` (có “dừng scroll” bằng cảnh lạ/đột ngột/đổi nhịp không)
- `pacing`: `fast` | `normal` | `slow` | `unknown`
- `cta_presence`: `strong` | `soft` | `none` | `unknown`

### C. Audio (ảnh hưởng CTR và đôi khi CTI)
- `voiceover`: `yes` | `no` | `unknown`
- `voice_style` (nếu voiceover=yes): `natural_ugc` | `narration` | `robotic` | `unknown`
- `music`: `none` | `low` | `trending` | `unknown`
- `audio_clarity`: `high` | `med` | `low` | `unknown`

### D. Claim / persuasion (ảnh hưởng CTI mạnh)
- `primary_claim`: `speed` | `result` | `save_money` | `simplify` | `health` | `productivity` | `entertainment` | `unknown`
- `claim_specificity`: `high` | `med` | `low` | `unknown` (claim có cụ thể/đo lường được không)
- `social_proof`: `yes` | `no` | `unknown` (review, rating, testimonial, user count)
- `offer_type`: `free_trial` | `discount` | `limited_time` | `none` | `unknown`

## 3) Lưu ý khi tag
- `has_person`: chỉ `yes` khi **thấy người/face/hands** rõ ràng (UGC/hands-only đều tính là yes nếu có bàn tay/nhân vật).
- `shows_product_ui`: `yes` khi có cảnh quay màn hình/app UI hoặc demo trực tiếp thao tác.
- `hook_first_2s`: chọn 1 nhãn chiếm ưu thế nhất trong 2 giây đầu.

