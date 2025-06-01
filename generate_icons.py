#!/usr/bin/env python3
"""
PWA 圖標生成器
為 VisionFlow 生成各種尺寸的 PWA 圖標
"""

import os
from PIL import Image, ImageDraw, ImageFont
import colorsys

def create_visionflow_icon(size, output_path):
    """創建 VisionFlow 圖標"""
    # 創建畫布
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 背景漸變
    for y in range(size):
        # 計算漸變顏色
        ratio = y / size
        r = int(59 + (99 - 59) * ratio)    # 從 #3b82f6 到 #6366f1
        g = int(130 + (102 - 130) * ratio)
        b = int(246 + (241 - 246) * ratio)
        
        # 繪製線條
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # 添加圓角效果（簡化版）
    mask = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(mask)
    corner_radius = size // 6
    mask_draw.rounded_rectangle([0, 0, size, size], corner_radius, fill=(255, 255, 255, 255))
    
    # 應用遮罩
    img = Image.alpha_composite(img, mask)
    
    # 添加眼睛圖標
    eye_size = size // 3
    eye_x = (size - eye_size) // 2
    eye_y = (size - eye_size) // 2
    
    # 外圈
    draw.ellipse([eye_x, eye_y, eye_x + eye_size, eye_y + eye_size], 
                 fill=(255, 255, 255, 255), outline=(255, 255, 255, 255), width=2)
    
    # 瞳孔
    pupil_size = eye_size // 3
    pupil_x = eye_x + (eye_size - pupil_size) // 2
    pupil_y = eye_y + (eye_size - pupil_size) // 2
    draw.ellipse([pupil_x, pupil_y, pupil_x + pupil_size, pupil_y + pupil_size], 
                 fill=(0, 0, 0, 255))
    
    # 高光
    highlight_size = pupil_size // 3
    highlight_x = pupil_x + pupil_size // 4
    highlight_y = pupil_y + pupil_size // 4
    draw.ellipse([highlight_x, highlight_y, highlight_x + highlight_size, highlight_y + highlight_size], 
                 fill=(255, 255, 255, 255))
    
    # 保存圖片
    img.save(output_path, 'PNG')
    print(f"已生成: {output_path} ({size}x{size})")

def create_favicon():
    """創建 Favicon"""
    # 創建 32x32 和 16x16 的 favicon
    for size in [32, 16]:
        output_path = f'/Users/litaicheng/Desktop/VisionFlow/web/static/images/favicon-{size}x{size}.png'
        create_visionflow_icon(size, output_path)

def create_apple_touch_icon():
    """創建 Apple Touch Icon"""
    output_path = '/Users/litaicheng/Desktop/VisionFlow/web/static/images/apple-touch-icon.png'
    create_visionflow_icon(180, output_path)

def create_pwa_icons():
    """創建 PWA 圖標"""
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        output_path = f'/Users/litaicheng/Desktop/VisionFlow/web/static/images/icon-{size}x{size}.png'
        create_visionflow_icon(size, output_path)

def create_badge_icon():
    """創建通知徽章圖標"""
    size = 72
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 紅色圓圈
    draw.ellipse([0, 0, size, size], fill=(239, 68, 68, 255))
    
    # 白色驚嘆號
    font_size = size // 2
    try:
        # 嘗試使用系統字體
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "!"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 2
    
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    output_path = '/Users/litaicheng/Desktop/VisionFlow/web/static/images/badge-72x72.png'
    img.save(output_path, 'PNG')
    print(f"已生成: {output_path}")

def create_action_icons():
    """創建操作圖標"""
    icons = {
        'view-icon.png': '👁',
        'dismiss-icon.png': '✕',
        'camera-icon.png': '📷',
        'alert-icon.png': '⚠',
        'analytics-icon.png': '📊'
    }
    
    for filename, emoji in icons.items():
        size = 96
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 背景圓圈
        draw.ellipse([8, 8, size-8, size-8], fill=(59, 130, 246, 255))
        
        # emoji 文字（簡化版，實際應使用圖標字體）
        font_size = size // 3
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial Unicode.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # 計算文字位置
        bbox = draw.textbbox((0, 0), emoji, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), emoji, fill=(255, 255, 255, 255), font=font)
        
        output_path = f'/Users/litaicheng/Desktop/VisionFlow/web/static/images/{filename}'
        img.save(output_path, 'PNG')
        print(f"已生成: {output_path}")

