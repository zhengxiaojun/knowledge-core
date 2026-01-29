# AI 测试用例自动生成系统  
## 接口设计文档

**Version:** 1.0  
**文档名称:** AI 测试用例自动生成系统 - 接口设计文档  
**创建日期:** 2026-01-28  

---

## 1. 接口总览

系统采用 **RESTful API** 设计风格，所有接口遵循统一的请求与响应规范。

### 1.1 接口分类

| 接口分类 | 说明 |
|----|----|
| 需求管理接口 | 需求上传、查询、意图分析 |
| 测试知识管理接口 | 向量检索、图谱查询 |
| 测试用例生成接口 | 测试点生成、用例生成、批量生成 |
| 结果管理接口 | 用例确认、编辑、导出 |

---

### 1.2 统一响应格式

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

**失败响应：**

```json
{
  "code": 40001,
  "message": "参数错误",
  "data": null
}
```

---

## 2. 需求管理接口

### 2.1 上传需求文档

* **接口地址**
  `POST /api/requirements/upload`

* **接口描述**
  上传需求文档（支持文本、Word、PDF、Excel、图片）

* **请求参数**

| 参数名        | 类型     | 说明                                    |
| ---------- | ------ | ------------------------------------- |
| project_id | string | 项目 ID                                 |
| input_type | string | 输入类型：text / doc / pdf / excel / image |
| files      | array  | 文件列表                                  |

* **响应字段**

| 字段             | 类型     | 说明     |
| -------------- | ------ | ------ |
| requirement_id | string | 需求 ID  |
| raw_chunks     | int    | 文档切块数量 |

---

### 2.2 获取需求详情

* **接口地址**
  `GET /api/requirements/{requirement_id}`

* **接口描述**
  获取需求详情信息

* **请求参数**

| 参数名            | 位置   | 类型     | 说明    |
| -------------- | ---- | ------ | ----- |
| requirement_id | path | string | 需求 ID |

* **响应字段**

`requirement_id, title, full_content, source_type, created_at`

---

### 2.3 需求意图分析

* **接口地址**
  `POST /api/requirements/{requirement_id}/intent`

* **接口描述**
  分析需求并提取测试意图

* **请求参数**

| 参数名            | 位置   | 类型     | 说明    |
| -------------- | ---- | ------ | ----- |
| requirement_id | path | string | 需求 ID |

* **响应字段**

`intents (array)`，每项包含：

* intent_id
* description
* scope

---

## 3. 测试知识管理接口

### 3.1 向量检索

* **接口地址**
  `POST /api/knowledge/search`

* **接口描述**
  基于语义相似度检索测试知识

* **请求参数**

| 参数名        | 类型     | 说明         |
| ---------- | ------ | ---------- |
| query_text | string | 查询文本       |
| top_k      | int    | 返回数量，默认 10 |

* **响应字段**

`results (array)`，每项包含：

* id：知识单元 ID
* content：文本内容
* type：类型
* score：相似度

---

### 3.2 图谱子图扩展

* **接口地址**
  `POST /api/graph/expand`

* **接口描述**
  从测试知识节点扩展相关子图

* **请求参数**

| 参数名      | 类型    | 说明        |
| -------- | ----- | --------- |
| node_ids | array | 节点 ID 列表  |
| depth    | int   | 扩展深度，默认 2 |

* **响应字段**

`subgraph (object)`，包含：

* nodes：节点列表
* relationships：关系列表

---

## 4. 测试用例生成接口

### 4.1 生成测试点

* **接口地址**
  `POST /api/testpoints/generate`

* **接口描述**
  基于需求和历史知识生成测试点

* **请求参数**

| 参数名             | 类型     | 说明        |
| --------------- | ------ | --------- |
| requirement_id  | string | 需求 ID     |
| history_context | object | 历史上下文（可选） |

* **响应字段**

`test_points (array)`，每项包含：

* point_id
* intent_id
* category：正常 / 异常 / 边界
* description

---

### 4.2 生成测试用例

* **接口地址**
  `POST /api/testcases/generate`

* **接口描述**
  将测试点转换为完整测试用例

* **请求参数**

| 参数名         | 类型    | 说明        |
| ----------- | ----- | --------- |
| test_points | array | 测试点 ID 列表 |

* **响应字段**

`test_cases (array)`，每项包含：

* case_id
* title
* precondition
* steps
* expected

---

### 4.3 批量生成测试用例

* **接口地址**
  `POST /api/testcases/batch-generate`

* **接口描述**
  一次性完成从需求到测试用例的生成

* **请求参数**

| 参数名            | 类型     | 说明    |
| -------------- | ------ | ----- |
| requirement_id | string | 需求 ID |
| options        | object | 生成选项  |

* **响应字段**

| 字段      | 类型     | 说明      |
| ------- | ------ | ------- |
| task_id | string | 生成任务 ID |
| status  | string | 任务状态    |

---

### 4.4 查询生成任务

* **接口地址**
  `GET /api/tasks/{task_id}`

* **接口描述**
  查询生成任务状态及结果

* **请求参数**

| 参数名     | 位置   | 类型     | 说明    |
| ------- | ---- | ------ | ----- |
| task_id | path | string | 任务 ID |

* **响应字段**

`task_id, status, progress, test_cases`

---

## 5. 结果管理接口

### 5.1 确认测试用例

* **接口地址**
  `POST /api/testcases/confirm`

* **接口描述**
  人工确认生成的测试用例

* **请求参数**

| 参数名           | 类型     | 说明       |
| ------------- | ------ | -------- |
| case_ids      | array  | 用例 ID 列表 |
| modifications | object | 修改内容（可选） |

* **响应字段**

| 字段              | 类型    | 说明     |
| --------------- | ----- | ------ |
| confirmed_count | int   | 确认数量   |
| failed_cases    | array | 失败用例列表 |

---

### 5.2 编辑测试用例

* **接口地址**
  `PUT /api/testcases/{case_id}`

* **接口描述**
  编辑测试用例内容

* **请求参数**

| 参数名          | 位置   | 类型     | 说明    |
| ------------ | ---- | ------ | ----- |
| case_id      | path | string | 用例 ID |
| title        | body | string | 用例标题  |
| precondition | body | string | 前置条件  |
| steps        | body | array  | 操作步骤  |
| expected     | body | string | 预期结果  |

* **响应字段**

`case_id, updated_at`

---

### 5.3 导出测试用例

* **接口地址**
  `POST /api/testcases/export`

* **接口描述**
  导出测试用例到指定格式

* **请求参数**

| 参数名      | 类型     | 说明                      |
| -------- | ------ | ----------------------- |
| case_ids | array  | 用例 ID 列表                |
| format   | string | 导出格式：excel / csv / json |

* **响应字段**

| 字段       | 类型     | 说明     |
| -------- | ------ | ------ |
| file_url | string | 文件下载地址 |

---

## 6. 错误码定义

| 错误码   | 错误类型     | 说明           |
| ----- | -------- | ------------ |
| 0     | 成功       | 请求成功         |
| 40001 | 参数错误     | 请求参数不符合要求    |
| 40101 | 认证失败     | Token 无效或已过期 |
| 40301 | 权限不足     | 无权访问该资源      |
| 40401 | 资源不存在    | 请求的资源未找到     |
| 50001 | 服务器错误    | 服务器内部错误      |
| 50002 | LLM 调用失败 | 大模型 API 调用失败 |

