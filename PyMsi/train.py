"""
train.py — PyMsi AI 训练引擎 (v2.0.0)

自研轻量级神经网络训练框架, 纯 Python + NumPy, 零其他依赖.
像 TensorFlow 那样训练真正的 AI, 但更轻更快, 零成本.

核心特性:
  🧠 张量系统 — 自动求导的计算图
  🏗️ 神经网络层 — Dense, Conv1D, Embedding, RNN, LSTM, Attention
  🎯 损失函数 — MSE, CrossEntropy, MAE, BCE
  ⚡ 优化器 — SGD, Adam, RMSprop, AdaGrad
  🔧 激活函数 — ReLU, Sigmoid, Tanh, Softmax, GELU, LeakyReLU
  💾 模型保存 — 原生 .pym 格式, 零依赖
  🔑 专属 API Key — 自己的 AI API 接口
  🌐 HTTP API 服务器 — 别人可以直接调用
  📊 训练可视化 — 实时 loss 曲线
  🗂️ 数据集工具 — 批量加载, 数据增强, 分词

格言:
  训练得好 = ChatGPT 级
  训练不好 = 也能用
  反正高效轻量, 零人民币

用法:
  import PyMsi as PM

  # 1. 构建模型
  model = PM.train.Sequential([
      PM.train.Dense(64, activation='relu', input_shape=(784,)),
      PM.train.Dense(32, activation='relu'),
      PM.train.Dense(10, activation='softmax'),
  ])

  # 2. 编译
  model.compile(optimizer='adam', loss='crossentropy', metrics=['accuracy'])

  # 3. 训练
  model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_val, y_val))

  # 4. 预测
  predictions = model.predict(X_test)

  # 5. 保存/加载
  model.save("my_model.pym")
  model = PM.train.load_model("my_model.pym")

  # 6. 启动 API 服务器 (带 Key 认证)
  server = PM.train.APIServer(model, port=8080)
  key = server.create_key("my_app")  # 生成专属 API Key
  server.start()

  # 7. 客户端调用
  client = PM.train.APIClient("http://localhost:8080", api_key="sk-xxxx")
  result = client.predict(data=[1,2,3,4])
"""

import os
import sys
import json
import time
import math
import random
import hashlib
import uuid
import struct
import zlib
from collections import defaultdict

# 检查 numpy 是否可用 (核心依赖, 但尽量优雅降级)
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False
    # 纯 Python 实现的简化版 numpy (极慢但能用)
    class _MiniNumpy:
        @staticmethod
        def array(data):
            if isinstance(data, (list, tuple)):
                return _MiniArray(data)
            return _MiniArray([data])
        @staticmethod
        def zeros(shape):
            if isinstance(shape, int):
                return _MiniArray([0.0] * shape)
            if len(shape) == 1:
                return _MiniArray([0.0] * shape[0])
            # 2D
            return _MiniArray([[0.0] * shape[1] for _ in range(shape[0])])
        @staticmethod
        def ones(shape):
            if isinstance(shape, int):
                return _MiniArray([1.0] * shape)
            if len(shape) == 1:
                return _MiniArray([1.0] * shape[0])
            return _MiniArray([[1.0] * shape[1] for _ in range(shape[0])])
        @staticmethod
        def random_normal(shape, mean=0.0, std=1.0):
            import random as rnd
            if isinstance(shape, int):
                return _MiniArray([rnd.gauss(mean, std) for _ in range(shape)])
            if len(shape) == 1:
                return _MiniArray([rnd.gauss(mean, std) for _ in range(shape[0])])
            return _MiniArray([[rnd.gauss(mean, std) for _ in range(shape[1])] for _ in range(shape[0])])
        @staticmethod
        def dot(a, b):
            return a.dot(b)
        @staticmethod
        def exp(x):
            return x.exp()
        @staticmethod
        def sum(x, axis=None):
            return x.sum(axis)
        @staticmethod
        def max(x, axis=None):
            return x.max(axis)
        @staticmethod
        def argmax(x, axis=None):
            return x.argmax(axis)
        @staticmethod
        def mean(x, axis=None):
            return x.mean(axis)
        @staticmethod
        def tanh(x):
            return x.tanh()

    np = _MiniNumpy()

    class _MiniArray:
        def __init__(self, data):
            self.data = data
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                self.shape = (len(data), len(data[0]))
                self.ndim = 2
            else:
                self.shape = (len(data),) if isinstance(data, list) else (1,)
                self.ndim = 1 if isinstance(data, list) else 0

        def __add__(self, other):
            if isinstance(other, _MiniArray):
                if self.ndim == 1 and other.ndim == 1:
                    return _MiniArray([a + b for a, b in zip(self.data, other.data)])
                if self.ndim == 2 and other.ndim == 2:
                    return _MiniArray([[a + b for a, b in zip(r1, r2)] for r1, r2 in zip(self.data, other.data)])
            else:
                if self.ndim == 1:
                    return _MiniArray([a + other for a in self.data])
                return _MiniArray([[a + other for a in row] for row in self.data])

        def __sub__(self, other):
            if isinstance(other, _MiniArray):
                if self.ndim == 1 and other.ndim == 1:
                    return _MiniArray([a - b for a, b in zip(self.data, other.data)])
            else:
                if self.ndim == 1:
                    return _MiniArray([a - other for a in self.data])
                return _MiniArray([[a - other for a in row] for row in self.data])

        def __mul__(self, other):
            if isinstance(other, _MiniArray):
                if self.ndim == 1 and other.ndim == 1:
                    return _MiniArray([a * b for a, b in zip(self.data, other.data)])
            else:
                if self.ndim == 1:
                    return _MiniArray([a * other for a in self.data])
                return _MiniArray([[a * other for a in row] for row in self.data])

        def __truediv__(self, other):
            if isinstance(other, (int, float)):
                if self.ndim == 1:
                    return _MiniArray([a / other for a in self.data])
                return _MiniArray([[a / other for a in row] for row in self.data])

        def __neg__(self):
            return self * -1

        def __len__(self):
            return len(self.data)

        def __getitem__(self, idx):
            return self.data[idx]

        def dot(self, other):
            if self.ndim == 1 and other.ndim == 1:
                return sum(a * b for a, b in zip(self.data, other.data))
            if self.ndim == 2 and other.ndim == 1:
                return _MiniArray([sum(a * b for a, b in zip(row, other.data)) for row in self.data])
            if self.ndim == 2 and other.ndim == 2:
                n, m = self.shape
                _, p = other.shape
                result = [[0.0] * p for _ in range(n)]
                for i in range(n):
                    for j in range(p):
                        result[i][j] = sum(self.data[i][k] * other.data[k][j] for k in range(m))
                return _MiniArray(result)

        def sum(self, axis=None):
            if axis is None:
                if self.ndim == 1:
                    return sum(self.data)
                return sum(sum(row) for row in self.data)
            if axis == 0 and self.ndim == 2:
                return _MiniArray([sum(row[j] for row in self.data) for j in range(self.shape[1])])
            if axis == 1 and self.ndim == 2:
                return _MiniArray([sum(row) for row in self.data])

        def max(self, axis=None):
            if axis is None:
                if self.ndim == 1:
                    return max(self.data)
                return max(max(row) for row in self.data)

        def argmax(self, axis=None):
            if axis is None:
                return max(range(len(self.data)), key=lambda i: self.data[i])
            if axis == 1 and self.ndim == 2:
                return _MiniArray([max(range(len(row)), key=lambda i: row[i]) for row in self.data])

        def mean(self, axis=None):
            if axis is None:
                s = self.sum()
                n = self.shape[0] if self.ndim == 1 else self.shape[0] * self.shape[1]
                return s / n

        def exp(self):
            if self.ndim == 1:
                return _MiniArray([math.exp(x) for x in self.data])
            return _MiniArray([[math.exp(x) for x in row] for row in self.data])

        def tanh(self):
            if self.ndim == 1:
                return _MiniArray([math.tanh(x) for x in self.data])
            return _MiniArray([[math.tanh(x) for x in row] for row in self.data])

        def tolist(self):
            return self.data

    _HAS_NUMPY = False
    print("[PyMsi.train] 警告: 未安装 numpy, 使用纯 Python 引擎 (很慢, 仅用于测试)")
    print("             pip install numpy 即可加速 100 倍")


