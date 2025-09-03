# 视频草稿 - 专业视频编辑工具

一个基于 Electron + React + Node.js 的专业视频编辑平台，支持跨平台使用，提供完整的用户管理和项目协作功能。

## 项目结构

```
├── backend/                 # 后端 API 服务
│   ├── src/
│   │   ├── controllers/     # 控制器
│   │   ├── models/          # 数据模型
│   │   ├── routes/          # 路由
│   │   ├── middleware/      # 中间件
│   │   ├── utils/           # 工具函数
│   │   └── config/          # 配置文件
│   ├── tests/               # 测试文件
│   ├── package.json
│   └── .env.example
├── web-portal/             # Web 门户页面
│   ├── src/
│   │   ├── components/      # React 组件
│   │   ├── pages/           # 页面组件
│   │   ├── hooks/           # 自定义 Hooks
│   │   ├── services/        # API 服务
│   │   ├── utils/           # 工具函数
│   │   └── styles/          # 样式文件
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
└── gui/                    # Electron 桌面应用（待开发）
```

## 功能特性

### 用户管理
- 用户注册和登录
- 个人资料管理
- 密码修改
- 用户偏好设置

### 视频编辑
- 多轨道编辑
- 实时预览
- 丰富特效和转场
- 4K 分辨率支持
- 多种导出格式

### 协作功能
- 团队协作
- 云端存储
- 版本控制
- 实时同步

### 平台支持
- Windows 应用
- macOS 应用
- Linux 应用
- Web 门户

## 技术栈

### 后端
- **Node.js** - 运行时环境
- **Express** - Web 框架
- **MongoDB** - 数据库
- **JWT** - 身份认证
- **bcrypt** - 密码加密

### 前端
- **React 18** - 前端框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design** - UI 组件库
- **Styled Components** - 样式管理
- **React Router** - 路由管理
- **React Query** - 数据管理

### 桌面端
- **Electron** - 桌面应用框架
- **React** - 用户界面

## 快速开始

### 环境要求
- Node.js 16+
- MongoDB 4.4+
- npm 或 yarn

### 安装依赖

```bash
# 后端
cd backend
npm install

# 前端
cd web-portal
npm install
```

### 环境配置

1. 复制环境变量文件：
```bash
cp backend/.env.example backend/.env
```

2. 编辑 `backend/.env` 文件，配置数据库连接等信息。

### 启动开发服务器

```bash
# 启动后端服务
cd backend
npm run dev

# 启动前端服务（新终端）
cd web-portal
npm run dev
```

### 访问应用
- Web 门户: http://localhost:3000
- 后端 API: http://localhost:5000

## API 文档

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `PUT /api/auth/profile` - 更新用户资料
- `POST /api/auth/change-password` - 修改密码

### 用户接口
- `GET /api/users/profile` - 获取用户资料
- `PUT /api/users/preferences` - 更新用户偏好
- `GET /api/users/videos` - 获取用户视频列表
- `GET /api/users/stats` - 获取用户统计

### 视频接口
- `POST /api/videos` - 创建视频项目
- `GET /api/videos` - 获取视频列表
- `GET /api/videos/:id` - 获取视频详情
- `PUT /api/videos/:id` - 更新视频项目
- `DELETE /api/videos/:id` - 删除视频项目
- `POST /api/videos/:id/duplicate` - 复制视频项目

## 部署

### 后端部署
```bash
cd backend
npm run build
npm start
```

### 前端部署
```bash
cd web-portal
npm run build
npm run preview
```

## 开发计划

- [x] 后端 API 服务
- [x] Web 门户页面
- [ ] Electron 桌面应用
- [ ] 视频编辑核心功能
- [ ] 云端存储集成
- [ ] 团队协作功能
- [ ] 移动端应用

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License