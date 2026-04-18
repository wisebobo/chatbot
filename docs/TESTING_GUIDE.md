# 测试文件组织说明

## 📁 测试文件位置

所有测试文件都应放在 `tests/` 目录下，遵循以下结构：

```
tests/
├── __init__.py
├── unit/                    # 单元测试
│   ├── __init__.py
│   ├── test_skills.py      # 技能注册表测试
│   ├── test_state.py       # 状态管理测试
│   └── test_rag_skill.py   # RAG 技能测试 ⭐ 新增
└── integration/             # 集成测试
    └── __init__.py
```

## ✅ 正确的做法

### 1. 单元测试位置

**正确**: `tests/unit/test_rag_skill.py`  
**错误**: `test_rag.py` (项目根目录)

### 2. 测试文件命名

- 使用 `test_*.py` 或 `*_test.py` 格式
- 文件名应清晰描述测试内容
- 例如: `test_rag_skill.py`, `test_api_endpoints.py`

### 3. 测试代码规范

```python
"""
Unit tests - RAG skill
Tests for the RAG knowledge base search skill
"""
import pytest
from app.skills.rag_skill import RagSkill


class TestRagSkill:
    """Test cases for RagSkill"""

    @pytest.fixture
    def rag_skill(self):
        """Create a RagSkill instance for testing"""
        return RagSkill()

    def test_rag_skill_initialization(self, rag_skill):
        """Test RagSkill initialization"""
        assert rag_skill.name == "rag_search"
```

## 🚫 避免的做法

### ❌ 不要在项目根目录创建测试文件

```
chatbot/
├── app/
├── tests/
├── test_rag.py          # ❌ 错误位置
├── main.py
└── README.md
```

### ❌ 不要使用临时测试脚本

除非是快速原型验证，否则不应在项目根目录保留测试脚本。

## 🧪 运行测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试文件

```bash
pytest tests/unit/test_rag_skill.py -v
```

### 运行特定测试类

```bash
pytest tests/unit/test_rag_skill.py::TestRagSkill -v
```

### 运行特定测试方法

```bash
pytest tests/unit/test_rag_skill.py::TestRagSkill::test_rag_skill_initialization -v
```

### 带覆盖率报告

```bash
pytest tests/ --cov=app --cov-report=html
```

## 📝 测试最佳实践

1. **使用 pytest fixtures**: 复用测试设置
2. **Mock 外部依赖**: 使用 `unittest.mock` 模拟 API 调用
3. **测试边界条件**: 包括无效输入、空值、异常等
4. **保持测试独立**: 每个测试应该可以独立运行
5. **清晰的测试名称**: 描述测试的目的和场景
6. **注释和文档字符串**: 说明测试的意图

## 🔍 示例：RAG 技能测试

```python
@pytest.mark.asyncio
async def test_rag_execute_with_mock_data(self, rag_skill):
    """Test RAG skill execution with mock API response"""
    # Arrange: 准备测试数据
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [...]}
    
    # Act: 执行被测试的代码
    result = await rag_skill.execute({"query": "test"})
    
    # Assert: 验证结果
    assert result.success is True
    assert len(result.data["results"]) > 0
```

## 📚 相关资源

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) - 异步测试支持
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html) - Mock 和补丁

---

**记住**: 所有测试文件都应该在 `tests/` 目录下，保持项目结构清晰！✨
