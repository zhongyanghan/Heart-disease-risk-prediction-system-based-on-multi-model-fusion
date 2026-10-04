# 数据集说明

训练数据 `data_heart.csv` **未随本仓库分发**，请自行获取后放置于**仓库根目录**，供 `notebooks/heart_disease_multi_model_analysis.ipynb` 复现训练流程使用。

> 运行桌面系统（`app/main.py`）不需要数据集，仓库自带训练好的 `models/model.pkl`。

## 数据格式要求

- CSV 文件，文件名 `data_heart.csv`
- 目标列为 `Result`（1 = 患心脏病，0 = 未患心脏病）
- 分类变量 `CpType`、`RestingECG`、`Thalassemia` 在训练时会被 One-Hot 编码，预测时输入特征需与 `models/model.pkl` 训练时的特征列保持一致（参见 notebook 中 `df_encoded` 的列结构）

## 字段说明

| 字段 | 说明 |
| --- | --- |
| `Age` | 年龄 |
| `Gender` | 性别（0 / 1） |
| `RestingBP` | 静息血压 |
| `SerumChol` | 血清胆固醇 |
| `FBG` | 空腹血糖 |
| `HRmax` | 最大心率 |
| `Angina` | 是否运动诱发心绞痛 |
| `StDescent` | 运动引起的 ST 段压低值（对应常见数据集中的 Oldpeak） |
| `StSlope` | ST 段斜率 |
| `GaNum` | 数值型心脏检查特征（原始数据集字段，具体医学含义请结合数据来源确认） |
| `CpType` | 胸痛类型（One-Hot 编码为 `CpType_0` ~ `CpType_4`） |
| `RestingECG` | 静息心电图结果（One-Hot 编码为 `RestingECG_0` ~ `RestingECG_2`） |
| `Thalassemia` | 地中海贫血/铊应激试验结果（One-Hot 编码为 `Thalassemia_1`、`Thalassemia_2`、`Thalassemia_fixed`、`Thalassemia_normal`、`Thalassemia_reversible`） |
| `Result` | 目标变量：是否患心脏病（1 = 患，0 = 未患） |