def create_placeholder_images():
    """創建佔位符圖片"""
    # 創建攝影機預覽佔位符
    for i in range(1, 9):
        size = (640, 480)
        img = Image.new('RGB', size, (26, 26, 26))
        draw = ImageDraw.Draw(img)
        
        # 網格背景
        grid_size = 40
        for x in range(0, size[0], grid_size):
            draw.line([(x, 0), (x, size[1])], fill=(40, 40, 40))
        for y in range(0, size[1], grid_size):
            draw.line([(0, y), (size[0], y)], fill=(40, 40, 40))
        
        # 攝影機圖標
        font_size = 48
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        text = f"📷 攝影機 {i}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text((x, y), text, fill=(156, 163, 175), font=font)
        
        # 狀態信息
        status_font_size = 24
        try:
            status_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", status_font_size)
        except:
            status_font = ImageFont.load_default()
        
        status_text = "1920x1080 • 30 FPS"
        bbox = draw.textbbox((0, 0), status_text, font=status_font)
        text_width = bbox[2] - bbox[0]
        
        x = (size[0] - text_width) // 2
        y = y + 60
        
        draw.text((x, y), status_text, fill=(107, 114, 128), font=status_font)
        
        output_path = f'/Users/litaicheng/Desktop/VisionFlow/web/static/images/camera_{i}_preview.jpg'
        img.save(output_path, 'JPEG', quality=85)
        print(f"已生成: {output_path}")

def create_screenshot_placeholders():
    """創建截圖佔位符"""
    # 桌面截圖
    size = (1280, 720)
    img = Image.new('RGB', size, (15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    # 模擬儀表板
    draw.rectangle([50, 50, size[0]-50, 100], fill=(59, 130, 246))
    
    font_size = 36
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    draw.text((60, 60), "VisionFlow 智能監控系統", fill=(255, 255, 255), font=font)
    
    # 模擬圖表區域
    chart_areas = [
        (50, 130, 400, 350),
        (430, 130, 780, 350),
        (810, 130, size[0]-50, 350),
        (50, 380, 400, 600),
        (430, 380, size[0]-50, 600)
    ]
    
    for i, (x1, y1, x2, y2) in enumerate(chart_areas):
        draw.rectangle([x1, y1, x2, y2], fill=(30, 41, 59), outline=(59, 130, 246))
        
        # 標題
        title_font_size = 18
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", title_font_size)
        except:
            title_font = ImageFont.load_default()
        
        titles = ["即時監控", "檢測統計", "系統狀態", "趨勢分析", "攝影機管理"]
        if i < len(titles):
            draw.text((x1 + 10, y1 + 10), titles[i], fill=(156, 163, 175), font=title_font)
    
    output_path = '/Users/litaicheng/Desktop/VisionFlow/web/static/images/screenshot-desktop.png'
    img.save(output_path, 'PNG')
    print(f"已生成: {output_path}")
    
    # 手機截圖
    mobile_size = (360, 640)
    mobile_img = Image.new('RGB', mobile_size, (15, 23, 42))
    mobile_draw = ImageDraw.Draw(mobile_img)
    
    # 標題欄
    mobile_draw.rectangle([0, 0, mobile_size[0], 60], fill=(59, 130, 246))
    mobile_draw.text((20, 20), "VisionFlow", fill=(255, 255, 255), font=title_font)
    
    # 內容區域
    content_y = 80
    for i in range(4):
        y1 = content_y + i * 130
        y2 = y1 + 120
        mobile_draw.rectangle([20, y1, mobile_size[0]-20, y2], fill=(30, 41, 59), outline=(59, 130, 246))
    
    mobile_output_path = '/Users/litaicheng/Desktop/VisionFlow/web/static/images/screenshot-mobile.png'
    mobile_img.save(mobile_output_path, 'PNG')
    print(f"已生成: {mobile_output_path}")

def main():
    """主函數"""
    print("🎨 正在生成 VisionFlow PWA 圖標和圖片...")
    
    # 確保目錄存在
    os.makedirs('/Users/litaicheng/Desktop/VisionFlow/web/static/images', exist_ok=True)
    
    try:
        create_favicon()
        create_apple_touch_icon()
        create_pwa_icons()
        create_badge_icon()
        create_action_icons()
        create_placeholder_images()
        create_screenshot_placeholders()
        
        print("\n✅ 所有圖標和圖片生成完成！")
        print("📁 檔案位置: /Users/litaicheng/Desktop/VisionFlow/web/static/images/")
        
    except Exception as e:
        print(f"❌ 生成過程中發生錯誤: {e}")
        print("💡 請確保已安裝 Pillow: pip install Pillow")

if __name__ == "__main__":
    main()
