## Report 
## Reporter: Thuận
## date: 15/10/2026

**Overview**
Phân tích được 276 Events (13 Predictions, 13 Realities, 13 Evaluations)
=> Dự đoán hướng đi đúng với thực tế (9/13) trường hợp khoảng 69,2%, nhưng số mẫu khá nhỏ và tổng 13 predictions đều dự đoán UP nên chưa thể kết luận được liệu agent có đi đúng hướng hay không
=> Evaluation chưa đánh giá được reason score (hiện tại đang bị NULL ở tất cả các evaluations). Điều này xảy ra là do toàn bộ actual_drivers của 13 Realities đều rỗng. Khả năng là do t prompt chưa chính xác ở phần tính này. Vì actual drivers đều rỗng nên tính điểm magnitude khá thấp và một số thì có vẻ không tương xứng với thực tế. 
=> Dự đoán đúng hướng nhưng chênh lệch so với thực tế khá nhiều. Horizon chỉ trong 1-2 tuần mà dự đoán tăng hẳn 10-30% trong khi thực tế chỉ tăng nhẹ khoảng vài % cao lắm là gần 10%.


**Bảng đối chiếu với thực tế**
| Ver| Kỳ kết thúc| Dự báo   | Thực tế | Kết quả | Dir. score | Matching|

| 1 | 08/07/2025  | UP (+20%)| +32.54% | Đúng    | 1.00       | 0.500 |
| 2 | 15/07/2025  | UP (+12%)| +1.85%  | Đúng    | 1.00       | 0.500 |
| 3 | 22/07/2025  | UP (+12%)| -0.11%  | Sai     | 0.00       | 0.000 |
| 4 | 29/07/2025  | UP (+12%)| +1.44%  | Đúng    | 1.00       | 0.500 |
| 5 | 05/08/2025  | UP (+12%)| +2.96%  | Đúng    | 1.00       | 0.548 |
| 6 | 12/08/2025  | UP (+3%) | +0.28%  | Đúng    | 1.00       | 0.864 |
| 7 | 19/08/2025  | UP (+8%) | -3.68%  | Sai     | 0.00       | 0.000 |
| 8 | 26/08/2025  | UP (+12%)| -1.35%  | Sai     | 0.00       | 0.000 |
| 9 | 03/09/2025  | UP (+8%) | +0.66%  | Đúng    | 1.00       | 0.633 |
| 10| 10/09/2025  | UP (+8%) | -0.99%  | Sai     | 0.00       | 0.051 |
| 11| 17/09/2025  | UP (+8%) | +1.93%  | Đúng    | 1.00       | 0.696 |
| 12| 24/09/2025  | UP (+8%) | +0.03%  | Đúng    | 1.00       | 0.601 |
| 13| 01/10/2025  | UP (+15%)| +1.87%  | Đúng    | 1.00       | 0.500 |

## Nhìn chung: hướng đi dự báo đúng 9/13 sai ở ver 3,7,8,10 

***
Các AUDIT lỗi và lỗ hổng nhận thấy

1. Cả 13 Predictions đều UP
2. expectation_change thường vào khoảng 0.08-0.12 trong khoảng 1 tuần trong khi actual value thì thấp hơn
3. Không đồng đều horizon, horizon ver1 dài hơn hẳn các ver còn lại.
4. Lỗ hổng về tính nhất quán cuar các tiêu chí dự báo. Trong record.json thì các resolution_criteria của nhiều predictions chẳng hạn ver 1,2, 5, 10 yêu cầu đánh giá tăng trưởng doanh thu Intelligent Cloud/Azure hoặc mức độ ứng dụng và  thương mại hóa AI. Tuy nhiên ở Reality.Metrics của cả 13 Reality đều sử dụng adjusted_price_return => Vì vậy điểm evaluation phản ánh đúng hướng của stocks nhưng không đủ căn cứ để kết luận các tiêu chí kinh doanh.
4. Cần kiểm tra lại các tính Matching score, Magnitude score, Direction score, Reason score. 

***

## Hướng optimize phần Predictions và Evaluation của t
1. Viết lại contract của Prediction, Reality, Evaluation
2. Bắt agent xét đủ 3 hướng UP/DOWN/FLAT, yêu cầu báo xác suất cho mỗi hướng và lý do bác bỏ các lựa chọn còn lại. Phải có evidences cho mỗi xác suất.
3. T nghĩ nên thêm schema validation + retry có giới hạn để bắt agent từ chối các prediction thiếu các tiêu chí như horizon, baseline, metric


## Conclusion: Dữ liệu hiện tại cho thấy ba rủi ro nền tảng: thiên lệch dự đoán UP, độ lớn dự báo có vẻ không cùng thang đo với biến động thực tế, và Evaluation chưa chấm reasoning/driver. Cần sửa contract và test số học so sánh với baseline đơn giản ròi mới tối ưu prompt hoặc model