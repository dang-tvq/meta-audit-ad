---
name: meta-ads-creative-analyst
description: phan tich creative testing tren facebook/meta ads tu file excel/csv hoac bang paste; tu dong chuan hoa cot (ad name/creative/asset, link ctr vs all ctr, app installs), lam sach so lieu, tinh cpi/cpm/ctr/cti; phan ra dong gop cpm/ctr/cti de giai thich cpi; phan cum creative theo pattern va playbook. neu nguoi dung cung cap asset video/image, thuc hien phan tich dinh tinh (nhan vat/hook 2s dau/voiceover/show ui/before-after/claim) va lien ket voi driver ctr/cti/cpm de tim winning elements.
---

# Meta Ads Creative Analyst

Skill phân tích hiệu quả creative testing trên Facebook/Meta Ads. Output hoàn toàn bằng **Tiếng Việt**.

---

## Các chỉ số cơ bản trong Meta Ads

### CPM – Cost Per Mille (Chi phí trên 1.000 lượt hiển thị)

**Định nghĩa**: Số tiền phải trả để quảng cáo hiển thị đến 1.000 người dùng.

**Công thức**:
```
CPM = (Tổng spend / Tổng impressions) × 1.000
```

**Ý nghĩa với creative**:
- CPM phản ánh **chi phí tiếp cận audience** – chịu ảnh hưởng bởi độ cạnh tranh của auction, chất lượng creative và audience targeting.
- CPM thấp = quảng cáo được phân phối hiệu quả, creative được Meta đánh giá tốt (relevance score cao).
- CPM cao = audience bị cạnh tranh nhiều, creative kém relevant, hoặc bị reject một phần.
- CPM cao mà CPI vẫn tốt → creative convert rất mạnh sau khi người dùng thấy quảng cáo.
- CPM thấp nhưng CPI cao → vấn đề nằm ở funnel phía sau (CTR hoặc CTI kém).

---

### CTR – Click-Through Rate (Tỷ lệ nhấp)

**Định nghĩa**: Tỷ lệ phần trăm người dùng nhìn thấy quảng cáo rồi nhấp vào.

**Công thức**:
```
CTR = (Tổng clicks / Tổng impressions) × 100%
```

**Ý nghĩa với creative**:
- CTR đo lường **sức hút của hook và visual** – người dùng có bị thu hút đủ để dừng lại và nhấp không.
- CTR cao = creative có hook mạnh, visual/copy cuốn hút, phù hợp với audience.
- CTR thấp = creative chưa đủ nổi bật trong newsfeed, cần xem lại thumbnail, dòng đầu tiên của copy, hoặc format.
- CTR cao nhưng CTI thấp → creative "câu click" tốt nhưng không chuyển đổi được sau đó (vấn đề ở store page hoặc landing page).

---

### CTI – Click-To-Install Rate (Tỷ lệ cài đặt sau khi nhấp)

**Định nghĩa**: Tỷ lệ phần trăm người dùng đã nhấp vào quảng cáo rồi thực sự cài đặt app.

**Công thức**:
```
CTI = (Tổng installs / Tổng clicks) × 100%
```

> *Lưu ý: Một số dashboard gọi chỉ số này là Install Rate hoặc CVR (Conversion Rate).*

**Ý nghĩa với creative**:
- CTI đo lường **chất lượng của intent sau click** – creative có đang thu hút đúng người dùng có nhu cầu thật sự không.
- CTI cao = creative targeting đúng audience có ý định cao, store page/landing page hỗ trợ tốt.
- CTI thấp = người dùng click vì tò mò nhưng không bị thuyết phục sau khi vào store → cần xem lại store listing (screenshots, description, ratings) hoặc creative đang misleading về app.
- So sánh CTI giữa các creative giúp xác định creative nào đang attract đúng quality user.

---

### CPI – Cost Per Install (Chi phí trên mỗi lượt cài đặt)

**Định nghĩa**: Số tiền phải trả để có được một lượt cài đặt app.

**Công thức**:
```
CPI = Tổng spend / Tổng installs
```

Hoặc có thể suy ra từ các chỉ số trên:
```
CPI = CPM / (CTR% × CTI%) × 100 / 1.000
   = CPM / (CTR × CTI / 10.000)
```

