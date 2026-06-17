#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 图片提取与压缩工具
功能：从 PDF 文件中提取所有图片，并可选择进行压缩
运行环境：Windows / Python 3.7+
"""

import os
import sys
import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("错误：缺少 PyMuPDF 库，请先安装：pip install pymupdf")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("错误：缺少 Pillow 库，请先安装：pip install pillow")
    sys.exit(1)


def extract_images_from_pdf(pdf_path, output_dir):
    """
    从 PDF 中提取所有图片
    
    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        
    Returns:
        提取的图片路径列表
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extracted_images = []
    img_count = 0
    
    print(f"正在处理: {pdf_path.name}")
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"打开 PDF 失败: {e}")
        return extracted_images
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        
        for img_idx, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # 生成文件名
            img_count += 1
            img_filename = f"{pdf_path.stem}_page{page_num+1:03d}_img{img_idx+1:02d}.{image_ext}"
            img_path = output_dir / img_filename
            
            # 保存图片
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            
            extracted_images.append(img_path)
    
    doc.close()
    print(f"共提取 {len(extracted_images)} 张图片")
    
    return extracted_images


def compress_image(image_path, output_path=None, quality=85, max_width=None, max_height=None, format=None):
    """
    压缩单张图片
    
    Args:
        image_path: 原始图片路径
        output_path: 输出路径，None 则覆盖原图
        quality: 压缩质量 1-100，数字越大质量越好
        max_width: 最大宽度（像素），超过则等比缩放
        max_height: 最大高度（像素），超过则等比缩放
        format: 输出格式，None 则保持原格式
        
    Returns:
        压缩后的文件大小（字节）
    """
    image_path = Path(image_path)
    if output_path is None:
        output_path = image_path
    else:
        output_path = Path(output_path)
    
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"  打开图片失败 {image_path.name}: {e}")
        return None
    
    original_size = image_path.stat().st_size
    
    # 处理透明通道
    if img.mode in ('RGBA', 'LA', 'P'):
        if format and format.lower() in ('jpg', 'jpeg'):
            # JPG 不支持透明，转为 RGB
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        else:
            # 保持透明通道
            if img.mode == 'P':
                img = img.convert('RGBA')
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 尺寸缩放
    if max_width or max_height:
        w, h = img.size
        ratio = 1.0
        
        if max_width and w > max_width:
            ratio = min(ratio, max_width / w)
        if max_height and h > max_height:
            ratio = min(ratio, max_height / h)
        
        if ratio < 1.0:
            new_w = int(w * ratio)
            new_h = int(h * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            print(f"  尺寸缩放: {w}x{h} -> {new_w}x{new_h}")
    
    # 确定输出格式
    if format is None:
        format = image_path.suffix.lstrip('.').lower()
    
    format_map = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'gif': 'GIF',
        'bmp': 'BMP',
        'tiff': 'TIFF',
        'webp': 'WEBP',
    }
    save_format = format_map.get(format.lower(), 'JPEG')
    
    # 保存参数
    save_kwargs = {}
    if save_format == 'JPEG':
        save_kwargs['quality'] = quality
        save_kwargs['optimize'] = True
        save_kwargs['progressive'] = True
    elif save_format == 'PNG':
        # PNG 是无损压缩，quality 映射为压缩级别 0-9
        compress_level = max(0, min(9, int((100 - quality) / 11.1)))
        save_kwargs['compress_level'] = compress_level
        save_kwargs['optimize'] = True
    elif save_format == 'WEBP':
        save_kwargs['quality'] = quality
        save_kwargs['method'] = 6  # 压缩方法 0-6，6 是最慢但压缩比最高
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        img.save(output_path, format=save_format, **save_kwargs)
    except Exception as e:
        print(f"  保存图片失败 {output_path.name}: {e}")
        return None
    
    compressed_size = output_path.stat().st_size
    ratio = (1 - compressed_size / original_size) * 100
    
    print(f"  {image_path.name}: {original_size/1024:.1f}KB -> {compressed_size/1024:.1f}KB (压缩 {ratio:.1f}%)")
    
    return compressed_size