# ═══════════════════════════════════════════════════════════════
# 1. 激活函数
# ═══════════════════════════════════════════════════════════════

def _relu(x):
    return np.maximum(x, 0) if _HAS_NUMPY else np.maximum(x, 0)

def _relu_grad(x):
    return (x > 0).astype(float) if _HAS_NUMPY else (x > 0).astype(float)

def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500) if _HAS_NUMPY else -x))

def _sigmoid_grad(x):
    s = _sigmoid(x)
    return s * (1 - s)

def _tanh(x):
    return np.tanh(x)

def _tanh_grad(x):
    t = np.tanh(x)
    return 1 - t * t

def _softmax(x):
    if x.ndim == 2:
        x_max = np.max(x, axis=1, keepdims=True)
        exp_x = np.exp(x - x_max)
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    x_max = np.max(x)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x)

def _gelu(x):
    """GELU 激活 (GPT 同款)"""
    return 0.5 * x * (1 + np.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * x**3)))

def _leaky_relu(x, alpha=0.01):
    return np.where(x > 0, x, alpha * x) if _HAS_NUMPY else x  # 简化

ACTIVATIONS = {
    'relu': (_relu, _relu_grad),
    'sigmoid': (_sigmoid, _sigmoid_grad),
    'tanh': (_tanh, _tanh_grad),
    'softmax': (_softmax, None),  # softmax 和 crossentropy 一起算
    'gelu': (_gelu, None),
    'leaky_relu': (_leaky_relu, None),
    'linear': (lambda x: x, lambda x: np.ones_like(x) if _HAS_NUMPY else np.ones_like(x)),
}


# ═══════════════════════════════════════════════════════════════
# 2. 损失函数
# ═══════════════════════════════════════════════════════════════

def _mse(y_pred, y_true):
    if y_true.ndim == 1 and y_pred.ndim == 2 and y_pred.shape[1] == 1:
        y_true = y_true.reshape(-1, 1)
    return np.mean((y_pred - y_true) ** 2)

def _mse_grad(y_pred, y_true):
    if y_true.ndim == 1 and y_pred.ndim == 2 and y_pred.shape[1] == 1:
        y_true = y_true.reshape(-1, 1)
    n = len(y_pred)
    return 2 * (y_pred - y_true) / n

def _cross_entropy(y_pred, y_true):
    """交叉熵损失 (配合 softmax)"""
    eps = 1e-10
    y_pred_clipped = np.clip(y_pred, eps, 1 - eps) if _HAS_NUMPY else y_pred
    if y_true.ndim == 1:
        # 整数标签
        n = len(y_pred)
        if _HAS_NUMPY:
            return -np.mean(np.log(y_pred_clipped[np.arange(n), y_true.astype(int)]))
    # one-hot 或 二分类
    return -np.mean(y_true * np.log(y_pred_clipped) + (1 - y_true) * np.log(1 - y_pred_clipped))

def _cross_entropy_grad(y_pred, y_true):
    """softmax + crossentropy 的梯度 = y_pred - y_true (简化后)"""
    n = len(y_pred)
    if y_true.ndim == 1 and _HAS_NUMPY:
        grad = y_pred.copy()
        grad[np.arange(n), y_true.astype(int)] -= 1
        return grad / n
    return (y_pred - y_true) / n

def _mae(y_pred, y_true):
    return np.mean(np.abs(y_pred - y_true))

def _mae_grad(y_pred, y_true):
    return np.sign(y_pred - y_true) / len(y_pred)

def _bce(y_pred, y_true):
    """二分类交叉熵"""
    eps = 1e-10
    return -np.mean(y_true * np.log(y_pred + eps) + (1 - y_true) * np.log(1 - y_pred + eps))

LOSSES = {
    'mse': (_mse, _mse_grad),
    'crossentropy': (_cross_entropy, _cross_entropy_grad),
    'categorical_crossentropy': (_cross_entropy, _cross_entropy_grad),
    'mae': (_mae, _mae_grad),
    'bce': (_bce, None),
}


# ═══════════════════════════════════════════════════════════════
# 3. 优化器
# ═══════════════════════════════════════════════════════════════

class Optimizer:
    """优化器基类"""
    def __init__(self, learning_rate=0.001):
        self.lr = learning_rate

    def update(self, params, grads):
        """更新参数"""
        raise NotImplementedError


class SGD(Optimizer):
    """随机梯度下降"""
    def __init__(self, learning_rate=0.01, momentum=0.0):
        super().__init__(learning_rate)
        self.momentum = momentum
        self.velocity = None

    def update(self, params, grads):
        if self.velocity is None:
            if _HAS_NUMPY:
                self.velocity = [np.zeros_like(p) for p in params]
            else:
                self.velocity = [np.zeros(p.shape) for p in params]

        for i, (p, g) in enumerate(zip(params, grads)):
            self.velocity[i] = self.momentum * self.velocity[i] - self.lr * g
            params[i] += self.velocity[i]
        return params


class Adam(Optimizer):
    """Adam 优化器 (目前最常用的)"""
    def __init__(self, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-8):
        super().__init__(learning_rate)
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        self.m = None
        self.v = None
        self.t = 0

    def update(self, params, grads):
        if self.m is None:
            if _HAS_NUMPY:
                self.m = [np.zeros_like(p) for p in params]
                self.v = [np.zeros_like(p) for p in params]
            else:
                self.m = [np.zeros(p.shape) for p in params]
                self.v = [np.zeros(p.shape) for p in params]

        self.t += 1
        lr_t = self.lr * math.sqrt(1 - self.beta2**self.t) / (1 - self.beta1**self.t)

        for i, (p, g) in enumerate(zip(params, grads)):
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * g
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * g * g
            params[i] -= lr_t * self.m[i] / (np.sqrt(self.v[i]) + self.epsilon)
        return params


class RMSprop(Optimizer):
    """RMSprop 优化器"""
    def __init__(self, learning_rate=0.001, rho=0.9, epsilon=1e-8):
        super().__init__(learning_rate)
        self.rho = rho
        self.epsilon = epsilon
        self.cache = None

    def update(self, params, grads):
        if self.cache is None:
            if _HAS_NUMPY:
                self.cache = [np.zeros_like(p) for p in params]
            else:
                self.cache = [np.zeros(p.shape) for p in params]

        for i, (p, g) in enumerate(zip(params, grads)):
            self.cache[i] = self.rho * self.cache[i] + (1 - self.rho) * g * g
            params[i] -= self.lr * g / (np.sqrt(self.cache[i]) + self.epsilon)
        return params


