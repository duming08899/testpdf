#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 图片提取压缩工具 - GUI 简洁版
基于 tkinter，无需额外 GUI 库
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

try:
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError:
    print("请先安装依赖: pip install pymupdf pillow")
    sys.exit(1)


class PDFImageExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 图片提取压缩工具")
        self.root.geometry("560x480")
        self.root.resizable(True, True)
        self.root.minsize(500, 400)
        
        # 变量
        self.input_path = tk.StringVar()
        self.mode = tk.StringVar(value="file")
        self.quality = tk.IntVar(value=85)
        self.enable_compress = tk.BooleanVar(value=True)
        self.keep_original = tk.BooleanVar(value=False)
        self.limit_width = tk.BooleanVar(value=False)
        self.max_width = tk.IntVar(value=1920)
        self.output_dir = None
        
        self._build_ui()
    
    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}
        
        # 标题
        ttk.Label(self.root, text="PDF 图片提取压缩工具", 
                  font=("Microsoft YaHei", 14, "bold")).pack(pady=(15, 10))
        
        # 输入选择
        input_frame = ttk.LabelFrame(self.root, text="选择输入", padding=10)
        input_frame.pack(fill=tk.X, padx=15, pady=5)
        
        mode_frame = ttk.Frame(input_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Radiobutton(mode_frame, text="单个文件", variable=self.mode, 
                        value="file").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="批量文件夹", variable=self.mode, 
                        value="folder").pack(side=tk.LEFT, padx=20)
        
        path_frame = ttk.Frame(input_frame)
        path_frame.pack(fill=tk.X)
        ttk.Entry(path_frame, textvariable=self.input_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="浏览", command=self._browse, width=8).pack(side=tk.LEFT, padx=(8, 0))
        
        # 压缩设置
        compress_frame = ttk.LabelFrame(self.root, text="压缩设置", padding=10)
        compress_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # 启用压缩
        ttk.Checkbutton(compress_frame, text="启用压缩", variable=self.enable_compress,
                        command=self._toggle_compress).pack(anchor=tk.W)
        
        # 质量滑块
        quality_frame = ttk.Frame(compress_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quality_frame, text="质量:").pack(side=tk.LEFT)
        self.quality_val = ttk.Label(quality_frame, text="85", width=4)
        self.quality_val.pack(side=tk.LEFT, padx=5)
        ttk.Scale(quality_frame, from_=10, to=100, orient=tk.HORIZONTAL,
                  variable=self.quality, command=self._update_quality).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 尺寸限制
        size_frame = ttk.Frame(compress_frame)
        size_frame.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(size_frame, text="限制宽度", variable=self.limit_width,
                        command=self._toggle_size).pack(side=tk.LEFT)
        self.width_entry = ttk.Entry(size_frame, textvariable=self.max_width, width=8, state="disabled")
        self.width_entry.pack(side=tk.LEFT, padx=8)
        ttk.Label(size_frame, text="px", foreground="gray").pack(side=tk.LEFT)
        
        # 保留原图
        ttk.Checkbutton(compress_frame, text="保留原图（压缩版另存）", 
                        variable=self.keep_original).pack(anchor=tk.W, pady=2)
        
        # 操作按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="开始处理", command=self._start, width=15)
        self.start_btn.pack(side=tk.LEFT)
        
        self.open_btn = ttk.Button(btn_frame, text="打开输出文件夹", 
                                   command=self._open_output, state="disabled")
        self.open_btn.pack(side=tk.LEFT, padx=10)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill=tk.X, padx=15, pady=5)
        
        # 状态文本
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(self.root, textvariable=self.status_var, 
                                 foreground="gray", font=("Microsoft YaHei", 9))
        status_label.pack(pady=(0, 15))
    
    def _update_quality(self, val):
        self.quality_val.config(text=str(int(float(val))))
    
    def _toggle_compress(self):
        pass  # 简单起见，始终显示设置
    
    def _toggle_size(self):
        state = "normal" if self.limit_width.get() else "disabled"
        self.width_entry.configure(state=state)
    
    def _browse(self):
        if self.mode.get() == "file":
            path = filedialog.askopenfilename(
                title="选择 PDF 文件",
                filetypes=[("PDF 文件", "*.pdf *.PDF"), ("所有文件", "*.*")]
            )
        else:
            path = filedialog.askdirectory(title="选择 PDF 文件夹")
        
        if path:
            self.input_path.set(path)
    
    def _set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()
    
    def _start(self):
        path = self.input_path.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择 PDF 文件或文件夹")
            return
        if not Path(path).exists():
            messagebox.showerror("错误", "文件或文件夹不存在")
            return
        
        self.start_btn.configure(state="disabled")
        self.progress.start(15)
        self._set_status("处理中...")
        self.output_dir = None
        
        params = {
            'quality': self.quality.get(),
            'compress': self.enable_compress.get(),
            'keep_original': self.keep_original.get(),
            'max_width': self.max_width.get() if self.limit_width.get() else None,
        }
        
        def worker():
            try:
                if self.mode.get() == "file":
                    self.output_dir = self._process_single(path, params)
                else:
                    self.output_dir = self._process_folder(path, params)
                
                self.root.after(0, lambda: self._finish(True))
            except Exception as e:
                self.root.after(0, lambda: self._finish(False, str(e)))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _finish(self, success, error=None):
        self.progress.stop()
        self.start_btn.configure(state="normal")
        
        if success:
            self._set_status("处理完成 ✓")
            self.open_btn.configure(state="normal")
            messagebox.showinfo("完成", "处理完成！")
        else:
            self._set_status("处理失败")
            messagebox.showerror("错误", f"处理失败：{error}")
    
    def _open_output(self):
        if self.output_dir and os.path.exists(self.output_dir):
            import subprocess
            subprocess.run(["open", self.output_dir])
    
    # ===== 核心功能 =====
    
    def _extract_images(self, pdf_path, output_dir):
        """提取 PDF 中的图片"""
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        images = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            for img_idx, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base = doc.extract_image(xref)
                ext = base["ext"]
                
                img_name = f"{pdf_path.stem}_p{page_num+1:03d}_{img_idx+1:02d}.{ext}"
                img_path = output_dir / img_name
                
                with open(img_path, "wb") as f:
                    f.write(base["image"])
                images.append(img_path)
        
        doc.close()
        return images
    
    def _compress_image(self, img_path, output_path, quality, max_width=None):
        """压缩单张图片"""
        img = Image.open(img_path)
        original_size = img_path.stat().st_size
        
        # 处理透明通道
        if img.mode in ('RGBA', 'LA', 'P'):
            if output_path.suffix.lower() in ('.jpg', '.jpeg'):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = bg
            else:
                if img.mode == 'P':
                    img = img.convert('RGBA')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 尺寸缩放
        if max_width and img.width > max_width:
            ratio = max_width / img.width
            new_h = int(img.height * ratio)
            img = img.resize((max_width, new_h), Image.LANCZOS)
        
        # 保存
        ext = output_path.suffix.lstrip('.').lower()
        fmt_map = {'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP'}
        fmt = fmt_map.get(ext, 'JPEG')
        
        kwargs = {}
        if fmt == 'JPEG':
            kwargs.update(quality=quality, optimize=True)
        elif fmt == 'PNG':
            kwargs.update(compress_level=max(0, min(9, int((100-quality)/11.1))))
        elif fmt == 'WEBP':
            kwargs.update(quality=quality, method=6)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format=fmt, **kwargs)
        
        return original_size, output_path.stat().st_size
    
    def _process_single(self, pdf_path, params):
        """处理单个 PDF"""
        pdf_path = Path(pdf_path)
        extract_dir = pdf_path.parent / f"{pdf_path.stem}_images"
        
        # 提取
        images = self._extract_images(pdf_path, extract_dir)
        if not images:
            return str(extract_dir)
        
        # 压缩
        if params['compress']:
            if params['keep_original']:
                compress_dir = pdf_path.parent / f"{pdf_path.stem}_compressed"
            else:
                compress_dir = extract_dir
            
            total_orig = 0
            total_comp = 0
            
            for img in images:
                out = compress_dir / img.name if params['keep_original'] else img
                orig, comp = self._compress_image(
                    img, out, params['quality'], params['max_width']
                )
                total_orig += orig
                total_comp += comp
            
            if params['keep_original']:
                return str(compress_dir)
        
        return str(extract_dir)
    
    def _process_folder(self, folder_path, params):
        """批量处理文件夹"""
        folder_path = Path(folder_path)
        pdf_files = list(folder_path.glob("*.pdf")) + list(folder_path.glob("*.PDF"))
        
        if not pdf_files:
            raise Exception("文件夹中没有找到 PDF 文件")
        
        last_dir = None
        for pdf in pdf_files:
            last_dir = self._process_single(pdf, params)
        
        return str(folder_path)


def main():
    # Windows DPI 适配
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    
    # 尝试使用 vista 主题
    style = ttk.Style()
    try:
        style.theme_use('vista')
    except:
        pass
    
    app = PDFImageExtractor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
