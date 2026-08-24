# 云端部署指引：PythonAnywhere 免费公网托管（推荐方案）

> 把已写好的 Flask 云端服务部署到 PythonAnywhere，获得一个**公网网址**，
> 任何设备打开浏览器都能访问，现场演示稳定、有"云端协同"效果。

---

## 为什么选这个方案（最适合你）

| 需求 | 方案满足 |
|------|---------|
| 公网访问 | ✅ 有 `你的用户名.pythonanywhere.com` 公网网址 |
| 免费 | ✅ 免费账号够用 |
| 不依赖不确定的第三方平台界面 | ✅ 用我们自己的 Flask 代码 |
| 复用已写好的代码 | ✅ 代码基本不用改 |
| 现场演示稳定 | ✅ 打开公网网页即可 |

---

## 第一步：注册 PythonAnywhere

1. 打开 https://www.pythonanywhere.com/
2. 点 "Pricing & signup" → 选 **Beginner（免费）**
3. 注册（邮箱 + 密码）
4. 注册后会得到你的用户名，例如 `chenlei2026`

你的公网网址将是：`https://chenlei2026.pythonanywhere.com`

## 第二步：上传代码

1. 登录后，点顶部 **Files** 菜单
2. 在 `/home/chenlei2026/` 下新建文件夹 `app/`
3. 进入 `app/` 文件夹，用 "Upload a file" 上传这几个文件：
   - `app.py`（云端主程序）
   - `templates/index.html`（展示页面）
   - `review_algorithm.py`（复习算法）
   - `question_model.py`（错题数据）
   - `requirements.txt`（依赖）

## 第三步：配置 Web App

1. 点顶部 **Web** 菜单
2. 点 "Add a new web app"
3. 选 **Flask**（如果提示选 Python 版本，选 3.10 或更高）
4. 它会生成一个 `wsgi.py` 配置，把里面的代码替换成下面这个：

```python
import sys
import os

# 指向我们的 app 目录
path = '/home/chenlei2026/app'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

5. 保存后，点绿色的 **Reload** 按钮

## 第四步：测试访问

1. 打开 `https://chenlei2026.pythonanywhere.com/`
2. 应该能看到"智能刷题助手 · 云端控制台"页面

## 第五步：模拟设备上传数据（演示用）

在你自己电脑的终端运行：

```bash
curl -X POST https://chenlei2026.pythonanywhere.com/api/upload \
  -H "Content-Type: application/json" \
  -d '{"subject": "数学", "content": "二次函数顶点坐标", "wrong_day": 0}'
```

然后刷新公网网页，新错题就出现了——这就是**云端协同**的完整演示。

---

## 需要准备的文件清单

在 software 目录下建一个 `deploy/` 文件夹，放：

```
deploy/
├── app.py                  ← 云端主程序（Flask）
├── templates/
│   └── index.html          ← 展示页面
├── review_algorithm.py     ← 复习算法
├── question_model.py       ← 错题数据
└── requirements.txt        ← 依赖清单（flask）
```

`requirements.txt` 内容：
```
flask
requests
```

---

## 常见问题

| 问题 | 解决 |
|------|------|
| Reload 后报错 500 | 检查 wsgi.py 里的路径是否写对（/home/用户名/app） |
| 找不到 flask | 在 Web 页面的 Virtualenv 里装：`pip3 install flask` |
| 上传后页面没更新 | 改完代码要点 **Reload** |
| 免费版有访问限制 | 演示够用，不要高并发访问即可 |