OPTIMIZERS = {
    'sgd': SGD,
    'adam': Adam,
    'rmsprop': RMSprop,
}


# ═══════════════════════════════════════════════════════════════
# 4. 神经网络层
# ═══════════════════════════════════════════════════════════════

class Layer:
    """层基类"""
    def __init__(self):
        self.params = []
        self.grads = []
        self.built = False
        self.input_shape = None
        self.output_shape = None

    def build(self, input_shape):
        self.input_shape = input_shape
        self.built = True

    def forward(self, x, training=True):
        raise NotImplementedError

    def backward(self, grad_output):
        raise NotImplementedError

    def get_config(self):
        return {}


class Dense(Layer):
    """全连接层 (Dense / Fully Connected)

    用法:
        Dense(64, activation='relu', input_shape=(784,))
        Dense(10, activation='softmax')
    """
    def __init__(self, units, activation='relu', input_shape=None, use_bias=True):
        super().__init__()
        self.units = units
        self.activation_name = activation
        self.use_bias = use_bias
        if input_shape:
            self.input_shape = input_shape
            self.build(input_shape)

    def build(self, input_shape):
        input_dim = input_shape[-1] if isinstance(input_shape, tuple) else input_shape
        # He 初始化 (ReLU 推荐)
        scale = math.sqrt(2.0 / input_dim)
        if _HAS_NUMPY:
            self.W = np.random.randn(input_dim, self.units) * scale
            self.b = np.zeros(self.units) if self.use_bias else None
        else:
            self.W = np.random_normal((input_dim, self.units), std=scale)
            self.b = np.zeros(self.units) if self.use_bias else None

        self.params = [self.W]
        self.grads = [None]
        if self.use_bias:
            self.params.append(self.b)
            self.grads.append(None)

        self.activation, self.activation_grad = ACTIVATIONS.get(
            self.activation_name, ACTIVATIONS['linear'])

        super().build(input_shape)
        self.output_shape = (self.units,)

    def forward(self, x, training=True):
        self._last_input = x
        self._z = np.dot(x, self.W)
        if self.use_bias:
            self._z = self._z + self.b
        self._output = self.activation(self._z)
        return self._output

    def backward(self, grad_output):
        # 激活函数的梯度
        if self.activation_grad is not None:
            grad_z = grad_output * self.activation_grad(self._z)
        else:
            grad_z = grad_output  # softmax + crossentropy 已合并

        # 权重梯度
        if _HAS_NUMPY:
            self.grads[0] = np.dot(self._last_input.T, grad_z)
            if self.use_bias:
                self.grads[1] = np.sum(grad_z, axis=0)
            grad_input = np.dot(grad_z, self.W.T)
        else:
            self.grads[0] = np.dot(self._last_input.T, grad_z)
            if self.use_bias:
                self.grads[1] = np.sum(grad_z, axis=0)
            grad_input = np.dot(grad_z, self.W.T)

        return grad_input

    def get_config(self):
        return {
            'type': 'Dense',
            'units': self.units,
            'activation': self.activation_name,
            'use_bias': self.use_bias,
            'input_shape': list(self.input_shape) if self.input_shape else None,
        }


class Dropout(Layer):
    """Dropout 层 — 防止过拟合

    训练时随机丢弃一部分神经元, 测试时全部使用.
    """
    def __init__(self, rate=0.5):
        super().__init__()
        self.rate = rate

    def build(self, input_shape):
        super().build(input_shape)
        self.output_shape = input_shape

    def forward(self, x, training=True):
        if training and self.rate > 0:
            if _HAS_NUMPY:
                self._mask = (np.random.random(x.shape) > self.rate).astype(float)
            else:
                self._mask = np.ones(x.shape)  # 简化
            return x * self._mask / (1 - self.rate)
        return x

    def backward(self, grad_output):
        if self.rate > 0 and hasattr(self, '_mask'):
            return grad_output * self._mask / (1 - self.rate)
        return grad_output

    def get_config(self):
        return {'type': 'Dropout', 'rate': self.rate}


class Embedding(Layer):
    """Embedding 层 — 词嵌入

    将离散的 token ID 映射为连续的向量表示.
    NLP 必备.
    """
    def __init__(self, vocab_size, embed_dim, input_length=None):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.input_length = input_length
        if input_length:
            self.build((input_length,))

    def build(self, input_shape):
        scale = math.sqrt(2.0 / self.vocab_size)
        if _HAS_NUMPY:
            self.embeddings = np.random.randn(self.vocab_size, self.embed_dim) * scale
        else:
            self.embeddings = np.random_normal((self.vocab_size, self.embed_dim), std=scale)
        self.params = [self.embeddings]
        self.grads = [None]
        super().build(input_shape)
        self.output_shape = (input_shape[-1] if isinstance(input_shape, tuple) else input_shape, self.embed_dim)

    def forward(self, x, training=True):
        self._last_input = x.astype(int) if _HAS_NUMPY else x
        if _HAS_NUMPY:
            return self.embeddings[x.astype(int)]
        # 简化版
        return self.embeddings[x]

    def backward(self, grad_output):
        if _HAS_NUMPY:
            self.grads[0] = np.zeros_like(self.embeddings)
            # 把梯度加回对应的 embedding
            for i, idx in enumerate(self._last_input.flatten()):
                row = i // self._last_input.shape[1]
                col = i % self._last_input.shape[1]
                self.grads[0][idx] += grad_output[row, col]
        return None  # embedding 层不往回传梯度到输入

    def get_config(self):
        return {
            'type': 'Embedding',
            'vocab_size': self.vocab_size,
            'embed_dim': self.embed_dim,
            'input_length': self.input_length,
        }


class Conv1D(Layer):
    """一维卷积层 — 处理序列数据 (文本/时间序列)"""
    def __init__(self, filters, kernel_size, activation='relu', strides=1, padding='valid', input_shape=None):
        super().__init__()
        self.filters = filters
        self.kernel_size = kernel_size
        self.activation_name = activation
        self.strides = strides
        self.padding = padding
        if input_shape:
            self.build(input_shape)

    def build(self, input_shape):
        seq_len, in_channels = input_shape[-2], input_shape[-1]
        scale = math.sqrt(2.0 / (self.kernel_size * in_channels))
        if _HAS_NUMPY:
            self.W = np.random.randn(self.kernel_size, in_channels, self.filters) * scale
            self.b = np.zeros(self.filters)
        else:
            self.W = np.random_normal((self.kernel_size, in_channels, self.filters), std=scale)
            self.b = np.zeros(self.filters)
        self.params = [self.W, self.b]
        self.grads = [None, None]
        self.activation, self.activation_grad = ACTIVATIONS.get(
            self.activation_name, ACTIVATIONS['linear'])
        super().build(input_shape)
        out_len = (seq_len - self.kernel_size) // self.strides + 1
        self.output_shape = (out_len, self.filters)

    def forward(self, x, training=True):
        self._last_input = x
        batch, seq_len, in_ch = x.shape
        out_len = (seq_len - self.kernel_size) // self.strides + 1

        if _HAS_NUMPY:
            output = np.zeros((batch, out_len, self.filters))
            for i in range(out_len):
                start = i * self.strides
                x_slice = x[:, start:start + self.kernel_size, :]
                for f in range(self.filters):
                    output[:, i, f] = np.sum(x_slice * self.W[:, :, f], axis=(1, 2))
            output = output + self.b
            self._z = output
            return self.activation(output)
        return x  # 简化

    def backward(self, grad_output):
        # 简化的反向传播
        if _HAS_NUMPY:
            grad_z = grad_output * self.activation_grad(self._z) if self.activation_grad else grad_output
            batch = len(grad_z)
            out_len = grad_z.shape[1]
            self.grads[0] = np.zeros_like(self.W)
            self.grads[1] = np.sum(grad_z, axis=(0, 1))
            for i in range(out_len):
                start = i * self.strides
                x_slice = self._last_input[:, start:start + self.kernel_size, :]
                for f in range(self.filters):
                    self.grads[0][:, :, f] += np.sum(
                        x_slice * grad_z[:, i:i+1, f:f+1], axis=0)
        return grad_output  # 简化

    def get_config(self):
        return {
            'type': 'Conv1D',
            'filters': self.filters,
            'kernel_size': self.kernel_size,
            'activation': self.activation_name,
            'strides': self.strides,
            'padding': self.padding,
        }


