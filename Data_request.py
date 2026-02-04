import requests
import pandas as pd
import time
from fake_useragent import UserAgent
all_data = []
# 请求 URL

def update_url(url, year1, page):
    # 替换年份和页数
    url = url.replace(f"year=2020", f"year={year1}")  # 替换年份
    url = url.replace(f"page=1", f"page={page}")    # 替换页数
    return url


if __name__ == '__main__':
    urls = [
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=99&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 四川大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=661&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 电子科技大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=264&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 成都中医药大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=101&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 西南财经大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=51&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 西南交通大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=263&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 西南科技大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=2491&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 成都大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=270&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 成都信息工程大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=273&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 四川轻化工大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=245&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 西华大学
        'https://api.zjzw.cn/web/api/?like_spname=&local_batch_id=7&local_province_id=51&local_type_id=1&page=1&school_id=100&size=10&sp_xuanke=&special_group=&uri=apidata/api/gk/score/special&year=2020',
        # 四川农业大学
    ]
    # 遍历年份和页数的范围
    for url in urls:
       for year1 in range(2020, 2025):
          for page in range(1, 6):
                updated_url = update_url(url, year1, page)
                print(updated_url)
                ua = UserAgent()
                print(ua.random)  # 随机产生
                headers = {
                    'User-Agent': ua.random  # 伪装
                }
                try:
                    res = requests.get(updated_url, headers=headers, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        if "data" in data and "item" in data["data"]:
                            for item in data["data"]["item"]:
                                all_data.append({
                                    "学校": item.get("name", ""),
                                    "专业": item.get("spname", ""),
                                    "最低分": item.get("min", ""),
                                    "平均分": item.get("average", ""),
                                    "最高分": item.get("max", ""),
                                    "招生年份": item.get("year", ""),
                                    "科类": item.get("local_type_name", ""),
                                    "批次": item.get("local_batch_name", ""),
                                    "最低位次": item.get("min_section", ""),
                                    "省控线": item.get("proscore", ""),
                                    "专业类别": item.get("level3_name", ""),
                                })
                        else:
                            print(f" 数据为空或格式不匹配: {updated_url}")
                    else:
                        print(f" 请求失败，状态码：{res.status_code}, URL: {updated_url}")
                        time.sleep(2)  # 等待 2 秒再重试
                except requests.exceptions.RequestException as e:
                    print(f" 请求异常: {e}")
                    time.sleep(5)  # 请求异常时等待 5 秒
    # **存储为 CSV 文件**
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv("招生数据.csv", index=False, encoding="UTF-8")
        print(" 数据已保存为 CSV 文件：招生数据.csv")
