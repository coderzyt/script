def merge(a, lo, mid, hi):
    i = lo
    j = mid + 1
    aux = list()

    for k in range(lo-1, hi):
        aux[k] = a[k]

    for k in range(lo-1, hi):
        if i > mid:
            a[k] = aux[j]
            j += 1
        elif j > hi:
            a[k] = aux[i]
            i += 1
        elif less(aux[j], a[i]):
            a[k] = aux[j]
            j += 1
        else:
            a[k] = a[i]
            i += 1

def less(a, b):
    return a > b
    
def main():
    j = 1
    j = j + 1
    print(j)

if __name__ == '__main__':
    main()