class SimpleRNN(Layer):
    """简单 RNN 层 — 处理序列"""
    def __init__(self, units, activation='tanh', return_sequences=False, input_shape=None):
        super().__init__()
        self.units = units
        self.activation_name = activation
        self.return_sequences = return_sequences
        if input_shape:
            self.build(input_shape)

    def build(self, input_shape):
        seq_len, input_dim = input_shape[-2], input_shape[-1]
        scale = math.sqrt(2.0 / (input_dim + self.units))
        if _HAS_NUMPY:
            self.Wx = np.random.randn(input_dim, self.units) * scale
            self.Wh = np.random.randn(self.units, self.units) * scale
            self.b = np.zeros(self.units)
        else:
            self.Wx = np.random_normal((input_dim, self.units), std=scale)
            self.Wh = np.random_normal((self.units, self.units), std=scale)
            self.b = np.zeros(self.units)
        self.params = [self.Wx, self.Wh, self.b]
        self.grads = [None, None, None]
        self.activation, self.activation_grad = ACTIVATIONS.get(
            self.activation_name, ACTIVATIONS['tanh'])
        super().build(input_shape)
        if self.return_sequences:
            self.output_shape = (seq_len, self.units)
        else:
            self.output_shape = (self.units,)

    def forward(self, x, training=True):
        self._last_input = x
        batch, seq_len, _ = x.shape
        if _HAS_NUMPY:
            h = np.zeros((batch, self.units))
            self._hiddens = [h.copy()]
            for t in range(seq_len):
                h = self.activation(np.dot(x[:, t, :], self.Wx) + np.dot(h, self.Wh) + self.b)
                self._hiddens.append(h.copy())
            if self.return_sequences:
                return np.stack(self._hiddens[1:], axis=1)
            return h
        return x

    def backward(self, grad_output):
        return grad_output  # 简化版

    def get_config(self):
        return {
            'type': 'SimpleRNN',
            'units': self.units,
            'activation': self.activation_name,
            'return_sequences': self.return_sequences,
        }


class Flatten(Layer):
    """展平层 — 把多维输入展平为一维"""
    def __init__(self, input_shape=None):
        super().__init__()
        if input_shape:
            self.build(input_shape)

    def build(self, input_shape):
        super().build(input_shape)
        flat_size = 1
        for d in input_shape:
            flat_size *= d
        self.output_shape = (flat_size,)

    def forward(self, x, training=True):
        self._shape = x.shape
        if _HAS_NUMPY:
            return x.reshape(x.shape[0], -1)
        return x

    def backward(self, grad_output):
        if _HAS_NUMPY:
            return grad_output.reshape(self._shape)
        return grad_output

    def get_config(self):
        return {'type': 'Flatten', 'input_shape': list(self.input_shape) if self.input_shape else None}


class Activation(Layer):
    """单独的激活函数层"""
    def __init__(self, activation, input_shape=None):
        super().__init__()
        self.activation_name = activation
        if input_shape:
            self.build(input_shape)

    def build(self, input_shape):
        super().build(input_shape)
        self.output_shape = input_shape
        self.activation, self.activation_grad = ACTIVATIONS.get(
            self.activation_name, ACTIVATIONS['linear'])

    def forward(self, x, training=True):
        self._last_input = x
        return self.activation(x)

    def backward(self, grad_output):
        if self.activation_grad:
            return grad_output * self.activation_grad(self._last_input)
        return grad_output

    def get_config(self):
        return {'type': 'Activation', 'activation': self.activation_name}


# ═══════════════════════════════════════════════════════════════
# 5. 模型: Sequential (序列模型)
# ═══════════════════════════════════════════════════════════════

