# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager
import matplotlib




sns.set(style='whitegrid', font_scale=1.1)

DATA_PATH = os.path.join(os.path.dirname(__file__), '招生数据_clean.csv')
OUT_DIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(OUT_DIR, exist_ok=True)

NUMERIC_COLS = ['最低分', '平均分', '最高分', '最低位次', '省控线', '招生年份']


def load_and_clean(path=DATA_PATH):
    df = pd.read_csv(path)
    # 尝试将可能为数字的列转换为数值类型
    for c in NUMERIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # 去除完全为空的列/行（如果有需要）
    df = df.dropna(how='all')
    return df


def summary_stats(df):
    summary = {}
    summary['shape'] = df.shape
    summary['dtypes'] = df.dtypes.to_dict()
    summary['missing'] = df.isna().sum().sort_values(ascending=False)
    summary['describe'] = df[NUMERIC_COLS].describe()
    return summary


def save_summary_text(summary, out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('数据形状: {}\n\n'.format(summary['shape']))
        f.write('列类型:\n')
        for k, v in summary['dtypes'].items():
            f.write(f'  {k}: {v}\n')
        f.write('\n缺失值统计:\n')
        f.write(summary['missing'].to_string())
        f.write('\n\n数值字段描述性统计:\n')
        f.write(summary['describe'].to_string())


def plot_hist_avg(df):
    plt.figure(figsize=(8, 5))
    sns.histplot(df['平均分'].dropna(), bins=30, kde=True, color='#4C72B0')
    plt.xlabel('平均分')
    plt.title('平均分分布')
    p = os.path.join(OUT_DIR, '平均分_分布.png')
    plt.tight_layout()
    plt.savefig(p)
    plt.close()


def plot_box_top_schools(df, top_n=10):
    if '学校' not in df.columns:
        return
    order = df.groupby('学校')['平均分'].median().dropna().sort_values(ascending=False).head(top_n).index
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df[df['学校'].isin(order)], x='平均分', y='学校', order=order)
    plt.title(f'按学校的平均分箱线图（前{top_n} 学校）')
    p = os.path.join(OUT_DIR, '学校_平均分_boxplot.png')
    plt.tight_layout()
    plt.savefig(p)
    plt.close()


def plot_trend_top_majors(df, top_n=6):
    if '专业' not in df.columns or '招生年份' not in df.columns:
        return
    majors = df.groupby('专业')['平均分'].mean().dropna().sort_values(ascending=False).head(top_n).index
    df_trend = df[df['专业'].isin(majors)].groupby(['招生年份', '专业'])['平均分'].mean().reset_index()
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df_trend, x='招生年份', y='平均分', hue='专业', marker='o')
    plt.title('Top 专业的平均分随年份变化')
    p = os.path.join(OUT_DIR, '专业_平均分_趋势.png')
    plt.tight_layout()
    plt.savefig(p)
    plt.close()


def _sanitize_filename(s: str) -> str:
    """简单的文件名清理，移除或替换文件名中的非法字符"""
    invalid = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for ch in invalid:
        s = s.replace(ch, '_')
    s = s.replace(' ', '_')
    return s


def plot_school_major_yearly(df, school: str, major: str, year_min: int = 2020, year_max: int = 2024):
    """绘制同一所`school`、同一`major`从 `year_min` 到 `year_max` 的录取分数（平均分）和录取排名（最低位次）折线图。

    - 输入: `df` 包含列 `学校`, `专业`, `招生年份`, `平均分`, `最低位次`。
    - 输出: 将图片保存到 `figures/`，文件名格式如：{学校}_{专业}_分数与位次_趋势.png
    """
    cols_needed = ['学校', '专业', '招生年份', '平均分', '最低位次']
    for c in cols_needed:
        if c not in df.columns:
            raise ValueError(f"缺少列: {c}")

    sub = df[(df['学校'] == school) & (df['专业'] == major) & (df['招生年份'].between(year_min, year_max))]
    if sub.empty:
        print(f'未找到 {school} - {major} 在 {year_min}-{year_max} 的记录')
        return

    agg = sub.groupby('招生年份').agg({'平均分': 'mean', '最低位次': 'median'}).reset_index().sort_values('招生年份')

    plt.figure(figsize=(10, 6))
    ax1 = plt.gca()
    ax2 = ax1.twinx()

    ax1.plot(agg['招生年份'], agg['平均分'], marker='o', color='#1f77b4', label='平均分')
    ax2.plot(agg['招生年份'], agg['最低位次'], marker='s', color='#ff7f0e', label='最低位次')

    ax1.set_xlabel('招生年份')
    ax1.set_ylabel('平均分')
    ax2.set_ylabel('最低位次 (越小表示位次越靠前)')
    ax2.invert_yaxis()  # 将位次轴反向显示，便于视觉上和分数高低对应

    plt.title(f"{school} - {major} ({year_min}-{year_max}) 分数与位次趋势")

    # 合并图例
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='best')

    fname = _sanitize_filename(f"{school}_{major}_分数与位次_趋势.png")
    p = os.path.join(OUT_DIR, fname)
    plt.tight_layout()
    plt.savefig(p)
    plt.close()
    print('已保存：', p)


