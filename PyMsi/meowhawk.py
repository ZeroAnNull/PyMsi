"""
meowhawk.py — MeowHawk 自研查找算法引擎 (v1.7.0)

轻量级、高性能的全文检索引擎, 纯 Python 零依赖, 对标主流搜索引擎核心算法:

核心算法 (全部公开):
  1. 分词器 (Tokenizer)
     - 中文: 双字 (bigram) 滑动窗口 + 单字 unigram
     - 英文: 非字母数字分割 + 小写化
     - 混合文本自动识别 CJK / Latin 区段

  2. 倒排索引 (Inverted Index)
     - term → [(doc_id, term_freq, positions)]
     - posting list 按 doc_id 排序, 支持高效交集运算
     - 紧凑存储, 内存友好

  3. BM25 排序 (Okapi BM25)
     - 与 Lucene / Elasticsearch 相同的排序公式
     - IDF = ln((N - df + 0.5) / (df + 0.5) + 1)
     - Score = IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * |D| / avgdl))
     - k1 = 1.2, b = 0.75 (行业标准参数)

  4. N-gram 模糊匹配
     - 词汇表的字符级 n-gram 索引
     - Jaccard 相似度找近似词
     - 支持拼写纠错 / 部分匹配

  5. 摘要提取 (Snippet)
     - 定位查询词在文档中的位置
     - 提取上下文窗口, 高亮命中词

用法:
  import PyMsi as PM
  mh = PM.meowhawk()                    # 创建引擎实例
  mh.add_document("Python是最流行的编程语言")
  mh.add_document("Java也是很好的编程语言")
  mh.add_document("Go语言并发性能很强")

  results = mh.search("编程语言")        # 搜索
  for r in results:
      print(f"  [{r.score:.2f}] {r.text}")
      print(f"    摘要: {r.snippet}")

  mh.search("编成语言", fuzzy=True)     # 模糊搜索 (自动纠错)
  mh.suggest("编")                       # 前缀补全
  mh.save("index.json")                 # 持久化
  mh2 = PM.meowhawk.load("index.json")  # 加载
"""

import math
import json
import re
import os
from collections import defaultdict, Counter

# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

# CJK 统一表意文字范围 (中日韩汉字)
_CJK_RANGES = [
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0x3400, 0x4DBF),   # CJK Extension A
    (0x20000, 0x2A6DF), # CJK Extension B
    (0x3040, 0x309F),   # Hiragana
    (0x30A0, 0x30FF),   # Katakana
]

# BM25 默认参数 (与 Lucene / Elasticsearch 一致)
BM25_K1 = 1.2
BM25_B = 0.75

# N-gram 参数
NGRAM_SIZE = 2  # bigram
FUZZY_THRESHOLD = 0.15  # Jaccard 相似度阈值 (低阈值兼容短词)

# 摘要参数
SNIPPET_WINDOW = 40  # 摘要窗口 (字符数)


def _is_cjk(ch):
    """判断字符是否为 CJK 字符"""
    cp = ord(ch)
    for lo, hi in _CJK_RANGES:
        if lo <= cp <= hi:
            return True
    return False


# ═══════════════════════════════════════════════════════════════
# 1. 分词器
# ═══════════════════════════════════════════════════════════════