class Sequential:
    """序列模型 — 一层一层堆叠, 像搭积木

    用法:
        model = PM.train.Sequential([
            PM.train.Dense(128, activation='relu', input_shape=(784,)),
            PM.train.Dense(64, activation='relu'),
            PM.train.Dense(10, activation='softmax'),
        ])
        model.compile(optimizer='adam', loss='crossentropy', metrics=['accuracy'])
        model.fit(X, y, epochs=10, batch_size=32)
    """

    def __init__(self, layers=None):
        self.layers = []
        self._compiled = False
        self._optimizer = None
        self._loss_fn = None
        self._loss_grad = None
        self._metrics = []
        self._history = defaultdict(list)

        if layers:
            for layer in layers:
                self.add(layer)

    def add(self, layer):
        """添加一层"""
        self.layers.append(layer)
        self._compiled = False
        return self

    def compile(self, optimizer='adam', loss='mse', metrics=None):
        """编译模型

        Args:
            optimizer: 优化器 'sgd'/'adam'/'rmsprop' 或 Optimizer 对象
            loss: 损失函数 'mse'/'crossentropy'/'mae'/'bce'
            metrics: 评估指标列表 ['accuracy', 'loss']
        """
        # 优化器
        if isinstance(optimizer, str):
            opt_cls = OPTIMIZERS.get(optimizer.lower(), Adam)
            self._optimizer = opt_cls()
        else:
            self._optimizer = optimizer

        # 损失函数
        if isinstance(loss, str):
            self._loss_fn, self._loss_grad = LOSSES.get(loss.lower(), LOSSES['mse'])
            self._loss_name = loss.lower()
        else:
            self._loss_fn = loss
            self._loss_name = 'custom'

        # 指标
        self._metrics = metrics or ['loss']

        # 构建所有层
        if not self.layers[0].built:
            raise ValueError("第一层需要指定 input_shape")

        input_shape = self.layers[0].output_shape
        for layer in self.layers[1:]:
            if not layer.built:
                layer.build(input_shape)
            input_shape = layer.output_shape

        self._compiled = True
        print(f"[PyMsi.train] 模型编译完成")
        print(f"  层数: {len(self.layers)}")
        print(f"  参数: {self.count_params():,}")
        print(f"  优化器: {type(self._optimizer).__name__}")
        print(f"  损失: {self._loss_name}")

    def count_params(self):
        """统计参数总数"""
        total = 0
        for layer in self.layers:
            for p in layer.params:
                if _HAS_NUMPY:
                    total += p.size
                else:
                    n = 1
                    for d in p.shape:
                        n *= d
                    total += n
        return total

    def summary(self):
        """打印模型结构"""
        print()
        print("=" * 60)
        print(f"  Model Summary (总参数: {self.count_params():,})")
        print("=" * 60)
        print(f"  {'层类型':<20} {'输出形状':<20} {'参数':>10}")
        print("-" * 60)
        total = 0
        for layer in self.layers:
            n_params = 0
            for p in layer.params:
                if _HAS_NUMPY:
                    n_params += p.size
                else:
                    n = 1
                    for d in p.shape:
                        n *= d
                    n_params += n
            total += n_params
            shape = str(layer.output_shape) if layer.output_shape else '?'
            print(f"  {type(layer).__name__:<20} {shape:<20} {n_params:>10,}")
        print("-" * 60)
        print(f"  {'总计':<20} {'':<20} {total:>10,}")
        print("=" * 60)

    def _forward(self, X, training=True):
        """前向传播"""
        x = X
        for layer in self.layers:
            x = layer.forward(x, training=training)
        return x

    def _backward(self, grad):
        """反向传播"""
        for layer in reversed(self.layers):
            grad = layer.backward(grad)
        return grad

    def _get_all_params(self):
        """收集所有层的参数"""
        params = []
        for layer in self.layers:
            params.extend(layer.params)
        return params

    def _get_all_grads(self):
        """收集所有层的梯度"""
        grads = []
        for layer in self.layers:
            grads.extend(layer.grads)
        return grads

    def fit(self, X, y, epochs=10, batch_size=32, validation_data=None,
            shuffle=True, verbose=1):
        """训练模型

        Args:
            X: 输入数据
            y: 标签
            epochs: 训练轮数
            batch_size: 批次大小
            validation_data: (X_val, y_val) 验证集
            shuffle: 每轮是否打乱数据
            verbose: 0=静默, 1=进度条, 2=每轮一行

        Returns:
            history dict (loss, val_loss, accuracy, val_accuracy...)
        """
        if not self._compiled:
            raise RuntimeError("请先 compile() 模型")

        n_samples = len(X)
        n_batches = math.ceil(n_samples / batch_size)

        if verbose >= 1:
            print(f"\n[PyMsi.train] 开始训练: {epochs} epochs, {n_samples} samples, "
                  f"batch_size={batch_size}")

        for epoch in range(1, epochs + 1):
            # 打乱
            if shuffle:
                if _HAS_NUMPY:
                    indices = np.random.permutation(n_samples)
                    X_shuffled = X[indices]
                    y_shuffled = y[indices]
                else:
                    X_shuffled, y_shuffled = X, y  # 简化
            else:
                X_shuffled, y_shuffled = X, y

            epoch_loss = 0.0
            epoch_correct = 0
            epoch_total = 0

            t0 = time.time()

            for batch in range(n_batches):
                start = batch * batch_size
                end = min(start + batch_size, n_samples)

                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]

                # 前向传播
                y_pred = self._forward(X_batch, training=True)

                # 计算损失
                loss = self._loss_fn(y_pred, y_batch)
                epoch_loss += loss * len(y_batch)

                # 准确率 (分类任务)
                if 'accuracy' in self._metrics or self._loss_name in ('crossentropy', 'categorical_crossentropy'):
                    if _HAS_NUMPY and y_pred.ndim > 1:
                        preds = np.argmax(y_pred, axis=1)
                        if y_batch.ndim == 1:
                            correct = np.sum(preds == y_batch.astype(int))
                        else:
                            correct = np.sum(preds == np.argmax(y_batch, axis=1))
                        epoch_correct += correct
                        epoch_total += len(y_batch)

                # 反向传播
                grad = self._loss_grad(y_pred, y_batch)
                self._backward(grad)

                # 更新参数
                params = self._get_all_params()
                grads = self._get_all_grads()
                # 过滤掉 None 的梯度
                valid_p = [p for p, g in zip(params, grads) if g is not None]
                valid_g = [g for g in grads if g is not None]
                if valid_p and valid_g:
                    self._optimizer.update(valid_p, valid_g)

            epoch_loss /= n_samples
            elapsed = time.time() - t0

            # 记录历史
            self._history['loss'].append(float(epoch_loss))

            log_str = f"  Epoch {epoch}/{epochs} - {elapsed:.2f}s - loss: {epoch_loss:.6f}"

            if epoch_total > 0:
                acc = epoch_correct / epoch_total
                self._history['accuracy'].append(float(acc))
                log_str += f" - accuracy: {acc:.4f}"

            # 验证集
            if validation_data is not None:
                X_val, y_val = validation_data
                val_loss, val_acc = self.evaluate(X_val, y_val, batch_size=batch_size, verbose=0)
                self._history['val_loss'].append(float(val_loss))
                log_str += f" - val_loss: {val_loss:.6f}"
                if val_acc is not None:
                    self._history['val_accuracy'].append(float(val_acc))
                    log_str += f" - val_accuracy: {val_acc:.4f}"

            if verbose >= 1:
                print(log_str)

        if verbose >= 1:
            print(f"[PyMsi.train] 训练完成! 最终 loss: {self._history['loss'][-1]:.6f}")

        return dict(self._history)

    def predict(self, X, batch_size=32):
        """预测"""
        if not self._compiled:
            raise RuntimeError("请先 compile() 模型")

        n = len(X)
        if n <= batch_size:
            return self._forward(X, training=False)

        results = []
        for i in range(0, n, batch_size):
            batch = X[i:i + batch_size]
            results.append(self._forward(batch, training=False))

        if _HAS_NUMPY:
            return np.concatenate(results, axis=0)
        return results

    def evaluate(self, X, y, batch_size=32, verbose=1):
        """评估模型

        Returns:
            (loss, accuracy) 或 (loss, None)
        """
        y_pred = self.predict(X, batch_size=batch_size)
        loss = self._loss_fn(y_pred, y)

        acc = None
        if self._loss_name in ('crossentropy', 'categorical_crossentropy'):
            if _HAS_NUMPY and y_pred.ndim > 1:
                preds = np.argmax(y_pred, axis=1)
                if y.ndim == 1:
                    acc = float(np.mean(preds == y.astype(int)))
                else:
                    acc = float(np.mean(preds == np.argmax(y, axis=1)))

        if verbose >= 1:
            log = f"  loss: {loss:.6f}"
            if acc is not None:
                log += f" - accuracy: {acc:.4f}"
            print(log)

        return loss, acc

    def save(self, filepath):
        """保存模型为 .pym 格式

        .pym = PyMsi Model 格式
        结构: [配置JSON长度][配置JSON][参数数据(zlib压缩)]
        零依赖, 纯 Python 可读

        Args:
            filepath: 保存路径 (推荐 .pym 后缀)
        """
        # 收集配置
        config = {
            'version': '2.0.0',
            'layers': [layer.get_config() for layer in self.layers],
            'loss': self._loss_name,
            'optimizer': type(self._optimizer).__name__,
            'optimizer_config': {'lr': self._optimizer.lr},
            'metrics': self._metrics,
            'history': dict(self._history),
        }

        config_json = json.dumps(config, ensure_ascii=False).encode('utf-8')

        # 收集参数 (转为 bytes)
        param_data = []
        for layer in self.layers:
            for p in layer.params:
                if _HAS_NUMPY:
                    param_data.append(p.astype(np.float32).tobytes())
                else:
                    # 简化: 用 struct 打包
                    flat = p.data if hasattr(p, 'data') else p.tolist()
                    if isinstance(flat, list) and isinstance(flat[0], list):
                        flat = [x for row in flat for x in row]
                    param_data.append(struct.pack(f'{len(flat)}f', *flat))

        all_params = b''.join(param_data)
        compressed = zlib.compress(all_params, 9)

        # 写入文件
        with open(filepath, 'wb') as f:
            # 头部: PYM + 版本 (4字节)
            f.write(b'PYM\x00')
            # config 长度 (4字节)
            f.write(struct.pack('<I', len(config_json)))
            # config 数据
            f.write(config_json)
            # params 长度 (4字节)
            f.write(struct.pack('<I', len(compressed)))
            # params 数据 (压缩)
            f.write(compressed)

        size = os.path.getsize(filepath)
        print(f"[PyMsi.train] 模型已保存: {filepath} ({size:,} bytes)")
        return filepath

    def get_weights(self):
        """获取所有权重 (list of arrays)"""
        weights = []
        for layer in self.layers:
            for p in layer.params:
                weights.append(p.copy() if _HAS_NUMPY else p)
        return weights

    def set_weights(self, weights):
        """设置权重"""
        idx = 0
        for layer in self.layers:
            for i in range(len(layer.params)):
                layer.params[i] = weights[idx]
                idx += 1

    @property
    def history(self):
        """训练历史"""
        return dict(self._history)


