from datasets import load_dataset
import pandas as pd

# 1. 加载数据集，重点是 streaming=True
# 这意味着我们只是建立了连接，没有下载任何数据到硬盘
print("正在建立连接...")
dataset = load_dataset("afwull/WikiTQ", split="train", streaming=True)

# 2. 获取前100条数据
# take(100) 就像一个阀门，只允许流出100条数据
print("正在获取前100条数据...")
mini_dataset = list(dataset.take(100))

# 3. 这里的每条数据通常是一个字典，包含问题、答案和对应的表格内容
# 我们可以打印第一条看看结构
print("\n=== 第一条数据示例 ===")
print(mini_dataset[0].keys()) 
# 输出通常包括: 'id', 'question', 'answers', 'table' (表格内容本身)

# 4. 如果你想存下来方便看，转成 Pandas DataFrame 或保存为 CSV
df = pd.DataFrame(mini_dataset)
df.to_csv("wiki_table_100_samples.csv", index=False)

print(f"\n成功！已下载 {len(df)} 条数据并保存为 CSV。")