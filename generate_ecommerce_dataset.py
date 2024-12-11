import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# 设置随机种子以确保可重复性
np.random.seed(42)

# 生成大规模电商用户行为数据集
def generate_ecommerce_dataset(num_records=50000):
    # 用户属性
    user_ids = range(1, 10001)  # 1万个唯一用户
    age_groups = ['18-25', '26-35', '36-45', '46-55', '56+']
    genders = ['Male', 'Female']
    education_levels = ['High School', 'Bachelor', 'Master', 'PhD']
    income_levels = ['Low', 'Medium', 'High']
    
    # 产品类别
    product_categories = [
        'Electronics', 'Clothing', 'Books', 'Home & Kitchen', 
        'Sports', 'Beauty', 'Toys', 'Furniture'
    ]
    
    # 城市
    cities = [
        'Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Chengdu', 
        'Hangzhou', 'Nanjing', 'Wuhan', 'Xi\'an', 'Suzhou'
    ]
    
    # 生成数据
    data = {
        'user_id': [],
        'age_group': [],
        'gender': [],
        'education': [],
        'income_level': [],
        'city': [],
        'product_category': [],
        'purchase_amount': [],
        'discount_applied': [],
        'is_first_purchase': [],
        'purchase_time': [],
        'device_type': [],
        'is_mobile': [],
        'loyalty_points': [],
        'shipping_method': [],
        'review_score': []
    }
    
    for _ in range(num_records):
        data['user_id'].append(random.choice(user_ids))
        data['age_group'].append(random.choice(age_groups))
        data['gender'].append(random.choice(genders))
        data['education'].append(random.choice(education_levels))
        data['income_level'].append(random.choice(income_levels))
        data['city'].append(random.choice(cities))
        data['product_category'].append(random.choice(product_categories))
        
        # 购买金额：不同类别价格范围不同
        category_price_ranges = {
            'Electronics': (500, 5000),
            'Clothing': (50, 500),
            'Books': (20, 200),
            'Home & Kitchen': (100, 1000),
            'Sports': (50, 800),
            'Beauty': (30, 300),
            'Toys': (20, 200),
            'Furniture': (200, 5000)
        }
        category = data['product_category'][-1]
        min_price, max_price = category_price_ranges[category]
        data['purchase_amount'].append(round(np.random.uniform(min_price, max_price), 2))
        
        data['discount_applied'].append(random.random() < 0.3)  # 30%概率有折扣
        data['is_first_purchase'].append(random.random() < 0.05)  # 5%是首次购买
        
        # 随机生成购买时间（过去一年）
        days_ago = random.randint(0, 365)
        data['purchase_time'].append((datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S'))
        
        # 设备类型
        device_types = ['Desktop', 'Mobile', 'Tablet']
        weights = [0.4, 0.5, 0.1]  # 移动设备占主导
        data['device_type'].append(np.random.choice(device_types, p=weights))
        data['is_mobile'].append(data['device_type'][-1] != 'Desktop')
        
        # 忠诚度积分
        data['loyalty_points'].append(random.randint(0, 1000))
        
        # 配送方式
        shipping_methods = ['Standard', 'Express', 'Next Day']
        shipping_weights = [0.6, 0.3, 0.1]
        data['shipping_method'].append(np.random.choice(shipping_methods, p=shipping_weights))
        
        # 评价分数
        data['review_score'].append(round(np.random.normal(4, 1), 1))
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 处理评价分数，确保在1-5范围内
    df['review_score'] = df['review_score'].clip(1, 5)
    
    return df

# 生成并保存数据集
ecommerce_data = generate_ecommerce_dataset()
ecommerce_data.to_csv('E:\\DSSec\\conn\\uploads\\ecommerce_user_behavior.csv', index=False)

# 打印数据集基本信息
print("数据集生成完成！")
print(f"总记录数: {len(ecommerce_data)}")
print("\n数据集预览:")
print(ecommerce_data.head())

print("\n数据集统计信息:")
print(ecommerce_data.describe())

print("\n数据集列信息:")
print(ecommerce_data.info())