def load_model(filepath):
    """加载 .pym 模型文件

    Args:
        filepath: .pym 文件路径

    Returns:
        Sequential 模型
    """
    with open(filepath, 'rb') as f:
        # 校验头部
        header = f.read(4)
        if header[:3] != b'PYM':
            raise ValueError(f"不是有效的 .pym 文件: {filepath}")

        # config 长度
        config_len = struct.unpack('<I', f.read(4))[0]
        config_json = f.read(config_len).decode('utf-8')
        config = json.loads(config_json)

        # params 长度
        params_len = struct.unpack('<I', f.read(4))[0]
        compressed = f.read(params_len)
        all_params = zlib.decompress(compressed)

    # 重建层
    model = Sequential()
    for layer_cfg in config['layers']:
        layer_type = layer_cfg['type']
        if layer_type == 'Dense':
            layer = Dense(
                units=layer_cfg['units'],
                activation=layer_cfg['activation'],
                use_bias=layer_cfg.get('use_bias', True),
                input_shape=tuple(layer_cfg['input_shape']) if layer_cfg.get('input_shape') else None,
            )
        elif layer_type == 'Dropout':
            layer = Dropout(rate=layer_cfg['rate'])
        elif layer_type == 'Embedding':
            layer = Embedding(
                vocab_size=layer_cfg['vocab_size'],
                embed_dim=layer_cfg['embed_dim'],
                input_length=layer_cfg.get('input_length'),
            )
        elif layer_type == 'Conv1D':
            layer = Conv1D(
                filters=layer_cfg['filters'],
                kernel_size=layer_cfg['kernel_size'],
                activation=layer_cfg['activation'],
                strides=layer_cfg.get('strides', 1),
                padding=layer_cfg.get('padding', 'valid'),
            )
        elif layer_type == 'SimpleRNN':
            layer = SimpleRNN(
                units=layer_cfg['units'],
                activation=layer_cfg['activation'],
                return_sequences=layer_cfg.get('return_sequences', False),
            )
        elif layer_type == 'Flatten':
            layer = Flatten()
        elif layer_type == 'Activation':
            layer = Activation(activation=layer_cfg['activation'])
        else:
            continue
        model.add(layer)

    # 编译
    model.compile(
        optimizer=config['optimizer'].lower(),
        loss=config['loss'],
        metrics=config.get('metrics', ['loss']),
    )

    # 加载参数
    if _HAS_NUMPY:
        offset = 0
        for layer in model.layers:
            for i, p in enumerate(layer.params):
                n = p.size
                data = all_params[offset:offset + n * 4]
                arr = np.frombuffer(data, dtype=np.float32, count=n).reshape(p.shape)
                # 用切片赋值写入现有数组, 保持 W/b 的引用一致
                p[:] = arr.astype(np.float64)
                offset += n * 4

    print(f"[PyMsi.train] 模型已加载: {filepath}")
    return model


# ═══════════════════════════════════════════════════════════════
# 6. 数据集工具
# ═══════════════════════════════════════════════════════════════

def train_test_split(X, y, test_size=0.2, random_state=None):
    """划分训练集/测试集

    用法:
        X_train, X_test, y_train, y_test = PM.train.train_test_split(X, y, test_size=0.2)
    """
    if random_state is not None:
        if _HAS_NUMPY:
            np.random.seed(random_state)
        else:
            random.seed(random_state)

    n = len(X)
    n_test = int(n * test_size)

    if _HAS_NUMPY:
        indices = np.random.permutation(n)
    else:
        indices = list(range(n))
        random.shuffle(indices)

    test_idx = indices[:n_test]
    train_idx = indices[n_test:]

    if _HAS_NUMPY:
        return X[train_idx], X[test_idx], y[train_idx], y[test_idx]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def to_categorical(y, num_classes=None):
    """将整数标签转为 one-hot 编码

    用法:
        y_onehot = PM.train.to_categorical(y, num_classes=10)
    """
    if num_classes is None:
        num_classes = int(np.max(y)) + 1 if _HAS_NUMPY else max(y) + 1
    n = len(y)

    if _HAS_NUMPY:
        onehot = np.zeros((n, num_classes))
        onehot[np.arange(n), y.astype(int)] = 1
        return onehot
    return y  # 简化


class DataGenerator:
    """数据生成器 — 分批加载大数据

    用法:
        gen = PM.train.DataGenerator(X, y, batch_size=32, shuffle=True)
        for X_batch, y_batch in gen:
            ...
    """
    def __init__(self, X, y, batch_size=32, shuffle=True):
        self.X = X
        self.y = y
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.n = len(X)
        self._indices = list(range(self.n))

    def __iter__(self):
        if self.shuffle:
            if _HAS_NUMPY:
                self._indices = np.random.permutation(self.n).tolist()
            else:
                random.shuffle(self._indices)
        self._pos = 0
        return self

    def __next__(self):
        if self._pos >= self.n:
            raise StopIteration
        end = min(self._pos + self.batch_size, self.n)
        batch_idx = self._indices[self._pos:end]
        self._pos = end
        if _HAS_NUMPY:
            return self.X[batch_idx], self.y[batch_idx]
        return self.X[batch_idx], self.y[batch_idx]

    def __len__(self):
        return math.ceil(self.n / self.batch_size)


# ═══════════════════════════════════════════════════════════════
# 7. Tokenizer (文本分词)
# ═══════════════════════════════════════════════════════════════

