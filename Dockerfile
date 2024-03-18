ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION}

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY ./ /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
