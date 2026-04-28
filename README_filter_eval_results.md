# Filter Eval Results Script

## 功能
- 读取 `prompts_per_dimension` 目录下的所有 txt 文件，提取每个维度的 case_name
- 读取输入目录下的所有 `*eval_results.json` 文件
- 过滤每个维度中不匹配的 case（基于 case_name）
- 重新计算剩余 case 的平均分（处理 boolean 类型的得分）
- 将修改后的文件保存到输出目录

## 使用方法

```bash
python filter_eval_results.py --prompts_dir <prompts_per_dimension目录路径> --input_dir <输入目录路径> --output_dir <输出目录路径>
```

### 参数说明
- `--prompts_dir`: 包含各个维度 case_name 的 txt 文件目录
- `--input_dir`: 包含 eval_results.json 文件的目录
- `--output_dir`: 保存处理后文件的目录

## 示例

```bash
python filter_eval_results.py --prompts_dir "d:\for_developing\syh_datasetslimer\datasetslimer\prompts_per_dimension" --input_dir "d:\for_developing\syh_datasetslimer\datasetslimer\test_eval_results" --output_dir "d:\for_developing\syh_datasetslimer\datasetslimer\filtered_results"
```

## 处理逻辑
1. 遍历 `prompts_per_dimension` 目录下的所有 txt 文件，构建维度到 case_name 集合的映射
2. 遍历输入目录下的所有 `*eval_results.json` 文件
3. 对于每个 json 文件，遍历其中的每个维度
4. 对于每个维度，过滤出 case_name 在对应 txt 文件中的 case
5. 重新计算过滤后 case 的平均分（boolean 类型的得分会被转换为 1.0 或 0.0）
6. 更新 json 文件中的平均分和 case 列表
7. 将修改后的文件保存到输出目录

## 注意事项
- 脚本会忽略在 `prompts_per_dimension` 目录中没有对应 txt 文件的维度
- case_name 严格匹配 `{case_name}-{num}.mp4` 格式中的 `case_name` 部分
- 对于 `video_results` 为 boolean 类型的情况，`true` 对应 1.0 分，`false` 对应 0.0 分