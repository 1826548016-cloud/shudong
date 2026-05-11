# 个人树洞网站（TreeHole）

基于 Django + DRF + Vue3 开发的个人树洞分享平台。

## 项目简介

这是一个个人专属的树洞日记与生活分享网站。

- 游客无需注册、无需登录即可浏览网站内容
- 支持匿名评论、点赞、查看图片与视频动态
- 管理员登录后台后，可以发布动态、管理评论、删除内容
- 适合作为个人博客、生活记录网站或个人情绪树洞平台

前端页面整体采用“字节跳动系”简洁、克制的视觉风格（高信息密度、卡片化内容、清爽主色）。

## 技术栈

### 后端

- Django
- Django REST Framework（DRF）
- SQLite
- JWT 身份认证（SimpleJWT）

### 前端

- Vue3 + Vite + TypeScript
- Axios
- Element Plus

## 功能介绍

### 游客功能

- 浏览所有树洞动态
- 查看图片与视频内容
- 查看动态浏览量
- 点赞动态
- 匿名发表评论

### 管理员功能

- 管理员登录（JWT）
- 发布树洞动态（支持图片/短视频上传）
- 编辑动态
- 删除动态
- 删除评论

## 项目结构

```bash
treehole/
├── backend/                 # Django 后端
│   ├── apps/
│   ├── media/               # 上传文件（运行后生成）
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/                # Vue3 前端
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## 快速开始

### 1）启动后端

```bash
cd backend
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### 2）启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开：

- http://localhost:5173

说明：

- 前端已配置开发代理（Vite proxy），会将 `/api`、`/media` 转发到 `http://127.0.0.1:8000`。

## API（简要）

- GET `/api/posts/`：动态列表
- GET `/api/posts/{id}/`：动态详情
- POST `/api/posts/`：创建动态（管理员）
- PATCH `/api/posts/{id}/`：编辑动态（管理员）
- DELETE `/api/posts/{id}/`：删除动态（管理员）
- POST `/api/posts/{id}/view/`：浏览量 +1
- POST `/api/posts/{id}/like/`：点赞
- GET `/api/posts/{post_id}/comments/`：评论列表
- POST `/api/posts/{post_id}/comments/`：匿名评论
- DELETE `/api/comments/{id}/`：删除评论（管理员）
- POST `/api/auth/token/`：获取 JWT（管理员登录）
- POST `/api/auth/token/refresh/`：刷新 JWT