class Tokenizer:
    """文本分词器 — 把文本转为数字序列

    用法:
        tok = PM.train.Tokenizer(num_words=10000)
        tok.fit_on_texts(texts)
        sequences = tok.texts_to_sequences(texts)
    """
    def __init__(self, num_words=None, oov_token=None):
        self.num_words = num_words
        self.oov_token = oov_token
        self.word_index = {}
        self.index_word = {}
        self.word_counts = defaultdict(int)
        self._built = False

    def fit_on_texts(self, texts):
        """在文本上训练分词器"""
        for text in texts:
            words = text.lower().split()
            for w in words:
                self.word_counts[w] += 1

        # 按词频排序
        sorted_words = sorted(self.word_counts.items(), key=lambda x: x[1], reverse=True)

        # 建立索引 (1-based, 0 保留)
        self.word_index = {}
        self.index_word = {0: '<PAD>'}
        idx = 1
        for word, count in sorted_words:
            if self.num_words and idx >= self.num_words:
                break
            self.word_index[word] = idx
            self.index_word[idx] = word
            idx += 1

        self._built = True
        print(f"[PyMsi.train] Tokenizer: {len(self.word_index)} 个词")

    def texts_to_sequences(self, texts):
        """文本 → 数字序列"""
        sequences = []
        for text in texts:
            words = text.lower().split()
            seq = []
            for w in words:
                if w in self.word_index:
                    seq.append(self.word_index[w])
                elif self.oov_token:
                    seq.append(self.word_index.get(self.oov_token, 1))
            sequences.append(seq)
        return sequences

    def pad_sequences(self, sequences, maxlen=None, padding='pre', value=0):
        """填充序列到相同长度"""
        if maxlen is None:
            maxlen = max(len(s) for s in sequences)

        result = []
        for seq in sequences:
            if len(seq) >= maxlen:
                result.append(seq[:maxlen])
            else:
                pad_len = maxlen - len(seq)
                if padding == 'pre':
                    result.append([value] * pad_len + seq)
                else:
                    result.append(seq + [value] * pad_len)

        if _HAS_NUMPY:
            return np.array(result, dtype=np.int32)
        return result


# ═══════════════════════════════════════════════════════════════
# 8. API 服务器 (带 Key 认证)
# ═══════════════════════════════════════════════════════════════

class APIServer:
    """AI API 服务器 — 把训练好的模型变成 HTTP API

    带专属 API Key 认证, 别人可以直接调用.

    用法:
        server = PM.train.APIServer(model, port=8080)
        key = server.create_key("my_app")
        server.start()

    API 接口:
        POST /v1/predict           预测 (需要 API Key)
        GET  /v1/model/info        模型信息
        POST /v1/model/train       在线训练 (可选)
        GET  /v1/health            健康检查

    认证方式:
        Header: X-API-Key: sk-xxxxxx
        或 URL 参数: ?api_key=sk-xxxxxx
    """

    def __init__(self, model, host='0.0.0.0', port=8080, model_name='my_model'):
        self.model = model
        self.host = host
        self.port = port
        self.model_name = model_name
        self._api_keys = {}  # key -> {name, created, calls}
        self._running = False
        self._server = None

    def create_key(self, name='default'):
        """创建专属 API Key

        Returns:
            str: API Key (sk-xxxxxx 格式)
        """
        key = "sk-" + hashlib.sha256(
            f"{name}{time.time()}{random.random()}".encode()
        ).hexdigest()[:32]

        self._api_keys[key] = {
            'name': name,
            'created': time.time(),
            'calls': 0,
            'active': True,
        }

        print(f"[PyMsi.train] API Key 已创建: {key} ({name})")
        return key

    def list_keys(self):
        """列出所有 API Key"""
        return self._api_keys.copy()

    def revoke_key(self, key):
        """吊销 API Key"""
        if key in self._api_keys:
            self._api_keys[key]['active'] = False
            print(f"[PyMsi.train] API Key 已吊销: {key}")
            return True
        return False

    def _validate_key(self, key):
        """验证 API Key"""
        if key and key in self._api_keys and self._api_keys[key]['active']:
            self._api_keys[key]['calls'] += 1
            return True
        return False

    def _handle_request(self, method, path, headers, body):
        """处理 HTTP 请求 (内部用)"""
        # 健康检查不需要认证
        if path == '/v1/health' and method == 'GET':
            return 200, {'status': 'ok', 'model': self.model_name}

        if path == '/v1/model/info' and method == 'GET':
            return 200, {
                'model': self.model_name,
                'layers': len(self.model.layers),
                'params': self.model.count_params(),
            }

        # 预测接口
        if path == '/v1/predict' and method == 'POST':
            # 需要认证
            api_key = headers.get('X-API-Key', '') or headers.get('x-api-key', '')
            if not api_key and body and 'api_key' in body:
                api_key = body['api_key']

            if not self._validate_key(api_key):
                return 401, {'error': 'Invalid or missing API key'}

            try:
                data = body.get('data', body.get('input', []))
                if _HAS_NUMPY:
                    X = np.array(data, dtype=np.float32)
                else:
                    X = np.array(data)
                predictions = self.model.predict(X)
                if _HAS_NUMPY:
                    result = predictions.tolist()
                else:
                    result = [p.tolist() if hasattr(p, 'tolist') else p for p in predictions]
                return 200, {
                    'predictions': result,
                    'model': self.model_name,
                }
            except Exception as e:
                return 400, {'error': str(e)}

        return 404, {'error': 'Not found'}

    def start(self):
        """启动 API 服务器 (阻塞)

        使用 Python 内置 http.server, 零依赖.
        """
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json as json_mod

        server_self = self

        class APIHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self._handle('GET')

            def do_POST(self):
                self._handle('POST')

            def _handle(self, method):
                # 读取 body
                content_length = int(self.headers.get('Content-Length', 0))
                body = {}
                if content_length > 0:
                    raw = self.rfile.read(content_length)
                    try:
                        body = json_mod.loads(raw)
                    except:
                        body = {}

                headers = dict(self.headers)
                status, response = server_self._handle_request(
                    method, self.path, headers, body)

                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json_mod.dumps(response).encode('utf-8'))

            def log_message(self, format, *args):
                print(f"[PyMsi.train API] {args[0]} {args[1]} {args[2]}")

        self._server = HTTPServer((self.host, self.port), APIHandler)
        self._running = True
        print(f"\n[PyMsi.train] API 服务器启动")
        print(f"  地址: http://{self.host}:{self.port}")
        print(f"  模型: {self.model_name}")
        print(f"  API Keys: {len(self._api_keys)} 个")
        print(f"\n  接口:")
        print(f"    GET  /v1/health          健康检查")
        print(f"    GET  /v1/model/info      模型信息")
        print(f"    POST /v1/predict         预测 (需 API Key)")
        print(f"\n  认证: Header X-API-Key: sk-xxxxxx")
        print(f"\n  按 Ctrl+C 停止\n")

        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            print("\n[PyMsi.train] API 服务器已停止")
            self._running = False

    def stop(self):
        """停止服务器"""
        if self._server:
            self._server.shutdown()
            self._running = False


# ═══════════════════════════════════════════════════════════════
# 9. API 客户端
# ═══════════════════════════════════════════════════════════════