**Ý nghĩa với creative**:
- CPI là **chỉ số tổng hợp cuối cùng** – phản ánh toàn bộ hiệu quả của creative từ impression → click → install.
- CPI thấp = creative hiệu quả, đang mang lại install với chi phí hợp lý.
- CPI cao = có điểm tắc nghẽn trong funnel (CPM quá cao, CTR quá thấp, hoặc CTI quá thấp) → cần dùng các chỉ số trên để xác định nguyên nhân.
- **CPI là chỉ số quyết định** khi so sánh và đánh giá creative – các chỉ số khác chỉ để giải thích *tại sao* CPI tốt hay kém.

---

### Mối quan hệ giữa các chỉ số

```
Impressions
    ↓ (CPM = chi phí để có impressions)
Clicks
    ↓ CTR = Clicks / Impressions
Installs
    ↓ CTI = Installs / Clicks

CPI = CPM / (CTR × CTI / 10.000)
```

| Tình huống | CPM | CTR | CTI | Kết luận |
|---|---|---|---|---|
| Creative tốt toàn diện | Thấp | Cao | Cao | CPI thấp ✅ |
| Hook tốt, store kém | Bình thường | Cao | Thấp | CPI cao, fix store page |
| Audience sai | Cao | Thấp | Thấp | CPI cao, review targeting |
| CPM cao nhưng convert mạnh | Cao | Cao | Cao | CPI có thể chấp nhận được |

---

## Bước 0: Chuẩn hóa input + tự phát hiện cột (NÂNG CẤP)

### 0.1 – Nguyên tắc chung
- Luôn chuẩn hóa về các cột canonical:
  - `creative_name`, `spend`, `impressions`, `clicks`, `installs`, `cpm`, `ctr`, `cti`, `cpi`
- Chấp nhận dữ liệu từ:
  - **File Excel / CSV** (ưu tiên):
    - Hỗ trợ upload **.xlsx / .xls** và **.csv**
    - Nếu file Excel có nhiều sheet, hỏi user sheet nào (hoặc mặc định sheet đầu tiên)
    - Đọc bằng pandas
  - **Paste bảng/text**: parse từ chat

### 0.2 – Tự map tên cột (column auto-mapping)

**Mapping gợi ý** (không giới hạn, đây là các biến thể thường gặp):
- `creative_name`: Ad name / Creative / Asset / Thumbnail / Name / Video
- `spend`: Spend / Amount spent / Cost
- `impressions`: Impressions / Impr / Views
- `clicks`: Clicks / Link clicks / Outbound clicks
- `installs`: Installs / App installs / Mobile app installs / Results
- `cpm`: CPM / Cost per 1,000 impressions
- `ctr`: CTR / **Link CTR** / All CTR
- `cti`: CTI / Install Rate / CVR / Conversion Rate
- `cpi`: CPI / Cost per install / Cost per app install / Cost per result

**Rule ưu tiên cho CTR**:
- Nếu đồng thời có **Link CTR** và **All CTR** → ưu tiên **Link CTR** (vì phản ánh hành vi click ra ngoài tốt hơn).
- Nếu chỉ có 1 loại → dùng loại đó và ghi chú “CTR đang dùng loại nào”.

**Rule ưu tiên cho installs**:
- Nếu có cả `mobile app installs` và `app installs` → ưu tiên `mobile app installs` (thường là metric chuẩn trong App Install reporting).

### 0.3 – Tự parse số liệu (number parsing)

Khi đọc dữ liệu, luôn làm sạch:
- Bỏ ký hiệu tiền tệ (`$`, `₫`), dấu `%`, khoảng trắng.
- Xử lý dấu phân tách:
  - Nếu có cả `,` và `.` → coi `,` là thousand separator (1,234.56 → 1234.56)
  - Nếu chỉ có `,` → có thể là decimal separator (1,23 → 1.23) hoặc thousand separator (1,234 → 1234), dùng heuristic.
- Nếu thiếu `cpm/ctr/cti/cpi` nhưng có raw counts → **tự tính**:
  - `cpm = spend / impressions * 1000`
  - `ctr = clicks / impressions`
  - `cti = installs / clicks`
  - `cpi = spend / installs`

### 0.4 – Nếu thiếu cột quan trọng
- Tối thiểu để phân tích đầy đủ cần: `creative_name`, `spend`, `impressions`, `clicks`, `installs`.
- Nếu thiếu → báo rõ thiếu cột nào, đề xuất người dùng export lại (hoặc paste thêm).

> Nếu user upload file, có thể dùng script kèm skill để làm sạch nhanh:
> `scripts/analyze_meta_creatives.py` (tạo file output CSV đã chuẩn hóa và có thêm decomposition + cluster nếu đủ cột).
>
> Ví dụ chạy với CSV:
> `python scripts/analyze_meta_creatives.py --input data.csv --output cleaned_output.csv`
>
> Ví dụ chạy với Excel (chọn sheet):
> `python scripts/analyze_meta_creatives.py --input data.xlsx --sheet "Sheet1" --output cleaned_output.csv`