def batch_compress_images(image_paths, output_dir=None, quality=85, max_width=None, max_height=None, format=None):
    """
    批量压缩图片
    
    Args:
        image_paths: 图片路径列表
        output_dir: 输出目录，None 则覆盖原图
        quality: 压缩质量
        max_width: 最大宽度
        max_height: 最大高度
        format: 输出格式
        
    Returns:
        统计信息字典
    """
    stats = {
        'total': len(image_paths),
        'success': 0,
        'failed': 0,
        'original_total_size': 0,
        'compressed_total_size': 0,
    }
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    for img_path in image_paths:
        img_path = Path(img_path)
        if not img_path.exists():
            print(f"跳过不存在的文件: {img_path}")
            stats['failed'] += 1
            continue
        
        original_size = img_path.stat().st_size
        stats['original_total_size'] += original_size
        
        if output_dir:
            out_path = output_dir / img_path.name
        else:
            out_path = None  # 覆盖原图
        
        result = compress_image(
            img_path,
            output_path=out_path,
            quality=quality,
            max_width=max_width,
            max_height=max_height,
            format=format
        )
        
        if result is not None:
            stats['success'] += 1
            stats['compressed_total_size'] += result
        else:
            stats['failed'] += 1
    
    # 计算总压缩率
    if stats['original_total_size'] > 0:
        stats['total_ratio'] = (1 - stats['compressed_total_size'] / stats['original_total_size']) * 100
    else:
        stats['total_ratio'] = 0
    
    return stats


def process_pdf(pdf_path, output_base_dir=None, extract_only=False, quality=85, 
                max_width=None, max_height=None, format=None, keep_original=False):
    """
    处理单个 PDF：提取图片 + 可选压缩
    
    Args:
        pdf_path: PDF 文件路径
        output_base_dir: 基础输出目录
        extract_only: 仅提取不压缩
        quality: 压缩质量
        max_width: 最大宽度
        max_height: 最大高度
        format: 输出格式
        keep_original: 是否保留原始图片（压缩时）
        
    Returns:
        结果字典
    """
    pdf_path = Path(pdf_path)
    
    # 设置输出目录
    if output_base_dir:
        output_base_dir = Path(output_base_dir)
    else:
        output_base_dir = pdf_path.parent
    
    extract_dir = output_base_dir / f"{pdf_path.stem}_extracted_images"
    
    # 提取图片
    images = extract_images_from_pdf(pdf_path, extract_dir)
    
    if not images:
        return {'pdf': pdf_path.name, 'extracted': 0, 'compressed': 0, 'extract_dir': str(extract_dir)}
    
    result = {
        'pdf': pdf_path.name,
        'extracted': len(images),
        'compressed': 0,
        'extract_dir': str(extract_dir),
    }
    
    # 压缩图片
    if not extract_only:
        if keep_original:
            compress_dir = output_base_dir / f"{pdf_path.stem}_compressed_images"
        else:
            compress_dir = extract_dir  # 覆盖原图
        
        print(f"\n开始压缩图片 (质量={quality})...")
        stats = batch_compress_images(
            images,
            output_dir=compress_dir if keep_original else None,
            quality=quality,
            max_width=max_width,
            max_height=max_height,
            format=format
        )
        
        result['compressed'] = stats['success']
        result['compress_stats'] = stats
        result['compress_dir'] = str(compress_dir)
        
        print(f"\n压缩完成：成功 {stats['success']} 张，失败 {stats['failed']} 张")
        print(f"总大小: {stats['original_total_size']/1024:.1f}KB -> {stats['compressed_total_size']/1024:.1f}KB")
        print(f"总压缩率: {stats['total_ratio']:.1f}%")
        print(f"压缩图片目录: {compress_dir}")
    
    return result