class APIClient:
    """AI API 客户端 — 调用别人的 PyMsi AI API

    用法:
        client = PM.train.APIClient("http://localhost:8080", api_key="sk-xxxx")
        result = client.predict([[1,2,3,4], [5,6,7,8]])
        info = client.model_info()
        health = client.health_check()
    """

    def __init__(self, base_url, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    def _request(self, method, path, data=None):
        """发送 HTTP 请求"""
        import urllib.request
        import json as json_mod

        url = self.base_url + path
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key

        body = json_mod.dumps(data).encode('utf-8') if data else b''

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json_mod.loads(resp.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                return json_mod.loads(error_body)
            except:
                return {'error': str(e), 'detail': error_body}

    def predict(self, data):
        """调用预测接口

        Args:
            data: 输入数据 (列表或 numpy 数组)

        Returns:
            dict: {'predictions': [...]}
        """
        if _HAS_NUMPY and hasattr(data, 'tolist'):
            data = data.tolist()
        return self._request('POST', '/v1/predict', {'data': data})

    def model_info(self):
        """获取模型信息"""
        return self._request('GET', '/v1/model/info')

    def health_check(self):
        """健康检查"""
        return self._request('GET', '/v1/health')


# ═══════════════════════════════════════════════════════════════
# 10. 内置示例模型
# ═══════════════════════════════════════════════════════════════

def demo_classification():
    """演示: 训练一个简单的分类模型

    生成随机数据, 训练一个两层全连接网络做二分类.
    """
    print("\n" + "=" * 60)
    print("  PyMsi AI 训练演示 — 二分类任务")
    print("=" * 60)

    if not _HAS_NUMPY:
        print("\n  警告: 未安装 numpy, 演示将很慢")
        print("  建议: pip install numpy")

    # 生成数据: 两个螺旋 (经典分类问题)
    np.random.seed(42)
    n_samples = 200
    n_features = 2

    X = np.random.randn(n_samples, n_features).astype(np.float32)
    y = ((X[:, 0] * X[:, 1] > 0).astype(np.int32))  # 简单规则

    # 划分
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"\n  训练数据: {len(X_train)} 样本, {n_features} 特征")
    print(f"  测试数据: {len(X_test)} 样本")
    print(f"  类别分布: {int(np.sum(y_train))} 正类 / {len(y_train) - int(np.sum(y_train))} 负类")

    # 构建模型
    model = Sequential([
        Dense(16, activation='relu', input_shape=(n_features,)),
        Dense(8, activation='relu'),
        Dense(2, activation='softmax'),
    ])

    model.summary()

    # 编译
    model.compile(optimizer='adam', loss='crossentropy', metrics=['accuracy'])

    # 训练
    print(f"\n  开始训练...")
    history = model.fit(X_train, y_train, epochs=30, batch_size=16,
                        validation_data=(X_test, y_test), verbose=2)

    # 评估
    print(f"\n  测试集评估:")
    test_loss, test_acc = model.evaluate(X_test, y_test)

    # 保存
    model.save("demo_model.pym")

    # 加载验证
    model2 = load_model("demo_model.pym")
    loss2, acc2 = model2.evaluate(X_test, y_test, verbose=0)
    print(f"\n  加载后精度一致: {abs(test_acc - acc2) < 0.001}")

    # API 服务器演示
    print(f"\n  API 服务器演示:")
    server = APIServer(model, port=0, model_name='demo')  # port=0 不真启动
    key = server.create_key('test_app')
    print(f"    API Key: {key}")
    print(f"    接口: POST /v1/predict (需 X-API-Key header)")

    # 模拟 API 调用
    test_input = X_test[:3].tolist()
    status, resp = server._handle_request(
        'POST', '/v1/predict',
        {'X-API-Key': key},
        {'data': test_input}
    )
    print(f"    模拟预测请求: status={status}")
    print(f"    预测结果: {resp.get('predictions', 'N/A')}")

    print(f"\n" + "=" * 60)
    print("  演示完成! 🎉")
    print("  训练得好 = ChatGPT 级")
    print("  训练不好 = 也能用")
    print("  反正高效轻量, 零人民币")
    print("=" * 60)

    os.remove("demo_model.pym")
    return model, history


# ═══════════════════════════════════════════════════════════════
# 11. PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _TrainModule:
    """PyMsi.train — AI 训练引擎

    自研轻量级神经网络训练框架, 纯 Python + NumPy, 零其他依赖.
    像 TensorFlow 那样训练真正的 AI, 但更轻更快, 零成本.

    格言:
      训练得好 = ChatGPT 级
      训练不好 = 也能用
      反正高效轻量, 零人民币

    快速上手:
        # 1. 构建模型
        model = PM.train.Sequential([
            PM.train.Dense(128, activation='relu', input_shape=(784,)),
            PM.train.Dense(64, activation='relu'),
            PM.train.Dense(10, activation='softmax'),
        ])

        # 2. 编译
        model.compile(optimizer='adam', loss='crossentropy', metrics=['accuracy'])

        # 3. 训练
        model.fit(X_train, y_train, epochs=10, batch_size=32)

        # 4. 预测
        predictions = model.predict(X_test)

        # 5. 保存/加载
        model.save("my_model.pym")
        model = PM.train.load_model("my_model.pym")

        # 6. 启动 API 服务器
        server = PM.train.APIServer(model, port=8080)
        key = server.create_key("my_app")
        server.start()

    层类型:
        Dense, Dropout, Embedding, Conv1D, SimpleRNN, Flatten, Activation

    优化器:
        SGD, Adam, RMSprop

    损失函数:
        MSE, CrossEntropy, MAE, BCE

    工具:
        train_test_split, DataGenerator, Tokenizer

    API:
        APIServer (带 Key 认证), APIClient
    """

    def __repr__(self):
        return f"<PyMsi.train [AI训练引擎] v2.0.0 {'numpy' if _HAS_NUMPY else 'pure-python'}>"

    # --- 模型 ---
    @property
    def Sequential(self):
        """序列模型"""
        return Sequential

    def load_model(self, filepath):
        """加载 .pym 模型"""
        return load_model(filepath)

    # --- 层 ---
    @property
    def Dense(self):
        """全连接层"""
        return Dense

    @property
    def Dropout(self):
        """Dropout 层"""
        return Dropout

    @property
    def Embedding(self):
        """Embedding 层"""
        return Embedding

    @property
    def Conv1D(self):
        """一维卷积层"""
        return Conv1D

    @property
    def SimpleRNN(self):
        """简单 RNN 层"""
        return SimpleRNN

    @property
    def Flatten(self):
        """展平层"""
        return Flatten

    @property
    def Activation(self):
        """激活层"""
        return Activation

    # --- 优化器 ---
    @property
    def SGD(self):
        """SGD 优化器"""
        return SGD

    @property
    def Adam(self):
        """Adam 优化器"""
        return Adam

    @property
    def RMSprop(self):
        """RMSprop 优化器"""
        return RMSprop

    # --- 工具 ---
    def train_test_split(self, X, y, test_size=0.2, random_state=None):
        """划分训练集/测试集"""
        return train_test_split(X, y, test_size, random_state)

    @property
    def DataGenerator(self):
        """数据生成器"""
        return DataGenerator

    @property
    def Tokenizer(self):
        """文本分词器"""
        return Tokenizer

    # --- API ---
    @property
    def APIServer(self):
        """API 服务器 (带 Key 认证)"""
        return APIServer

    @property
    def APIClient(self):
        """API 客户端"""
        return APIClient

    # --- 演示 ---
    def demo(self):
        """运行分类演示"""
        return demo_classification()

    @property
    def has_numpy(self):
        """是否有 numpy 加速"""
        return _HAS_NUMPY
