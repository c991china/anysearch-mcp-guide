# 用 curl 调 AnySearch（进阶）

```bash
# 带超时与最大返回条数
curl -sS -X POST https://api.anysearch.com/v1/search \
  -H "Authorization: Bearer $ANYSEARCH_API_KEY" \
  -H "Content-Type: application/json" \
  --max-time 30 \
  -d '{"query":"向量数据库对比","top_k":5}'
```

## 批量搜索
把多个 query 写进 `queries.txt`，逐行调用即可；注意控制速率避免触发限流。