class Tokenizer:
    """混合分词器 — 中文双字 + 英文单词

    策略:
      - 英文/数字: 连续的 [a-zA-Z0-9] 组成一个 token, 小写化
      - CJK: 双字滑动窗口 (bigram) + 单字 (unigram) 同时输出
        bigram 捕获词组语义, unigram 保证召回率
      - 标点/空格: 分隔符, 丢弃

    示例:
      Tokenizer.tokenize("Python编程语言") → ["python", "编程", "程语", "语言", "编", "程", "语", "言"]
    """

    # 英文 token 正则
    _LATIN_RE = re.compile(r'[a-zA-Z0-9]+')

    @staticmethod
    def tokenize(text):
        """将文本分词, 返回 token 列表 (含位置信息)"""
        tokens = []
        i = 0
        n = len(text)

        while i < n:
            ch = text[i]

            if ch.isspace() or (not ch.isalnum() and not _is_cjk(ch)):
                # 分隔符, 跳过
                i += 1
                continue

            if _is_cjk(ch):
                # CJK 区段: 收集连续的 CJK 字符
                j = i
                cjk_chars = []
                while j < n and _is_cjk(text[j]):
                    cjk_chars.append(text[j])
                    j += 1

                cjk_str = ''.join(cjk_chars)
                # 双字滑动窗口
                for k in range(len(cjk_str) - 1):
                    tokens.append(cjk_str[k:k+2])
                # 单字
                for ch in cjk_str:
                    tokens.append(ch)

                i = j
            else:
                # Latin/数字 区段
                m = Tokenizer._LATIN_RE.match(text, i)
                if m:
                    tokens.append(m.group().lower())
                    i = m.end()
                else:
                    i += 1

        return tokens

    @staticmethod
    def tokenize_with_positions(text):
        """分词并返回 (token, start_pos) 列表, 用于位置索引"""
        tokens = []
        i = 0
        n = len(text)

        while i < n:
            ch = text[i]

            if ch.isspace() or (not ch.isalnum() and not _is_cjk(ch)):
                i += 1
                continue

            if _is_cjk(ch):
                j = i
                cjk_chars = []
                while j < n and _is_cjk(text[j]):
                    cjk_chars.append(text[j])
                    j += 1

                cjk_str = ''.join(cjk_chars)
                # 双字滑动窗口
                for k in range(len(cjk_str) - 1):
                    tokens.append((cjk_str[k:k+2], i + k))
                # 单字
                for k, ch in enumerate(cjk_str):
                    tokens.append((ch, i + k))

                i = j
            else:
                m = Tokenizer._LATIN_RE.match(text, i)
                if m:
                    tokens.append((m.group().lower(), i))
                    i = m.end()
                else:
                    i += 1

        return tokens


# ═══════════════════════════════════════════════════════════════
# 2. 倒排索引
# ═══════════════════════════════════════════════════════════════

class Posting:
    """倒排表项: (doc_id, term_frequency, positions)"""
    __slots__ = ('doc_id', 'tf', 'positions')

    def __init__(self, doc_id, tf, positions):
        self.doc_id = doc_id
        self.tf = tf
        self.positions = positions  # 在文档中的位置列表

    def __repr__(self):
        return f"Posting(doc={self.doc_id}, tf={self.tf}, pos={self.positions})"


