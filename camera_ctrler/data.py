import redis
r = redis.Redis(host='redis', port=6379, db=0)
# 假設攝影機的 URL 列表已經提前準備好
camera_urls = [
"https://cctv-ss03.thb.gov.tw:443/T144-001K+150E",
"https://cctv-ss03.thb.gov.tw:443/T144-003K+200E",
"https://cctv-ss03.thb.gov.tw:443/T144-003K+250W",
]

count = 0
# 清空舊的攝影機列表
for worker_id in range(1, 4):
    worker_key = f'worker_{worker_id}_urls'
    r.delete(worker_key)
    count += 1

# # 分配新的攝影機到容器
# for url in camera_urls:
#     worker_id = count%3 + 1  # 工作器 ID
#     worker_key = f'worker_{worker_id}_urls'
#     r.sadd(worker_key, f'{count}|{url}')
#     count += 1

# 發布更新事件給所有工作器
for worker_id in range(1, 4):
    worker_key = f'worker_{worker_id}_urls'
    r.publish(f'{worker_key}_update', 'updated')