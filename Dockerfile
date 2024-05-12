# 選擇一個基礎映像
FROM python:3.10.7

# 安裝 PortAudio
RUN apt-get update && apt-get install -y portaudio19-dev

# 設置工作目錄
WORKDIR /app

# 將你的 Python 依賴拷貝到容器中
COPY requirements.txt /app/requirements.txt

# 安裝 Python 依賴
RUN pip install -r requirements.txt

# 拷貝你的代碼到容器中
COPY . /app

# 運行你的應用
CMD ["python", "your_app.py"]
