#! D:/Anaconda

class Merge(object):

    @staticmethod
    def sort(a):
        lo = 0
        hi = a.length - 1
        return Merge.sort2(a, lo, hi)

    @staticmethod
    def sort2(a, lo, hi):
        if lo >= hi:
            return
        mid = lo + (hi - lo) / 2
        Merge.sort2(a, lo, mid)
        Merge.sort2(a, mid + 1, hi)
        Merge.merge(a, lo, mid, hi)

    @staticmethod
    def less(a, b):
        return a > b

    @staticmethod
    def merge(a, lo, mid, hi):
        aux = list()
        for k in range(lo, hi + 1):
            aux[k] = a[k]
        i = lo
        j = mid + 1

        for k in range(lo, hi + 1):
            if i > mid:
                a[k] = a[j]
                j += 1
            elif j > hi:
                a[k] = a[i]
                i += 1
            elif Merge.less(a[i], a[j]):
                a[k] = a[j]
                j += 1
            else:
                a[k] = a[i]
                i += 1