---

## Bước 1: Thu thập dữ liệu và benchmark

### Nhận dữ liệu đầu vào
Chấp nhận cả hai dạng:
- **File Excel / CSV**: đọc bằng pandas (khuyến khích chạy chuẩn hóa như Bước 0).
  - Hỗ trợ upload **.xlsx / .xls** và **.csv**.
  - Nếu Excel có nhiều sheet, hỏi user sheet name (ví dụ: `Data`, `Sheet1`).
- **Paste text/bảng**: parse trực tiếp từ nội dung người dùng gửi vào chat.

### Xác nhận benchmark
Luôn hỏi người dùng cung cấp benchmark **trước khi phân tích** (nếu chưa có trong message):

```
Bạn đang dùng benchmark nào? Ví dụ:
- CPI tốt: < $X | trung bình: $X–$Y | kém: > $Y
- CPM tốt: < $X
- CTR tốt: > X%
- CTI (Click-to-Install) tốt: > X%
```

Nếu người dùng không có benchmark:
- Dùng ngưỡng tương đối dựa trên median của data (top 25% = tốt, bottom 25% = kém)
- Và ghi chú đây là benchmark tương đối (không phải target business).

---

## Bước 2: Phân tích

### 2.1 – Bảng tóm tắt creative performance

Tạo bảng với các cột:
| Creative Name | Spend | CPI | CPM | CTR | CTI | Đánh giá tổng |
|---|---|---|---|---|---|---|

**Đánh giá tổng** = dựa trên CPI (key metric):
- ✅ **WORK** – CPI dưới ngưỡng tốt
- ⚠️ **TRUNG BÌNH** – CPI trong vùng trung bình
- ❌ **KHÔNG WORK** – CPI vượt ngưỡng kém

Ngoài ra:
- Nếu số liệu quá ít (spend/click/install thấp) → gắn nhãn **“Chưa đủ data”** thay vì kết luận mạnh.

### 2.2 – Insight sâu theo từng chỉ số

**CPI (Key Metric – đánh giá chính)**
- Creative nào có CPI tốt nhất / tệ nhất?
- Chênh lệch bao nhiêu % so với benchmark?

**CPM (Chi phí tiếp cận)**
- CPM cao bất thường? → Có thể do audience bị overlap hoặc creative bị reject một phần
- CPM thấp nhưng CPI cao → Vấn đề ở funnel sau impression (CTR hoặc CTI kém)

**CTR (Click-through Rate)**
- Creative nào có CTR cao nhưng CTI thấp → Hook tốt nhưng landing page / store listing kém
- Creative nào có CTR thấp → Cần kiểm tra visual/copy có đủ cuốn hút không

**CTI (Click-to-Install Rate)**
- CTI thấp → Người dùng click nhưng không install → Vấn đề ở store page, app description, screenshots
- So sánh CTI giữa các creative để xem creative nào convert tốt hơn sau click

### 2.3 – Phân tích tương quan

Nếu đủ data (≥ 5 creatives), tìm pattern:
- Creative format nào (video vs image, short vs long) có CPI tốt hơn?
- Hook/angle nào consistently cho CTR cao?
- Có creative nào outlier tích cực không (CPI tốt hơn trung bình >30%)?

---

## Bước 2.4: Phân rã CPI thành 3 nguồn (CPM / CTR / CTI) theo “độ đóng góp” (NÂNG CẤP)

### Mục tiêu
Không chỉ nói chung chung “CTR thấp” hay “CTI thấp”, mà lượng hoá:
- CPI xấu chủ yếu do CPM (auction đắt) hay do CTR (hook yếu) hay do CTI (intent/store yếu).

### Cách tính (counterfactual trên median)
1) Tính median của dataset: `CPM_med`, `CTR_med`, `CTI_med`
2) Tính **CPI baseline** (dùng toàn median):

Với `CTR` và `CTI` ở dạng **fraction** (vd 1.2% = 0.012):
```
CPI_base = CPM_med / (1000 * CTR_med * CTI_med)
```
3) Tạo 3 CPI “expected” khi chỉ thay 1 thành phần:
```
CPI_if_CPM = CPM_i / (1000 * CTR_med * CTI_med)
CPI_if_CTR = CPM_med / (1000 * CTR_i * CTI_med)
CPI_if_CTI = CPM_med / (1000 * CTR_med * CTI_i)
```
4) Delta do từng thành phần:
```
ΔCPM = CPI_if_CPM - CPI_base
ΔCTR = CPI_if_CTR - CPI_base
ΔCTI = CPI_if_CTI - CPI_base
```
5) Tính % đóng góp theo hướng “tệ hơn” (nếu CPI_i xấu hơn baseline) hoặc “tốt hơn” (nếu CPI_i tốt hơn baseline).