class InvertedIndex:
    """倒排索引 — 搜索引擎的核心数据结构

    结构:
      index: {term: [Posting, Posting, ...]}  # 按 doc_id 排序
      documents: {doc_id: {"text": str, "length": int, "meta": dict}}
      df: {term: document_frequency}  # 每个词出现在多少文档中

    特性:
      - posting list 按 doc_id 升序, 支持 O(n+m) 交集
      - df 缓存避免重复计算
      - 平均文档长度 avgdl 在搜索时计算
    """

    def __init__(self):
        self.index = defaultdict(list)  # term -> [Posting]
        self.documents = {}  # doc_id -> {text, length, meta}
        self.df = defaultdict(int)  # term -> document frequency
        self._next_doc_id = 0
        # tf 缓存: (term, doc_id) -> tf, O(1) 查找
        self._tf_cache = None
        self._avgdl_cache = None

    def add_document(self, text, metadata=None):
        """添加文档到索引"""
        doc_id = self._next_doc_id
        self._next_doc_id += 1

        tokens_pos = Tokenizer.tokenize_with_positions(text)
        tokens = [t for t, _ in tokens_pos]

        # 统计每个 token 的位置
        term_positions = defaultdict(list)
        for token, pos in tokens_pos:
            term_positions[token].append(pos)

        # 构建 posting list
        for term, positions in term_positions.items():
            posting = Posting(doc_id, len(positions), positions)
            self.index[term].append(posting)
            self.df[term] += 1

        self.documents[doc_id] = {
            'text': text,
            'length': len(tokens),
            'meta': metadata or {}
        }

        # 使缓存失效
        self._tf_cache = None
        self._avgdl_cache = None

        return doc_id

    def remove_document(self, doc_id):
        """从索引中删除文档"""
        if doc_id not in self.documents:
            return False

        # 删除文档
        del self.documents[doc_id]

        # 从所有 posting list 中删除
        empty_terms = []
        for term, postings in self.index.items():
            self.index[term] = [p for p in postings if p.doc_id != doc_id]
            if not self.index[term]:
                empty_terms.append(term)
            else:
                self.df[term] = len(self.index[term])

        for term in empty_terms:
            del self.index[term]
            if term in self.df:
                del self.df[term]

        # 使缓存失效
        self._tf_cache = None
        self._avgdl_cache = None

        return True

    @property
    def num_documents(self):
        return len(self.documents)

    @property
    def avg_doc_length(self):
        if not self.documents:
            return 0
        if self._avgdl_cache is None:
            self._avgdl_cache = sum(d['length'] for d in self.documents.values()) / len(self.documents)
        return self._avgdl_cache

    @property
    def vocabulary_size(self):
        return len(self.index)

    def get_postings(self, term):
        """获取 term 的 posting list"""
        return self.index.get(term, [])

    def get_tf(self, term, doc_id):
        """O(1) 获取 (term, doc_id) 的词频 — 用于 BM25 快速打分"""
        if self._tf_cache is None:
            self._build_tf_cache()
        return self._tf_cache.get((term, doc_id), 0)

    def _build_tf_cache(self):
        """构建 (term, doc_id) -> tf 的缓存, 消除线性扫描"""
        self._tf_cache = {}
        for term, postings in self.index.items():
            for p in postings:
                self._tf_cache[(term, p.doc_id)] = p.tf

    def intersect(self, terms):
        """多词交集: 返回同时包含所有 terms 的 doc_id 列表"""
        if not terms:
            return []

        # 按 df 升序排列, 从最稀有的词开始 (优化策略)
        sorted_terms = sorted(terms, key=lambda t: self.df.get(t, 0))

        # 第一个 term 的 doc_id 集合
        result = set(p.doc_id for p in self.get_postings(sorted_terms[0]))

        # 依次与其他 terms 交集
        for term in sorted_terms[1:]:
            postings = self.get_postings(term)
            doc_ids = set(p.doc_id for p in postings)
            result &= doc_ids
            if not result:
                return []

        return sorted(result)


# ═══════════════════════════════════════════════════════════════
# 3. BM25 排序器
# ═══════════════════════════════════════════════════════════════

class BM25Scorer:
    """Okapi BM25 排序算法 — 与 Lucene / Elasticsearch 相同

    公式:
      IDF(q) = ln( (N - df(q) + 0.5) / (df(q) + 0.5) + 1 )
      Score(q, D) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))

    参数:
      k1 = 1.2  (词频饱和控制, 越大越允许高频词影响)
      b = 0.75  (文档长度归一化, 0=不考虑长度, 1=完全归一化)
    """

    def __init__(self, index, k1=BM25_K1, b=BM25_B):
        self.index = index
        self.k1 = k1
        self.b = b

    def idf(self, term):
        """计算 term 的 IDF (Inverse Document Frequency)"""
        N = self.index.num_documents
        df = self.index.df.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((N - df + 0.5) / (df + 0.5) + 1.0)

    def score_term(self, term, doc_id):
        """计算单个 term 对单个文档的 BM25 分数 (O(1) 查找)"""
        tf = self.index.get_tf(term, doc_id)
        if tf == 0:
            return 0.0

        doc_len = self.index.documents[doc_id]['length']
        avgdl = self.index.avg_doc_length or 1

        idf = self.idf(term)
        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avgdl)

        return idf * numerator / denominator

    def score(self, query_tokens, doc_id):
        """计算查询对文档的总 BM25 分数"""
        total = 0.0
        for term in query_tokens:
            total += self.score_term(term, doc_id)
        return total


# ═══════════════════════════════════════════════════════════════
# 4. N-gram 模糊匹配器
# ═══════════════════════════════════════════════════════════════

