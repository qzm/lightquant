# 代码风格指南

## 自动格式化

本项目使用 pre-commit 钩子自动格式化代码，确保代码风格一致。每次提交代码时，以下检查会自动运行：

1. **black** - Python 代码格式化工具
2. **isort** - 导入语句排序工具（配置为与 black 兼容）
3. **trailing-whitespace** - 删除行尾空白
4. **end-of-file-fixer** - 确保文件以换行符结束
5. **check-yaml** - 检查 YAML 文件格式
6. **check-added-large-files** - 防止提交大文件

## 安装

新开发者需要执行以下步骤：

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 Git 钩子
pre-commit install
```

## 手动运行

可以手动运行格式化检查：

```bash
# 检查所有文件
pre-commit run --all-files

# 检查暂存区的文件
pre-commit run
```

## 跳过检查

在特殊情况下，可以跳过 pre-commit 检查：

```bash
git commit -m "消息" --no-verify
```

但不建议经常这样做，应尽量保持代码风格一致。