### Output yêu cầu
Với mỗi creative “kém” hoặc “outlier”, đưa kết luận dạng:
- “CPI xấu chủ yếu do **CTR thấp (~60%)**, **CTI thấp (~30%)**, **CPM (~10%)**.”
- Hoặc “CPI tốt hơn baseline chủ yếu nhờ **CTI cao (~55%)** và **CTR (~35%)**.”

---

## Bước 2.5: Phân cụm creative theo pattern + playbook (NÂNG CẤP)

### Cách phân cụm (heuristic theo median)
Dùng median làm ngưỡng:
- CTR_high nếu `CTR_i ≥ CTR_med`
- CTI_high nếu `CTI_i ≥ CTI_med`
- CPM_high nếu `CPM_i ≥ CPM_med`

Gán label:
1) **Hook mạnh – intent yếu**: CTR_high & CTI_low
2) **Hook yếu – intent mạnh**: CTR_low & CTI_high
3) **Auction đắt nhưng convert tốt**: CPM_high & CTR_high & CTI_high
4) **Toàn funnel yếu**: CPM_low & CTR_low & CTI_low
5) **Trung tính / hỗn hợp**: còn lại

### Playbook theo cluster
- **Hook mạnh – intent yếu**
  - Creative đang “câu click” ổn nhưng không ra install.
  - Hành động: kiểm tra store page (screenshots, rating, messaging), đảm bảo creative không misleading; test phiên bản “expectation matching” (show UI thật, claim cụ thể hơn).

- **Hook yếu – intent mạnh**
  - Ai click thì dễ install, nhưng ít người click.
  - Hành động: cải thiện thumb/first 2s, hook mạnh hơn, UGC-style, benefit upfront; giữ core message vì intent ok.

- **Auction đắt nhưng convert tốt**
  - CPM cao nhưng CTR+CTI kéo được CPI.
  - Hành động: scale có kiểm soát; thử mở audience/placement để giảm CPM; test biến thể giảm “tính quảng cáo” để tăng relevance.

- **Toàn funnel yếu**
  - Vừa đắt vừa không click vừa không install.
  - Hành động: tắt sớm (nếu đủ data), thay angle/format hoàn toàn.

- **Trung tính / hỗn hợp**
  - Dùng để “iterate”: chọn 1 bottleneck lớn nhất (theo decomposition) và tối ưu.

---

## Bước 2.4: Phân tích định tính creative (hình ảnh/âm thanh/cấu trúc)

> Mục tiêu: tìm “winning elements” (ví dụ: **có nhân vật vs không nhân vật**, hook 2 giây đầu, voiceover, show UI, before/after…) và **liên kết** chúng với driver định lượng (CTR/CTI/CPM) để giải thích vì sao creative work/không work.

### 2.4.1 – Điều kiện để phân tích định tính (bắt buộc)
Skill chỉ phân tích định tính **khi người dùng cung cấp creative assets** (video/image/thumbnail) hoặc tối thiểu là ảnh chụp màn hình keyframe.

Chấp nhận 3 mức input (ưu tiên theo thứ tự):
1. **Upload file assets** (video/image) + bảng performance có `creative_name` trùng với tên file (hoặc user cung cấp bảng mapping).
2. **Link asset** (nếu user có thể chia sẻ) + có cột `creative_id`/`ad_id` để map.
3. **Chỉ có naming convention** (UGC_Female_BeforeAfter_15s…) → chỉ suy luận theo tên, **không** kết luận về hình/âm thanh thật.

Nếu user yêu cầu phân tích định tính nhưng không có assets → phải nói rõ giới hạn và đề nghị upload tối thiểu **3–5 creative đại diện** (top + bottom) để tìm điểm winning.

### 2.4.2 – Tạo “Creative Feature Sheet” (tag định tính)
- Dùng taxonomy tại `references/creative_taxonomy.md`.
- Với **video**: tag ưu tiên dựa trên **2 giây đầu** + các cảnh demo chính (quan sát trực tiếp video hoặc keyframes user cung cấp).
- Với **image**: tag bố cục, có nhân vật, text overlay, claim, social proof, CTA.
- Không chắc chắn → đặt `unknown` (không suy đoán).