def plot_school_multiple_majors(df, school: str, majors: list = None, metric: str = '平均分', year_min: int = 2020, year_max: int = 2024, top_n: int = 6):
    """绘制同一所学校中若干专业在指定年份范围内的 `metric` 折线图。

    - 如果 `majors` 为 None，会选择该学校中按 `metric` 平均值排序的前 `top_n` 个专业。
    - `metric` 默认是 `平均分`，也可以是 `最低分` 等数值列。
    """
    if '学校' not in df.columns or '专业' not in df.columns or '招生年份' not in df.columns:
        raise ValueError('数据缺少必须的列：学校、专业或招生年份')

    school_df = df[df['学校'] == school].copy()
    if school_df.empty:
        print(f'未找到学校: {school}')
        return

    if majors is None:
        if metric not in school_df.columns:
            raise ValueError(f'度量列 {metric} 不存在')
        majors = school_df.groupby('专业')[metric].mean().dropna().sort_values(ascending=False).head(top_n).index.tolist()

    sub = school_df[school_df['专业'].isin(majors) & school_df['招生年份'].between(year_min, year_max)]
    if sub.empty:
        print('未找到符合条件的数据')
        return

    trend = sub.groupby(['招生年份', '专业'])[metric].mean().reset_index()

    plt.figure(figsize=(11, 6))
    sns.lineplot(data=trend, x='招生年份', y=metric, hue='专业', marker='o')
    plt.title(f"{school} 不同专业 {metric} 趋势 ({year_min}-{year_max})")
    plt.xlabel('招生年份')
    plt.ylabel(metric)

    fname = _sanitize_filename(f"{school}_不同专业_{metric}_趋势.png")
    p = os.path.join(OUT_DIR, fname)
    plt.tight_layout()
    plt.savefig(p)
    plt.close()
    print('已保存：', p)



def plot_score_vs_rank(df, sample_n=3000):
    if '最低分' not in df.columns or '最低位次' not in df.columns:
        return
    sub = df[['最低分', '最低位次', '招生年份']].dropna()
    if len(sub) > sample_n:
        sub = sub.sample(sample_n, random_state=42)
    plt.figure(figsize=(8, 6))
    sc = plt.scatter(sub['最低位次'], sub['最低分'], c=sub['招生年份'], cmap='viridis', alpha=0.7)
    plt.xlabel('最低位次')
    plt.ylabel('最低分')
    plt.title('最低分 vs 最低位次（采样）')
    plt.colorbar(sc, label='招生年份')
    p = os.path.join(OUT_DIR, '最低分_vs_最低位次.png')
    plt.tight_layout()
    plt.savefig(p)
    plt.close()


def main():
    matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    matplotlib.rcParams['axes.unicode_minus'] = False
    print('加载数据...')
    df = load_and_clean()
    print('样本量:', len(df))

    print('计算统计摘要...')
    summary = summary_stats(df)
    save_summary_text(summary, os.path.join(OUT_DIR, 'analysis_summary.txt'))
    print('摘要已写入:', os.path.join(OUT_DIR, 'analysis_summary.txt'))

    print('绘图：平均分分布')
    plot_hist_avg(df)
    print('绘图：学校箱线图')
    plot_box_top_schools(df)
    print('绘图：专业平均分趋势')
    plot_trend_top_majors(df)
    print('绘图：最低分 vs 最低位次')
    plot_score_vs_rank(df)
    plot_school_major_yearly(df, school='四川大学', major='临床医学', year_min=2020, year_max=2024)
    plot_school_multiple_majors(df, school='四川大学', majors=None, metric='平均分', year_min=2020, year_max=2024, top_n=10)
    print('所有图表已保存到:', OUT_DIR)


if __name__ == '__main__':
    main()