def process_folder(folder_path, **kwargs):
    """
    批量处理文件夹中的所有 PDF
    
    Args:
        folder_path: 文件夹路径
        **kwargs: 传递给 process_pdf 的参数
        
    Returns:
        结果列表
    """
    folder_path = Path(folder_path)
    pdf_files = list(folder_path.glob("*.pdf")) + list(folder_path.glob("*.PDF"))
    
    if not pdf_files:
        print(f"在 {folder_path} 中未找到 PDF 文件")
        return []
    
    print(f"找到 {len(pdf_files)} 个 PDF 文件")
    print("-" * 50)
    
    results = []
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}]", end=" ")
        result = process_pdf(pdf_file, **kwargs)
        results.append(result)
        print("\n" + "-" * 50)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="PDF 图片提取与压缩工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 提取单个 PDF 的图片（不压缩）
  python pdf_image_extractor.py input.pdf --extract-only
  
  # 提取并压缩（质量 85）
  python pdf_image_extractor.py input.pdf -q 85
  
  # 提取并压缩，限制最大宽度 1920px
  python pdf_image_extractor.py input.pdf -q 80 --max-width 1920
  
  # 提取并转换为 WebP 格式
  python pdf_image_extractor.py input.pdf -q 80 --format webp
  
  # 批量处理文件夹中的所有 PDF
  python pdf_image_extractor.py --folder ./pdfs -q 75
  
  # 只压缩已有的图片文件夹
  python pdf_image_extractor.py --compress-folder ./images -q 80
        """
    )
    
    parser.add_argument("pdf", nargs="?", help="PDF 文件路径")
    parser.add_argument("--folder", "-f", help="包含 PDF 的文件夹路径（批量处理）")
    parser.add_argument("--output", "-o", help="输出目录（默认与 PDF 同目录）")
    
    # 提取选项
    parser.add_argument("--extract-only", action="store_true", help="仅提取图片，不压缩")
    
    # 压缩选项
    parser.add_argument("--quality", "-q", type=int, default=85, 
                        help="压缩质量 1-100（默认 85），数字越大质量越好")
    parser.add_argument("--max-width", type=int, help="最大宽度（像素），超过则等比缩放")
    parser.add_argument("--max-height", type=int, help="最大高度（像素），超过则等比缩放")
    parser.add_argument("--format", choices=["jpg", "png", "webp"], 
                        help="输出图片格式（默认保持原格式）")
    parser.add_argument("--keep-original", action="store_true", 
                        help="保留原始图片，压缩版另存到新目录")
    
    # 直接压缩图片文件夹
    parser.add_argument("--compress-folder", help="直接压缩指定文件夹中的所有图片")
    
    args = parser.parse_args()
    
    # 模式 1：直接压缩图片文件夹
    if args.compress_folder:
        folder = Path(args.compress_folder)
        if not folder.exists():
            print(f"错误：文件夹不存在 {folder}")
            sys.exit(1)
        
        # 支持的图片格式
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.webp',
                      '*.JPG', '*.JPEG', '*.PNG', '*.GIF', '*.BMP', '*.TIFF', '*.WEBP']
        image_files = []
        for ext in extensions:
            image_files.extend(folder.glob(ext))
        
        # 去重
        image_files = list(set(image_files))
        
        if not image_files:
            print(f"在 {folder} 中未找到图片文件")
            sys.exit(0)
        
        print(f"找到 {len(image_files)} 张图片")
        print(f"开始压缩 (质量={args.quality})...\n")
        
        output_dir = folder.parent / f"{folder.name}_compressed" if args.keep_original else None
        
        stats = batch_compress_images(
            image_files,
            output_dir=output_dir,
            quality=args.quality,
            max_width=args.max_width,
            max_height=args.max_height,
            format=args.format
        )
        
        print(f"\n{'='*50}")
        print(f"压缩完成！")
        print(f"  总计: {stats['total']} 张")
        print(f"  成功: {stats['success']} 张")
        print(f"  失败: {stats['failed']} 张")
        print(f"  原始总大小: {stats['original_total_size']/1024:.1f} KB")
        print(f"  压缩后总大小: {stats['compressed_total_size']/1024:.1f} KB")
        print(f"  总压缩率: {stats['total_ratio']:.1f}%")
        if output_dir:
            print(f"  输出目录: {output_dir}")
        print(f"{'='*50}")
        
        sys.exit(0)
    
    # 模式 2：处理单个 PDF
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"错误：文件不存在 {pdf_path}")
            sys.exit(1)
        
        result = process_pdf(
            pdf_path,
            output_base_dir=args.output,
            extract_only=args.extract_only,
            quality=args.quality,
            max_width=args.max_width,
            max_height=args.max_height,
            format=args.format,
            keep_original=args.keep_original
        )
        
        print(f"\n{'='*50}")
        print(f"处理完成！")
        print(f"  PDF 文件: {result['pdf']}")
        print(f"  提取图片: {result['extracted']} 张")
        print(f"  图片目录: {result['extract_dir']}")
        if not args.extract_only:
            print(f"  压缩图片: {result['compressed']} 张")
        print(f"{'='*50}")
    
    # 模式 3：批量处理文件夹
    elif args.folder:
        results = process_folder(
            args.folder,
            output_base_dir=args.output,
            extract_only=args.extract_only,
            quality=args.quality,
            max_width=args.max_width,
            max_height=args.max_height,
            format=args.format,
            keep_original=args.keep_original
        )
        
        total_extracted = sum(r['extracted'] for r in results)
        total_compressed = sum(r['compressed'] for r in results)
        
        print(f"\n{'='*50}")
        print(f"批量处理完成！")
        print(f"  处理 PDF: {len(results)} 个")
        print(f"  提取图片总计: {total_extracted} 张")
        if not args.extract_only:
            print(f"  压缩图片总计: {total_compressed} 张")
        print(f"{'='*50}")
    
    # 无参数时显示帮助
    else:
        parser.print_help()
        print("\n提示：请提供 PDF 文件路径或文件夹路径")


if __name__ == "__main__":
    main()
