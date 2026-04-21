# datasetslimer 工具

一个用于生成、压缩和对比数据集的工具包，包含三个主要脚本：

- `generate_random_metadata.py` - 生成随机元数据
- `generate_subsets.py` - 使用 K-means 聚类生成代表性数据集子集
- `compare_subsets.py` - 对比原始数据集与压缩子集

## 目录结构

```
datasetslimer/
├── generate_random_metadata.py    # 生成随机元数据
├── generate_subsets.py            # 生成数据集子集
├── compare_subsets.py             # 对比数据集子集
├── info_sample.json               # 样例信息文件
├── multi_data_sample/             # 样例原始数据
├── multi_data_sample_compressed/  # 样例压缩数据
└── comparison_figures_sample/     # 样例对比图表
```

---

## 1. generate_random_metadata.py - 生成随机元数据

### 功能说明

该脚本用于生成带有评分和难度分布的随机元数据集。可以从现有 info.json 文件生成，或从头创建全新的数据集。

### 命令行参数

| 参数 | 简称 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--info_file` | - | str | None | 现有 info.json 文件路径（如果指定，其他生成参数将被忽略） |
| `--num_subsets` | - | int | 3 | 要生成的子集数量 |
| `--max_dimension` | - | int | 3 | difficulty_map 的最大维度 |
| `--max_avg` | - | float | 0.5 | 最大平均分数 |
| `--case_range` | - | int[] | [100, 200] | 样本数量范围 [最小值, 最大值] |
| `--score_types` | - | str[] | ['score0', 'score1', 'score2'] | 分数列名称 |
| `--output_dir` | - | str | './generated_data' | 输出目录 |

### 使用示例

#### 从头生成数据集

```bash
python generate_random_metadata.py --num_subsets 3 --case_range 100 200 --output_dir ./multi_data_sample
```

#### 使用现有 info.json 生成

```bash
python generate_random_metadata.py --info_file info_sample.json --output_dir ./multi_data_sample
```

### 输入输出详解

#### 输入
- **info_sample.json** (样例): 包含数据集配置信息的 JSON 文件
  ```json
  [
      {
          "name": "random_metadata0",    // 数据集名称
          "count": 160,                   // 样本数量
          "avg_scores": [0.05, 0.44, 0.35],  // 各分数列的平均值
          "difficulty_map": {             // 难度映射
              "level0": 0,
              "level1": 1,
              "level2": 2
          }
      },
      ...
  ]
  ```

#### 输出 (multi_data_sample/)
- **info.json**: 记录各数据集信息的配置文件
- **{dataset_name}.csv**: 每个数据集对应的 CSV 文件
  - `id`: 样本唯一标识符
  - `score0`, `score1`, `score2`: 评分列（数值 0-1）
  - `difficulty`: 难度级别（如 level0, level1, level2）

  样例数据:
  ```csv
  id,score0,score1,score2,difficulty
  eyoqdm,0.13,0.65,0.37,level0
  glzgurmuplzu,0.0,0.45,0.51,level0
  ngomuim,0.0,0.55,0.43,level2
  ```

---

## 2. generate_subsets.py - 生成数据集子集

### 功能说明

该脚本使用 K-means 聚类算法从原始数据集中抽取具有代表性的子集，同时也会生成随机子集作为对比。

### 命令行参数

| 参数 | 简称 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | `-i` | str | **必填** | 包含 info.json 和元数据 CSV 文件的目录 |
| `--output` | `-o` | str | **必填** | 保存输出样本的目录 |
| `--compression-ratio` | `-r` | float | 0.1 | 目标压缩比 (0-1) |
| `--random-state` | `-s` | int | 42 | 随机种子（用于可复现性） |

### 使用示例

```bash
python generate_subsets.py -i ./multi_data_sample -o ./multi_data_sample_compressed -r 0.1
```

### 输入输出详解

#### 输入
- **multi_data_sample/info.json**: 数据集信息配置
- **multi_data_sample/{dataset_name}.csv**: 原始数据集 CSV 文件

#### 输出 (multi_data_sample_compressed/)
该目录下包含两个子目录：

**representative/** (代表性子集)
- **info.json**: 代表性子集的信息
- **{dataset_name}.csv**: K-means 代表性样本
- **{dataset_name}_ids.json**: 代表性样本的 ID 列表

**random/** (随机子集)
- **info.json**: 随机子集的信息
- **{dataset_name}.csv**: 随机样本
- **{dataset_name}_ids.json**: 随机样本的 ID 列表

#### 代表性子集抽样策略
1. 使用 K-means 将数据聚类为 n 个簇
2. 首先选择每个簇中距离质心最近的样本
3. 剩余样本根据各簇大小比例分配抽取

---

## 3. compare_subsets.py - 对比数据集子集

### 功能说明

该脚本对比原始数据集与压缩子集，生成可视化图表和统计摘要，评估代表性抽样方法的效果。

### 命令行参数

| 参数 | 简称 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--original` | `-o` | str | **必填** | 包含原始数据集和 info.json 的目录 |
| `--compressed` | `-c` | str | **必填** | 包含压缩数据集的目录（有 representative 和 random 子目录） |
| `--figures-dir` | `-f` | str | 'figures' | 保存图表的目录 |

### 使用示例

```bash
python compare_subsets.py -o ./multi_data_sample -c ./multi_data_sample_compressed -f ./comparison_figures_sample
```

### 输入输出详解

#### 输入
- **multi_data_sample/**: 原始数据集目录
- **multi_data_sample_compressed/**: 压缩数据集目录（包含 representative 和 random）

#### 输出 (comparison_figures_sample/)
- **{dataset_name}_means_comparison.png**: 各分数列均值对比柱状图
- **{dataset_name}_difficulty_distributions.png**: 难度分布对比柱状图
- **comparison_summary.json**: 详细的统计对比摘要

#### comparison_summary.json 结构
```json
[
    {
        "dataset_name": "random_metadata0",
        "sizes": {
            "full": 160,              // 原始数据集大小
            "representative": 16,     // 代表性子集大小
            "random": 16              // 随机子集大小
        },
        "means": {
            "Full Dataset": {         // 完整数据集各分数列均值
                "score0": 0.087,
                "score1": 0.433,
                "score2": 0.339
            },
            "K-means Representative": { ... },  // 代表性子集均值
            "Random": { ... }                     // 随机子集均值
        },
        "correlations": {
            "representative": {
                "full": -0.011,     // 完整数据集相关性均值
                "sample": -0.161     // 代表性子集相关性均值
            },
            "random": { ... }
        }
    },
    ...
]
```

---

## 完整工作流示例

1. **生成随机数据集**
   ```bash
   python generate_random_metadata.py --num_subsets 3 --output_dir ./my_data
   ```

2. **生成压缩子集**
   ```bash
   python generate_subsets.py -i ./my_data -o ./my_data_compressed -r 0.1
   ```

3. **对比评估**
   ```bash
   python compare_subsets.py -o ./my_data -c ./my_data_compressed -f ./my_comparison
   ```

## 依赖库

- pandas
- numpy
- scikit-learn
- matplotlib
