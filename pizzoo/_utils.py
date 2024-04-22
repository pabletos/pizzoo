def clamp(n, minn, maxn):
	return max(min(maxn, n), minn)

__all__ = ('clamp')