class NGramMatcher:
    """N-gram 模糊匹配 — 用于拼写纠错和近似搜索

    原理:
      1. 为词汇表中的每个 term 生成字符 n-gram (bigram)
      2. 构建 n-gram → terms 的反向索引
      3. 查询时生成查询词的 n-gram, 通过交集找候选
      4. 用 Jaccard 相似度排序候选词

    Jaccard(A, B) = |A ∩ B| / |A ∪ B|
    """

    def __init__(self, ngram_size=NGRAM_SIZE):
        self.ngram_size = ngram_size
        self.ngram_index = defaultdict(set)  # ngram -> {term, ...}
        self.vocabulary = set()

    @staticmethod
    def _generate_ngrams(term, n=NGRAM_SIZE):
        """生成 term 的字符 n-gram 集合 (bigram + unigram)

        对短词 (len < n+1) 也包含单字, 保证 CJK 短词间有交集:
          '编程' → {'编', '程', '编程'}
          '编写' → {'编', '写', '编写'}
        交集 '编' → Jaccard > 0, 可匹配
        """
        result = set()
        # 单字 (unigram)
        for ch in term:
            result.add(ch)
        # n-gram (bigram+)
        if len(term) >= n:
            for i in range(len(term) - n + 1):
                result.add(term[i:i+n])
        return result

    def add_term(self, term):
        """将一个词加入 n-gram 索引"""
        if term in self.vocabulary:
            return
        self.vocabulary.add(term)
        ngrams = self._generate_ngrams(term, self.ngram_size)
        for ng in ngrams:
            self.ngram_index[ng].add(term)

    def find_similar(self, query_term, threshold=FUZZY_THRESHOLD, limit=5):
        """查找与查询词最相似的词

        Args:
            query_term: 查询词
            threshold: Jaccard 相似度阈值
            limit: 返回的最大候选数

        Returns:
            [(term, similarity), ...] 按相似度降序
        """
        query_ngrams = self._generate_ngrams(query_term, self.ngram_size)

        # 找候选: 与查询共享至少 1 个 n-gram 的词
        candidates = set()
        for ng in query_ngrams:
            candidates |= self.ngram_index.get(ng, set())

        if not candidates:
            return []

        # 计算 Jaccard 相似度
        results = []
        for term in candidates:
            term_ngrams = self._generate_ngrams(term, self.ngram_size)
            intersection = len(query_ngrams & term_ngrams)
            union = len(query_ngrams | term_ngrams)
            if union > 0:
                sim = intersection / union
                if sim >= threshold:
                    results.append((term, sim))

        results.sort(key=lambda x: -x[1])
        return results[:limit]

    def build_from_index(self, inverted_index):
        """从倒排索引构建 n-gram 索引"""
        for term in inverted_index.index:
            self.add_term(term)


# ═══════════════════════════════════════════════════════════════
# 5. 摘要提取器
# ═══════════════════════════════════════════════════════════════

