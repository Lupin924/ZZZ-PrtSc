#!/usr/bin/env python3
"""从 PNG 生成标准多尺寸 ICO 文件"""

from PIL import Image
import struct
import io

def png_to_ico(png_path, ico_path):
    print(f"=== 从 PNG 生成 ICO ===")
    print(f"输入: {png_path}")
    print(f"输出: {ico_path}")
    
    img = Image.open(png_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Windows 标准图标尺寸
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # 收集各尺寸的 BMP 数据
    bmp_data_list = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        bmp_data = _create_bmp_data(resized, size[0], size[1])
        bmp_data_list.append((size, bmp_data))
        print(f"  ✓ {size[0]}x{size[1]}: {len(bmp_data)} 字节")
    
    # 构建 ICO 文件
    num_images = len(bmp_data_list)
    
    # 计算偏移量
    header_size = 6
    dir_entry_size = 16
    data_offset = header_size + dir_entry_size * num_images
    
    # ICO 头
    ico = struct.pack('<HHH', 0, 1, num_images)
    
    # 目录项 + 数据
    current_offset = data_offset
    for (size, bmp_data) in bmp_data_list:
        w = size[0] if size[0] < 256 else 0
        h = size[1] if size[1] < 256 else 0
        
        dir_entry = struct.pack('<BBBBHHII',
            w,           # 宽度 (0=256)
            h,           # 高度 (0=256)
            0,           # 调色板颜色数
            0,           # 保留
            1,           # 色彩平面数
            32,          # 每像素位数
            len(bmp_data),  # 图像数据大小
            current_offset  # 数据偏移
        )
        ico += dir_entry
        current_offset += len(bmp_data)
    
    # 添加图像数据
    for (_, bmp_data) in bmp_data_list:
        ico += bmp_data
    
    with open(ico_path, 'wb') as f:
        f.write(ico)
    
    print(f"\n✓ ICO 文件已生成: {ico_path}")
    print(f"  文件大小: {len(ico)} 字节")
    print(f"  包含 {num_images} 个尺寸")
    return True

def _create_bmp_data(img, width, height):
    """创建 BMP DIB 数据（ICO 格式要求）"""
    # BITMAPINFOHEADER (40 字节)
    bmp_header = struct.pack('<IiiHHIIiiII',
        40,          # biSize
        width,       # biWidth
        height * 2,  # biHeight (ICO 格式要求 2 倍高度)
        1,           # biPlanes
        32,          # biBitCount (RGBA)
        0,           # biCompression (BI_RGB)
        0,           # biSizeImage
        0,           # biXPelsPerMeter
        0,           # biYPelsPerMeter
        0,           # biClrUsed
        0            # biClrImportant
    )
    
    # 像素数据 (BGRA 格式，自底向上)
    pixels = img.load()
    pixel_data = bytearray()
    for y in range(height - 1, -1, -1):  # BMP 自底向上
        for x in range(width):
            r, g, b, a = pixels[x, y]
            pixel_data.extend([b, g, r, a])  # BGRA 顺序
    
    # AND 掩码 (32位对齐，每行 4 字节对齐)
    and_row_size = ((width + 31) // 32) * 4
    and_mask = bytearray(and_row_size * height)
    
    return bmp_header + bytes(pixel_data) + bytes(and_mask)

if __name__ == "__main__":
    png_to_ico('app_icon.png', 'app_icon.ico')
