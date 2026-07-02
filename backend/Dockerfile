# FROM python:3.11.9-slim

# WORKDIR /app

# #复制依赖文件
# COPY requirements.txt .

# # 安装依赖
# RUN pip install --no-cache-dir -r requirements.txt \
#     -i https://pypi.tuna.tsinghua.edu.cn/simple

# # 复制项目代码
# COPY . .

# CMD ["python", "main.py"]


# ===== Base Image =====
FROM python:3.11.9-slim

# ===== 基础环境变量 =====
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ===== 工作目录 =====
WORKDIR /app

# ===== 系统依赖（按需加）=====
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# ===== 依赖层（缓存优化核心）=====
COPY requirements.txt .

RUN pip install -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# ===== 应用代码 =====
COPY . .

# # ===== 非 root 用户（生产必备）=====
# RUN useradd -m appuser && chown -R appuser /app
# USER appuser

# ===== 启动命令 =====
CMD ["python", "main.py"]