Output bảng (tối thiểu):
| Creative | format | has_person | person_type | hook_first_2s | shows_product_ui | voiceover | music | before_after | social_proof | offer_type | ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|---|

### 2.4.3 – Liên kết định tính với driver định lượng (giải thích “vì sao”)

**Bước A – Xác định driver chính**
- Dựa trên decomposition (`share_cpm/share_ctr/share_cti`) hoặc so sánh với median/benchmark:
  - **CTR driver**: CTR cao rõ rệt; CTI không nhất thiết cao.
  - **CTI driver**: CTI cao rõ rệt (intent mạnh); CTR có thể trung bình.
  - **CPM issue**: CPM cao bất thường làm CPI xấu.

**Bước B – So sánh có đối chứng (khuyến nghị mạnh)**
- Nếu có breakdown (campaign/adset/geo/OS/placement) → so sánh trong **cùng cohort**.
- Nếu không có → tối thiểu so sánh theo **format** (video vs static).

**Bước C – Rút “winning elements” theo cơ chế over-index**
- Chọn nhóm *tốt* vs *kém* theo driver:
  - CTR: top CTR (hoặc top 25%) vs bottom CTR
  - CTI: top CTI vs bottom CTI
  - CPM: CPM thấp (tốt) vs CPM cao (xấu)
- Tính tỷ lệ xuất hiện feature trong mỗi nhóm (định tính):
  - Ví dụ: `has_person=yes` xuất hiện 80% ở nhóm CTR cao vs 30% ở nhóm CTR thấp → hypothesis “nhân vật có thể tăng CTR”.
- Bắt buộc có **counter-example check**:
  - Có creative CTR cao nhưng `has_person=no` không? Nếu có, hypothesis phải refine (ví dụ: hook/overlay mới là yếu tố chính).

### 2.4.4 – Kết luận định tính (viết dưới dạng hypothesis, không khẳng định tuyệt đối)
Format khuyến nghị:
- **Giải thích theo driver**: “Creative A CPI tốt vì CTR driver (share_ctr ~60%).”
- **Hypothesis winning element**: “CTR cao có thể đến từ: has_person=yes + selfie facecam + hook pain trong 2s đầu.”
- **Chứng cứ đối chiếu**: “Trong top CTR, 4/5 creative có nhân vật; trong bottom CTR chỉ 1/5.”
- **Test kế tiếp để isolate**: đề xuất 2–3 biến thể giữ nguyên angle nhưng đổi 1 yếu tố (person vs no person, voiceover vs no voiceover…).

### 2.4.5 – Playbook theo pattern (định tính)
Tham chiếu playbook tại `references/qual_playbooks.md`.


## Bước 3: Khuyến nghị hành động

### Danh sách SCALE 🚀
Creative đạt đủ điều kiện:
- CPI ≤ ngưỡng tốt
- Và có đủ data (spend/click/install đủ để kết luận)

Format: 
> **[Tên creative]** – Scale. CPI: $X (tốt hơn benchmark X%). Lý do: [driver chính từ decomposition]. Gợi ý: tăng budget X%.

### Danh sách TẮT ❌
Creative thỏa mãn ít nhất một trong:
- CPI vượt ngưỡng kém **và** đã đủ data để kết luận
- CTR rất thấp **và** CPM cao (tốn tiền mà không ai click)

Format:
> **[Tên creative]** – Tắt. CPI: $X (tệ hơn benchmark X%). Lý do chính: [CTR/CTI/CPM] + % đóng góp.

### Danh sách CHỜ THÊM DATA ⏳
Creative chưa đủ data.

### Gợi ý cải thiện 💡
Dựa trên:
- Pattern tương quan
- Decomposition (bottleneck lớn nhất)
- Cluster playbook

Đưa 2–5 gợi ý test tiếp theo, ưu tiên các hypothesis cụ thể (hook, format, length, proof, CTA).

---

## Nguyên tắc khi phân tích

- **CPI là chỉ số quyết định** – các chỉ số khác chỉ để giải thích *tại sao* CPI tốt hay kém
- Không kết luận creative kém nếu data quá ít – luôn note “chưa đủ data”
- Luôn ghi rõ CTR đang dùng **Link CTR** hay **All CTR** (nếu xác định được)
- Nếu data có vấn đề (thiếu cột, format lỗi), báo ngay và yêu cầu bổ sung thay vì tự suy đoán
- Output hoàn toàn bằng **Tiếng Việt**
