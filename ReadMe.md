# 信息安全管理系统课程开源社区建设

## 项目概述
本项目是信息安全管理课程的开源社区建设作业，旨在通过实践来学习和应用信息安全管理的相关知识。项目采用开源协作的方式，由本课程小组成员共同维护和开发。
(Open source community construction of information security management course)

## 项目结构
```
.
├── 漏洞靶场/          # 存放选定的漏洞靶场代码
└── 成员代码/          # 存放各成员开发的代码
    └── ChenJingyao/   # 成员陈璟耀个人代码目录
        └── EasySpiderCJY.py  # 网页爬虫工具
    └── WangCheng/     # 成员王骋个人代码目录
        └── CryptoAPI.py  # 密码学接口工具
    └── HanTianchi/     # 成员韩天驰个人代码目录
        └── Analyzer.py  # Python静态代码分析工具
    └── Zhaoluwen/     # 成员赵璐文个人代码目录
        └── convertGraph.py  # 图格式转换工具
```

## 功能说明

### 成员代码

#### ChenJingyao

##### EasySpiderCJY.py
这是一个简单但功能完整的网页爬虫工具，主要功能包括：

- 网页内容抓取：支持通过URL获取网页内容
- 智能解析：使用BeautifulSoup解析HTML，提取标题和链接
- 错误处理：包含重试机制和异常处理
- 结果保存：支持将爬取结果保存到本地文件

---

#### WangCheng
这是一个基于 Flask 的 RESTful API，提供多种加密算法、哈希函数、编码解码、密钥生成及数字签名功能。核心功能包括：
1. **​哈希计算​**​
- **​支持算法​**​：SHA1, SHA256, SHA3, RIPEMD160, HMAC-SHA1, HMAC-SHA256, PBKDF2
- **​输入​**​：明文文本
- **​输出​**​：哈希值的十六进制字符串

2. **​编码/解码​**​
- **​支持格式​**​：Base64, UTF-8
- **​功能​**​：对文本进行编码转换或解码还原

3. **​密钥生成​**​
- **​RSA​**​：生成 1024 位密钥对（PEM 格式）
- **​ECC​**​：基于 SECP256R1 曲线生成密钥对（PEM 格式）
- **​ECDSA​**​：使用 NIST192p 曲线生成 160 位密钥对（Hex 格式）

4. **​数字签名与验证​**​
- **​RSA-SHA1​**​：签名与验签功能
- **​ECDSA​**​：基于 NIST192p 曲线的签名与验签

5. **​加密/解密​**​
- **​对称加密​**​：
  - AES (ECB 模式)
  - SM4 (国密算法，ECB 模式)
  - RC6 (ECB 模式)
- **​非对称加密​**​：
  - RSA (PKCS1_v1_5 填充)
  - ECC (结合 ECDH 密钥交换 + AES-GCM 加密)


 ---

 #### HanTianchi
这是一个专门用于检测Python代码中潜在安全漏洞的工具，通过静态代码分析技术，对代码进行全面的安全审查。该分析器能够处理单个文件和整个项目目录，并生成详细的安全分析报告。核心功能包括：

1.**核心分析功能**
- 文件分析能力：支持对单个Python源代码文件进行深度分析
- 目录扫描能力：可以递归扫描整个项目目录中的所有Python文件
- 语法树分析：利用抽象语法树技术进行代码结构分析
- 模式匹配：基于预定义的安全规则进行漏洞识别
 
2.**安全检测范围**
- 危险模块导入检测：识别可能导致安全问题的模块导入
- SQL注入漏洞检测：分析数据库操作相关的代码
- 命令注入漏洞检测：检查系统命令执行相关的函数调用
- 不安全反序列化检测：识别可能导致代码执行的反序列化操作
- 敏感信息泄露检测：查找代码中硬编码的敏感信息
 
3.**分析方法论**
- 静态代码分析：通过解析代码结构而不执行代码
- 语法树遍历：系统地检查代码中的每个节点
- 规则匹配：将代码模式与预定义的安全规则进行对比
- 上下文分析：考虑代码的上下文环境进行判断
 
4.**漏洞报告机制**
- 漏洞类型标识：清晰标注发现的漏洞类型
- 位置信息：精确定位问题代码的文件和行号
- 详细描述：提供漏洞的具体描述信息
- 风险等级：对发现的问题进行风险等级划分


 ---

 #### Zhaoluwen
此工具用于将图形数据从GML格式转换为GraphSage所需的格式，主要功能包括：

1.**数据转换与预处理**
- GML图数据读取与解析
- 节点特征提取与标准化
- 自动生成节点ID映射和类别映射

2.**图数据集划分**
- 自动将域名节点划分为训练集、验证集和测试集
- 支持自定义划分比例

3.**多格式输出**
- 生成GraphSage兼容的JSON格式图结构
- 保存节点特征矩阵(numpy格式)
- 导出节点和边的CSV格式数据(用于异构图模型)

4.**特征工程**
- 处理不同类型节点的特征差异
- 时间戳转换
- 支持类别标签
  