class SnippetGenerator:
    """摘要提取器 — 从文档中提取与查询相关的片段

    策略:
      1. 找到查询词在文档中的最早位置
      2. 以该位置为中心, 提取 SNIPPET_WINDOW 字符的上下文
      3. 用 【】 高亮命中的查询词
    """

    @staticmethod
    def generate(text, query_terms, window=SNIPPET_WINDOW):
        """生成摘要

        Args:
            text: 原文档文本
            query_terms: 查询词列表
            window: 摘要窗口大小 (字符数)

        Returns:
            str 带高亮标记的摘要
        """
        if not text:
            return ""

        # 找最早匹配位置
        best_pos = -1
        matched_terms = set()

        for term in query_terms:
            idx = text.find(term)
            if idx != -1:
                if best_pos == -1 or idx < best_pos:
                    best_pos = idx
                matched_terms.add(term)

        if best_pos == -1:
            # 没有精确匹配, 用单字
            for term in query_terms:
                for ch in term:
                    idx = text.find(ch)
                    if idx != -1:
                        if best_pos == -1 or idx < best_pos:
                            best_pos = idx
                        matched_terms.add(ch)

        if best_pos == -1:
            # 实在找不到, 返回开头
            snippet = text[:window]
            return snippet + ("..." if len(text) > window else "")

        # 提取窗口
        start = max(0, best_pos - window // 3)
        end = min(len(text), start + window)

        snippet = text[start:end]

        # 高亮
        for term in sorted(matched_terms, key=len, reverse=True):
            snippet = snippet.replace(term, f"【{term}】")

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return prefix + snippet + suffix


# ═══════════════════════════════════════════════════════════════
# 6. 搜索结果
# ═══════════════════════════════════════════════════════════════

class SearchResult:
    """搜索结果项"""
    __slots__ = ('doc_id', 'text', 'score', 'snippet', 'metadata', 'matched_terms')

    def __init__(self, doc_id, text, score, snippet, metadata, matched_terms):
        self.doc_id = doc_id
        self.text = text
        self.score = score
        self.snippet = snippet
        self.metadata = metadata
        self.matched_terms = matched_terms

    def __repr__(self):
        return f"SearchResult(score={self.score:.4f}, text={self.text[:50]}...)"

    def to_dict(self):
        return {
            'doc_id': self.doc_id,
            'text': self.text,
            'score': round(self.score, 4),
            'snippet': self.snippet,
            'metadata': self.metadata,
            'matched_terms': self.matched_terms,
        }


# ═══════════════════════════════════════════════════════════════
# 7. MeowHawk 主引擎
# ═══════════════════════════════════════════════════════════════

class MeowHawk:
    """MeowHawk 搜索引擎 — 轻量级高性能全文检索

    算法公开, 纯 Python 零依赖:
      - 倒排索引 (Inverted Index)
      - BM25 排序 (Okapi BM25, 同 Lucene/ES)
      - N-gram 模糊匹配 (Jaccard 相似度)
      - 中文双字分词 + 英文单词分词
      - 摘要提取与高亮

    用法:
        mh = MeowHawk()
        mh.add_document("Python是最流行的编程语言")
        mh.add_document("Java也是很好的编程语言")
        results = mh.search("编程语言")
        results = mh.search("编成语言", fuzzy=True)  # 模糊搜索
        mh.save("index.json")
        mh2 = MeowHawk.load("index.json")
    """

    def __init__(self, k1=BM25_K1, b=BM25_B):
        self.index = InvertedIndex()
        self.scorer = BM25Scorer(self.index, k1=k1, b=b)
        self.ngram = NGramMatcher()
        self.snippet_gen = SnippetGenerator()
        self._ngram_dirty = True  # n-gram 索引是否需要重建

    def __repr__(self):
        return (f"<MeowHawk [docs={self.index.num_documents}, "
                f"vocab={self.index.vocabulary_size}, "
                f"avgdl={self.index.avg_doc_length:.1f}]>")

    def add_document(self, text, metadata=None):
        """添加文档到搜索引擎

        Args:
            text: 文档文本
            metadata: 可选的元数据 (dict), 如 {"url": "...", "title": "..."}

        Returns:
            doc_id
        """
        doc_id = self.index.add_document(text, metadata)
        self._ngram_dirty = True
        return doc_id

    def add_documents(self, texts):
        """批量添加文档

        Args:
            texts: 文本列表 或 (text, metadata) 元组列表

        Returns:
            [doc_id, ...]
        """
        doc_ids = []
        for item in texts:
            if isinstance(item, (tuple, list)):
                text, meta = item[0], item[1]
            else:
                text, meta = item, None
            doc_ids.append(self.add_document(text, meta))
        return doc_ids

    def remove_document(self, doc_id):
        """删除文档"""
        result = self.index.remove_document(doc_id)
        if result:
            self._ngram_dirty = True
        return result

    def _ensure_ngram(self):
        """确保 n-gram 索引是最新的"""
        if self._ngram_dirty:
            self.ngram = NGramMatcher()
            self.ngram.build_from_index(self.index)
            self._ngram_dirty = False

    def _expand_query(self, query_tokens, fuzzy=True):
        """查询扩展: 用模糊匹配找近似词

        Returns:
            (expanded_tokens, original_tokens_set)
        """
        if not fuzzy:
            return query_tokens, set(query_tokens)

        self._ensure_ngram()
        expanded = list(query_tokens)
        original_set = set(query_tokens)

        for token in query_tokens:
            if len(token) < 2:
                continue  # 单字不做模糊扩展
            similar = self.ngram.find_similar(token, threshold=0.2, limit=3)
            for term, sim in similar:
                if term not in original_set:
                    expanded.append(term)

        return expanded, original_set

    def search(self, query, limit=10, fuzzy=True, min_score=0.0):
        """搜索文档

        Args:
            query: 查询字符串
            limit: 返回结果数上限
            fuzzy: 是否启用模糊匹配 (拼写纠错/近似搜索)
            min_score: 最低分数阈值, 低于此分数的结果不返回

        Returns:
            [SearchResult, ...] 按 BM25 分数降序

        示例:
            mh.search("编程语言")           # 精确搜索
            mh.search("编成语言", fuzzy=True) # 模糊搜索 (自动纠错)
        """
        query_tokens = Tokenizer.tokenize(query)
        if not query_tokens:
            return []

        # 查询扩展
        expanded_tokens, original_tokens = self._expand_query(query_tokens, fuzzy)

        # 找候选文档
        # 策略: 先找同时包含所有原始词的文档 (AND), 如果没有就找包含任一词的 (OR)
        candidate_docs = self.index.intersect(query_tokens)

        if not candidate_docs:
            # OR 搜索: 包含任意一个词的文档
            doc_set = set()
            for token in query_tokens:
                for p in self.index.get_postings(token):
                    doc_set.add(p.doc_id)
            candidate_docs = sorted(doc_set)

        if not candidate_docs and fuzzy:
            # 模糊扩展后的 OR 搜索
            doc_set = set()
            for token in expanded_tokens:
                for p in self.index.get_postings(token):
                    doc_set.add(p.doc_id)
            candidate_docs = sorted(doc_set)

        if not candidate_docs:
            return []

        # BM25 打分
        scored = []
        for doc_id in candidate_docs:
            # 用扩展后的 tokens 打分
            score = self.scorer.score(expanded_tokens, doc_id)
            if score >= min_score:
                doc = self.index.documents[doc_id]
                # 找命中的词 (用 tf 缓存 O(1) 查找)
                matched = []
                for token in query_tokens:
                    if self.index.get_tf(token, doc_id) > 0:
                        matched.append(token)
                # 如果原始词没命中, 检查扩展词
                if not matched:
                    for token in expanded_tokens:
                        if token in original_tokens:
                            continue
                        if self.index.get_tf(token, doc_id) > 0:
                            matched.append(token)

                snippet = self.snippet_gen.generate(doc['text'], matched)
                scored.append(SearchResult(
                    doc_id=doc_id,
                    text=doc['text'],
                    score=score,
                    snippet=snippet,
                    metadata=doc['meta'],
                    matched_terms=matched
                ))

        scored.sort(key=lambda r: -r.score)
        return scored[:limit]

    def suggest(self, prefix, limit=10):
        """前缀补全 / 搜索建议

        Args:
            prefix: 前缀字符串
            limit: 返回建议数上限

        Returns:
            [term, ...] 词汇表中以 prefix 开头的词

        示例:
            mh.suggest("编") → ["编程", "编辑", "编写", ...]
        """
        prefix_lower = prefix.lower()
        results = []
        for term in self.index.index:
            if term.startswith(prefix_lower):
                # 用 df 排序: 更常见的词优先
                results.append((term, self.index.df.get(term, 0)))
        results.sort(key=lambda x: -x[1])
        return [term for term, _ in results[:limit]]

    def stats(self):
        """返回引擎统计信息"""
        return {
            'num_documents': self.index.num_documents,
            'vocabulary_size': self.index.vocabulary_size,
            'avg_doc_length': round(self.index.avg_doc_length, 2),
            'total_terms_indexed': sum(
                len(postings) for postings in self.index.index.values()
            ),
        }

    def save(self, path):
        """将索引持久化到 JSON 文件"""
        data = {
            'version': '1.0',
            'k1': self.scorer.k1,
            'b': self.scorer.b,
            'next_doc_id': self.index._next_doc_id,
            'documents': {
                str(doc_id): doc for doc_id, doc in self.index.documents.items()
            },
            'index': {},
            'df': dict(self.index.df),
        }

        # 序列化 posting list
        for term, postings in self.index.index.items():
            data['index'][term] = [
                {'doc_id': p.doc_id, 'tf': p.tf, 'positions': p.positions}
                for p in postings
            ]

        path = os.path.abspath(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[MeowHawk] 索引已保存: {path} ({self.index.num_documents} 文档)")
        return path

    @classmethod
    def load(cls, path):
        """从 JSON 文件加载索引"""
        path = os.path.abspath(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        engine = cls(k1=data.get('k1', BM25_K1), b=data.get('b', BM25_B))
        engine.index._next_doc_id = data.get('next_doc_id', 0)

        # 恢复文档
        for doc_id_str, doc in data['documents'].items():
            engine.index.documents[int(doc_id_str)] = doc

        # 恢复倒排索引
        for term, postings_data in data['index'].items():
            for pd in postings_data:
                posting = Posting(pd['doc_id'], pd['tf'], pd['positions'])
                engine.index.index[term].append(posting)

        # 恢复 df
        engine.index.df = defaultdict(int, data.get('df', {}))

        engine._ngram_dirty = True
        print(f"[MeowHawk] 索引已加载: {path} ({engine.index.num_documents} 文档)")
        return engine


# ═══════════════════════════════════════════════════════════════
# 8. _MeowHawkModule — PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _MeowHawkModule:
    """PyMsi.meowhawk — MeowHawk 自研查找算法引擎

    轻量级全文检索引擎, 对标搜索引擎核心算法:
      - BM25 排序 (同 Lucene / Elasticsearch)
      - 倒排索引 + N-gram 模糊匹配
      - 中文双字分词 + 英文单词分词
      - 摘要提取与高亮
      - 纯 Python, 零依赖

    用法:
        mh = PM.meowhawk()              # 创建引擎
        mh.add_document("Python编程")
        mh.add_document("Java编程")
        results = mh.search("编程")      # 搜索
        results = mh.search("编成", fuzzy=True)  # 模糊搜索
        mh.suggest("编")                # 补全建议
        mh.save("index.json")           # 持久化
        mh2 = PM.meowhawk.load("index.json")  # 加载

        # 也可以直接用类
        from PyMsi.meowhawk import MeowHawk
        mh = MeowHawk()
    """

    def __init__(self):
        self._default_k1 = BM25_K1
        self._default_b = BM25_B

    def __repr__(self):
        return "<PyMsi.meowhawk [MeowHawk 搜索引擎] v1.7.0>"

    def __call__(self, k1=BM25_K1, b=BM25_B):
        """创建 MeowHawk 引擎实例: PM.meowhawk() → MeowHawk(k1, b)"""
        return MeowHawk(k1=k1, b=b)

    def create(self, k1=BM25_K1, b=BM25_B):
        """创建引擎实例 (显式方法)"""
        return MeowHawk(k1=k1, b=b)

    def load(self, path):
        """从文件加载索引"""
        return MeowHawk.load(path)

    def search_in(self, documents, query, limit=10, fuzzy=True):
        """快捷搜索: 一次性索引+搜索

        Args:
            documents: 文档列表 [str, ...]
            query: 查询字符串
            limit: 返回数上限
            fuzzy: 是否模糊匹配

        Returns:
            [SearchResult, ...]
        """
        mh = MeowHawk()
        mh.add_documents(documents)
        return mh.search(query, limit=limit, fuzzy=fuzzy)

    def demo(self):
        """运行演示: 展示 MeowHawk 的搜索能力"""
        print()
        print("=" * 60)
        print("  MeowHawk 搜索引擎演示")
        print("  自研查找算法 | BM25 排序 | N-gram 模糊匹配")
        print("=" * 60)

        docs = [
            "Python是最流行的编程语言, 简单易学, 适合初学者",
            "Java是一种面向对象的编程语言, 广泛用于企业级开发",
            "Go语言由Google开发, 以并发性能著称, 适合云原生应用",
            "JavaScript是Web前端的核心语言, 也可以做后端(Node.js)",
            "Rust语言注重内存安全和零成本抽象, 是系统编程的未来",
            "C语言是最底层的高级语言, 操作系统内核的首选",
            "Swift是Apple推出的编程语言, 用于iOS和macOS开发",
            "Kotlin是JetBrains开发的语言, Google官方推荐的Android开发语言",
            "TypeScript是JavaScript的超集, 添加了静态类型系统",
            "Ruby以优雅著称, Rails框架让Web开发变得高效",
        ]

        mh = MeowHawk()
        mh.add_documents(docs)

        print(f"\n  索引: {mh.index.num_documents} 文档, "
              f"{mh.index.vocabulary_size} 词汇, "
              f"平均文档长度 {mh.index.avg_doc_length:.1f}")

        queries = [
            ("编程语言", False),
            ("python", False),
            ("web前端", False),
            ("编成语言", True),   # 故意打错, 测试模糊搜索
            ("gogle", True),     # 故意打错
        ]

        for query, fuzzy in queries:
            mode = "模糊搜索" if fuzzy else "搜索"
            print(f"\n  --- {mode}: \"{query}\" ---")
            results = mh.search(query, limit=3, fuzzy=fuzzy)
            if not results:
                print("    (无结果)")
            for r in results:
                print(f"    [{r.score:.3f}] {r.snippet}")

        # 搜索建议
        print(f"\n  --- 搜索建议: \"go\" ---")
        suggestions = mh.suggest("go", limit=5)
        print(f"    {suggestions}")

        # 统计
        print(f"\n  引擎统计: {mh.stats()}")
        print("\n" + "=" * 60)
        print("  MeowHawk 演示完成!")
        print("=" * 60)

        return mh

    def benchmark(self, num_docs=1000, num_queries=100):
        """性能基准测试

        Args:
            num_docs: 文档数量
            num_queries: 查询次数

        Returns:
            dict 性能数据
        """
        import time
        import random

        # 生成测试文档
        subjects = ["编程", "算法", "数据结构", "数据库", "网络", "操作系统",
                     "人工智能", "机器学习", "深度学习", "云计算", "区块链",
                     "前端", "后端", "全栈", "运维", "测试", "安全", "架构"]

        verbs = ["是", "可以", "包括", "涉及", "需要", "使用", "支持", "提供"]

        objects = ["核心技术", "重要概念", "基础理论", "实践方法", "开发工具",
                    "设计模式", "最佳实践", "关键步骤", "主要特点", "应用场景"]

        docs = []
        for i in range(num_docs):
            parts = []
            for _ in range(random.randint(3, 8)):
                parts.append(f"{random.choice(subjects)}{random.choice(verbs)}{random.choice(objects)}")
            docs.append(''.join(parts))

        # 索引测试
        t0 = time.perf_counter()
        mh = MeowHawk()
        mh.add_documents(docs)
        t_index = time.perf_counter() - t0

        # 搜索测试
        queries = [random.choice(subjects) + random.choice(objects) for _ in range(num_queries)]
        t0 = time.perf_counter()
        for q in queries:
            mh.search(q, limit=10, fuzzy=False)
        t_search = time.perf_counter() - t0

        # 模糊搜索测试
        t0 = time.perf_counter()
        for q in queries:
            mh.search(q, limit=10, fuzzy=True)
        t_fuzzy = time.perf_counter() - t0

        result = {
            'num_docs': num_docs,
            'vocab_size': mh.index.vocabulary_size,
            'index_time_ms': round(t_index * 1000, 2),
            'search_time_ms': round(t_search * 1000, 2),
            'search_per_query_ms': round(t_search * 1000 / num_queries, 3),
            'fuzzy_time_ms': round(t_fuzzy * 1000, 2),
            'fuzzy_per_query_ms': round(t_fuzzy * 1000 / num_queries, 3),
            'queries_per_sec': round(num_queries / t_search),
        }

        print(f"\n[MeowHawk Benchmark]")
        print(f"  文档数: {num_docs}, 词汇量: {mh.index.vocabulary_size}")
        print(f"  索引时间: {result['index_time_ms']}ms")
        print(f"  精确搜索: {result['search_per_query_ms']}ms/query ({result['queries_per_sec']} qps)")
        print(f"  模糊搜索: {result['fuzzy_per_query_ms']}ms/query")

        return result
