# AIDeer-FastAPI

这是 AIDeer 的后端项目，使用 FastAPI 框架构建。

This project is the backend of AIDeer, which is built with FastAPI.

## 项目结构

```plaintext
.
├── app
│   ├── api # API
│   │   ├── routes # 路由 Routes
│   │   │   ├── __init__.py
│   │   │   ├── chats.py
│   │   │   ├── codes.py
│   │   │   ├── presets.py
│   │   │   └── sessions.py
│   │   │   └── tasks.py
│   │   │   └── users.py
│   │   │   └── utils.py
│   │   ├── __init__.py
│   │   ├── main.py # 主路由 Main Routes
│   │   ├── deps.py # 依赖 Dependencies
│   │   ├── resps.py # 响应 Response
│   ├── core # 核心 Core
│   │   ├── clients # 客户端 Clients
│   │   │   ├── __init__.py
│   │   │   ├── dashscope.py # DashScope 客户端 DashScope Client
│   │   │   ├── wechat.py # 微信客户端 WeChat Client
│   │   ├── connections # 连接 Connections
│   │   │   ├── __init__.py
│   │   │   ├── rabbitmq.py # RabbitMQ 连接 RabbitMQ Connection
│   │   │   ├── redis.py # Redis 连接 Redis Connection
│   │   │   ├── sql.py # SQL 连接 SQL Connection
│   │   ├── managers # 管理 Managers
│   │   │   ├── __init__.py
│   │   │   ├── credit.py # 积分管理 Credit Manager
│   │   │   ├── message.py # 消息管理 Message Manager
│   │   │   ├── redeem.py # 兑换码管理 Redeem Manager
│   │   │   ├── task.py # 任务管理 Task Manager
│   │   ├── __init__.py
│   │   ├── config.py # 配置 Config
│   │   ├── security.py # 安全 Security
│   │   └── stream.py # 流 Stream
│   ├── models # SQLModel 模型 SQLModel Models
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── credit.py
│   │   ├── dashscope.py
│   │   ├── message.py
│   │   ├── preset.py
│   │   ├── security.py
│   │   ├── server.py
│   │   ├── task.py
│   │   ├── user.py
│   ├── __init__.py
├── .env.example # 环境变量示例 Environment Variables Example
├── .gitignore
├── Dockerfile # Docker 镜像构建文件 Docker Image Build File
├── API.md # API 文档 API Document
├── README.md # 说明文档 Readme Document
└── requirements.txt # 依赖 Dependencies
```

## 部署指南

启动服务：

```bash
uvicorn app.main:app --reload
```

服务将在 `http://127.0.0.1:8000` 上运行。请访问 `http://127.0.0.1:8000/docs` 查看 API 文档。

### API 调用指南

此处仅提供关键接口调用流程概述。更多详尽接口文档，请参阅 [API 文档](API.md) 或访问 `/docs` 页面以获取完整信息。

#### 1. 用户身份验证与登录

- **常规用户认证**：

  - 使用 `/api/v1/session/oauth2/token` 接口进行 OAuth2 密码授权模式的登录，以获取访问令牌（Access Token）。
  - 请求时需通过 `OAuth2PasswordRequestForm` 提供用户名和密码信息。

- **微信用户登录**：

  - 微信用户通过访问 `/api/v1/session/wechat/token` 接口完成登录并获得 Access Token 和 Refresh Token。
  - 当 Access Token 需要刷新时，调用 `/api/v1/session/wechat/refresh` 接口，使用 Refresh Token 获取新的 Access Token。
  - 微信登录过程需要用户提供有效的 `code` 参数，系统将自动处理新用户的注册。
  - Access Token 的有效期为一天，Refresh Token 的有效期为 90 天；当微信登录状态失效后，Refresh Token 将无法继续用于刷新 Access Token，需重新发起登录流程。

- **鉴权机制**：

  - 大多数接口要求在请求头中携带已获取的 Access Token 进行鉴权。
  - Access Token 应放置于请求头的 `Authorization` 字段中，格式应为 `Bearer {access_token}`。

- **管理员权限**：
  - 权限等级为 2 的用户具有管理员权限。
  - 管理员能够管理其他用户、公共预设及兑换码等资源。详细操作请参考 API 文档。

#### 2. 用户注册与账户信息管理

- 有关用户注册、账户信息更新以及头像设置的详细接口信息，请查阅 `/docs` 页面提供的相关文档。

- **用户头像管理**：
  - 使用 `/api/v1/users/me/avatar` 接口可以实现用户头像的上传与获取功能。
  - 系统会自动将上传的头像转换为尺寸为 128x128 的 JPEG 格式图片，并在获取时返回该格式的图片文件。

#### 3. 消息交互、预设模板与聊天服务

- **消息处理**：

  - 消息是记录用户与机器人对话的历史记录实体，具有 `user`、`assistant` 或 `system` 角色标识。
  - 消息内容可包含文本 (`text`) 或图片 (`image`) 类型，其中图片类型的消息内容存储为图片 URL。
  - 消息还可具备可见性属性，若 `Visibility` 设置为 `False`，则该消息不会展示给用户查看。

- **预设模板**：

  - 预设模板是一系列预先设定的消息组合及模型参数集合。
  - 对于预设模板中涉及的聊天模型和参数的具体操作细节，请参照阿里云 [DashScope 参考文档](https://help.aliyun.com/zh/dashscope/developer-reference/api-details?spm=a2c4g.11186623.0.0.6312140bro4zEE)。

- **聊天会话**：
  - 聊天会话由一系列用户与机器人之间按预设模板进行的多轮对话组成。
  - 在创建聊天会话时，必须指定对应的预设 ID 以确定对话场景和模型参数。

#### 4. 任务调度与执行

- **任务创建**：

  - 当用户发送消息至机器人时，系统应当创建一个任务，用于触发 AI 模型生成回复。
  - 创建任务前，须确保用户发送的消息已成功记录到相应的聊天会话中。
  - 创建任务时，只需传递 `chat_id` 即可关联到相应的聊天上下文。

- **流式响应获取**：
  - 任务创建成功后，服务器将返回一个任务 ID。
  - 利用此任务 ID，可通过访问 `/api/v1/tasks/{task_id}/stream` 接口实时接收任务执行的流式输出结果。
  - 每个任务仅允许一次有效的流式返回接口调用，重复调用会导致错误。

#### 5. 积分与兑换码管理

- **积分查询与兑换**：

  - 使用 `/api/v1/users/me/credits` 接口，GET 请求可查询用户的当前积分余额及其积分变动历史记录；POST 请求可用于提交兑换码以兑换积分。
  - 用户在执行基于 AI 模型的任务时，系统会根据所使用的模型和 Token 消耗对应的积分。
  - 若积分不足以支付任务费用，则任务将无法创建。

- **兑换码管理**：
  - 管理员可以通过 GET 请求访问 `/api/v1/codes/{code}` 接口来查询特定兑换码的信息。
  - 同时，管理员还拥有 POST 请求创建兑换码或 DELETE 请求删除兑换码的权限。
