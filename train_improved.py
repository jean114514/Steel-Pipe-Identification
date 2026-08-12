"""
▼ 改进版训练脚本
  优化点：
    1. 使用更大的模型（yolo11m.pt 比 yolo11n.pt 精度更高）
    2. 增加数据增强（Mosaic、MixUp 等）
    3. 降低学习率，更精细地收敛
    4. 训练更长时间
    5. 自动恢复到上次训练进度
"""
from ultralytics import YOLO
import os
import glob

# 确认数据路径
DATA_YAML = os.path.join("dataset", "steel_aug", "data.yaml")
# with open(DATA_YAML, "r", encoding="utf-8") as f:
#     content = f.read()
#     print(content)
#     print("content 输出结束")
#     print("#################")
if not os.path.exists(DATA_YAML):
    # 修正路径
    with open(DATA_YAML, "r", encoding="utf-8") as f:
        content = f.read()
        print(content)
    content = content.replace(
        "D:/bishe/pipe_dataset/pipe_dataset/steel_aug",
        os.path.abspath("dataset/steel_aug").replace("\\", "/")
    )
    with open(DATA_YAML, "w", encoding="utf-8") as f:
        f.write(content)

print(f"数据配置文件: {os.path.abspath(DATA_YAML)}")

# 方案 A：继续上次训练
############################################
resume_path = "runs/detect/runs/pipe_train/weights/last.pt"
if os.path.exists(resume_path):
    print(f"发现上次训练进度: {resume_path}")
    print("使用方案 A：恢复训练\n")
    model = YOLO(resume_path)
    results = model.train(
        data=DATA_YAML,
        epochs=100,          # 总 100 轮，从上次的地方继续
        imgsz=640,
        batch=8,
        device="cpu",
        workers=2,
        name="pipe_train",   # 和上次同名，会自动续上
        patience=30,         # 30 轮没提升才停（比上次宽松）
        save=True,
        project="runs",
        resume=True,         # 关键：恢复训练
    )
else:
    print("没有上次的训练记录，使用方案 B：从头训练（加大模型）")
    
    # 方案 B：用更大的模型从头训练
    # 换 yolo11m.pt，精度更高
    ########################################
    model = YOLO("yolo11m.pt")
    results = model.train(
        data=DATA_YAML,
        epochs=100,
        imgsz=640,
        batch=8,
        device="cpu",
        workers=2,
        name="pipe_train_v2",
        patience=30,
        save=True,
        project="runs",
        # 数据增强
        hsv_h=0.015,          # 色调增强
        hsv_s=0.7,            # 饱和度增强
        hsv_v=0.4,            # 明度增强
        degrees=0.0,          # 旋转（钢管不需要）
        translate=0.1,        # 平移
        scale=0.5,            # 缩放
        shear=0.0,
        perspective=0.0,
        flipud=0.0,           # 上下翻转（钢管不需要）
        fliplr=0.5,           # 左右翻转
        mosaic=1.0,           # Mosaic 增强
        mixup=0.0,            # MixUp 增强
        # 优化器
        lr0=0.001,            # 初始学习率
        lrf=0.01,             # 最终学习率
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
    )

print(f"\n训练完成！")
print(f"最佳模型: runs/detect/{results.save_dir.split(os.sep)[-1]}/weights/best.pt")

# ── 评估 ──
print("\n正在评估验证集...")
metrics = model.val(data=DATA_YAML)
print(f"mAP@0.5:     {metrics.box.map50:.4f}")
print(f"mAP@0.5:0.95:{metrics.box.map:.4f}")
print(f"Precision:   {metrics.box.p:.4f}")
print(f"Recall:      {metrics.box.r:.4f}")

# ── 替换说明 ──
print("\n" + "="*60)
print("训练完成后，执行以下命令替换模型：")
print("="*60)
print(f'copy "runs\\detect\\{results.save_dir.split(os.sep)[-1]}\\weights\\best.pt"')
print('"F:\\钢管\\Pycharm+VS Code.zip\\Pycharm+VS Code\\Pycharm+VS Code\\steel_pipe_backend\\best.pt"')
print("="*60)
