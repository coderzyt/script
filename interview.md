# java基础
## 1. List和Set的区别

List和Set都继承了Collection
Set是最简单的一种集合, 集合中的对象不按特定的方式排序, 并且没有重复的对象.
List的特征是其元素以线性方式存储, 集合中可以存放重复对象.

## 2. HashSet是如何保证不重复的?

在调用HashSet中的add方法时, 实际是在调用 HashMap的put方法, 像hashmap中添加key.
HashMap在put一个key时会判断将要放进去的key的hash值和对象地址或者内容是否一样,
则判断出来要添加的Key与HashMap中的Key重复, 把Value的值给替换成最新的.
当然HashSet中的Value是一个固定值PRESENT. 所以修改不修改无所谓.

## 3. HashMap是线程安全的吗, 为什么不是线程安全的(最好画图说明多线程环境下不安全)

不是线程安全的.

![put方法](put.png)

① put的时候导致的多线程数据不一致。
这个问题比较好想象，比如有两个线程A和B，首先A希望插入一个key-value对到HashMap中，首先计算记录所要
落到的桶的索引坐标，然后获取到该桶里面的链表头结点，此时线程A的时间片用完了，而此时线程B被调度得以
执行，和线程A一样执行，只不过线程B成功将记录插到了桶里面，假设线程A插入的记录计算出来的桶索引和线程
B要插入的记录计算出来的桶索引是一样的，那么当线程B成功插入之后，线程A再次被调度运行时，它依然持有过
期的链表头但是它对此一无所知，以至于它认为它应该这样做，如此一来就覆盖了线程B插入的记录，这样线程B插
入的记录就凭空消失了，造成了数据不一致的行为。

② 另外一个比较明显的线程不安全的问题是HashMap的get操作可能因为resize而引起死循环（cpu100%），具体分析如下：
下面的代码是resize的核心内容：

```java
void transfer(Entry[] newTable, boolean rehash) {
    int newCapacity = newTable.length;
    for (Entry<K,V> e : table) {
        while(null != e) {
            Entry<K,V> next = e.next;
            if (rehash) {
                e.hash = null == e.key ? 0 : hash(e.key);
            }
            int i = indexFor(e.hash, newCapacity);
            e.next = newTable[i];
            newTable[i] = e;
            e = next;
        }
    }
}
```
这个方法的功能是将原来的记录重新计算在新桶的位置，然后迁移过去。

![多线程HashMap的resize](resize.png)

我们假设有两个线程同时需要执行resize操作，我们原来的桶数量为2，记录数为3，需要resize桶到4，原来的记录分别为：
[3,A],[7,B],[5,C]，在原来的map里面，我们发现这三个entry都落到了第二个桶里面。
假设线程thread1执行到了transfer方法的Entry next = e.next这一句，然后时间片用完了，此时的e = [3,A], next = [7,B]。
线程thread2被调度执行并且顺利完成了resize操作，需要注意的是，此时的[7,B]的next为[3,A]。此时线程thread1重新被调度运行，
此时的thread1持有的引用是已经被thread2 resize之后的结果。线程thread1首先将[3,A]迁移到新的数组上，然后再处理[7,B]，
而[7,B]被链接到了[3,A]的后面，处理完[7,B]之后，就需要处理[7,B]的next了啊，而通过thread2的resize之后，[7,B]的next
变为了[3,A]，此时，[3,A]和[7,B]形成了环形链表，在get的时候，如果get的key的桶索引和[3,A]和[7,B]一样，那么就会陷入死循
环。

## 4. HashMap的扩容过程

首先要了解HashMap的扩容过程, 我们就得了解一些HashMap中的变量：
① Node<K,V>：链表节点, 包含了key、value、hash、next指针四个元素
② table：Node<K,V>类型的数组, 里面的元素是链表, 用于存放HashMap元素的实体
③ size：记录了放入HashMap的元素个数
④ loadFactor：负载因子
⑤ threshold：阈值, 决定了HashMap何时扩容, 以及扩容后的大小, 一般等于table大小乘以loadFactor.
值得注意的是, 当我们自定义HashMap初始容量大小时, 构造函数并非直接把我们定义的数值当做HashMap容量大小,
而是把该数值当做参数调用方法tableSizeFor, 然后把返回值作为HashMap的初始容量大小：
```java
/**
 *Returns a power of two size for the givenk target capacity.
 */
static final int tableSizeFor(int cap) {
    int n = cap - 1;
    n |= n >>> 1;
    n |= n >>> 2;
    n |= n >>> 4;
    n |= n >>> 8;
    n |= n >>> 16;
    return (n < 0) ? 1 : (n >= MAXIMUM_CAPACITY) ? MAXIMUM_CAPACITY : n + 1;
}
```
该方法会返回一个大于等于当前参数的2的倍数, 因此HashMap中的table数组的容量大小总是2的倍数.
HashMap使用的是懒加载, 构造完HashMap对象后, 只要不进行put 方法插入元素之前, HashMap并不会去初始化或者扩容table：
```java
public V put(K key, V value) {
    return putVal(hash(key), key, value, false, true);
}
final V putVal(int hash, K key, V value, boolean onlyIfAbsent, boolean evict) {
    Node<K,V>[] tab; Node<K,V> p; int n, i;
    if ((tab = table) == null || (n = tab.length) == 0)
        n = (tab = resize()).length;
    if ((p = tab[i = (n - 1) & hash]) == null)
        tab[i] = newNode(hash, key, value, null);
    else {
        ...
    }
    ++modCount;
    if (++size > threshold)
        resize();
    afterNodeInsertion(evict);
    return null;
}
```
在putVal方法第8、9行我们可以看到, 当首次调用put方法时, HashMap会发现table为空然后调用resize方法进行初始化
在putVal方法第16、17行我们可以看到, 当添加完元素后, 如果HashMap发现size（元素总数）大于threshold（阈值）, 则会调用resize
方法进行扩容在这里值得注意的是, 在putVal方法第10行我们可以看到, 插入元素的hash值是一个32位的int值, 而实际当前元素插入table
的索引的值为 ：
```java
(table.size - 1) & hash
例如: 01111 & hash 等于hash值的后4位
```
又由于table的大小一直是2的倍数, 2的N次方, 因此当前元素插入table的索引的值为其hash值的后N位组成的值

## 5. HashMap 1.7 与 1.8 的区别, 说明1.8做了哪些优化, 如何优化的?

在JDK7中, HashMap 的结构都是这么简单, 基于一个数组以及多个链表的实现,
hash值冲突的时候, 就将对应节点以链表的形式存储. 这样子 HashMap 性能上
就抱有一定的疑问, 如果说成百上千个节点在 hash 时发生碰撞, 存储于一个链
表中, 那么如果查找其中一个节点, 那就不可避免的花费O(N)的查找时间, 这将是多么大的性能损失. 这个JDK8中得到了解决. 在最坏的情
况下, 查找一个节点的时间复杂度为 O(N), 而红黑树一直是 O(logN), 这样会提高 HashMap 的效率. JDK7中 HashMap 采用位桶+链表的
方式, 即我们常说的散列链表的方式, JDK8中采用的是位桶+链表/红黑树的方式, 也是非线程安全的. 当某个位桶的链表长度达到某个阈值的
时候, 这个链表就将转换成红黑树.
JDK8中, 当某个 hash 值的节点数不小于8时, 将不再以链表的形式存储, 会被调整成一颗红黑树.

## 6. final finally finalize

final 用于修饰类, 成员变量和成员方法. final 修饰的类, 不能被继承, 其中所有的方法都不能被重写, 所以不能同时用 abstract 和 
final 修饰类. final 修饰的方法不能被重写, 但是子类可以用父类中 final 修饰的方法. final 修饰的成员变量是不可变的, 如果成员
变量是基本数据类型, 初始化后成员变量的值不能被改变, 如果成员变量是引用类型, 那么它只能指向初始化时指向的那个对象, 不能再指向
别的对象, 但是对象当中的内容是允许改变的.

finally 通常和 try catch 搭配使用, 保证不管有没有发生异常, 资源都能够被释放

finalize是 Object 类中的一个方法, 子类可以重写 finalize()方法实现对资源的回收. 垃圾回收只负责回收内存, 并不负责资源的回收, 
资源回收是由程序员完成. java虚拟机在垃圾回收之前会先调用垃圾对象的 finalize 方法用于使对象释放资源, 自后才进行垃圾回收, 这个
方法一般不会显示的调用, 在垃圾回收时垃圾回收器会主动调用.

## 7. 强引用, 软引用, 弱引用, 虚引用

强引用: 只要引用存在, 垃圾回收器永远不会回收
Object obj = new Object(); // 可直接通过 obj 取得对应的对象如 obj.equals(new Object());
而这样 obj 对象是对后面 new Object的一个强引用, 只有当 obj 这个引用被释放之后, 对象才会被释放掉, 这也是我们经常使用的编码形式.

软引用: 非必须引用, 内存溢出之前进行回收, 可以通过以下代码实现
Object obj = new Object();
SoftReference<Object> sf = new SoftReference<Object>(obj);
obj = null;
sf.get();//有时候会返回null
这时候sf是对obj的一个软引用, 通过sf.get()方法可以取到这个对象, 当然, 当这个对象被标记为需要回收的对象时, 则返回null；
软引用主要用户实现类似缓存的功能, 在内存足够的情况下直接通过软引用取值, 无需从繁忙的真实来源查询数据, 提升速度；当内存不足时, 
自动删除这部分缓存数据, 从真正的来源查询这些数据。

弱引用：
第二次垃圾回收时回收, 可以通过如下代码实现
Object obj = new Object();
WeakReference<Object> wf = new WeakReference<Object>(obj);
obj = null;
wf.get();//有时候会返回null
wf.isEnQueued();//返回是否被垃圾回收器标记为即将回收的垃圾
弱引用是在第二次垃圾回收时回收, 短时间内通过弱引用取对应的数据, 可以取到, 当执行过第二次垃圾回收时, 将返回null。
弱引用主要用于监控对象是否已经被垃圾回收器标记为即将回收的垃圾, 可以通过弱引用的isEnQueued方法返回对象是否被垃圾回收器标记。

虚引用：
垃圾回收时回收, 无法通过引用取到对象值, 可以通过如下代码实现
```java
Object obj = new Object();
PhantomReference<Object> pf = new PhantomReference<Object>(obj);
obj=null;
pf.get();//永远返回null
pf.isEnQueued();//返回是否从内存中已经删除
```
虚引用是每次垃圾回收的时候都会被回收, 通过虚引用的get方法永远获取到的数据为null, 因此也被成为幽灵引用。
虚引用主要用于检测对象是否已经从内存中删除。

## 8. java反射



## 9. Arrays.sort的实现原理和Collection实现原理

Arrays.sort
数组长度 N < 47 时, 使用插入排序算法
数组长度 47 < N < 286 时, 使用双轴快速排序算法
数组长度 N >= 286 时,连续性好用归并排序, 连续性不好用双轴快速排序算法




Collections.sort
先判断useLegacyMergeSort是否为true, 如果为true就会使用传统归并排序, 如果不为true就会使用叫Timsort算法
Timsort的核心过程
Timsort算法为了减少对升序部分的回溯和对降序部分的性能倒退, 将输入按其升序和降序特点进行了分区。排序的输入的单位不是一个个单独的数字，
而是一个个的块-分区。其中每一个分区叫一个run。针对这些 run 序列，每次拿一个 run 出来按规则进行合并。每次合并会将两个 run合并成一个
run。合并的结果保存到栈中。合并直到消耗掉所有的 run，这时将栈上剩余的 run合并到只剩一个 run 为止。这时这个仅剩的 run 便是排好序的结果。
综上述过程，Timsort算法的过程包括
（0）如何数组长度小于某个值, 直接用二分插入排序算法.
（1）找到各个run, 并入栈.
（2）按规则合并run.



## 10. LinkedHashMap的应用



## 11. cloneable接口实现原理



## 12. 异常分类以及处理机制



## 13. wait和sleep的区别

#### sleep()
sleep()使当前线程进入停滞状态（阻塞当前线程）, 让出CUP的使用、目的是不让当前线程独自霸占该进程所获的CPU资源,
以留一定时间给其他线程执行的机会;
sleep()是Thread类的Static(静态)的方法；因此他不能改变对象的锁状态, 所以当在一个Synchronized块中调用Sleep()方法时,
线程虽然休眠了, 但是对象的锁并木有被释放, 其他线程无法访问这个对象（即使睡着也持有对象锁）。
在sleep()休眠时间期满后, 该线程不一定会立即执行, 这是因为其它线程可能正在运行而且没有被调度为放弃执行, 除非此线程
具有更高的优先级。
#### wait()
wait()方法是Object类里的方法；当一个线程执行到wait()方法时，它就进入到一个和该对象相关的等待池中，同时失去（释放）
了对象的机锁（暂时失去机锁，wait(long timeout)超时时间到后还需要返还对象锁）；其他线程可以访问；
wait()使用notify或者notifyAlll或者指定睡眠时间来唤醒当前等待机锁k池中的线程。
wiat()必须放在synchronized block中，否则会在program runtime时扔出"java.lang.IllegalMonitorStateException"异常。

所以sleep()和wait()方法的最大区别是：
　　　　sleep()睡眠时，保持对象锁，仍然占有该锁；
　　　　而wait()睡眠时，释放对象锁。

## 14. 数组在内存中如何分配

Java中数组存储两类事物: 基本数据类型或者引用(对象指针).
当一个对象通过new 创建, 那么将在堆内存中分配一段空间, 并返回其引用(指针).
对于数组也是同样的方式.
Java中的数组,也是对象(继承Object),因此数组所在的区域和对象是一样的.

```java
class A {
    int x;
    int y;
}
public void m1() {
    int i = 0;
    m2();
}
public void m2() {
    A a = new A();
}
```

上面的代码片段中,让我们执行 m1()方法看看发生了什么:
    ① 当 m1 被调用时,一个新的栈帧(Frame-1)被压入JVM栈中,当然,相关的局部变量也在 Frame-1中创建, 比如 i;
    ② 然后 m1调用m2,,又有一个新的栈帧(Frame-2)被压入到JVM栈中;
    ③ m2方法在堆内存中创建了A类的一个对象,此对象的引用保存在 Frame-2的局部变量 a 中. 此时,堆内存和栈内存
    看起来如下所示:
    ![内存图示](stack.png)

# java并发
## 1. synchronized的实现原理以及锁优化
synchronized关键字是最基本的互斥同步手段, 经过编译后, 会在同步块前后分别形成monitorenter 和 monitorexit两个字节码指令, 这两个字节码都需要一个reference类型参数来指明要锁定和解锁的对象, 如果java程序中明确指明了对象参数, 那就是这个对象的reference, 如果没有明确指定, 那就根据synchronized修饰的是实例方法还是类方法, 去取对应的对象实例或class对象来作为锁对象.
在执行monitorenter指令时, 首先要尝试获取对象的锁. 如果这个对象没被锁定, 或者当前线程已经拥有了对象的锁, 把锁的计数器加1, 相应的, 在执行monitorexit指令时会将锁计数器减1, 当计数器为0 时, 锁就被释放. 如果获取对象锁失败, 那当前线程就要阻塞等待, 直到对象锁被另一个线程释放为止.
### 锁优化
适应性自旋 Adaptive Spinning:
线程挂起和恢复都需要转入内核态中完成, 性能消耗大, 对于那些锁定状态持续时间很短的共享数据, 不值得. 我们可以让请求锁的线程"稍等一下", 但不放弃处理器的执行时间, 看看持有锁的线程是否很快就会释放锁. 为了让线程等待, 只需让线程执行一个忙循环(自旋), 这就是所谓的自旋锁.
但自旋要有限度, 默认自旋10次, 可以通过-XX:PreBlockSpin更改, 而自适应的自旋锁意味着自旋的时间不再固定, 而是由前一次在同一个锁上的自旋时间和锁的拥有者的状态决定
锁消除 Lock Elimination
锁粗化 Lock Coarsening
轻量级锁 Lightweight Locking
偏向锁 Biased Locking

## 2. volatile的实现原理是
volatile可以保证线程可见性且提供了一定的有序性, 但是无法保证原子性. 在JVM底层volatile是采用"内存屏障"来实现的.
上面的这句话有两层语义.
- 保证可见性, 不保证原子性
- 禁止指令重排序
在执行程序时为了提高性能, 编译器和处理器通常会对指令做重排序
- 编译器重排序, 编译器在不改变单线程程序语义的前提下, 可以重新安排语句的执行顺序
- 处理器重排序, 如果不存在数据依赖性, 处理器可以改变语句对应机器指令的执行顺序.
指令重排序对单线程没有什么影响, 它不会影响程序的运行结果, 但是会影响多线程的正确性, 既然指令重排序会影响多线程执行的正确性, 那么我们就需要禁止重排序, 那么JVM是如何禁止重排序的呢? 这个问题稍后回答, 我们先看另一个原则happens-before, happens-before原则保证了程序的有序性, 它规定如果两个操作的执行顺序无法从happens-before原则中推导出来, 那么他们就不能保证有序性, 可以随意进行重排序, 其定义如下:
- 同一个线程中, 前面的操作happens-before后续的操作(即单线程内按代码顺序执行, 但是, 在不影响单线程执行结果的前提下, 编译器和处理器可以进行重排序, 这是合法的, 换句话说, 这一规则无法保证编译重排和指令重排)
- 监视器上的解锁操作happens-before其后续的加锁操作(synchronized规则)
- 对volatile变量的写操作happens-before该线程所有的后续操作(volatile规则)
- 线程的start方法happens-before该线程所有的后续操作(线程启动规则
- 线程所有的操作happens-before其他线程在该线程上调用join返回成功后的操作
- 如果a happens-before b, b happens-before c, 则 a happens-before c. (传递性)

volatile关键字禁止指令重排序有两层意思:
- 当程序执行到volatile变量的读操作或者写操作时, 在其前面的操作的更改肯定全部已经进行, 且结果已经对后面的操作可见; 在其后面的操作肯定还没有进行;
- 在进行指令优化时, 不能将在对volatile变量访问的语句放在其后面执行, 也不能把volatile变量后面的语句放在其前面执行.
```java
//x、y为非volatile变量
//flag为volatile变量

x = 2;        //语句1
y = 0;        //语句2
flag = true;  //语句3
x = 4;         //语句4
y = -1;       //语句5
```
由于flag变量为volatile变量，那么在进行指令重排序的过程的时候，不会将语句3放到语句1、语句2前面，也不会讲语句3放到语句4、语句5后面。但是要注意语句1和语句2的顺序、语句4和语句5的顺序是不作任何保证的。并且volatile关键字能保证，执行到语句3时，语句1和语句2必定是执行完毕了的，且语句1和语句2的执行结果对语句3、语句4、语句5是可见的。那么我们回到前面举的一个例子：
```java
//线程1:
context = loadContext();   //语句1
inited = true;             //语句2

//线程2:
while(!inited ){
  sleep()
}
doSomethingwithconfig(context);
```
前面举这个例子的时候，提到有可能语句2会在语句1之前执行，那么就可能导致context还没被初始化，而线程2中就使用未初始化的context去进行操作，导致程序出错。这里如果用volatile关键字对inited变量进行修饰，就不会出现这种问题了，因为当执行到语句2时，必定能保证context已经初始化完毕。

### 实现机制
前面讲述了源于volatile关键字的一些使用，下面我们来探讨一下volatile到底如何保证可见性和禁止指令重排序的。在x86处理器下通过工具获取JIT编译器生成的汇编指令来看看对Volatile进行写操作CPU会做什么事情。
```java
Java代码: instance = new Singleton();//instance是volatile变量
汇编代码:  0x01a3de1d: movb $0x0,0x1104800(%esi);0x01a3de24: lock addl $0x0,(%esp);
```
观察加入volatile关键字和没有加入volatile关键字时所生成的汇编代码发现，加入volatile关键字时，会多出一个lock前缀指令。lock前缀指令实际上相当于一个内存屏障（也成内存栅栏），内存屏障会提供3个功能：
- 它确保指令重排序时不会把其后面的指令排到内存屏障之前的位置, 也不会把前面的指令排到内存屏障的后面; 即在执行到内存屏障这句指令时, 在它前面的操作已经全部完成;
- 它会强制将对缓存的修改操作立即写入主内存
- 如果是写操作, 它会导致其他CPU中对应的缓存失效

### 实现原理
#### 可见性
处理器为了提高处理速度，不直接和内存进行通讯，而是将系统内存的数据独到内部缓存后再进行操作，但操作完后不知什么时候会写到内存。
如果对声明了volatile变量进行写操作时，JVM会向处理器发送一条Lock前缀的指令，将这个变量所在缓存行的数据写会到系统内存。这一步确保了如果有其他线程对声明了volatile变量进行修改，则立即更新主内存中数据。
但这时候其他处理器的缓存还是旧的，所以在多处理器环境下，为了保证各个处理器缓存一致，每个处理会通过嗅探在总线上传播的数据来检查 自己的缓存是否过期，当处理器发现自己缓存行对应的内存地址被修改了，就会将当前处理器的缓存行设置成无效状态，当处理器要对这个数据进行修改操作时，会强制重新从系统内存把数据读到处理器缓存里。 这一步确保了其他线程获得的声明了volatile变量都是从主内存中获取最新的。
#### 有序性
Lock前缀指令实际上相当于一个内存屏障（也成内存栅栏），它确保指令重排序时不会把其后面的指令排到内存屏障之前的位置，也不会把前面的指令排到内存屏障的后面；即在执行到内存屏障这句指令时，在它前面的操作已经全部完成。

### 使用场景
synchronized关键字是防止多个线程同时执行一段代码，那么就会很影响程序执行效率，而volatile关键字在某些情况下性能要优于synchronized，但是要注意volatile关键字是无法替代synchronized关键字的，因为volatile关键字无法保证操作的原子性。通常来说，使用volatile必须具备以下2个条件：
（1）对变量的写操作不依赖于当前值 
（2）该变量没有包含在具有其他变量的不变式中
实际上，这些条件表明，可以被写入volatile变量的这些有效值独立于任何程序的状态，包括变量的当前状态。即实际就是上面的2个条件需要保证操作是原子性操作，才能保证使用volatile关键字的程序在并发时能够正确执行. 
下面列举Java中使用volatile的几个场景。
- 状态标记量
```java
volatile boolean inited = false;
//线程1:
context = loadContext();
inited = true;

//线程2:
while(!inited ){
    sleep();
}
doSomethingwithconfig(context);
```
- double check（单例模式）
```java
class Singleton{
    private volatile static Singleton instance = null;
    private Singleton() {

    }
    public static Singleton getInstance() {
        if(instance == null) {
            synchronized (Singleton.class) {
                if(instance == null)
                    instance = new Singleton();
            }
        }
        return instance;
    }
}
```
## 3. java信号灯
java.util.concurrent.Semaphore
用于控制并发访问数量, 只有获取运行令牌(信号灯)后, 才可以运行当令牌(信号灯)使用完了, 后面的访问只能等着. 直到有令牌被释放后, 获取令牌才可以继续访问. 


## 4. synchronized在静态方法和普通方法的区别
静态方法: 锁的是类
普通方法: 锁的是对象

## 5. 怎么实现所有线程在等待某个时间的发生才会去执行?



## 6. CAS? CAS有什么缺陷? 如何解决?

Compare and Swap. 比较并交换
CAS存在一个逻辑漏洞: 如果一个变量V初次读取的时候是A值, 并且在准备赋值的时候检查到它仍然为A值, 那我们就能说它的值
没有被其他线程改变过了吗? 如果在这段期间它的值曾经被改成了B, 后来又被改回A, 那CAS操作就会误认为它从来没有被改变过.
这个漏洞被称为CAS操作的"ABA"的问题.
java.util.concurrent包为了解决这个问题, 提供了一个带有标记的原子引用类 "AtomicStampedReference", 它可以通过控制变量值的版本来保证CAS的正确性. 或者使用 传统的互斥同步.
## 7. synchronized和lock有什么区别?
- synchronized在编译后增加两个字节码指令 monitorenter 和 monitorexit, 利用这两个指令来实现同步. 属于悲观锁.
- Lock底层是使用volatile和CAS操作来实现的一种乐观锁. Lock可以实现公平锁.

类别                    synchronized                                                   Lock
存在层次            Java的关键字，在jvm层面上	                                        是一个类
锁的释放     1、以获取锁的线程执行完同步代码，释放锁                        在finally中必须释放锁，不然容易造成线程死锁
            2、线程执行发生异常，jvm会让线程释放锁   
锁的获取    假设A线程获得锁，B线程等待。如果A线程阻塞，B线程会一直等待     分情况而定，Lock有多个锁获取的方式，具体下面会说道，
                                                                        大致就是可以尝试获得锁，线程可以不用一直等待
锁状态                      无法判断                                                    可以判断
锁类型                  可重入 不可中断 非公平                                    可重入 可中断 可公平（两者皆可）可非公平
性能                        少量同步                                                    大量同步

## 8. HashTable是怎么加锁的?

读写操作时加了互斥锁

## 9. HashMap的并发问题?



## 10. ConcurrentHashMap介绍? 1.8中为什么要用红黑树?

红黑树:
降低查找同hash值的对象时的时间复杂度, 链表 => 链表/红黑树.
O(N) -> O(lgN)

## 11. AQS
AbstractQueuedSynchronizer
juc 里所有的这些锁机制都是基于 AQS （ AbstractQueuedSynchronizer ）框架上构建的
一个同步器至少需要包含两个功能：
- 获取同步状态:   如果允许，则获取锁，如果不允许就阻塞线程，直到同步状态允许获取。
- 释放同步状态:   修改同步状态，并且唤醒等待线程。
根据作者论文， aqs 同步机制同时考虑了如下需求：
- 独占锁和共享锁两种机制。
- 线程阻塞后，如果需要取消，需要支持中断。
- 线程阻塞后，如果有超时要求，应该支持超时后中断的机制。


## 12. 如何检测死锁? 怎么预防死锁?
所谓死锁，是指多个进程循环等待它方占有的资源而无限期地僵持下去的局面。
### 产生死锁的必要条件:
〈1〉互斥条件。即某个资源在一段时间内只能由一个进程占有，不能同时被两个或两个以上的进程占有。必须在占有该资源的进程主动释放它之后，其它进程才能占有该资源。这是由资源本身的属性所决定的。
〈2〉不可抢占条件。进程所获得的资源在未使用完毕之前，资源申请者不能强行地从资源占有者手中夺取资源.
〈3〉占有且申请条件。进程至少已经占有一个资源，但又申请新的资源；由于该资源已被另外进程占有，此时该进程阻塞；但是，它在等待新资源之时，仍继续占用已占有的资源。
〈4〉循环等待条件。存在一个进程等待序列{P1，P2，...，Pn}，其中P1等待P2所占有的某一资源，P2等待P3所占有的某一源，......，而Pn等待P1所占有的的某一资源，形成一个进程循环等待环。就像前面的过独木桥问题，甲等待乙占有的桥面，而乙又等待甲占有的桥面，从而彼此循环等待。
死锁发生时的四个必要条件，只要破坏这四个必要条件中的任意一个条件，死锁就不会发生。这就为我们解决死锁问题提供了可能。一般地，解决死锁的方法分为死锁的预防，避免，检测与恢复三种（注意：死锁的检测与恢复是一个方法）。我们将在下面分别加以介绍。
### 死锁的预防是保证系统不进入死锁状态的一种策略。它的基本思想是要求进程申请资源时遵循某种协议，从而打破产生死锁的四个必要条件中的一个或几个，保证系统不会进入死锁状态。
〈1〉打破互斥条件。即允许进程同时访问某些资源。但是，有的资源是不允许被同时访问的，像打印机等等，这是由资源本身的属性所决定的。所以，这种办法并无实用价值。

〈2〉打破不可抢占条件。即允许进程强行从占有者那里夺取某些资源。就是说，当一个进程已占有了某些资源，它又申请新的资源，但不能立即被满足时，它必须释放所占有的全部资源，以后再重新申请。它所释放的资源可以分配给其它进程。这就相当于该进程占有的资源被隐蔽地强占了。这种预防死锁的方法实现起来困难，会降低系统性能。    

〈3〉打破占有且申请条件。可以实行资源预先分配策略。即进程在运行前一次性地向系统申请它所需要的全部资源。如果某个进程所需的全部资源得不到满足，则不分配任何资源，此进程暂不运行。只有当系统能够满足当前进程的全部资源需求时，才一次性地将所申请的资源全部分配给该进程。由于运行的进程已占有了它所需的全部资源，所以不会发生占有资源又申请资源的现象，因此不会发生死锁。但是，这种策略也有如下缺点：
- 在许多情况下，一个进程在执行之前不可能知道它所需要的全部资源。这是由于进程在执行时是动态的，不可预测的；
- 资源利用率低。无论所分资源何时用到，一个进程只有在占有所需的全部资源后才能执行。即使有些资源最后才被该进程用到一次，但该进程在生存期间却一直占有它们，造成长期占着不用的状况。这显然是一种极大的资源浪费；
- 降低了进程的并发性。因为资源有限，又加上存在浪费，能分配到所需全部资源的进程个数就必然少了。    
〈4〉打破循环等待条件，实行资源有序分配策略。采用这种策略，即把资源事先分类编号，按号分配，使进程在申请，占用资源时不会形成环路。所有进程对资源的请求必须严格按资源序号递增的顺序提出。进程占用了小号资源，才能申请大号资源，就不会产生环路，从而预防了死锁。这种策略与前面的策略相比，资源的利用率和系统吞吐量都有很大提高，但是也存在以下缺点：
- 限制了进程对资源的请求，同时给系统中所有资源合理编号也是件困难事，并增加了系统开销；
- 为了遵循按编号申请的次序，暂不使用的资源也需要提前申请，从而增加了进程对资源的占用时间。

### 死锁的恢复
一旦在死锁检测时发现了死锁，就要消除死锁，使系统从死锁状态中恢复过来。
（1）最简单，最常用的方法就是进行系统的重新启动，不过这种方法代价很大，它意味着在这之前所有的进程已经完成的计算工作都将付之东流，包括参与死锁的那些进程，以及未参与死锁的进程。
（2）撤消进程，剥夺资源。终止参与死锁的进程，收回它们占有的资源，从而解除死锁。这时又分两种情况：一次性撤消参与死锁的全部进程，剥夺全部资源；或者逐步撤消参与死锁的进程，逐步收回死锁进程占有的资源。一般来说，选择逐步撤消的进程时要按照一定的原则进行，目的是撤消那些代价最小的进程，比如按进程的优先级确定进程的代价；考虑进程运行时的代价和与此进程相关的外部作业的代价等因素。
## 13. java内存模型

<1> 运行时数据区域
- java堆
对于大多数应用来说, java堆是java虚拟机所管理的内存中最大的一块, java堆是被所有线程共享的一块内存区域, 在虚拟机启东时创建, 此内存区域的唯一目的就是存放对象实例, 几乎所有的对象实例都在这里分配内存. 这一点java虚拟机规范中的描述是: 所有对象实例以及数组都要在堆上分配. 但是随着JIT编译器的发展和逃逸分析技术的逐渐成熟, 栈上分配, 标量替换优化技术将会到这一些微妙的变化发生, 所有的对象都分配在堆上也渐渐的不那么"绝对"了.
- 方法区
方法区与java堆一样, 是各个线程共享的内存区域, 它用于存储已被虚拟机加载的类信息, 常量吗静态变量, 即时编译器编译后的代码等数据. 虽然java虚拟机规范把方法区描述为堆的一部分, 有个别名Non_Heap

- 虚拟机栈
与程序计数器一样, java虚拟机栈是线程私有的, 它的生命周期与线程相同, 虚拟机栈描述的是java方法执行的内存模型: 每个方法在执行的同时都会创建一个栈帧用于存储局部变量表, 操作数栈, 动态链接, 方法出入口等信息. 每一个方法从调用直至执行完成的过程, 就对应着一个栈帧在虚拟机栈中入栈到出栈的过程.

- 本地方法栈
本地方法栈与虚拟机栈所发挥的作用是非常相似的, 他们之间的区别不过是虚拟机执行java方法(也就是字节码)服务, 而本地方法栈则为虚拟机使用到的Native方法服务.

- 程序计数器
程序计数器是一块较小的内存空间, 它可以看作是当前线程所执行的字节码的行号指示器. 在虚拟机的概念模型里(仅是概念模型, 各种虚拟机会通过一些更高效的方式去实现), 字节码解释器工作时就是通过改变这个计数器的值来选取下一条需要执行的字节码指令, 分支, 循环, 跳转, 异常处理, 线程恢复等基础功能都需要依赖这个计数器来完成.
由于java虚拟机的多线程是通过线程轮流切换并分配处理器执行时间的方式来实现的, 在任何一个确定的时刻, 一个处理器(对于多核处理器来说是一个内核)都只会执行一条线程中的指令, 因此, 为了线程切换后能恢复到正确的执行位置, 每条线程都需要有一个独立的程序计数器, 各条线程之间计数器互不影响, 独立存储, 我们称这类内存区域为"线程私有"的内存.
如果线程正在执行的是一个java方法, 这个计数器记录的是正在执行的虚拟机字节码指令的地址, 如果正在执行的Native方法, 这个计数器值则为空(Undefined). 此内存区域是唯一一个在java虚拟机规范中没有任何OutOfMemoryError情况的区域.

- 运行时常量池
运行时常量池是方法区的一部分, Class文件中除了有类的版本, 字段, 方法, 接口等描述信息外, 还有一项信息是常量池, 用于存放编译期生成的各种字面量和符号引用, 这部分内容将在类加载后进入方法区的运行时常量池中存放.

- 直接内存
直接内存并不是虚拟机运行时数据区的一部分, 也不是java虚拟机规范中定义的内存区域, 但是这部分内存也被频繁的使用, 而且也可能导致OutOfMemory异常出现.

## 14. 如何保证多线程下i++结果正确
### 使用synchronized关键字
```java
public class Test {
    public  int inc = 0;

    public synchronized void increase() {
        inc++;
    }

    public static void main(String[] args) {
        final Test test = new Test();
        for(int i=0;i<10;i++){
            new Thread(){
                public void run() {
                    for(int j=0;j<1000;j++)
                        test.increase();
                };
            }.start();
        }

        while(Thread.activeCount()>1)  //保证前面的线程都执行完
            Thread.yield();
        System.out.println(test.inc);
    }
}
```
### 使用Lock
```java
public class Test {
    public  int inc = 0;
    Lock lock = new ReentrantLock();

    public  void increase() {
        lock.lock();
        try {
            inc++;
        } finally{
            lock.unlock();
        }
    }

    public static void main(String[] args) {
        final Test test = new Test();
        for(int i=0;i<10;i++){
            new Thread(){
                public void run() {
                    for(int j=0;j<1000;j++)
                        test.increase();
                };
            }.start();
        }

        while(Thread.activeCount()>1)  //保证前面的线程都执行完
            Thread.yield();
        System.out.println(test.inc);
    }
}
```
### 使用AtomicInteger
```java
public class Test {
    public  AtomicInteger inc = new AtomicInteger();

    public  void increase() {
        inc.getAndIncrement();
    }

    public static void main(String[] args) {
        final Test test = new Test();
        for(int i=0;i<10;i++){
            new Thread(){
                public void run() {
                    for(int j=0;j<1000;j++)
                        test.increase();
                };
            }.start();
        }

        while(Thread.activeCount()>1)  //保证前面的线程都执行完
            Thread.yield();
        System.out.println(test.inc);
    }
}
```
## 15. 线程池的种类, 区别和使用场景
固定数量线程池
定时线程池



## 16. 分析线程池的实现原理和线程的调度过程?
一个线程池包括以下四个基本组成部分：
<1> 线程池管理器（ThreadPool）：用于创建并管理线程池，包括创建线程池，销毁线程池，添加新任务；
<2> 工作线程（PoolWorker）：我们把用来执行用户任务的线程称为工作线程,工作线程就是不断从队列中获取任务对象并执行对象上的业务方法。线程池中线程，在没有任务时处于等待状态，可以循环的执行任务；
<3> 任务接口（Task）：每个任务必须实现的接口，以供工作线程调度任务的执行，它主要规定了任务的入口，任务执行完后的收尾工作，任务的执行状态等；
<4> 任务队列（taskQueue）：用于存放没有处理的任务。提供一种缓冲机制。

## 17. 线程池如何调优, 最大数目如何确认?
创建线程及后续的销毁过程的代价是非常昂贵的, 因为jvm和操作系统都需要分配资源.
如果手动创建线程, 如果不进行适当管理, 很可能引发灾难性后果.每个线程都需要一定的栈内存空间. 在最近
的64位jvm中, 默认的栈大小是1024KB, 持续的创建线程会占用大量的线程栈空间, 每个线程代码执行过程中创
建对象, 还可能在堆上创建对象, 这样的情况恶化下去, 将会超出堆内存, 并产生大量的垃圾回收操作, 最终引
发 内存溢出(OutOfMemoryErrors)线程栈大小引发的内存问题, 可以通过-Xss开关来调整栈大小, 缩小线程栈
大小后, 可以减少每个线程的开销, 但是可能会引发栈溢出(StackOverFlowErrors). 对于一般的应用程序而
言, 默认的1024KB过于富裕, 调小为256KB或者512KB可能更为合适. java允许的最小值是160KB. 为了避免持
续创建新线程, 可以通过使用简单的线程池来限定线程池的上限. 线程池会管理所有的线程, 如果线程数还没有
达到上限, 线程池会创建线程到上限, 且尽可能复用空闲的线程.

### 设置最大线程数
对于给定硬件上的给定负载，最大线程数设置为多少最好呢？这个问题回答起来并不简单：它取决于负载特
性以及底层硬件。特别是，最优线程数还与每个任务阻塞的频率有关。

假设JVM有4个CPU可用，很明显最大线程数至少要设置为4。的确，除了处理这些任务，JVM还有些线程要做
其他的事，但是它们几乎从来不会占用一个完整的CPU，至于这个数值是否要大于4，则需要进行大量充分的测试。

有以下两点需要注意：

一旦服务器成为瓶颈，向服务器增加负载时非常有害的；

对于CPU密集型或IO密集型的机器增加线程数实际会降低整体的吞吐量；

### 设置最小线程数
一旦确定了线程池的最大线程数，就该确定所需的最小线程数了。大部分情况下，开发者会直截了当的将他们
设置成同一个值。

将最小线程数设置为其他某个值（比如1），出发点是为了防止系统创建太多线程，以节省系统资源。指定一个最
小线程数的负面影响相当小。如果第一次就有很多任务要执行，会有负面影响：这是线程池需要创建一个新线程。
创建线程对性能不利，这也是为什么起初需要线程池的原因。

一般而言，对于线程数为最小值的线程池，一个新线程一旦创建出来，至少应该保留几分钟，以处理任何负载飙升。
空闲时间应该以分钟计，而且至少在10分钟到30分钟之间，这样可以防止频繁创建线程。

### 线程池任务大小
等待线程池来执行的任务会被保存到某个队列或列表中；当池中有线程可以执行任务时，就从队列中拉出一个。这
会导致不均衡：队列中任务的数量可能变得非常大。如果队列太大，其中的任务就必须等待很长时间，直到前面的
任务执行完毕。

对于任务队列，线程池通常会限制其大小。但是这个值应该如何调优，并没有一个通用的规则。若要确定哪个值能
带来我们需要的性能，测量我们的真实应用是唯一的途径。不管是哪种情况，如果达到了队列限制，再添加任务就
会失败。ThreadPoolExecutor有一个rejectedExecution方法，用于处理这种情况，默认会抛出RejectedExecutionExecption。
应用服务器会向用户返回某个错误：或者是HTTP状态码500，或者是Web服务器捕获异常错误，并向用户给出合理的解释
消息—其中后者是最理想的。

### 设置ThreadPoolExecutor的大小
线程池的一般行为是这样的：创建时准备最小数目的线程，如果来了一个任务，而此时所有的线程都在忙碌，则启动
一个新线程（一直到达到最大线程数），任务就会立即执行。否则，任务被加入到等待队列，如果队列中已经无法加
入新任务，则拒接之。

根据所选任务队列的类型，ThreadPoolExecutor会决定何时会启动一个新线程。有以下三种可能：

#### SynchronousQueue
如果ThreadPoolExecutor搭配的是SynchronousQueue，则线程池的行为和我们预期的一样，它会考虑线程数：如果所
有的线程都在忙碌，而且池中的线程数尚未达到最大，则会为新任务启动一个新线程。然而这个队列没办法保存等待
的任务：如果来了一个任务，创建的线程数已经达到最大值，而且所有的线程都在忙碌，则新的任务都会被拒绝，所
以如果是管理少量的任务，这是个不错的选择，对于其他的情况就不适合了。

#### 无界队列
如果ThreadPoolExecutor搭配的是无界队列，如LinkedBlockingQueue，则不会拒绝任何任务（因为队列大小没有限制）。
这种情况下，ThreadPoolExecutor最多仅会按照最小线程数创建线程，也就是说最大线程池大小被忽略了。如果最大线
程数和最小线程数相同，则这种选择和配置了固定线程数的传统线程池运行机制最为接近。

#### 有界队列
搭配了有界队列，如ArrayBlockingQueue的ThreadPoolExecutor会采用一个非常负责的算法。比如假定线程池的最小线
程数为4，最大为8所用的ArrayBlockingQueue最大为10。随着任务到达并被放到队列中，线程池中最多运行4个线程
（即最小线程数）。即使队列完全填满，也就是说有10个处于等待状态的任务，ThreadPoolExecutor也只会利用4个线程。

如果队列已满，而又有新任务进来，此时才会启动一个新线程，这里不会因为队列已满而拒接该任务，相反会启动一个
新线程。新线程会运行队列中的第一个任务，为新来的任务腾出空间。

这个算法背后的理念是：该池大部分时间仅使用核心线程（4个），即使有适量的任务在队列中等待运行。这时线程池
就可以用作节流阀。如果挤压的请求变得非常多，这时该池就会尝试运行更多的线程来清理；这时第二个节流阀—最大
线程数就起作用了。

## 18. ThreadLocal原理, 用的时候需要注意什么?
每一个线程的Thread对象都有一个ThreadLocalMap对象, 这个对象存储了一组以ThreadLocal.ThreadLocalHashCode为键, 以
本地线程变量为值的 K-V 值对, ThreadLocal对象就是当前线程的 ThreadLocalMap的访问入口, 每一个ThreadLocal对象都包含
一个独一无二的threadLocalHashCode值, 使用这个值就可以在线程 K-V 值中找回对应的本地线程变量.

为什么使用弱引用
从表面上看内存泄漏的根源在于使用了弱引用。网上的文章大多着重分析ThreadLocal使用了弱引用会导致内存泄漏，但是另一个问题也同样值得思考：为什么使用弱引用而不是强引用？

我们先来看看官方文档的说法：

To help deal with very large and long-lived usages, the hash table entries use WeakReferences for keys.
为了应对非常大和长时间的用途，哈希表使用弱引用的 key。

下面我们分两种情况讨论：

key 使用强引用：引用的ThreadLocal的对象被回收了，但是ThreadLocalMap还持有ThreadLocal的强引用，如果没有手动删除，ThreadLocal不会被回收，导致Entry内存泄漏。
key 使用弱引用：引用的ThreadLocal的对象被回收了，由于ThreadLocalMap持有ThreadLocal的弱引用，即使没有手动删除，ThreadLocal也会被回收。value在下一次ThreadLocalMap调用set,get，remove的时候会被清除。
比较两种情况，我们可以发现：由于ThreadLocalMap的生命周期跟Thread一样长，如果都没有手动删除对应key，都会导致内存泄漏，但是使用弱引用可以多一层保障：弱引用ThreadLocal不会内存泄漏，对应的value在下一次ThreadLocalMap调用set,get,remove的时候会被清除。

因此，ThreadLocal内存泄漏的根源是：由于ThreadLocalMap的生命周期跟Thread一样长，如果没有手动删除对应key就会导致内存泄漏，而不是因为弱引用。

### 注意事项:
① 初始化时, 使用initValue方法.
② 每一个线程都只是使用ThreadLocal标注变量的副本进行计算, 每一个线程的ThreadLocal变量值都是独立的, 不被其他线程影响.

## 19. CountDownLatch和CyclicBarrier的用法, 以及相互之间的差别?




## 20. LockSupport工具
长久以来对线程阻塞与唤醒经常我们会使用object的wait和notify,除了这种方式，java并发包还提供了另外一种方式对线程进行挂起和恢复，它就是并发包子包locks提供的LockSupport。
LockSupport 和 CAS 是Java并发包中很多并发工具控制机制的基础，它们底层其实都是依赖Unsafe实现。
LockSupport是用来创建锁和其他同步类的基本线程阻塞原语。LockSupport 提供park()和unpark()方法实现阻塞线程和解除线程阻塞，LockSupport和每个使用它的线程都与一个许可(permit)关联。permit相当于1，0的开关，默认是0，调用一次unpark就加1变成1，调用一次park会消费permit, 也就是将1变成0，同时park立即返回。再次调用park会变成block（因为permit为0了，会阻塞在这里，直到permit变为1）, 这时调用unpark会把permit置为1。每个线程都有一个相关的permit, permit最多只有一个，重复调用unpark也不会积累。
park()和unpark()不会有 “Thread.suspend和Thread.resume所可能引发的死锁” 问题，由于许可的存在，调用 park 的线程和另一个试图将其 unpark 的线程之间的竞争将保持活性。如果调用线程被中断，则park方法会返回。同时park也拥有可以设置超时时间的版本。
需要特别注意的一点：park 方法还可以在其他任何时间“毫无理由”地返回，因此通常必须在重新检查返回条件的循环里调用此方法。从这个意义上说，park 是“忙碌等待”的一种优化，它不会浪费这么多的时间进行自旋，但是必须将它与 unpark 配对使用才更高效。

## 21. Condition接口及其实现原理



## 22. Fork/Join框架的理解



## 23. 分段锁的原理, 锁力度减小的思考
在分析ConcurrentHashMap的源码的时候，了解到这个并发容器类的加锁机制是基于粒度更小的分段锁，分段锁也是提升多并发程序性能的重要手段之一。
在并发程序中，串行操作是会降低可伸缩性，并且上下文切换也会减低性能。在锁上发生竞争时将通水导致这两种问题，使用独占锁时保护受限资源的时候，基本上是采用串行方式—-每次只能有一个线程能访问它。所以对于可伸缩性来说最大的威胁就是独占锁。
我们一般有三种方式降低锁的竞争程度：
1、减少锁的持有时间
2、降低锁的请求频率
3、使用带有协调机制的独占锁，这些机制允许更高的并发性。
在某些情况下我们可以将锁分解技术进一步扩展为一组独立对象上的锁进行分解，这成为分段锁。其实说的简单一点就是：容器里有多把锁，每一把锁用于锁容器其中一部分数据，那么当多线程访问容器里不同数据段的数据时，线程间就不会存在锁竞争，从而可以有效的提高并发访问效率，这就是ConcurrentHashMap所使用的锁分段技术，首先将数据分成一段一段的存储，然后给每一段数据配一把锁，当一个线程占用锁访问其中一个段数据的时候，其他段的数据也能被其他线程访问。
比如：在ConcurrentHashMap中使用了一个包含16个锁的数组，每个锁保护所有散列桶的1/16，其中第N个散列桶由第（N mod 16）个锁来保护。假设使用合理的散列算法使关键字能够均匀的分部，那么这大约能使对锁的请求减少到越来的1/16。也正是这项技术使得ConcurrentHashMap支持多达16个并发的写入线程。
当然，任何技术必有其劣势，与独占锁相比，维护多个锁来实现独占访问将更加困难而且开销更加大。
下面给出一个基于散列的Map的实现，使用分段锁技术。
```java
import java.util.Map;

/**
 * Created by louyuting on 17/1/10.
 */
public class StripedMap {
    //同步策略: buckets[n]由 locks[n%N_LOCKS] 来保护
    private static final int N_LOCKS = 16;//分段锁的个数
    private final Node[] buckets;
    private final Object[] locks;
    /**
     * 结点
     * @param <K>
     * @param <V>
     */
    private static class Node<K,V> implements Map.Entry<K,V>{
        final K key;//key
        V value;//value
        Node<K,V> next;//指向下一个结点的指针
        int hash;//hash值
        //构造器，传入Entry的四个属性
        Node(int h, K k, V v, Node<K,V> n) {
            value = v;
            next = n;//该Entry的后继
            key = k;
            hash = h;
        }
        public final K getKey() {
            return key;
        }
        public final V getValue() {
            return value;
        }
        public final V setValue(V newValue) {
            V oldValue = value;
            value = newValue;
            return oldValue;
        }
    }
    /**
     * 构造器: 初始化散列桶和分段锁数组
     * @param numBuckets
     */
    public StripedMap(int numBuckets) {
        buckets = new Node[numBuckets];
        locks = new Object[N_LOCKS];
        for(int i=0; i<N_LOCKS; i++){
            locks[i] = new Object();
        }
    }
    /**
     * 返回散列之后在散列桶之中的定位
     * @param key
     * @return
     */
    private final int hash(Object key){
        return Math.abs(key.hashCode() % N_LOCKS);
    }
    /**
     * 分段锁实现的get
     * @param key
     * @return
     */
    public Object get(Object key){
        int hash = hash(key);//计算hash值
        //获取分段锁中的某一把锁
        synchronized (locks[hash% N_LOCKS]){
            for(Node m=buckets[hash]; m!=null; m=m.next){
                if(m.key.equals(key)){
                    return m.value;
                }
            }
        }
        return null;
    }
    /**
     * 清除整个map
     */
    public void clear() {
        //分段获取散列桶中每个桶地锁，然后清除对应的桶的锁
        for(int i=0; i<buckets.length; i++){
            synchronized (locks[i%N_LOCKS]){
                buckets[i] = null;
            }
        }
    }
}
```
上面的实现中：使用了N_LOCKS个锁对象数组，并且每个锁保护容器的一个子集，对于大多数的方法只需要回去key值的hash散列之后对应的数据区域的一把锁就行了。但是对于某些方法却要获得全部的锁，比如clear()方法，但是获得全部的锁不必是同时获得，可以使分段获得，具体的查看源码。
## 24. 八种阻塞队列以及各个阻塞队列的特性
#### ArrayBlockingQueue: 一个由数组结构组成的有界阻塞队列
用数组实现的有界阻塞队列。此队列按照先进先出（FIFO）的原则对元素进行排序。默认情况下不保证访问者公平的访问队列，
所谓公平访问队列是指阻塞的所有生产者线程或消费者线程，当队列可用时，可以按照阻塞的先后顺序访问队列，即先阻塞的
生产者线程，可以先往队列里插入元素，先阻塞的消费者线程，可以先从队列里获取元素。通常情况下为了保证公平性会降低
吞吐量。我们可以使用以下代码创建一个公平的阻塞队列：
ArrayBlockingQueue fairQueue = new  ArrayBlockingQueue(1000,true);

#### LinkedBlockingQueue: 一个由链表结构组成的有界阻塞队列。
基于链表的阻塞队列，同ArrayListBlockingQueue类似，此队列按照先进先出（FIFO）的原则对元素进行排序，其内部也
维持着一个数据缓冲队列（该队列由一个链表构成），当生产者往队列中放入一个数据时，队列会从生产者手中获取数据，
并缓存在队列内部，而生产者立即返回；只有当队列缓冲区达到最大值缓存容量时（LinkedBlockingQueue可以通过构造函
数指定该值），才会阻塞生产者队列，直到消费者从队列中消费掉一份数据，生产者线程会被唤醒，反之对于消费者这端的
处理也基于同样的原理。而LinkedBlockingQueue之所以能够高效的处理并发数据，还因为其对于生产者端和消费者端分别
采用了独立的锁来控制数据同步，这也意味着在高并发的情况下生产者和消费者可以并行地操作队列中的数据，以此来提高
整个队列的并发性能。 
作为开发者，我们需要注意的是，如果构造一个LinkedBlockingQueue对象，而没有指定其容量大小，LinkedBlockingQueue
会默认一个类似无限大小的容量（Integer.MAX_VALUE），这样的话，如果生产者的速度一旦大于消费者的速度，也许还没有
等到队列满阻塞产生，系统内存就有可能已被消耗殆尽了。 
ArrayBlockingQueue和LinkedBlockingQueue是两个最普通也是最常用的阻塞队列，一般情况下，在处理多线程间的生产者
消费者问题，使用这两个类足以。

#### PriorityBlockingQueue: 一个支持优先级排序的无界阻塞队列。
是一个支持优先级的无界队列。默认情况下元素采取自然顺序升序排列。可以自定义实现compareTo()方法来指定元素进行排
序规则，或者初始化PriorityBlockingQueue时，指定构造参数Comparator来对元素进行排序。需要注意的是不能保证同
优先级元素的顺序。

#### DelayQueue: 一个使用优先级队列实现的无界阻塞队列。
是一个支持延时获取元素的无界阻塞队列。队列使用PriorityQueue来实现。队列中的元素必须实现Delayed接口，在创建元
素时可以指定多久才能从队列中获取当前元素。只有在延迟期满时才能从队列中提取元素。我们可以将DelayQueue运用在以
下应用场景：

① 缓存系统的设计：可以用DelayQueue保存缓存元素的有效期，使用一个线程循环查询DelayQueue，一旦能从DelayQueue
中获取元素时，表示缓存有效期到了。
② 定时任务调度：使用DelayQueue保存当天将会执行的任务和执行时间，一旦从DelayQueue中获取到任务就开始执行，比如
TimerQueue就是使用DelayQueue实现的。

#### SynchronousQueue: 一个不存储元素的阻塞队列。
是一个不存储元素的阻塞队列。每一个put操作必须等待一个take操作，否则不能继续添加元素。SynchronousQueue可以看成
是一个传球手，负责把生产者线程处理的数据直接传递给消费者线程。队列本身并不存储任何元素，非常适合于传递性场景,比
如在一个线程中使用的数据，传递给另外一个线程使用，SynchronousQueue的吞吐量高于LinkedBlockingQueue 和 
ArrayBlockingQueue。

#### LinkedTransferQueue: 一个由链表结构组成的无界阻塞队列。
是一个由链表结构组成的无界阻塞TransferQueue队列。相对于其他阻塞队列，LinkedTransferQueue多了tryTransfer和transfer
方法。 
transfer方法。如果当前有消费者正在等待接收元素（消费者使用take()方法或带时间限制的poll()方法时），transfer方法可以
把生产者传入的元素立刻transfer（传输）给消费者。如果没有消费者在等待接收元素，transfer方法会将元素存放在队列的tail
节点，并等到该元素被消费者消费了才返回。transfer方法的关键代码如下：
① Node pred = tryAppend(s, haveData);
② return awaitMatch(s, pred, e, (how == TIMED), nanos);
第一行代码是试图把存放当前元素的s节点作为tail节点。第二行代码是让CPU自旋等待消费者消费元素。因为自旋会消耗CPU，所以
自旋一定的次数后使用Thread.yield()方法来暂停当前正在执行的线程，并执行其他线程。

tryTransfer方法。则是用来试探下生产者传入的元素是否能直接传给消费者。如果没有消费者等待接收元素，则返回false。
和transfer方法的区别是tryTransfer方法无论消费者是否接收，方法立即返回。而transfer方法是必须等到消费者消费了才返回。

对于带有时间限制的tryTransfer(E e, long timeout, TimeUnit unit)方法，则是试图把生产者传入的元素直接传给消费者，
但是如果没有消费者消费该元素则等待指定的时间再返回，如果超时还没消费元素，则返回false，如果在超时时间内消费了元素，
则返回true。

#### LinkedBlockingDeque: 一个由链表结构组成的双向阻塞队列。
是一个由链表结构组成的双向阻塞队列。所谓双向队列指的你可以从队列的两端插入和移出元素。双端队列因为多了一个操作队列的入口，
在多线程同时入队时，也就减少了一半的竞争。相比其他的阻塞队列，LinkedBlockingDeque多了addFirst，addLast，offerFirst，
offerLast，peekFirst，peekLast等方法，以First单词结尾的方法，表示插入，获取（peek）或移除双端队列的第一个元素。
以Last单词结尾的方法，表示插入，获取或移除双端队列的最后一个元素。另外插入方法add等同于addLast，移除方法remove等效
于removeFirst。但是take方法却等同于takeFirst，不知道是不是Jdk的bug，使用时还是用带有First和Last后缀的方法更清楚。
在初始化LinkedBlockingDeque时可以设置容量防止其过渡膨胀。另外双向阻塞队列可以运用在“工作窃取”模式中。

# Spring
## 1. BeanFactory 和 FactoryBean?
#### Bean: Java类实例
每一个Bean对应Spring容器里的一个Java实例. 
定义Bean时通常需要指定两个属性。
① Id：确定该Bean的唯一标识符，容器对Bean管理、访问、以及该Bean的依赖关系，都通过该属性完成。Bean的id属性在Spring
容器中是唯一的。
② Class：指定该Bean的具体实现类。注意这里不能使接口。通常情况下，Spring会直接使用new关键字创建该Bean的实例，因此，
这里必须提供Bean实现类的类名。

#### BeanFactory: 
BeanFactory是Spring IOC最基本的容器，负责生产和管理bean，它为其他具体的IOC容器实现提供了最基本的规范，例如
DefaultListableBeanFactory, XmlBeanFactory, ApplicationContext 等具体的容器都是实现了BeanFactory，
再在其基础之上附加了其他的功能。
下面可以看看BeanFactory提供的基本功能：
```java
public interface BeanFactory {
    String FACTORY_BEAN_PREFIX = "&";
    Object getBean(String name) throws BeansException;
    <T> T getBean(String name, Class<T> requiredType) throws BeansException;
    <T> T getBean(Class<T> requiredType) throws BeansException;
    Object getBean(String name, Object... args) throws BeansException;
    boolean containsBean(String name);
    boolean isSingleton(String name) throws NoSuchBeanDefinitionException;
    boolean isPrototype(String name) throws NoSuchBeanDefinitionException;
    boolean isTypeMatch(String name, Class<?> targetType) throws NoSuchBeanDefinitionException;
    Class<?> getType(String name) throws NoSuchBeanDefinitionException;
    String[] getAliases(String name);
}
```
#### FactoryBean:
FactoryBean是一个接口，当在IOC容器中的Bean实现了FactoryBean接口后，通过getBean(String BeanName)获取到的Bean
对象并不是FactoryBean的实现类对象，而是这个实现类中的getObject()方法返回的对象。要想获取FactoryBean的实现类，
就要getBean(&BeanName)，在BeanName之前加上&。
```java
public interface FactoryBean<T> {
    T getObject() throws Exception;
    Class<?> getObjectType();
    boolean isSingleton();
}
```

#### 区别
通过以上源码和示例来看，基本上能印证以下结论，也就是二者的区别。
① BeanFactory是个Factory，也就是 IOC 容器或对象工厂，所有的Bean都是由BeanFactory( 也就是 IOC 容器 ) 来进行管理。
② FactoryBean是一个能生产或者修饰生成对象的工厂Bean(本质上也是一个bean)，可以在BeanFactory（IOC容器）中被管理，所以
它并不是一个简单的Bean。当使用容器中factory bean的时候，该容器不会返回factory bean本身，而是返回其生成的对象。要
想获取FactoryBean的实现类本身，得在getBean(String BeanName)中的BeanName之前加上&,写成getBean(String &BeanName)。

## 2. Spring IOC 的理解, 其初始化过程?
IOC即依赖控制反转, 利用java反射机制, 将实例的初始化交给spring, 由spring来控制管理实例. 
默认实现是单例模式. 

问: 为什么不使用工厂模式?
答: 如果需求发生变化, 工厂模式需要更改factory类的方法, 而ioc只需要更改类属性, 并且由于ioc利用了java反射机制, 对象
是动态生成的, 我们可以热插拔对象...???

控制反转 IoC(Inversion of Control) 是面对对象编程中的一种设计原则, 用来降低计算机代码之间的耦合度. 又被称作依赖注入
DI(Dependency Injection)

IoC需要实现两个技术:
对象的创建
对象的绑定

BeanFactory
默认采用延迟初始化策略.
① BeanDefinition实现了bean的定义, 且完成了对依赖的定义
② BeanDefinitionRegistry 将定义好的bean，注册到容器中（此时会生成一个注册码）
③ BeanFactory 是一个bean工厂类，从中可以取到任意定义过的bean最重要的部分就是BeanDefinition,它完成了Bean的生成过程。
一般情况下我们都是通过配置文件（xml,properties）的方式对bean进行配置，每种文件都需要实现BeanDefinitionReader,因此是
reader本身现了配置文字 到bean对象的转换过程。当然我们自己也可以实现任意格式的配置文件，只需要自己来实现reader即可。Bean
的生成大致可以分为两个阶段：容器启动阶段和bean实例化阶段
![bean初始化过程](bean.png)
容器启动阶段:
① 加载配置文件(通常是xml文件)
② 通过reader生成BeanDefinition
③ beanDefinition注册到beanDefinitionRegistry


## 3. BeanFactory 和 ApplicationContext?
简单来说ApplicationContext是BeanFactory的拓展.
ApplicationContext 容器建立BeanFactory之上，拥有BeanFactory的所有功能，但在实现上会有所差别。我认为差别主要体现在两个方面：
① bean的生成方式；
② 扩展了BeanFactory的功能，提供了更多企业级功能的支持。
## 4. Spring Bean 的生命周期, 如何被管理的?
对于普通的 java 对象, 当 new 的时候创建对象, 当它没有任何引用的时候被垃圾回收机制回收. 而由 Spring IOC 容器托管的对象, 他们的生命周期完全有容器控制. Spring 中每个 Bean 的生命周期如下:
![bean 的生命周期](bean.jpg)
对于普通的 java 对象, 当 new 的时候创建对象, 当它没有任何引用的时候被垃圾回收机制回收. 而由 Spring IOC 容器托管的对象, 他们
的生命周期完全有容器控制. Spring 中每个 Bean 的生命周期如下:
![bean 的生命周期](bean生命周期.jpg)
### 实例化 Bean
对于 BeanFactory 容器, 当客户端请求一个尚未初始化的 bean 时, 或初始化 bean 的时候需要注入另一个尚未初始化的依赖时, 容器就会
调用 createBean进行实例化.
对于 ApplicationContext 容器, 容器启动结束后, 便实例化所有的 bean.
容器通过获取 BeanDefinition 对象中的信息进行实例化. 并且这一步仅仅是简单的实例化, 并未进行依赖注入.
实例化对象被包装在 BeanWrapper 对象中, BeanWrapper 提供了设置对象属性的接口, 从而避免了使用反射机制设置属性.
### 设置对象属性
实例化后的对象被封装在 BeanWrapper 对象中, 并且此时对象仍然是一个原生的状态, 并没有进行依赖注入.
紧接着, Spring 根据 BeanDefinition 中的信息进行依赖注入.
并且通过 BeanWrapper 提供的设置属性的接口完成依赖注入.
### 注入 Aware 接口
紧接着, Spring 会检测该对象是否实现了 xxxAware 接口, 并将相关的 xxxAware 实例注入给 bean.
### BeanPostProcessor
当经过上述的几个步骤后, bean对象已经被正确构造, 但如果你想要对象被使用前再进行一些自定义的处理, 就可以通过 BeanPostProcessor
接口实现. 该接口提供了两个函数:
postProcessBeforeInitialization(Object bean, String beanName)
当前正在初始化的 bean 对象会被传递进来, 我们就可以对这个 bean 做任何处理. 这个函数会先于 InitializationBean 执行, 因此成为前
置处理. 所有 Aware 接口的注入就是在这一步完成的.
postProcessAfterInitialization(Object bean, String beanName)
当前正在初始化的 bean 对象会被传递进来, 我们就可以对这个 bean 作任何处理, 这个函数会在 InitializationBean 完成后执行, 因此称
为后置处理.
### InitializingBean与 init-method
当 BeanPostProcessor 的前置处理完成后就会进入本阶段
InitializingBean 接口只有一个函数:
afterPropertiesSet()
这一阶段也可以在 bean 正式构造完成前增加我们自定义的逻辑, 但他与前置处理不同, 由于该函数并不会把当前 bean 对象传进来, 因此在这
一步没办法处理对象本身, 只能增加一些额外的逻辑. 若要使用它, 我们需要让 bean 实现该接口, 并把要增加的逻辑写在该函数中. 然后 spring 
会在前置处理完成后检测当前 bean 是否实现了该接口, 并执行 afterPropertiesSet 函数.
当然 Spring 为了降低对客户代码的侵入性, 给 bean 的配置提供了 init-method 的属性, 该属性指定了在这一阶段需要执行的函数名, Spring 
便会在初始化阶段执行我们设置的函数. init-method 本质上仍然使用了 InitializingBean 接口.
### DisposableBean 和 destroy-method
和 init-method 一样, 通过给 destroy-method 指定函数, 就可以在 bean 销毁前执行指定的逻辑.

## 5. Spring Bean 的加载过程是怎样的?
先从表面上可以看到 bean 的加载可大致分为:
从 xml 读取 bean 的信息加载到 spring 容器中, 通过 xml 配置的 id 从 Spring 容器反射得到这个类的实例对象.

获取配置文件资源
对获取的 xml 文件资源进行一定的处理检验
处理包装资源
解析处理包装过后的资源
加载提取 bean 并注册(添加到 beanDefinitionMap 中)

获取 bean, 从 beanDefinitionMap 中获取
## 6. 如果要你实现Spring AOP, 请问怎么实现?
### 代理模式: 为其他对象提供一种代理以控制对这个对象的访问. 比如A对象要做一件事情，在没有代理前，自己来做，在对A代理后，由A的代理类B来做。代理其实是在原实例前后加了一层处理，这也是AOP的初级轮廓。
### 静态代理原理及实践: 
静态代理说白了就是在程序运行前就已经存在代理类的字节码文件，代理类和原始类的关系在运行前就已经确定。
```java
// 接口
public interface IUserDao {
	void save();
	void find();
}
//目标对象
class UserDao implements IUserDao{
	@Override
	public void save() {
		System.out.println("模拟：保存用户！");
	}
	@Override
	public void find() {
		System.out.println("模拟：查询用户");
	}
}
/**
    静态代理
          特点：
	1. 目标对象必须要实现接口
	2. 代理对象，要实现与目标对象一样的接口
 */
class UserDaoProxy implements IUserDao{
	// 代理对象，需要维护一个目标对象
	private IUserDao target = new UserDao();
	@Override
	public void save() {
		System.out.println("代理操作： 开启事务...");
		target.save();   // 执行目标对象的方法
		System.out.println("代理操作：提交事务...");
	}
	@Override
	public void find() {
		target.find();
	}
}
```
静态代理虽然保证了业务类只需关注逻辑本身，代理对象的一个接口只服务于一种类型的对象，如果要代理的方法很多，势必要为每一种方法都进行代理。再者，如果增加一个方法，除了实现类需要实现这个方法外，所有的代理类也要实现此方法。增加了代码的维护成本。那么要如何解决呢?答案是使用动态代理。
### 动态代理原理及实践
动态代理类的源码是在程序运行期间通过JVM反射等机制动态生成，代理类和委托类的关系是运行时才确定的。
```java
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
// 接口
public interface IUserDao {
	void save();
	void find();
}
//目标对象
 class UserDao implements IUserDao{
	@Override
	public void save() {
		System.out.println("模拟： 保存用户！");
	}
	@Override
	public void find() {
		System.out.println("查询");
	}
}
/**
 * 动态代理：
 *    代理工厂，给多个目标对象生成代理对象！
 *
 */
class ProxyFactory {
	// 接收一个目标对象
	private Object target;
	public ProxyFactory(Object target) {
		this.target = target;
	}
	// 返回对目标对象(target)代理后的对象(proxy)
	public Object getProxyInstance() {
		Object proxy = Proxy.newProxyInstance(
			target.getClass().getClassLoader(),  // 目标对象使用的类加载器
			target.getClass().getInterfaces(),   // 目标对象实现的所有接口
			new InvocationHandler() {			// 执行代理对象方法时候触发
				@Override
				public Object invoke(Object proxy, Method method, Object[] args)
						throws Throwable {

					// 获取当前执行的方法的方法名
					String methodName = method.getName();
					// 方法返回值
					Object result = null;
					if ("find".equals(methodName)) {
						// 直接调用目标对象方法
						result = method.invoke(target, args);
					} else {
						System.out.println("开启事务...");
						// 执行目标对象方法
						result = method.invoke(target, args);
						System.out.println("提交事务...");
					}
					return result;
				}
			}
		);
		return proxy;
	}
}
```
在运行测试类中创建测试类对象代码中
```java
IUserDao proxy = (IUserDao)new ProxyFactory(target).getProxyInstance();
```
其实是jdk动态生成了一个类去实现接口,隐藏了这个过程:
```java
class $jdkProxy implements IUserDao{}
```
使用jdk生成的动态代理的前提是目标类必须有实现的接口。但这里又引入一个问题,如果某个类没有实现接口,就不能使用jdk动态代理,所以Cglib代理就是解决这个问题的。
Cglib是以动态生成的子类继承目标的方式实现，在运行期动态的在内存中构建一个子类，如下:
```java
public class UserDao{}
//Cglib是以动态生成的子类继承目标的方式实现,程序执行时,隐藏了下面的过程
public class $Cglib_Proxy_class  extends UserDao{}
```
Cglib使用的前提是目标类不能为final修饰。因为final修饰的类不能被继承。
现在，我们可以看看AOP的定义：面向切面编程，核心原理是使用动态代理模式在方法执行前后或出现异常时加入相关逻辑。
通过定义和前面代码我们可以发现3点：

AOP是基于动态代理模式。
AOP是方法级别的（要测试的方法不能为static修饰，因为接口中不能存在静态方法，编译就会报错）。
AOP可以分离业务代码和关注点代码（重复代码），在执行业务代码时，动态的注入关注点代码。切面就是关注点代码形成的类。

前文提到jdk代理和cglib代理两种动态代理，优秀的spring框架把两种方式在底层都集成了进去,我们无需担心自己去实现动态生成代理。那么，spring是如何生成代理对象的？

创建容器对象的时候，根据切入点表达式拦截的类，生成代理对象。
如果目标对象有实现接口，使用jdk代理。如果目标对象没有实现接口，则使用cglib代理。然后从容器获取代理后的对象，在运行期植入"切面"类的方法。

如果目标类没有实现接口，且class为final修饰的，则不能进行spring AOP编程！
## 7. 如果要你实现Spring IOC, 你会注意哪些问题?
## 8. Spring是如何管理事务的, 事务管理机制?
## 9. Spring的不同事务传播行为有哪些, 干什么用的?
- PROPAGATION_REQUIRED
默认的事务传播级别, 使用该级别的特点是, 如果上下文中已经存在事务, 那么就加入该事务中执行, 如果当前上下文中不存在事务, 则新建事务执行. 所以这个级别通常能满足大多数的业务场景.
- PROPAGATION_SUPPORTS 
从字面意思就知道, supports 支持, 该传播级别的特点是, 如果上下文中存在事务, 则支持加入事务, 如果没有事务, 则使用非事务方式执行. 所以说, 并非所有的包在transactionTemplate.execute中的代码都会有事务支持, 这个通常用来处理那些并非原子性的非核心业务逻辑操作. 应用场景较少.
- PROPAGATION_MANDATORY
该级别的事务要求上下文中必须存在事务, 否则就会抛出异常! 配置该方式的传播级别是有效控制上下文调用代码遗漏添加事务控制的保证手段. 比如一段代码不能单独被调用执行, 但是一旦被调用, 就必须有事务包含的情况, 就可以使用这个传播级别.
- PROPAGATION_REQUIRED_NEW
从字面意思知道, new 每次都要新建事务, 该事务级别的特点是, 每次都新建一个事务, 并且将上下文的事务挂起,执行当前新建事务完成以后, 上下文事务恢复再执行.
这是一个很有用的传播级别, 举一个应用场景, 现在有一个发送100个红包的操作, 在发送之前, 要做一些系统的初始化, 验证, 数据记录操作, 然后发送100封红包, 然后再记录发送日志, 发送日志要求100%的准确, 如果日志不准确那么整个父事务逻辑需要回滚.
怎么处理整个业务需求呢? 就是通过这个PROPAGATION_REQUIREDS_NEW级别的事务传播控制就可以完成. 完成红包的子事务不会直接影响到父事务的提交和回滚.
- PROPAGATION_NOT_SUPPORTED
这个也可以从字面得知, not supported, 不支持, 当前级别的特点就是上下文中存在事务, 则挂起事务, 执行当前逻辑, 结束后恢复上下文的事务.
这个级别有什么好处? 可以帮助你将事务极可能的缩小. 我们知道一个事务越大, 它存在的风险也就越多. 所以在处理事务的过程中, 要保证尽可能的缩小范围. 比如一段代码, 是每次逻辑操作都必须调用的, 比如循环1000次的某个非核心业务逻辑操作. 这样的代码如果包在事务中, 势必造成事务太大, 导致出现一些难以考虑周全的异常情况. 所以这个事务这个级别的传播级别就派上用场了. 用当前级别的事务模板抱起来就可以了.
- PROPAGATION_NEVER
该事务更严格, 上面一个事务传播只是不支持而已, 有事务就挂起, 而PROPAGATION_NEVER传播级别要求上下文中不能存在事务, 一旦有事务, 就抛出runtime异常, 强制停止执行! 这个级别上辈子跟事务有仇.
- PROPAGATION_NESTED
字面也可知道, nested, 嵌套级别事务, 该传播级别特征是, 如果上下文中存在事务, 则嵌套事务执行, 如果不存在事务, 则新建事务.
嵌套是子事务套在父事务中执行, 子事务是父事务的一部分, 在进入子事务之前, 父事务建立一个回滚点, 叫save point 然后执行子事务, 这个子事务的执行也算是父事务的一部分, 然后子事务执行结束, 父事务继续执行. 重点就在于那个save point.
### 如果子事务回滚，会发生什么？ 
父事务会回滚到进入子事务前建立的save point，然后尝试其他的事务或者其他的业务逻辑，父事务之前的操作不会受到影响，更不会自动回滚。
### 如果父事务回滚，会发生什么？ 
父事务回滚，子事务也会跟着回滚！为什么呢，因为父事务结束之前，子事务是不会提交的，我们说子事务是父事务的一部分，正是这个道理。那么：
### 事务的提交，是什么情况？ 
是父事务先提交，然后子事务提交，还是子事务先提交，父事务再提交？答案是第二种情况，还是那句话，子事务是父事务的一部分，由父事务统一提交。
## 10. Spring中用到了哪些设计模式?
- 简单工厂
又叫做静态工厂方法（StaticFactory Method）模式，但不属于23种GOF设计模式之一。
简单工厂模式的实质是由一个工厂类根据传入的参数，动态决定应该创建哪一个产品类。 
spring中的BeanFactory就是简单工厂模式的体现，根据传入一个唯一的标识来获得bean对象，但是否是在传入参数后创建还是传入参数前创建这个要根据具体情况来定。如下配置，就是在 HelloItxxz 类中创建一个 itxxzBean。
```xml
<beans>
    <bean id="singletonBean" class="com.itxxz.HelloItxxz">
        <constructor-arg>
            <value>Hello! 这是singletonBean!value>
        </constructor-arg>
    </bean>
    <bean id="itxxzBean" class="com.itxxz.HelloItxxz"
        singleton="false">
        <constructor-arg>
            <value>Hello! 这是itxxzBean! value>
        </constructor-arg>
    </bean>
</beans>
```
- 工厂方法
通常由应用程序直接使用new创建新的对象，为了将对象的创建和使用相分离，采用工厂模式,即应用程序将对象的创建及初始化职责交给工厂对象。
一般情况下,应用程序有自己的工厂对象来创建bean.如果将应用程序自己的工厂对象交给Spring管理,那么Spring管理的就不是普通的bean,而是工厂Bean。
```java
public class StaticFactoryBean {
      public static Integer createRandom() {
           return new Integer(new Random().nextInt());
       }
}
```
建一个config.xml配置文件，将其纳入Spring容器来管理,需要通过factory-method指定静态方法名称
```xml
//createRandom方法必须是static的,才能找到
<bean id="random" class="example.chapter3.StaticFactoryBean" factory-method="createRandom" scope="prototype"
/>
```
测试:
```java
public static void main(String[] args) {
      //调用getBean()时,返回随机数.如果没有指定factory-method,会返回StaticFactoryBean的实例,即返回工厂Bean的实例
      XmlBeanFactory factory = new XmlBeanFactory(new ClassPathResource("config.xml"));System.out.println("我是IT学习者创建的实例:"+factory.getBean("random").toString());
}
```
- 单例模式
保证一个类仅有一个实例，并提供一个访问它的全局访问点。 
spring中的单例模式完成了后半句话，即提供了全局的访问点BeanFactory。但没有从构造器级别去控制单例，这是因为spring管理的是是任意的java对象。 
核心提示点：Spring下默认的bean均为singleton，可以通过singleton=“true|false” 或者 scope=“？”来指定
- 适配器
在Spring的Aop中，使用的Advice（通知）来增强被代理类的功能。Spring实现这一AOP功能的原理就使用代理模式（1、JDK动态代理。2、CGLib字节码生成技术代理。）对类进行方法级别的切面增强，即，生成被代理类的代理类， 并在代理类的方法前，设置拦截器，通过执行拦截器重的内容增强了代理方法的功能，实现的面向切面编程。
Adapter类接口：Target
```java
public interface AdvisorAdapter {
    boolean supportsAdvice(Advice advice);
    MethodInterceptor getInterceptor(Advisor advisor);
}
```
MethodBeforeAdviceAdapter类，Adapter
```java
class MethodBeforeAdviceAdapter implements AdvisorAdapter, Serializable {
      public boolean supportsAdvice(Advice advice) {
            return (advice instanceof MethodBeforeAdvice);
      }
      public MethodInterceptor getInterceptor(Advisor advisor) {
            MethodBeforeAdvice advice = (MethodBeforeAdvice) advisor.getAdvice();
            return new MethodBeforeAdviceInterceptor(advice);
      }
}
```
## 11. Spring MVC 的工作原理?
## 12. Spring 的循环注入的原理?
## 13. Spring AOP 的理解, 各个术语, 他们是怎么相互工作的?
spring aop 即 面向切面编程.
① 通知 (Advice)
通知定义了切面是是什么及何时使用, 描述了切面要完成的工作及何时执行这个动作.
② 连接点 (Joinpoint)
程序执行的某个特定位置
③ 切点 (Pointcut)
在上面说的连接点的基础上，来定义切入点，你的一个类里，有15个方法，那就有几十个连接点了对把，但是你并不想在所有方法附近都使用通知（使用叫织入，以后再说），你只想让其中的几个，在调用这几个方法之前，之后或者抛出异常时干点什么，那么就用切点来定义这几个方法，让切点来筛选连接点，选中那几个你想要的方法。
④ 切面 (Aspect)
切面是通知和切入点的结合。现在发现了吧，没连接点什么事情，连接点就是为了让你好理解切点，搞出来的，明白这个概念就行了。通知说明了干什么和什么时候干（什么时候通过方法名中的before,after，around等就能知道），而切入点说明了在哪干（指定到底是哪个方法），这就是一个完整的切面定义。
⑤ 引入 (introduction)
允许我们向现有的类添加新方法属性, 这不就是把切面（也就是新方法属性：通知定义的）用到目标类中吗
### Advice 通知
### Joinpoint 连接点
就是程序执行的某个特定位置
### Pointcut 切点
### Aspect 切面
## 14. Spring 如何保证Controller并发的安全?
通常情况下不需要考虑多线程问题, spring mvc中的controller, service, dao对象默认是单例的即 scope是singleton.
如果controller中有多线程公用的变量, 会导致多线程问题, 解决方法有几个:
1、在控制器中不使用实例变量
2、将控制器的作用域从单例改为原型，即在spring配置文件Controller中声明 scope="prototype"，每次都创建新的controller
3、在Controller中使用ThreadLocal变量

# Netty
## 1. BIO, 伪异步IO, NIO和AIO

IO多路复用
select epoll
① epoll支持一个进程打开的socket描述符(fd)不受限制
仅受限于操作系统的最大文件句柄数 => 通常与系统的内存关系比较大 1G内存机器上大约可以打开10万个句柄左右, 8G => 80万句柄左右
② I/O效率不会随着FD数目的增加而线性下降
select/poll每次调用回线性扫描全部的socket集合, 而epoll是根据每个fd上面的callback函数来实现的, 只有活跃的socket才会去主动掉说能callback, 其他idle的socket则不会
③ 使用mmap加速内核与用户空间的消息传递
无论是select, poll 还是epoll都需要内核把FD消息通知给用户空间, 如何避免不必要的内存复制就显得非常重要, epoll是通过内核和用户空间mmap同一块内存来实现的.
④ epoll的API更加简单.
包括创建一个epoll描述符, 添加监听事件, 阻塞等待所监听的事件发生, 关闭epoll描述符.

### BIO Blocking I/O 同步阻塞I/O
网络编程的基本模型是Client/Server模型, 也就是两个进程相互通信, 其中服务端提供位置信息, 客户端通过连接操作向服务端监听的地址发起连接请求, 通过三次握手连接成功后, 双方建立网络套接字进行通信.
采用BIO通信模型的服务端, 通常由一个独立的Acceptor线程负责监听客户端连接, 它接收到客户端连接请求之后为每个客户端创建一个新的线程进行链路处理, 处理完成之后, 通过输出流返回应答给客户端, 线程销毁, 这就是典型的一请求一应答通信模型. 该模型的最大的问题就是缺乏弹性伸缩能力, 当客户端并发访问量增加后, 服务端的线程个数和客户端并发访问数呈1:1的正比关系, 由于线程是java虚拟机非常宝贵的系统资源, 当线程数膨胀之后, 系统的性能将急剧下降, 随着并发访问量的继续增大, 系统会发生线程堆栈溢出, 创建新线程失败等问题, 并最终导致进程宕机或者僵死, 不能对外提供服务.
### 伪异步I/O
采用线程池和任务队列可以实现一种叫做伪异步的I/O通信框架.
当有新的客户端接入时, 将客户端的Socket封装成一个Task投递到后端的线程池中进行处理. JDK的线程池维护一个消息队列和N个活跃线程, 对消息队列中的任务进行处理, 由于线程池可以设置消息队列的大小和最大线程数, 因此, 它的资源占用是可控的, 无论多少个客户端并发访问, 都不会导致资源的耗尽和宕机.
java同步I/O API说明, 当对Socket的输入流进行读取操作的时候, 它会一直阻塞下去, 直到发生如下的三种事件.
① 有数据可读
② 可用数据已经读取完毕
③ 发生空指针或者I/O异常
## 1. BIO, NIO和AIO
### BIO 同步阻塞 IO / Blocking I/O
通过由一个独立的 Acceptor 线程负责监听客户端的连接, 它接受到客户端的连接请求后, 为每个客户端创建一个新的线程进行链路处理. 一请
求一应答通信模型缺乏弹性收缩能力, 当并发访问量增加到一定量后, 服务端性能下降, 系统发生堆栈溢出.
### 伪异步 IO
采用线程池和任务队列实现. 当有新的客户端接入时, 将客户端 socket 封装成一个 Task(该任务实现 Runnable 接口)投递到后端的线程池中处理, JDK 的线程池维护了一个消息队列和N 个活跃线程, 对消息队列中的任务进行处理, 资源可控. 由于底层的通信模型还是采用同步阻塞模型, 因此无法解决根本问题. 无法解决同步 I/O 导致通信线程阻塞的问题
### NIO Nonblocking I/O 非阻塞 IO
缓冲区 Buffer
Buffer 是一个对象, 它包含一些要写入或者要读出的数据. 在 NIO 类库中加入 Buffer 对象, 体现了新库与原 I/O 的一个重要区别. 在面向流的 I/O 中, 可以将数据直接写入或者将数据直接读到 Stream对象中. 在 NIO 库中, 所有数据都是用缓冲区处理的. 在读取数据时, 它是直接读到缓冲区中的, 在写入数据时, 写入到缓冲区中. 任何时候访问 NIO 中的数据, 都是通过缓冲区进行操作;
缓冲区实质上是一个数组, 通常它是一个字节数组 ByteBuffer, 也可以使用其他种类的数组, 但是一个缓冲区不仅仅是一个数组, 缓冲区提供了对数据的结构化访问以及维护读写位置等信息. 最常用的缓冲区是 ByteBuffer, 一个ByteBuffer提供了一组功能用于操作 byte 数组.
通道 Channel
网络数据通过 Channel 读取和写入, 通道与流的不同之处在于通道是双向的, 流只能在一个方向上移动(一个流必须是 InputStream 或者 OutputStream 的子类), 而通道可以用于读写或者二者同时进行. 因为 Channel 是全双工的, 所以它可以比流更好的映射底层操作系统的 API, 特别是在 UNIX 网络编程模型中, 底层操作系统的通道都是全双工的, 同时支持读写操作. Channel 分为两大类: 用于网络读写的 SelectableChannel 和用于文件操作的 FileChannel; 本书涉及的 ServerSocketChannel 和 SocketChannel 都是 SelectableChannel 的子类.
多路复用器 Selector
Selector 会不断地轮询注册在其上的 Channel, 如果某个 Channel 上面发生读写事件, 这个 Channel 就处于就绪状态, 会被 Selector 轮询出来, 然后通过 SelectionKey 可以获取就绪 Channel 的集合, 进行后续的 I/O 操作. 一个 Selector 多路复用器可以同时轮询多个 Channel, 由于 JDK 使用了 epoll() 代替传统的 select 实现, 所有它没有最大连接句柄1024/2048的限制.  这也就意味着只需要一个线程负责 Selector 的轮询, 就可以接入成千上万的客户端, 这确实是个非常巨大的进步.
① 客户端发起的连接操作是异步的, 可以通过在多路复用器注册 OP_CONNECT 等待后续结果, 不需要像之前的客户端那样被同步阻塞.
② SocketChannel 的读写操作都是异步的, 如果没有可读写的数据它不会同步等待, 直接返回, 这样 I/O 通信线程就可以处理其他的链路, 不需要同步等待这个链路可用
③ 线程模型优化, 由于 JDK 的 Selector 在 linux 等主流操作系统上通过 epoll 实现, 它没有连接句柄数的限制(只受限于操作系统的最大句柄数或者单个进程的句柄限制),

### AIO 异步 I/O
JDK1.7升级了 NIO 类库, 升级后的 NIO 类库被称为 NIO2.0. 提供了异步文件 I/O 操作, 同时提供了 UNIX 网络编程事件驱动 I/O 对应 AIO.
NIO2.0提过了异步文件通道和异步套接字通道的实现. NIO2.0的异步套接字通道是真正的异步非阻塞 I/O, 它不需要通过多路复用器 Selector 对注册的通道进行轮询操作即可实现异步读写.AIO希望的是，你select，poll，epoll都需要用一个函数去监控一大堆fd，那么我AIO不需要了，你把fd告诉内核，你应用程序无需等待，内核会通过信号等软中断告诉应用程序，数据来了，你直接读了，所以，用了AIO可以废弃select，poll，epoll。
## 2. Netty的各大组件?
### Channel接口
基础的IO操作，如绑定、连接、读写等都依赖于底层网络传输所提供的原语，在Java的网络编程中，基础核心类是Socket，而Netty的Channel提
供了一组API，极大地简化了直接与Socket进行操作的复杂性，并且Channel是很多类的父类，如EmbeddedChannel、LocalServerChannel、
NioDatagramChannel、NioSctpChannel、NioSocketChannel等。
### EventLoop接口
EventLoop定义了处理在连接过程中发生的事件的核心抽象. EventlLoop是由EventLoopGroup来提供的。
一个EventLoopGroup可以包含多个EventLoop；一个EventLoop是一个Tread线程，可以分配给一个或者多个channel；
### ChannelFuture接口
作为异步回调的监听方法，可设置addListener监听，用于发送信息后的回调等操作。
Netty中的所有IO操作都是异步的，不会立即返回，需要在稍后确定操作结果。因此Netty提供了ChannelFuture，其addListener方法可以注册一
个ChannelFutureListener，当操作完成时，不管成功还是失败，均会被通知。ChannelFuture存储了之后执行的操作的结果并且无法预测操作何
时被执行，提交至Channel的操作按照被唤醒的顺序被执行。
### ChannelHandler接口
从应用开发者看来，ChannelHandler是最重要的组件，其中存放用来处理进站和出站数据的用户逻辑。ChannelHandler的方法被网络事件触发，
ChannelHandler可以用于几乎任何类型的操作，如将数据从一种格式转换为另一种格式或处理抛出的异常。例如，其子接口ChannelInboundHandler，
接受进站的事件和数据以便被用户定义的逻辑处理，或者当响应所连接的客户端时刷新ChannelInboundHandler的数据。
### ChannelPipeline
ChannelPipeline为ChannelHandler链提供了一个容器并定义了用于沿着链传播入站和出站事件流的API。当创建Channel时，会自动创建一个附属的ChannelPipeline。ChannelHandlers按照如下步骤安装在ChannelPipeline中。
　　· 一个ChannelInitializer的实现在ServerBootstrap中进行注册。
　　· 当ChannelInitializer的initChannel方法被调用时，ChannelInitializer在管道中安装一组自定义的ChannelHandlers。
　　· ChannelInitializer从ChannelPipeline中移除自身。
　　ChannelHandler可被当做放置任何代码的容器，用于处理到达并通过ChannelPipeline的事件或者数据，数据可以沿着处理链进行传递。
![ChannelPipeline](ChannelPipeline.png)
## 3. Netty的线程模型?
## 4. TCP 粘包/拆包的原因及解决方法
TCP 是一个流协议, 所谓流就是没有界限的一串数据. TCP 底层并不了解上层业务数据的具体含义, 它会根据 TCP 缓冲区的实际情况进行包的划分, 所以业务上认为, 一个完整的包可能会被 TCP 拆分成多个包进行发送, 也有可能把多个小包封装成一个大的数据包进行发送, 这就是所谓的 TCP 拆包和粘包问题.
解决方法
① 消息定长
② 在包尾增加回车换行符进行分割
③ 将消息分为消息头和消息体, 消息头中包含表示消息总长度(或者消息体长度的字段, 通常设计思路为消息头的第一个字段使用 int32来表示消息的总长度)
④ 更复杂的应用层协议
## 5. 了解哪几种序列化协议? 包括使用场景和如何去选择
序列化（serialization）就是将对象序列化为二进制形式（字节数组），一般也将序列化称为编码（Encode），主要用于网络传输、数据持久化等；

反序列化（deserialization）则是将从网络、磁盘等读取的字节数组还原成原始对象，以便后续业务的进行，一般也将反序列化称为解码（Decode），主要用于网络传输对象的解码，以便完成远程调用。
### XML
定义: XML（Extensible Markup Language）是一种常用的序列化和反序列化协议， 它历史悠久，从1998年的1.0版本被广泛使用至今。
优点: 人机可读性好, 可指定元素或特性的名称
缺点: 
序列化数据只包含数据本身以及类的结构，不包括类型标识和程序集信息。
类必须有一个将由 XmlSerializer 序列化的默认构造函数。
只能序列化公共属性和字段, 不能序列化方法
文件庞大，文件格式复杂，传输占带宽
使用场景:
当作配置文件存储数据
实时数据转换
### JSON
定义: JSON(JavaScript Object Notation, JS 对象标记) 是一种轻量级的数据交换格式。它基于 ECMAScript (w3c制定的js规范)的一个子集， JSON采用与编程语言无关的文本格式，但是也使用了类C语言（包括C， C++， C#， Java， JavaScript， Perl， Python等）的习惯，简洁和清晰的层次结构使得 JSON 成为理想的数据交换语言。
优点: 
前后兼容性高
数据格式比较简单，易于读写
序列化后数据较小，可扩展性好，兼容性好
与XML相比，其协议比较简单，解析速度比较快
缺点:
数据的描述性比XML差
不适合性能要求为ms级别的情况
额外空间开销比较大
使用场景:
跨防火墙访问
可调式性要求高的情况
基于Web browser的Ajax请求
传输数据量相对小，实时性要求相对低（例如秒级别）的服务
### Fastjson
定义: Fastjson是一个Java语言编写的高性能功能完善的JSON库。它采用一种“假定有序快速匹配”的算法，把JSON Parse的性能提升到极致。
优点: 接口简单易用, 序列化 反序列化速度快
缺点: 过于注重快，而偏离了“标准”及功能性 代码质量不高，文档不全
使用场景: 协议交互 Web输出
### Thrift
定义: Thrift不仅仅是序列化协议，而是一个RPC框架。它可以让你选择客户端与服务端之间传输通信协议的类别，即文本(text)和二进制(binary)传输协议, 为节约带宽，提供传输效率，一般情况下使用二进制类型的传输协议。
优点: 
序列化后的体积小, 速度快
支持多种语言和丰富的数据类型
对于数据字段的增删具有较强的兼容性
支持二进制压缩编码
缺点:
使用者较少
跨防火墙访问时，不安全
不具有可读性，调试代码时相对困难
不能与其他传输层协议共同使用（例如HTTP）
无法支持向持久层直接读写数据，即不适合做数据持久化序列化协议
使用场景: 分布式系统的RPC解决方案
### Avro
定义: Avro属于Apache Hadoop的一个子项目。 Avro提供两种序列化格式：JSON格式或者Binary格式。Binary格式在空间开销和解析性能方面可以和Protobuf媲美，Avro的产生解决了JSON的冗长和没有IDL的问题
优点: 
支持丰富的数据类型
简单的动态语言结合功能
具有自我描述属性
提高了数据解析速度
快速可压缩的二进制数据形式
可以实现远程过程调用RPC
支持跨编程语言实现
缺点: 对于习惯于静态类型语言的用户不直观
适用场景: 在Hadoop中做Hive、Pig和MapReduce的持久化数据格式
### ProtoBuf
定义: protocol buffers 由谷歌开源而来，在谷歌内部久经考验。它将数据结构以.proto文件进行描述，通过代码生成工具可以生成对应数据结构的POJO对象和Protobuf相关的方法和属性。
优点:
序列化后码流小，性能高
结构化数据存储格式（XML JSON等）
通过标识字段的顺序，可以实现协议的前向兼容
结构化的文档更容易管理和维护
缺点:
需要依赖于工具生成代码
使用场景:
对性能要求高的RPC调用
### 其他
Jboss marshaling可以直接序列化Java类
Message pack 一种高性能的二进制序列化协议
Hessian 采用二进制协议的轻量级remoting onhttp工具
## 6. Netty的零拷贝实现
Netty的零拷贝主要体现在三个方面:
① Netty的接收和发送ByteBuffer采用DIRECT BUFFERS, 使用堆外直接内存进行Socket读写, 不需要进行字节缓冲区的二次拷贝. 如果使用传统的堆内存(HEAP BUFFERS)进行Socket读写, JVM会将堆内存Buffer拷贝一份到直接内存中, 然后才写入Socket中, 相比于堆外直接内存, 消息在发送过程中多了一次缓冲区的内存拷贝. 接收缓冲区ByteBuffer的分配由ChannelConfig负责, 为了提升I/O操作的性能, 默认使用direct buffer, 这就避免了读写数据报的二次内存拷贝, 实现了读写Socket的零拷贝功能.
② 第二种零拷贝的实现 CompositeByteBuf 它对外将多个ByteBuf封装成一个ByteBuf, 对外提供统一封装后的ByteBuf接口, 添加ByteBuf, 不需要做内存拷贝.
③ 第三种零拷贝就是文件传输, Netty文件传输类DefaultFileRegion通过transferTo方法将文件发送到目标Channel. 直接将文件缓冲区的内容发送到目标Channel中, 而不需要通过循环拷贝的方式, 这是一种高效的传输方式, 提升了传输性能, 降低CPU和内存占用, 实现了文件传输的零拷贝.
## 7. Netty的高性能体现在哪些方面?
### ① 使用epoll并打开edge-triggered notification(边缘触发通知模式)通知模式, java的NIO和NIO.2都只是用了epoll，没有打开edge-triggered notification
epoll分为三个函数，第一个函数创建一个session类似的东西，第二个函数告诉内核维持这个session，并把属于session内的fd传给内核，第三个函数epoll_wait是真正的监控多个文件描述符函数，只需要告诉内核，我在等待哪个session，而session内的fd，内核早就分析过了，不再在每次epoll调用的时候分析，这就节省了内核大部分工作。这样每次调用epoll，内核不再重新扫描fd数组，因为我们维持了session。
epoll的效率还不仅仅体现在这里，在内核通知方式上，也改进了，我们先看select和poll的通知方式，也就是level-triggered notification(条件触发模式)，内核在被DMA中断，捕获到IO设备来数据后，本来只需要查找这个数据属于哪个文件描述符，进而通知线程里等待的函数即可，但是，select和poll要求内核在通知阶段还要继续再扫描一次刚才所建立的内核fd和io对应的那个数组，因为应用程序可能没有真正去读上次通知有数据后的那些fd，应用程序上次没读，内核在这次select和poll调用的时候就得继续通知，这个os和应用程序的沟通方式效率是低下的。只是方便编程而已（可以不去读那个网络io，方正下次会继续通知）。
于是epoll设计了另外一种通知方式：edge-triggered notification，在这个模式下，io设备来了数据，就只通知这些io设备对应的fd，上次通知过的fd不再通知，内核不再扫描一大堆fd了。
基于以上分析，我们可以看到epoll是专门针对大网络并发连接下的os和应用沟通协作上的一个设计，在linux下的网络服务器，必然要采用这个，nginx、php的国产异步框架swool、varnish，都是采用这个。

### 高性能的三大要素
1) 传输：用什么样的通道将数据发送给对方，BIO、NIO或者AIO，IO模型在很大程度上决定了框架的性能。
2) 协议：采用什么样的通信协议，HTTP或者内部私有协议。协议的选择不同，性能模型也不同。相比于公有协议，内部私有协议的性能通常可以被设计的更优。
3) 线程：数据报如何读取？读取之后的编解码在哪个线程进行，编解码后的消息如何派发，Reactor线程模型的不同，对性能的影响也非常大。

### Netty的高性能之道
1) 异步非阻塞通信 
采用I/O多路复用技术, 系统开销小, 系统不需要创建新的额外进程和线程, 降低系统维护工作量, 节省了系统资源.
Netty的IO线程NioEventLoop由于聚合了多路复用器Selector，可以同时并发处理成百上千个客户端Channel，由于读写操作都是非阻塞的，这就可以充分提升IO线程的运行效率，避免由于频繁IO阻塞导致的线程挂起。另外，由于Netty采用了异步通信模式，一个IO线程可以并发处理N个客户端连接和读写操作，这从根本上解决了传统同步阻塞IO一连接一线程模型，架构的性能、弹性伸缩能力和可靠性都得到了极大的提升。
2) 零拷贝
- Netty的接收和发送ByteBuffer采用DIRECT BUFFERS，使用堆外直接内存进行Socket读写，不需要进行字节缓冲区的二次拷贝。如果使用传统的堆内存（HEAP BUFFERS）进行Socket读写，JVM会将堆内存Buffer拷贝一份到直接内存中，然后才写入Socket中。相比于堆外直接内存，消息在发送过程中多了一次缓冲区的内存拷贝。
- Netty提供了组合Buffer对象 CompositeByteBuffer，可以聚合多个ByteBuffer对象，用户可以像操作一个Buffer那样方便的对组合Buffer进行操作，避免了传统通过内存拷贝的方式将几个小Buffer合并成一个大的Buffer。
- Netty的文件传输采用了transferTo方法，它可以直接将文件缓冲区的数据发送到目标Channel，避免了传统通过循环write方式导致的内存拷贝问题。
3) 内存池
随着JVM虚拟机和JIT即时编译技术的发展，对象的分配和回收是个非常轻量级的工作。但是对于缓冲区Buffer，情况却稍有不同，特别是对于堆外直接内存的分配和回收，是一件耗时的操作。为了尽量重用缓冲区，Netty提供了基于内存池的缓冲区重用机制。Netty提供了多种内存管理策略，通过在启动辅助类中配置相关参数，可以实现差异化的定制。
4) 高效的Reactor线程模型
常用的Reactor线程模型有三种，分别如下：
- Reactor单线程模型；
- Reactor多线程模型；
- 主从Reactor多线程模型
Reactor单线程模型，指的是所有的IO操作都在同一个NIO线程上面完成，NIO线程的职责如下：
- 作为NIO服务端，接收客户端的TCP连接；
- 作为NIO客户端，向服务端发起TCP连接；
- 读取通信对端的请求或者应答消息；
- 向通信对端发送消息请求或者应答消息。
由于Reactor模式使用的是异步非阻塞IO，所有的IO操作都不会导致阻塞，理论上一个线程可以独立处理所有IO相关的操作。从架构层面看，一个NIO线程确实可以完成其承担的职责。例如，通过Acceptor接收客户端的TCP连接请求消息，链路建立成功之后，通过Dispatch将对应的ByteBuffer派发到指定的Handler上进行消息解码。用户Handler可以通过NIO线程将消息发送给客户端。
对于一些小容量应用场景，可以使用单线程模型。但是对于高负载、大并发的应用却不合适，主要原因如下：
- 一个NIO线程同时处理成百上千的链路，性能上无法支撑，即便NIO线程的CPU负荷达到100%，也无法满足海量消息的编码、解码、读取和发送；
- 当NIO线程负载过重之后，处理速度将变慢，这会导致大量客户端连接超时，超时之后往往会进行重发，这更加重了NIO线程的负载，最终会导致大量消息积压和处理超时，NIO线程会成为系统的性能瓶颈；
- 可靠性问题：一旦NIO线程意外跑飞，或者进入死循环，会导致整个系统通信模块不可用，不能接收和处理外部消息，造成节点故障。
Rector多线程模型与单线程模型最大的区别就是有一组NIO线程处理IO操作
Reactor多线程模型的特点：
- 有专门一个NIO线程-Acceptor线程用于监听服务端，接收客户端的TCP连接请求；
- 网络IO操作-读、写等由一个NIO线程池负责，线程池可以采用标准的JDK线程池实现，它包含一个任务队列和N个可用的线程，由这些NIO线程负责消息的读取、解码、编码和发送；
- 1个NIO线程可以同时处理N条链路，但是1个链路只对应1个NIO线程，防止发生并发操作问题。
在绝大多数场景下，Reactor多线程模型都可以满足性能需求；但是，在极特殊应用场景中，一个NIO线程负责监听和处理所有的客户端连接可能会存在性能问题。例如百万客户端并发连接，或者服务端需要对客户端的握手消息进行安全认证，认证本身非常损耗性能。在这类场景下，单独一个Acceptor线程可能会存在性能不足问题，为了解决性能问题，产生了第三种Reactor线程模型-主从Reactor多线程模型。
主从Reactor线程模型的特点是：服务端用于接收客户端连接的不再是个1个单独的NIO线程，而是一个独立的NIO线程池。Acceptor接收到客户端TCP连接请求处理完成后（可能包含接入认证等），将新创建的SocketChannel注册到IO线程池（sub reactor线程池）的某个IO线程上，由它负责SocketChannel的读写和编解码工作。Acceptor线程池仅仅只用于客户端的登陆、握手和安全认证，一旦链路建立成功，就将链路注册到后端subReactor线程池的IO线程上，由IO线程负责后续的IO操作。
利用主从NIO线程模型，可以解决1个服务端监听线程无法有效处理所有客户端连接的性能不足问题。因此，在Netty的官方demo中，推荐使用该线程模型。

事实上，Netty的线程模型并非固定不变，通过在启动辅助类中创建不同的EventLoopGroup实例并通过适当的参数配置，就可以支持上述三种Reactor线程模型。正是因为Netty 对Reactor线程模型的支持提供了灵活的定制能力，所以可以满足不同业务场景的性能诉求。
### 无锁化的串行设计理念
在大多数场景下，并行多线程处理可以提升系统的并发性能。但是，如果对于共享资源的并发访问处理不当，会带来严重的锁竞争，这最终会导致性能的下降。为了尽可能的避免锁竞争带来的性能损耗，可以通过串行化设计，即消息的处理尽可能在同一个线程内完成，期间不进行线程切换，这样就避免了多线程竞争和同步锁。
为了尽可能提升性能，Netty采用了串行无锁化设计，在IO线程内部进行串行操作，避免多线程竞争导致的性能下降。表面上看，串行化设计似乎CPU利用率不高，并发程度不够。但是，通过调整NIO线程池的线程参数，可以同时启动多个串行化的线程并行运行，这种局部无锁化的串行线程设计相比一个队列-多个工作线程模型性能更优。
Netty的NioEventLoop读取到消息之后，直接调用ChannelPipeline的fireChannelRead(Object msg)，只要用户不主动切换线程，一直会由NioEventLoop调用到用户的Handler，期间不进行线程切换，这种串行化处理方式避免了多线程操作导致的锁的竞争，从性能角度看是最优的。
### 高效的并发编程
Netty的高效并发编程主要体现在如下几点：
1) volatile的大量、正确使用;
2) CAS和原子类的广泛使用；
3) 线程安全容器的使用；
4) 通过读写锁提升并发性能。
### 高性能的序列化框架
影响序列化性能的关键因素总结如下：
1) 序列化后的码流大小（网络带宽的占用）；
2) 序列化&反序列化的性能（CPU资源占用）；
3) 是否支持跨语言（异构系统的对接和开发语言切换）。
Netty默认提供了对Google Protobuf的支持，通过扩展Netty的编解码接口，用户可以实现其它的高性能序列化框架，例如Thrift的压缩二进制编解码框架。
### 灵活的TCP参数配置能力
合理设置TCP参数在某些场景下对于性能的提升可以起到显著的效果，例如SO_RCVBUF和SO_SNDBUF。如果设置不当，对性能的影响是非常大的。下面我们总结下对性能影响比较大的几个配置项：
1) SO_RCVBUF和SO_SNDBUF：通常建议值为128K或者256K；
2) SO_TCPNODELAY：NAGLE算法通过将缓冲区内的小封包自动相连，组成较大的封包，阻止大量小封包的发送阻塞网络，从而提高网络应用效率。但是对于时延敏感的应用场景需要关闭该优化算法；
3) 软中断：如果Linux内核版本支持RPS（2.6.35以上版本），开启RPS后可以实现软中断，提升网络吞吐量。RPS根据数据包的源地址，目的地址以及目的和源端口，计算出一个hash值，然后根据这个hash值来选择软中断运行的cpu，从上层来看，也就是说将每个连接和cpu绑定，并通过这个hash值，来均衡软中断在多个cpu上，提升网络并行处理性能。

epoll(linux), kqueue(freebsd), /dev/poll(solaris) 作为针对select和poll的升级（可以这么理解:)）,主要它们做了两件事情:
#### 避免了每次调用select/poll时kernel分析参数建立事件等待结构的开销，kernel维护一个长期的事件关注列表，应用程序通过句柄修改这个列表和捕获I/O事件。
#### 避免了select/poll返回后，应用程序扫描整个句柄表的开销，Kernel直接返回具体的事件列表给应用程序。

## 8. 为什么linux下epoll最好, Netty要比NIO2.0好 ?
基本的IO编程过程（包括网络IO和文件IO）是，打开文件描述符（windows是handler，java是stream或channel），多路捕获（Multiplexe，即select和poll和epoll）IO可读写的状态，而后可以读写的文件描述符进行IO读写，由于IO设备速度和CPU内存比速度会慢，为了更好的利用CPU和内存，会开多线程，每个线程读写一个文件描述符。
  但C10K问题，让我们意识到在超大数量的网络连接下，机器设备和网络速度不再是瓶颈，瓶颈在于操作系统和IO应用程序的沟通协作的方式。

  举个例子，一万个socket连接过来，传统的IO编程模型要开万个线程来应对，还要注意，socket会关闭打开，一万个线程要不断的关闭线程重建线程，资源都浪费在这上面了，我们算建立一个线程耗1M内存，1万个线程机器至少要10G内存，这在IA-32的机器架构下基本是不可能的（要开PAE），现在x64架构才有可能舒服点，要知道，这仅仅是粗略算的内存消耗。别的资源呢？

  所以，高性能的网络编程（即IO编程），第一，需要松绑IO连接和应用程序线程的对应关系，这就是非阻塞（nonblocking）、异步（asynchronous）的要求的由来（构造一个线程池，epoll监控到有数的fd，把fd传入线程池，由这些worker thread来读写io）。第二，需要高性能的OS对IO设备可读写（数据来了）的通知方式：从level-triggered notification到edge-triggered notification，关于这个通知方式，我们稍后谈。

  需要注意异步，不等于AIO（asynchronous IO），linux的AIO和java的AIO都是实现异步的一种方式，都是渣，这个我们也接下来会谈到。

  针对前面说的这两点，我们看看select和poll的问题
  这两个函数都在每次调用的时候要求我们把需要监控（看看有没有数据）的文件描述符，通过数组传递进入内核，内核每次都要扫描这些文件描述符，去理解它们，建立一个文件描述符和IO对应的数组（实际内核工作会有好点的实现方式，但可以这么理解先），以便IO来的时候，通知这些文件描述符，进而通知到进程里等待的这些select、poll。当有一万个文件描述符要监控的时候呢（一万个网络连接）？这个工作效率是很低的，资源要求却很高。

  我们看epoll

  epoll很巧妙，分为三个函数，第一个函数创建一个session类似的东西，第二函数告诉内核维持这个session，并把属于session内的fd传给内核，第三个函数epoll_wait是真正的监控多个文件描述符函数，只需要告诉内核，我在等待哪个session，而session内的fd，内核早就分析过了，不再在每次epoll调用的时候分析，这就节省了内核大部分工作。这样每次调用epoll，内核不再重新扫描fd数组，因为我们维持了session。

  说道这里，只有一个字，开源，赞，众人拾柴火焰高，赞。

  epoll的效率还不仅仅体现在这里，在内核通知方式上，也改进了，我们先看select和poll的通知方式，也就是level-triggered notification，内核在被DMA中断，捕获到IO设备来数据后，本来只需要查找这个数据属于哪个文件描述符，进而通知线程里等待的函数即可，但是，select和poll要求内核在通知阶段还要继续再扫描一次刚才所建立的内核fd和io对应的那个数组，因为应用程序可能没有真正去读上次通知有数据后的那些fd，应用程序上次没读，内核在这次select和poll调用的时候就得继续通知，这个os和应用程序的沟通方式效率是低下的。只是方便编程而已（可以不去读那个网络io，方正下次会继续通知）。

  于是epoll设计了另外一种通知方式：edge-triggered notification，在这个模式下，io设备来了数据，就只通知这些io设备对应的fd，上次通知过的fd不再通知，内核不再扫描一大堆fd了。

  基于以上分析，我们可以看到epoll是专门针对大网络并发连接下的os和应用沟通协作上的一个设计，在linux下编网络服务器，必然要采用这个，nginx、php的国产异步框架swool、varnish，都是采用这个。

  注意还要打开epoll的edge-triggered notification。而java的NIO和NIO.2都只是用了epoll，没有打开edge-triggered notification，所以不如JBoss的Netty。

  接下来我们谈谈AIO的问题，AIO希望的是，你select，poll，epoll都需要用一个函数去监控一大堆fd，那么我AIO不需要了，你把fd告诉内核，你应用程序无需等待，内核会通过信号等软中断告诉应用程序，数据来了，你直接读了，所以，用了AIO可以废弃select，poll，epoll。

  但linux的AIO的实现方式是内核和应用共享一片内存区域，应用通过检测这个内存区域（避免调用nonblocking的read、write函数来测试是否来数据，因为即便调用nonblocking的read和write由于进程要切换用户态和内核态，仍旧效率不高）来得知fd是否有数据，可是检测内存区域毕竟不是实时的，你需要在线程里构造一个监控内存的循环，设置sleep，总的效率不如epoll这样的实时通知。所以，AIO是渣，适合低并发的IO操作。所以java7引入的NIO.2引入的AIO对高并发的网络IO设计程序来说，也是渣，只有Netty的epoll+edge-triggered notification最牛，能在linux让应用和OS取得最高效率的沟通
# 分布式相关
## 1. Dubbo的底层实现原理和机制
Dubbo是一个分布式服务框架，致力于提供高性能和透明化的RPC远程服务调用方案，以及SOA服务治理方案。

## 2. 描述一个服务从发布到被消费的详细过程
## 3. 分布式系统怎么服务治理?
## 4. 接口幂等性的概念
## 5. 消息中间件如何解决消息丢失的问题
## 6. Dubbo的服务请求失败怎么处理
## 7. 重连机制会不会造成错误
## 8. 对分布式事务的理解
## 9. 如何实现负载均衡? 有哪些算法可以实现?
负载均衡，英文名称为Load Balance，指由多台服务器以对称的方式组成一个服务器集合，每台服务器都具有等价的地位，都可以单独对外提供服务而无须其他服务器的辅助。通过某种负载分担技术，将外部发送来的请求均匀分配到对称结构中的某一台服务器上，而接收到请求的服务器独立地回应客户的请求。负载均衡能够平均分配客户请求到服务器阵列，借此提供快速获取重要数据，解决大量并发访问服务问题，这种集群技术可以用最少的投资获得接近于大型主机的性能。

负载均衡分为软件负载均衡和硬件负载均衡，前者的代表是阿里章文嵩博士研发的LVS，后者则是均衡服务器比如F5，当然这只是提一下，不是重点。
- 轮询法 (Round Robin)
```java
public class RoundRobin
{
    private static Integer pos = 0;
    public static String getServer()
    {
        // 重建一个Map，避免服务器的上下线导致的并发问题
        Map<String, Integer> serverMap = 
                new HashMap<String, Integer>();
        serverMap.putAll(IpMap.serverWeightMap);
        // 取得Ip地址List
        Set<String> keySet = serverMap.keySet();
        ArrayList<String> keyList = new ArrayList<String>();
        keyList.addAll(keySet);
        String server = null;
        synchronized (pos)
        {
            if (pos > keySet.size())
                pos = 0;
            server = keyList.get(pos);
            pos ++;
        }
        return server;
    }
}
```
轮询法的优点在于：试图做到请求转移的绝对均衡。
轮询法的缺点在于：为了做到请求转移的绝对均衡，必须付出相当大的代价，因为为了保证pos变量修改的互斥性，需要引入重量级的悲观锁synchronized，这将会导致该段轮询代码的并发吞吐量发生明显的下降。

- 随机法
通过系统随机函数，根据后端服务器列表的大小值来随机选择其中一台进行访问。由概率统计理论可以得知，随着调用量的增大，其实际效果越来越接近于平均分配流量到每一台后端服务器，也就是轮询的效果。
随机法的代码实现大致如下：
```java
public class Random
{
    public static String getServer()
    {
        // 重建一个Map，避免服务器的上下线导致的并发问题
        Map<String, Integer> serverMap = new HashMap<String, Integer>();
        serverMap.putAll(IpMap.serverWeightMap);
        // 取得Ip地址List
        Set<String> keySet = serverMap.keySet();
        ArrayList<String> keyList = new ArrayList<String>();
        keyList.addAll(keySet);
        java.util.Random random = new java.util.Random();
        int randomPos = random.nextInt(keyList.size());
        return keyList.get(randomPos);
    }
}
```
整体代码思路和轮询法一致，先重建serverMap，再获取到server列表。在选取server的时候，通过Random的nextInt方法取0~keyList.size()区间的一个随机值，从而从服务器列表中随机获取到一台服务器地址进行返回。基于概率统计的理论，吞吐量越大，随机算法的效果越接近于轮询算法的效果。
- 源地址哈希法(hash)
源地址哈希的思想是获取客户端访问的IP地址值，通过哈希函数计算得到一个数值，用该数值对服务器列表的大小进行取模运算，得到的结果便是要访问的服务器的序号。源地址哈希算法的代码实现大致如下：
```java
public class Hash
{
    public static String getServer() {
        // 重建一个Map，避免服务器的上下线导致的并发问题
        Map<String, Integer> serverMap = 
                new HashMap<String, Integer>();
        serverMap.putAll(IpMap.serverWeightMap);
        // 取得Ip地址List
        Set<String> keySet = serverMap.keySet();
        ArrayList<String> keyList = new ArrayList<String>();
        keyList.addAll(keySet);
        // 在Web应用中可通过HttpServlet的getRemoteIp方法获取
        String remoteIp = "127.0.0.1";
        int hashCode = remoteIp.hashCode();
        int serverListSize = keyList.size();
        int serverPos = hashCode % serverListSize;
        return keyList.get(serverPos);
    }
}
```
源地址哈希法的优点在于：保证了相同客户端IP地址将会被哈希到同一台后端服务器，直到后端服务器列表变更。根据此特性可以在服务消费者与服务提供者之间建立有状态的session会话。
源地址哈希算法的缺点在于：除非集群中服务器的非常稳定，基本不会上下线，否则一旦有服务器上线、下线，那么通过源地址哈希算法路由到的服务器是服务器上线、下线前路由到的服务器的概率非常低，如果是session则取不到session，如果是缓存则可能引发"雪崩"。

- 加权轮询法(Weight Round Robin)
## 10. Zookeeper的用途, 选举的原理是什么?
## 11. 数据的垂直拆分和水平拆分
## 12. Zookeeper的原理和适用场景
## 13. Zookeeper watch机制
## 14. redis/zk节点宕机如何处理
## 15. 分布式集群下如何做到唯一序列号
## 16. 如何做一个分布式锁
## 17. 用过哪些MQ, 怎么用的, 和其他MQ比较有什么优缺点, MQ的连接是线程安全的吗?
## 18. MQ系统的数据如何保证不丢失?
## 19. 列举出你能想到的数据库分库分表策略, 分库分表后, 如何解决全表查询问题
## 20. Zookeeper的选举策略
## 21. 全局ID

# 数据库
## 1. MySql分页有哪些优化?
1) 当使用limit加上偏移量进行分页查询时, 要尽可能使用索引覆盖扫描. 
2) 有时候可以将LIMIT查询转换为已知位置的查询, 让MySQL通过范围扫描获得相应的结果. 例如如果在一个位置列上有索引, 并且预先计算出了边界值, 上面的查询就可以改写为:
```SQL
select film_id, description from sakila.film
where position between 50 and 54 order by position;
```
3) 对数据进行排名的问题也与此类似, 但往往还会同时和GROUP BY混合使用. 在这种情况下通常都需要先计算并存储排名信息. LIMIT和OFFSET的问题, 其实是OFFSET的问题, 它会导致MySQL扫描大量不需要的行, 然后再抛弃. 如果可以使用书签记录上次取数据的位置. 那么下次就可以直接从该书签记录的位置开始扫描, 这样就可以避免使用OFFSET.
4) 另一个常用的技巧是在LIMIT语句中加上SQL_CALC_FOUND_ROWS提示(hint), 这样就可以获得去掉LIMIT以后满足条件的行数, 因此可以作为分页的总数. 加上这个提示以后, 不管是否需要, MySQL都会扫描所有满足条件的行, 然后再抛弃掉不需要的行, 而不是在满足LIMIT的行数后就终止扫描.
在很多分页的程序中都这样写
```sql
SELECT COUNT(*) from `table` WHERE ......;  查出符合条件的记录总数
SELECT * FROM `table` WHERE ...... limit M,N; 查询当页要显示的数据
```sql
这样的语句可以改成:
```sql
SELECT SQL_CALC_FOUND_ROWS * FROM `table` WHERE ......  limit M, N;
SELECT FOUND_ROWS();
```
5) 加缓存, 在缓存中进行分页. 
6) 增加下一页按钮, 假设每页显示20条, 那么每次查询时都是用LIMIT返回21条记录并只显示20条, 如果21条存在, 那么我们就显示"下一条"按钮, 否则则说明没有更多的数据, 也就无须显示下一页按钮了.

## 2. 悲观锁, 乐观锁

悲观锁: 
认为不做正确的事, 结果就不正确.
与乐观锁相对应的就桑悲观锁了, 悲观锁就是在操作数据时, 认为此操作会出现数据冲突, 所以进行每次操作的时候都要通过获取锁才能进行相同数据的操作, 这点跟java中的synchronized很相似, 所以悲观锁需要耗费较多的时间, 另外与乐观锁相对应的, 悲观锁是由数据库自己实现的, 要用的时候, 我们直接调用数据库的相关语句就可以了.
共享锁和排它锁都是悲观锁的不同实现, 都属于悲观锁的范畴.
共享锁指的是对于多个不同的事务, 对同一资源共享同一个锁, 相当于对于同一把门, 它拥有多个钥匙一样.在执行语句的后面加上lock in share mode就代表对某些资源加上共享锁了.

排他锁与共享锁相对应, 就是指多个不同事务, 对同一个资源只能有一把锁.
与共享锁类型, 在需要执行的语句后面加上for update就可以了.

乐观锁:
乐观锁不是数据库自带的, 需要我们自己去实现. 乐观锁是指在操作数据库时, 想法很乐观, 认为这次操作不会产生冲突, 在操作数据时, 并不进行其他的特殊处理也就是不加锁, 在进行更新后, 再去判断是否有冲突.
通常实现是这样的: 在表中的数据进行操作时(更新), 先给数据表加一个版本(version)字段, 没操作一次, 将那条记录的版本号加1, 也就是先查询出这条记录, 获取出version字段, 如果要对那条记录进行操作, 则先判断此刻version的值是否与刚刚查询出来的version的值相等, 如果相等, 则说明这段时间, 没有其他程序对其进行操作, 则可以执行更新, 将version字段值加1, 如果更新时发现此刻的version值与刚刚获取出来的verion的值不相等, 则说明这段期间已经有其他程序对其进行操作了, 则不进行更新操作.
## 3. 组合索引, 最左原则
单列索引: 一个索引只包含单个列, 一个表可以有多个单列索引, 但这不是组合索引
组合索引: 即一个索引包含多个列

如果我们的查询where条件只有一个, 我们完全可以用单列索引, 这样的查询速度较快, 索引也比较瘦身. 如果我们的业务场景是需要经常查询多个组合列, 不要试图分别基于单个列建立多个单列索引(因为虽然有多个单列索引, 但是MySQL只能用到其中的那个它认为似乎最有效率的单列索引). 这是因为当SQL语句所查询的列, 全部都出现在复合索引中时, 此时由于只需要查询索引块即可获得所有数据, 当然比使用多个单列索引要快得多.
```sql
CREATE TABLE people ( peopleid SMALLINT NOT NULL AUTO_INCREMENT, firstname CHAR(50)　NOT NULL, lastname CHAR(50) NOT NULL, age SMALLINT NOT NULL, townid SMALLINT NOT　NULL, PRIMARY KEY (peopleid) );
//建立多列索引
ALTER TABLE people ADD INDEX fname_lname_age (firstname,lastname,age);
```
由于索引文件以B+树格式保存, MySQL能够立即转到合适的firstname, 然后再转到lastname, 最后转到合适的age, 在没有扫描数据文件任何一个记录的情况下, MySQL就正确地找到了搜索的目标记录.
如果你有三个单列的索引，MySQL会试图选择一个限制最严格的索引。但是，即使是限制最严格的单列索引，它的限制能力也肯定远远低于firstname、lastname、age这三个列上的多列索引。

继续考虑前面的例子, 现在我们有一个firstname, lastname, age列上的多列索引, 我们称这个索引为fname_lname_age. 它相当于我们创建了(firstname, lastname, age), (firstname, lastname) 以及
(firstname) 这些组合上的索引. 为什么没有(lastname, age)等这样的组合索引呢? 这是因为mysql组合索引"最左前缀"(Leftmost Prefixing)的结果. 简单的理解就是只从最左面的开始组合.

注：在创建多列索引时，要根据业务需求，where子句中使用最频繁的一列放在最左边。
## 4. mysql的表锁, 行锁
### 表锁

### InnoDB实现了以下两种类型的行锁。
共享锁（S）：允许一个事务去读一行，阻止其他事务获得相同数据集的排他锁。
排他锁（X）：允许获取排他锁的事务更新数据，阻止其他事务取得相同的数据集共享读锁和排他写锁。
另外，为了允许行锁和表锁共存，实现多粒度锁机制，InnoDB还有两种内部使用的意向锁（Intention Locks），这两种意向锁都是表锁。
意向共享锁（IS）：事务打算给数据行加共享锁，事务在给一个数据行加共享锁前必须先取得该表的IS锁。
意向排他锁（IX）：事务打算给数据行加排他锁，事务在给一个数据行加排他锁前必须先取得该表的IX锁。

当前锁模式/是否兼容/请求锁模式      X       IX      S       IS
          X                     冲突     冲突    冲突     冲突
          IX                    冲突     兼容    冲突     兼容
          S                     冲突     冲突    兼容     兼容
          IS                    冲突     兼容    兼容     兼容

如果一个事务请求的锁模式与当前的锁兼容，InnoDB就请求的锁授予该事务；反之，如果两者两者不兼容，该事务就要等待锁释放。
意向锁是InnoDB自动加的，不需用户干预。对于UPDATE、DELETE和INSERT语句，InnoDB会自动给涉及及数据集加排他锁（X）；对于普通SELECT语句，InnoDB不会任何锁；事务可以通过以下语句显示给记录集加共享锁或排锁。
共享锁（S）：SELECT * FROM table_name WHERE ... LOCK IN SHARE MODE
排他锁（X）：SELECT * FROM table_name WHERE ... FOR UPDATE
用SELECT .. IN SHARE MODE获得共享锁，主要用在需要数据依存关系时确认某行记录是否存在，并确保没有人对这个记录进行UPDATE或者DELETE操作。但是如果当前事务也需要对该记录进行更新操作，则很有可能造成死锁，对于锁定行记录后需要进行更新操作的应用，应该使用SELECT ... FOR UPDATE方式获取排他锁。
### InnoDB行锁实现方式
InnoDB行锁是通过索引上的索引项来实现的，这一点MySQL与Oracle不同，后者是通过在数据中对相应数据行加锁来实现的。InnoDB这种行锁实现特点意味者：只有通过索引条件检索数据，InnoDB才会使用行级锁，否则，InnoDB将使用表锁！
在实际应用中，要特别注意InnoDB行锁的这一特性，不然的话，可能导致大量的锁冲突，从而影响并发性能。

间隙锁（Next-Key锁）
当我们用范围条件而不是相等条件检索数据，并请求共享或排他锁时，InnoDB会给符合条件的已有数据的索引项加锁；对于键值在条件范围内但并不存在的记录，叫做“间隙(GAP)”，InnoDB也会对这个“间隙”加锁，这种锁机制不是所谓的间隙锁（Next-Key锁）。
举例来说，假如emp表中只有101条记录，其empid的值分别是1,2,...,100,101，下面的SQL：
```sql
SELECT * FROM emp WHERE empid > 100 FOR UPDATE
```
是一个范围条件的检索，InnoDB不仅会对符合条件的empid值为101的记录加锁，也会对empid大于101（这些记录并不存在）的“间隙”加锁。
InnoDB使用间隙锁的目的，一方面是为了防止幻读，以满足相关隔离级别的要求，对于上面的例子，要是不使用间隙锁，如果其他事务插入了empid大于100的任何记录，那么本事务如果再次执行上述语句，就会发生幻读；另一方面，是为了满足其恢复和复制的需要。有关其恢复和复制对机制的影响，以及不同隔离级别下InnoDB使用间隙锁的情况。
很显然，在使用范围条件检索并锁定记录时，InnoDB这种加锁机制会阻塞符合条件范围内键值的并发插入，这往往会造成严重的锁等待。因此，在实际开发中，尤其是并发插入比较多的应用，我们要尽量优化业务逻辑，尽量使用相等条件来访问更新数据，避免使用范围条件。
## 5. mysql性能优化
## 6. mysql的索引分类: B+, hash; 什么情况下用什么索引?
https://tech.meituan.com/mysql-index.html
### 索引目的
索引的目的在于提高查询效率, 可以类比字典, 如果要查"mysql"这个单词, 我们肯定需要定位到m字母, 然后从上忘下找到y字母, 再找到剩下的sql. 如果没有索引, 那么你可能需要把所有单词看一遍才能找到你想要的, 如果我想找到m开头的单词呢? 或者ze开头的单词呢? 是不是觉得如果没有索引, 这个事情根本无法完成?
### 索引原理
除了词典, 生活随处可见索引的例子, 如果火车站的车次表, 图书的目录等. 它们的原理都是一样的通过不断的缩小想要获得数据的范围来筛选出最终想要的结果, 同时把随机的事件变成顺序的事件, 也就是我们总是通过同一种查找方式来锁定数据.
数据库也是一样, 但显然要复杂许多, 因为不仅面临着等值查询, 还有范围查询(<, >, between, in), 模糊查询(like), 并集查询(or)等等. 数据库应该选择怎么样的方式来应对所有的问题呢? 我们回想字典的例子, 能不能把数据分成段, 然后分段查询呢? 最简单的如果1000条数据, 1-100分成第一段, 101-200分成第二段, 201-300分成第三段...这样查第250条数据, 只要找第三段就可以了, 一下子去除了90%的无效数据. 但如果是1000万的记录呢, 分成极端比较好? 稍有算法基础的同学都会想到搜索树, 其平均复杂度为O(logN), 具备不错的查询性能. 但这里我们忽略了一个关键问题, 复杂度模型是基于每次相同的操作成本来考虑的, 数据库的实现比较复杂, 数据保存在磁盘上, 而为了提高性能, 每次又可以把部分的数据读入内存来计算, 因为我们知道访问磁盘的成本大概是访问内存的十万倍左右, 所以简单的搜索树难以满足复杂的应用场景.
### 磁盘i/o与预读
前面提到了访问磁盘, 那么这里先简单介绍一下磁盘I/O和预读, 磁盘读取数据靠的是机械运动, 每次读取数据花费的时间可以分为寻道时间, 旋转延迟, 传输时间三个部分, 寻道时间指的是磁臂移动到指定磁道所需要的时间, 主流磁盘一般在5ms以下; 旋转延迟就是我们经常说的磁盘转速, 比如一个磁盘7200转, 表示每分钟能转7200次, 也就是说1秒钟能转120次, 旋转延迟就是1/120/2=4.17ms; 传输时间指的是从磁盘读出或将数据写入磁盘的时间, 即一次磁盘I/O的时间约等于5+4.17=9ms左右, 听起来还挺不错的, 但要知道一台500-MIPS的机器每秒可以执行5亿条指令, 因为指令依靠的是电的性质, 换句话说执行一次IO的时间可以执行40万条指令, 数据库动辄十万百万乃至千万级的数据, 每次9毫秒的时间显然是个灾难.
考虑到磁盘I/O是非常高昂的操作, 计算机操作系统做了一些优化, 当一次I/O时, 不光把当前磁盘地址的数据, 而且把相邻的数据也都读取到内存缓冲区, 因为局部预读性原理告诉我们, 当计算机访问一个地址的数据的时候, 与其相邻的数据也会很快被访问, 每一次IO读取的数据我们称之为一页. 具体一页有多大数据跟操作系统有关, 一般为4k或8k, 也就是我们读取一页内的数据的时候, 实际上才发生了一次IO, 这个理论对于索引的数据结构设计非常有帮助.
### 索引的数据结构
前面讲了色生活中索引的例子, 索引的基本原理, 数据库的复杂性, 又讲了操作系统的相关知识, 目的就是让大家了解, 任何一种数据结构都不是凭空产生的, 一定会有他的背景和使用场景, 我们现在总结一下, 我们需要这种数据结构能够做些什么, 其实很简单, 那就是每次查找数据时, 把磁盘I/O次数控制在一个很小的数量级, 最好是常数数量级, 那么我们就想到如果一个高度可控的多路搜索树是否能满足需求呢?这样, b+树就应运而生.
![b+树](btree.jpg)
如上图, 是一颗b+树, 关于b+树的定义可以参见B+树(http://zh.wikipedia.org/wiki/B%2B%E6%A0%91), 这里只说一些重点, 浅蓝色的快我们称之为一个磁盘快, 可以看到每次磁盘块包含几个数据项(深蓝色所示)和指针(黄色所示), 如磁盘块1包含数据项17和35, 包含指针P1, P2, P3; P1表示小于17的磁盘块, P2表示在17和35之间的磁盘块, P3表示大于35的磁盘块. 真实的数据存在于叶子节点即3,5,9,10,13,14,28,29,36,60,75,79,90,99. 非叶子节点不存储真实的数据, 只存储指引搜索方向的数据项, 如17, 35并不真实存在于数据表中.
### B-Tree索引适用于全键值, 键值范围或键前缀查找. 其中键前缀查找只适用于根据左前缀的查找.
全值匹配: 全值匹配指的是和索引中的所有列进行匹配
匹配最左前缀
匹配列前缀: 可以只匹配某一列的值的开头部分
匹配范围值
精准匹配某一列并范围匹配另外一列

### 哈希索引
哈希索引基于哈希表实现, 只有精确匹配索引所有列的查询才有效. 对于每一行数据, 存储引擎都会对所有的索引列计算出一个哈希码, 哈希码是一个较小的值, 并且不同的键值的行计算出来的哈希码不一样, 哈希索引将所有的哈希码存储在索引中, 同时在哈希表中保存指向每个数据行的指针.
在MySQL中, 只有Memory引擎显式支持哈希索引, 同时支持唯一和非唯一哈希索引.
NDB集群引擎也支持唯一哈希索引.
InnoDB引擎有一个特殊的功能叫做"自适应哈希索引"(adaptive hash index). 当InnoDB注意到某些索引值被使用得非常频繁时, 它会在内存中基于B-Tree索引之上再创建一个哈希索引. 这样就让B-Tree索引也具有哈希索引的一些优点, 比如快速的哈希查找. 这是一个完全自动的,内部的行为. 用户无法控制或者配置,不过如果有必要, 完全可以关闭改功能.
### 空间数据索引(R-Tree)
### 全文索引(FULLTEXT)
适用于MATCH AGAINST操作, 它查找的是文本中的关键词而不是直接比较索引中的值.
## 7. 事务的特性和隔离级别
ACID
Atomicity 原子性
Consistency 一致性
Isolation 隔离性
Durability 持久性
- 原子性:
事务中的所有操作要么全部执行, 要么都不执行; 如果事务没有原子性的保证, 那么在发生系统故障情况下, 数据库就有可能处于不一致状态.
- 一致性
主要强调的是, 如果在执行事务之前数据库时一致的, 那么在执行事务之后数据库也还是一致的. 所谓一致性简单地说就是数据库中数据的完整性, 包括他们的正确性.
- 隔离性
即使多个事务并发执行, 每个事务都感觉不到系统中有其他的事务在执行, 因而也就能保证数据库的一致性.
- 持久性
事务成功执行后它对数据库的修改是永久的, 即使系统出现故障也不受影响. 持久性的含义是说, 一旦事务成功执行之后, 它对数据库的更新时永久的. 
## 8. Innodb中的事务隔离级别和锁的关系
数据库遵循的是两段锁协议, 将事务分成两个阶段, 加锁阶段和解锁阶段(所以叫两段锁)
- 加锁阶段: 在该阶段可以进行加锁操作. 在对任何数据进行读操作之前要申请并获得S锁(共享锁, 其他事务可以继续加共享锁, 但不能加排它锁), 在进行写操作之前要申请并获得X锁(排它锁, 其他事物不能再获得任何锁). 加锁不成功, 则事务进入等待状态, 直到加锁成功才继续执行.
- 解锁阶段: 当事务释放了一个封锁之后, 事务进入解锁阶段, 在该阶段只能进行解锁操作不能再进行加锁操作.
|事务                     |               加锁/解锁处理     |
|------------------------:|-------------------------------:|
|begin                    |                                |
|insert into test ......  |             加insert对应的锁    |
|update test set ......   |             加update对应的锁    |
|delete from test ......  |             加delete对应的锁    |
|commit;                  |   事务提交时，同时释放insert、update、delete对应的锁|

这种方式虽然无法避免死锁, 但是两段锁协议可以保证事务的并发调度是串行化的(串行化很重要, 尤其是在数据恢复和备份的时候).
### 数据库的读现象
- 脏读
脏读又称无效数据的读出，是指在数据库访问中，事务T1将某一值修改，然后事务T2读取该值，此后T1因为某种原因撤销对该值的修改，这就导致了T2所读取到的数据是无效的。
脏读就是指当一个事务正在访问数据，并且对数据进行了修改，而这种修改还没有提交(commit)到数据库中，这时，另外一个事务也访问这个数据，然后使用了这个数据。因为这个数据是还没有提交的数据，那么另外一个事务读到的这个数据是脏数据，依据脏数据所做的操作可能是不正确的。
- 不可重复读
不可重复读，是指在数据库访问中，一个事务范围内两个相同的查询却返回了不同数据。这是由于查询时系统中其他事务修改的提交而引起的。比如事务T1读取某一数据，事务T2读取并修改了该数据，T1为了对读取值进行检验而再次读取该数据，便得到了不同的结果。
一种更易理解的说法是：在一个事务内，多次读同一个数据。在这个事务还没有结束时，另一个事务也访问该同一数据。那么，在第一个事务的两次读数据之间。由于第二个事务的修改，那么第一个事务读到的数据可能不一样，这样就发生了在一个事务内两次读到的数据是不一样的，因此称为不可重复读，即原始读取不可重复。
- 幻读
幻读是指当事务不是独立执行时发生的一种现象，例如第一个事务对一个表中的数据进行了修改，比如这种修改涉及到表中的“全部数据行”。同时，第二个事务也修改这个表中的数据，这种修改是向表中插入“一行新数据”。那么，以后就会发生操作第一个事务的用户发现表中还有没有修改的数据行，就好象发生了幻觉一样.一般解决幻读的方法是增加范围锁RangeS，锁定检锁范围为只读，这样就避免了幻读。
幻读(phantom read)"是不可重复读(Non-repeatable reads)的一种特殊场景：当事务没有获取范围锁的情况下执行SELECT … WHERE操作可能会发生"幻读(phantom read)。

- 解决方案
要想解决脏读, 不可重复读, 幻读等读现象, 那么就需要提高事务的隔离级别. 但与此同时, 事务的隔离级别越高, 并发能力也就越低. 所以, 还需要读者根据业务需要进行权衡.

### 事务的四种隔离级别
https://www.jianshu.com/p/296116ccd603?utm_campaign=maleskine&utm_content=note&utm_medium=seo_notes&utm_source=recommendation
隔离级别      脏读（Dirty Read）  不可重复读（NonRepeatable Read） 幻读（Phantom Read）
未提交读（Read uncommitted）    可能    可能    可能
已提交读（Read committed）      不可能  可能    可能
可重复读（Repeatable read）     不可能  不可能  可能
可串行化（Serializable ）       不可能  不可能  不可能

- 未提交读(Read Uncommitted): 允许脏读, 也就是读取到其他会话中未提交事务修改的数据.
- 提交读(Read Committed): 只能读取到已经提交的数据. Oracle等多数数据库默认都是该级别(不重复读)
- 可重复读(Repeated Read): 可重复读. 在同一个事务内的查询都是与事务开始时刻一致的, InnoDB默认级别. 在SQL标准中, 该隔离级别消除了不可重复读, 但还存在幻象读.
- 串行读(Serializable): 完全串行化的读, 每次读都需要获得表级共享锁, 读写相互都会阻塞
# 缓存
## 1. Redis用过哪些数据结构, 以及Redis底层是怎么实现的?
#### String 字符串
Redis中字符串是由redis自己构建的一种名为简单动态字符串(simple dynamic string, SDS)的抽象类型来表示的,
并将SDS用作Redis的默认字符串表示.
```java
struct sdshdr { 
    // 记录buf数组中已使用字节的数量
    // 等于SDS中所保存字符串的长度
    int len;

    // 记录buf数组中未使用字节的数量
    int free;

    // 字节数组, 用于保存字符串
    char buf[];
}
```
#### List 列表
redis 构建了自己的链表实现
```C++
typedef struct listNode {
    // 前置节点
    struct listNode * prev;

    // 后置节点
    struct listNode * next;

    // 节点的值
    void * value;
} listNode
```
Redis里的链表并没有什么特别需要说明的地方，和其他语言中的链表类似，定义了链表节点listNode结构，包含
prev(listNode)属性，next(listNode)属性，value属性的结构，同时使用list来持有链表，list的结构包含
head(listNode)属性，tail(listNode)属性，len(long)属性，还有一些方法，如复制，释放，对比函数

#### Hash 哈希表

字典，又称为符号表，关联数组，或者映射，是一种用于保存键值对的抽象数据结构。可以说Redis里所有的结构
都是用字典来存储的。那么字典是如何来使先的呢？字典的结构从高层到底层实现分别是：字典（dict），字典哈
希表（dictht），哈希表节点（dictEntry）。我们先来看看字典哈希表和哈希表节点
```C++
typedef struct dictht {
    //哈希表数组
    dictEntry **table;
    //哈希表大小
    unsigned long size;
    //哈希表大小掩码
    //总是等于size-1
    //用于计算索引值
    unsigned long sizemask;
    //该哈希表已有的节点的数量
    unsigned long used;
} dictht
```
注释已经很好的解释了每个变量的含义，下面我们来看看dictEntry的结构类型，其中key表示键的指针，v表示值，
这个值可以是一个指针val，也可以是无符号整数或者有符号整数。
#### Set 集合
#### SortedSet 有序集合




## 2. Redis缓存穿透, 缓存雪崩

### 缓存雪崩
缓存雪崩是由于原有的缓存失效（过期），新缓存未到期间。所有请求都去查询数据库，而对数据库cpu和内存造成巨大压力，
严重的会造成数据库宕机。从而形成一系列连锁反应，造成整个系统崩溃。

① 碰到这种情况，一般并发量不是特别多的时候，使用最多的解决方案是加锁排队

② 加锁排队只是为了减轻数据库的压力，并没有提高系统吞吐量。假设在高并发下，缓存重建期间key是锁着的，这是过来
1000个请求999个都在阻塞的。同样会导致用户等待超时，这是个治标不治本的方法。
  还有一个解决办法解决方案是：给每一个缓存数据增加相应的缓存标记，记录缓存的是否失效，如果缓存标记失效，则更新
数据缓存。

缓存标记：记录缓存数据是否过期，如果过期会触发通知另外的线程在后台去更新实际key的缓存。
缓存数据：它的过期时间比缓存标记的时间延长1倍，例：标记缓存时间30分钟，数据缓存设置为60分钟。 这样，当缓存标记key
过期后，实际缓存还能把旧数据返回给调用端，直到另外的线程在后台更新完成后，才会返回新缓存。
这样做后，就可以一定程度上提高系统吞吐量。

### 缓存穿透
缓存穿透是指用户查询数据，在数据库没有，自然在缓存中也不会有。这样就导致用户查询的时候，在缓存中找不到，
每次都要去数据库查询一遍，然后返回空。这样请求就绕过直接查数据库，这也是经常提的缓存命中率问题。
解决的办法就是：如果查询数据库为空，直接设置一个默认值存到缓存，这样第二次到缓冲中获取就有值了。而不会
继续访问数据库，这种办法最简单粗暴。
把空结果，也给缓存起来，这样下次同样的请求就可以直接返回空了，即可以避免当查询的值为空时引起的缓存穿透。
同时也可以单独设置个缓存区域存储空值，对要查询的key进行预先校验，然后再放行给后面的正常缓存处理逻辑

### 缓存预热
缓存预热就是系统上线后，将相关的缓存数据直接加载到缓存系统。这样避免用户请求的时候，再去加载相关的数据。
解决思路：
① 直接写个缓存刷新页面，上线时手动操作下。
② 数据量不大，可以在web系统启动的时候加载。
③ 定时刷新缓存。

## 3. 如何使用Redis来实现分布式锁?

使用分布式锁要满足的几个条件？
① 系统是一个分布式系统（关键是分布式，单机的可以使用ReentrantLock或者synchronized代码块来实现）。
② 共享资源（各个系统访问同一资源，资源的载体可能是传统关系型数据库或者NoSQL）。
③ 同步访问（即有多个进程同时访问同一个共享资源。没有同步访问，谁管你资源竞争不竞争）。
应用场景：
```java
long N=0L;
//N从redis获取值
if(N<5){
    N++；
    //N写回redis
}
```
应用场景很常见，像秒杀，全局递增id，ip访问限制等。以IP访问限制来说，恶意攻击者可能发起无限次访问，并发量
比较大，分布式环境下对N的边界检查就不可靠，因为从redis读的N可能已经是脏数据。传统的加锁做法也没用，因为这是
分布式环境，这个同步问题的救火队员也束手无策。
分布式锁可以基于很多种方式实现，比如zookeeper，redis等。不管哪种方式，他的基本原理是不变的：用一个状态值表示
锁，对锁的占用和释放通过状态值来标识。

使用redis的setNX命令实现分布式锁
① 实现的原理
redis为单进程单线程模式，采用队列模式将并发访问变成串行访问，且多客户端对redis的连接并不存在竞争关系。redis
的setNX命令可以方便的实现分布式锁。
② 基本命令解析
setNX(SET if Not exists)
    语法：SETNX key value
        将key的值设为value，当且仅当key不存在。
        若给定的key已经存在，则setNX不做任何动作。
        SETNX是【SET if Not exists】（如果不存在，则SET）的简写。
    返回值：
    　　设置成功，返回 1 。
    　　设置失败，返回 0 。
    所以我们使用执行下面的命令
        SETNX lock.foo <current Unix time + lock timeout + 1>
        如返回1，则该客户端获得锁，把lock.foo的键值设置为时间值表示该键已被锁定，该客户端最后可以通过DEL lock.foo来释放该锁。
        如返回0，表明该锁已被其他客户端取得，这时我们可以先返回或进行重试等对方完成或等待锁超时。

getSET
    语法：GETSET key value
        将给定的key的值设为value，并返回key的旧值（old value）。
        当key存在但不是字符串类型时，返回一个错误。
    返回值：
        返回给定key的旧值
        当key没有旧值时，也即是，key不存在时，返回nil。

get
    语法: GET key
    返回值：
        当key不存在时，返回nil，否则，返回key的值。
        如果key不是字符串类型，那么返回错误。

解决死锁
上面的锁定逻辑有一个问题：如果一个持有锁的客户端失败或崩溃了不能释放锁，该怎么解决？
我们可以通过锁的键对应的时间戳来判断这种情况是否发生了，如果当前的时间已经大于lock.foo的值，说明
锁已失效，可以被重新使用。
发生这种情况时，不能通过简单的DEL来删除锁，然后再SETNX一次，当多个客户端检测到超时后都会尝试去释放它，
这里可能出现一个竞态条件。
为避免这种情况，客户端应该这样：
C3发送SETNX lock.foo 想要获得锁，由于C0还持有锁，所以Redis返回给C3一个0
C3发送GET lock.foo 以检查锁是否超时了，如果没超时，则等待或重试。
反之，如果已超时，C3通过下面的操作来尝试获得锁：
GETSET lock.foo <current Unix time + lock timeout + 1>
通过GETSET，C3拿到的时间戳如果仍然是超时的，那就说明，C3如愿以偿拿到锁了。
如果在C3之前，有个叫C4的客户端比C3快一步执行了上面的操作，那么C3拿到的时间戳是个未超时的值，这时，
C3没有如期获得锁，需要再次等待或重试。留意一下，尽管C3没拿到锁，但它改写了C4设置的锁的超时值，不过
这一点非常微小的误差带来的影响可以忽略不计。

注意：为了让分布式锁的算法更稳键些，持有锁的客户端在解锁之前应该再检查一次自己的锁是否已经超时，再去做DEL操作，
因为可能客户端因为某个耗时的操作而挂起，操作完的时候锁因为超时已经被别人获得，这时就不必解锁了。

## 4. Redis的并发竞争问题是如何解决的?

redis的并发竞争问题, 主要发生在并发写竞争.

使用乐观锁解决,成本较低, 非阻塞, 性能较高
本质上是假设不会进行冲突, 使用redis的命令watch进行构造条件. 伪代码:
```sh
watch price
get price $price
$price = $price + 10
multi
set price $price
exec
```
watch这里表示监控该key值，后面的事务是有条件的执行，如果从watch的exec语句执行时，watch的key对应的value值被修改了，
则事务不会执行。

大量并发请求时, 可以使用优先队列, 依次进行操作.

## 5. Redis的持久化的几种方式, 优缺点是什么, 是怎么实现的?

Redis提供了两种方式对数据进行持久化方式, 分别是RDB和AOF.
RDB持久化方式能够在指定的时间间隔能对你的数据进行快照存储.
AOF持久化方式记录每次对服务器写的操作, 当服务器重启的时候会重新执行这些命令来回复原始的数据, AOF命令以redis
协议追加保存每次写的操作到文件末尾. Redis还能对AOF文件进行后台重写, 使得AOF文件的体积不至于过大. 
如果同时开启两种持久化方式, 在这种情况下, 当redis重启的时候会优先载入AOF文件来恢复原始的数据, 因为在通常情况
下AOF文件保存的数据集要比RDB文件保存的数据集要完整.
## 6. Redis的缓存失效策略
## 7. Redis的集群, 高可用, 原理
### 高可用
高可用（High Availability），是当一台服务器停止服务后，对于业务及用户毫无影响。 停止服务的原因可能由于网卡、路由器、机房、CPU负载过高、内存溢出、自然灾害等不可预期的原因导致，在很多时候也称单点问题。
### 如何容灾?
redis提供了主从热备机制，主服务器的数据同步到从服务器，通过哨兵实时监控主服务器状态并负责选举主服务器。当发现主服务器异常时根据一定的算法重新选举主服务器并将问题服务器从可用列表中去除，最后通知客户端.
### Sentinel 哨兵模式
Sentinel 是 Redis的高可用解决方案: 由一个或多个Sentinel实例组成Sentinel系统可以监视任意多个主服务器, 以及这些主服务器的下属的所有从服务器, 并在监视的主服务器进入下线状态时, 自动将下线主服务器下属的某个从服务器升级为新的主服务器, 然后由新的主服务器代替已下线的主服务器继续处理命令请求


## 8. Redis缓存分片
Redis 集群键分布算法使用数据分片（sharding）而非一致性哈希（consistency hashing）来实现： 一个 Redis 集群包含 16384 个哈希槽（hash slot）， 它们的编号为0、1、2、3……16382、16383，这个槽是一个逻辑意义上的槽，实际上并不存在。redis中的每个key都属于这 16384 个哈希槽的其中一个，存取key时都要进行key->slot的映射计算。

HASH_SLOT(key)= CRC16(key) % 16384

Redis中的分片类似于MySQL的分表操作, 分片是利用将数据划分为多个部分的方法, 对数据的划分可以基于键包含的ID, 基于键的哈希值, 
或者基于以上两者的某种组合, 通过对数据进行分片, 用户可以将数据存储到多台机器里面, 也可以从多台机器里面获取数据, 这种方法在
解决某些问题时可以获得线性级别的性能提升.

假设有4个Redis实例R0, R1, R2, R3, 还有很多表示用户的键, user: 1, user: 2...等等, 有不同的方式来选择一个指定的键存储在哪
个实例中. 最简单的方式是范围分片, 例如用户id 从0-1000的存储到实例R0中, 用户id从 1001 - 2000的存储在实例R1中, 等等. 但是
这样需要维护一张映射范围表, 维护操作代价很高. 还有一种方式哈希分片, 使用CRC32哈希函数将键转换为一个数字, 在对实例数量求模就
能知道应该存储的实例.

### 客户端分片
客户端使用一致性哈希算法决定键应该分布到哪个节点.

### 代理分片
将客户端请求发送到代理上, 由代理转发请求到正确的节点上.

### 服务器分片
Redis Cluster


## 9. Redis的数据淘汰策略

Redis作为一个高性能的内存NoSQL数据库，其容量受到最大内存限制的限制。
用户在使用阿里云Redis时，除了对性能，稳定性有很高的要求外，对内存占用也比较敏感。
在使用过程中，有些用户会觉得自己的线上实例内存占用比自己预想的要大。事实上，实例中的内存除了保存
原始的键值对所需的开销外，还有一些运行时产生的额外内存，包括：
① 垃圾数据和过期Key所占空间
② 字典渐进式Rehash导致未及时删除的空间
③ Redis管理数据，包括底层数据结构开销，客户端信息，读写缓冲区等
④ 主从复制，bgsave时的额外开销
⑤ 其它
### Redis过期数据清理策略
#### 过期数据清理时机
为了防止一次性清理大量过期Key导致Redis服务受影响，Redis只在空闲时清理过期Key。
具体Redis逐出过期Key的时机为:

① 访问Key时，会判断Key是否过期，逐出过期Key;
```java
robj *lookupKeyRead(redisDb *db, robj *key) {
    robj *val;
    expireIfNeeded(db,key);
    val = lookupKey(db,key);
    ...
    return val;
}
```

② CPU空闲时在定期serverCron任务中，逐出部分过期Key;
```java
    aeCreateTimeEvent(server.el, 1, serverCron, NULL, NULL)

    int serverCron(struct aeEventLoop *eventLoop, long long id, void *clientData) {
        ...
        databasesCron();
        ...
    }

    void databasesCron(void) {
        /* Expire keys by random sampling. Not required for slaves
            + as master will synthesize DELs for us. */
        if (server.active_expire_enabled && server.masterhost == NULL)
            activeExpireCycle(ACTIVE_EXPIRE_CYCLE_SLOW);
            ...
    }
```

③ 每次事件循环执行的时候，逐出部分过期Key;
```java
    void aeMain(aeEventLoop *eventLoop) {
        eventLoop->stop = 0;
        while (!eventLoop->stop) {
            if (eventLoop->beforesleep != NULL)
                eventLoop->beforesleep(eventLoop);
            aeProcessEvents(eventLoop, AE_ALL_EVENTS);
        }
    }
```
```java
    void beforeSleep(struct aeEventLoop *eventLoop) {
        /* Run a fast expire cycle (the called function will return
         - ASAP if a fast cycle is not needed). */
        if (server.active_expire_enabled && server.masterhost == NULL)
            activeExpireCycle(ACTIVE_EXPIRE_CYCLE_FAST);
    }
```
#### 过期数据清理算法
Redis过期Key清理的机制对清理的频率和最大时间都有限制，在尽量不影响正常服务的情况下，进行
过期Key的清理，以达到长时间服务的性能最优.
Redis会周期性的随机测试一批设置了过期时间的key并进行处理。测试到的已过期的key将被删除。
具体的算法如下:
① Redis配置项hz定义了serverCron任务的执行周期，默认为10，即CPU空闲时每秒执行10次;
② 每次过期key清理的时间不超过CPU时间的25%，即若hz=1，则一次清理时间最大为250ms，若hz=10，则一次清理时间最大为25ms;
③ 清理时依次遍历所有的db;
④ 从db中随机取20个key，判断是否过期，若过期，则逐出;
⑤ 若有5个以上key过期，则重复步骤4，否则遍历下一个db;
⑥ 在清理过程中，若达到了25%CPU时间，退出清理过程;
这是一个基于概率的简单算法，基本的假设是抽出的样本能够代表整个key空间，redis持续清理过期的数据直至将
要过期的key的百分比降到了25%以下。这也意味着在长期来看任何给定的时刻已经过期但仍占据着内存空间的key的
量最多为每秒的写操作量除以4.
① 由于算法采用的随机取key判断是否过期的方式，故几乎不可能清理完所有的过期Key;
② 调高hz参数可以提升清理的频率，过期key可以更及时的被删除，但hz太高会增加CPU时间的消耗.

### Redis数据逐出策略
#### 数据逐出时机
```java
// 执行命令
int processCommand(redisClient *c) {
        ...
        /**
         * Handle the maxmemory directive.
         * First we try to free some memory if possible (if there are volatile
         * keys in the dataset). If there are not the only thing we can do
         * is returning an error. 
         */
        if (server.maxmemory) {
            int retval = freeMemoryIfNeeded();
            ...
    }
    ...
}
```

#### 数据逐出算法
在逐出算法中，根据用户设置的逐出策略，选出待逐出的key，直到当前内存小于最大内存值为主.
可选逐出策略如下：
① volatile-lru：从已设置过期时间的数据集（server.db[i].expires）中挑选最近最少使用 的数据淘汰
② volatile-ttl：从已设置过期时间的数据集（server.db[i].expires）中挑选将要过期的数 据淘汰
③ volatile-random：从已设置过期时间的数据集（server.db[i].expires）中任意选择数据 淘汰
④ allkeys-lru：从数据集（server.db[i].dict）中挑选最近最少使用的数据淘汰
⑤ allkeys-random：从数据集（server.db[i].dict）中任意选择数据淘汰
⑥ no-enviction（驱逐）：禁止驱逐数据

# JVM
## 1. 详细jvm内存模型
![jvm内存模型](jvm.png)
### 堆内存
堆内存是所有线程共享的, 可以分为两个部分: 年轻代和老年代. 下图中的Perm代表的是永久代, 但是注意永久代不属于堆内存的一部分, 
同时jdk1.8之后永久代将被移除.
![hotspot heap memory](heap.png)
GC(垃圾回收器)对年轻代中的对象进行回收称为Minor GC, 用通俗一点的话说年轻代就是用来存放年轻的对象, 年轻对象是什么意思呢? 
年轻对象可以简单理解为没有经历多次垃圾回收的对象, 如果一个对象经历了一定次数的Minor GC, JVM一般会把这个对象放入老年代, 
而JVM对于老年代的对象的回收则称为Major GC.
如上图所示, 年轻代可以细分为三个部分, 我们需要重点关注这几个点:
① 大部分对象刚创建的时候, JVM会将其分布到Eden区域.
② 当Eden区的对象达到一定数量的时候, 就会进行Minor GC, 经历这次垃圾回收后所有存活的对象都会进入两个Survivor Place中的一个.
③ 同一时刻两个Survivor Place, 即s0和s1中总有一个是空的.
④ 年轻代中的对象经历过了多次的垃圾回收就会转移到年老代中，可以通过MaxTenuringThrehold参数来控制。

Xmx: 设置JVM堆最大内存。
Xms: 设置JVM堆初始内存。
Xmn: 设置年轻代大小。
PretenureSizeThreshold: 直接晋升到老年代的对象大小，设置这个参数后，大于这个参数的对象将直接在老年代分配。
MaxTenuringThrehold: 晋升到老年代的对象年龄。每个对象在坚持过一次Minor GC之后，年龄就会加1，当超过这个参数值时就进入老年代。
UseAdaptiveSizePolicy: 动态调整Java堆中各个区域的大小以及进入老年代的年龄。
SurvivorRattio: 新生代Eden区域与Survivor区域的容量比值，默认为8，代表Eden: Suvivor= 8: 1。
NewRatio: 设置新生代（包括Eden和两个Survivor区）与老年代的比值（除去持久代），设置为3，则新生代与老年代所占比值为1：3，新生代占整个堆栈的1/4。

### 方法区
方法区与Java堆一样，是各个线程共享的区域，它用于存储已被虚拟机加载的类信息，常量，静态变量，即时编译(JIT)后的代码等数据。

对于JDK1.8之前的HotSpot虚拟机而言，很多人经常将方法区称为我们上图中所描述的永久代，实际上两者并不等价，因为这仅仅是HotSpot
的设计团队选择利用永久代来实现方法区而言。同时对于其他虚拟机比如IBM J9中是不存在永久代的概念的。

其实，移除永久代的工作从JDK1.7就开始了。JDK1.7中，存储在永久代的部分数据就已经转移到了Java Heap或者是 Native Heap。但永久
代仍存在于JDK1.7中，并没完全移除，譬如符号引用(Symbols)转移到了native heap；字面量(interned strings)转移到了java heap；
类的静态变量(class statics)转移到了java heap。而在JDK1.8之后永久代概念也已经不再存在取而代之的是元空间metaspace。

常量池其实是方法区中的一部分，因为这里比较重要，所以我们拿出来单独看一下。注意我们这里所说的运行时的常量池并不仅仅是指Class
文件中的常量池，因为JVM可能会进行即时编译进行优化，在运行时将部分常量载入到常量池中。

### 程序计数器
JVM中的程序计数器和计算机组成原理中提到的程序计数器PC概念类似，是线程私有的，用来记录当前执行的字节码位置。还是稍微解释一下吧，
CPU的占有时间是以分片的形式分配给给每个不同线程的，从操作系统的角度来讲，在不同线程之间切换的时候就是依赖程序计数器来记录上一
次线程所执行到具体的代码的行数，在JVM中就是字节码。

### Java虚拟机栈
与程序计数器一样，Java虚拟机栈也是线程私有的，用通俗的话将它就是我们常常听说到堆栈中的那个“栈内存”。虚拟机栈描述的是Java方法执
行的内存模型：每个方法在执行的同时都会创建一个栈帧(Stack Frame)用于存储局部变量表（局部变量表需要的内存在编译期间就确定了所以
在方法运行期间不会改变大小），操作数栈，动态链接，方法出口等信息。每一个方法从调用至出栈的过程，就对应着栈帧在虚拟机中从入栈到
出栈的过程。

### 本地方法栈
本地方法栈和Java虚拟机栈类似，只不过是为JVM执行Native方法服务.

## 2. 讲讲什么情况下会出内存溢出, 内存泄漏?
① 生命周期极长的集合类的不当持有
② Scope定义不对, 方法的局部变量定义成类的变量, 类的静态变量
③ 异常时没有加 finallyl 来释放资源.

内存溢出就是内存越界 
内存越界有一种很常见的情况是调用栈溢出（即stackoverflow），虽然这种情况可以看成是栈内存不足的一种体现。但内存溢出并不一定跟内存
分配有什么关系，因为还有一种情况是缓冲区溢出。

内存泄露是指你的应用使用资源之后没有及时释放，导致应用内存中持有了不需要的资源，这是一种状态描述

而内存溢出是指你的应用的内存已经不能满足正常使用了，堆栈已经达到系统设置的最大值，进而导致崩溃，这是一种结果描述

而且通常都是由于内存泄露导致堆栈内存不断增大，从而引发内存溢出。

## 3. 说说java线程栈
线程栈是指某时刻内存中线程调度的栈信息, 当前调用的方法总是位于栈顶, 线程栈的内容随着线程的运行状态变化而变化, 研究线程栈必须选择
一个运行的时刻.

线程生命周期:
新建 New
可运行 Runnable
运行 Running
阻塞 Blocking
死亡 Dead

线程阻塞有多种
睡眠(sleep), 等待(yield), 获取线程锁而阻塞
1、调用线程的sleep()方法，使线程睡眠一段时间
2、调用线程的yield()方法，使线程暂时回到可运行状态，来使其他线程有机会执行。
3、调用线程的join()方法，使当前线程停止执行，直到当前线程中加入的线程执行完毕后，当前线程才可以执行。
## 4. JVM年轻代到老年代的晋升过程的判断条件是什么?
① 经历过数次(默认为15次)Minor GC之后仍然存活的对象会被移动到老年代
② 大对象会直接进入到老年代
③ 内存分配时, 如果 Eden 区和 Survivor区中的空间不够, 则会通过分配担保转移到老年代中.
## 5. JVM出现fullGC很频繁, 怎么去线上排查问题?
## 6. 类加载为什么要使用双亲委派模式, 有没有什么场景是打破了这个模式?
类加载器的双亲委派模式是在jdk1.2期间被引入并被广泛运用于之后所有的java程序中, 但它并不是一个强制性的约束模型, 而是Java设计者推
荐给Java开发者的一种类加载器实现方式.
双亲委派的工作过程: 
如果一个类加载器收到一个类加载请求, 首先它不会尝试自己去加载这个类, 而是把这个请求委派给父类加载器去完成, 每个层次的加载器都是如
此, 因此所有的加载请求都应该传送到顶层的类加载器中, 只有当父加载器反馈自己无法完成这个加载请求(它的搜索范围中没有找到所需要的类)
的时候, 子加载器才会尝试自己去加载.
使用双亲委派模式来组织类加载器之间的关系, 一个显而易见的好处是Java类随着他的类加载器一起具备了一种带有优先级的层次关系. 例如java.lang.Object类, 
它存放在rt.jar中, 无论哪一个类加载器要加载这个类,  最终都是委派给处于模型顶端的启动类加载器进行加载, 因此Object类在程序的各种类
加载器环境中都是同一个类. 相反, 如果没有双亲委派模型, 由各个类加载器自行去加载的话, 如果用户编写了一个称为java.lang.Object类, 
并放在程序的ClassPath中, 那系统中将会出现多个不同的Object类, java类型体系中最基础的行为也就无法保证, 应用程序也将变得一片混乱.

有三个场景打破了这个模式:
① jdk1.2之前, 允许用户继承java.lang.ClassLoader重写loadClass
② 双亲委派很好的解决了各个类加载器的基础类统一问题, 但如果基础类要调用回用户代码, 这时, 启动类加载器无法识别这些类. 例如 JNDI.
③ 用户对于程序动态性的追求导致(即代码热替换, 模块热部署等), 这时, 自定义的类加载器出现的不符合双亲委派原则的行为.

## 7. 类的实例化顺序

先父类再子类
先静态变量, 静态方法, main(), 再构造块, 构造方法, 然后普通变量, 普通方法 
## 8. JVM垃圾回收机制, 何时触发MinorGC等操作
当Eden区没有足够的空间来分配的时候触发Minor GC.
新生代 GC (Minor GC): 指发生在新生代的垃圾收集动作, 因为 Java 对象大多都具备朝生夕灭的特性, 所以 Minor GC 非常频繁, 一般回收速度也比较快.
老年代 GC (Major GC / Full GC): 指发生在老年代的 GC, 出现了 Major GC, 经常会伴随至少一次的 Minor GC(但非绝对, 在 Parallel Scanvenge 
收集器的收集策略里就有直接进行 Major GC的策略选择过程). Major GC 的速度一般会比 Minor GC 慢10倍以上. 

大多数情况下, 对象在 新生代Eden 区中分配, 当 Eden 区没有足够的空间进行分配时, 虚拟机将发起一次 Minor GC.

大多数情况下, 新对象在新生代Eden区中分配. 当Eden区没有足够的空间进行分配时, 虚拟机将发起一次Minor GC.

## 9. JVM中一次完整的GC流程(从 ygc 到 fgc)是怎么样的
## 10. 各种回收器, 各自优缺点, 重点CMS, G1
### Serial收集器
Serial收集器是最古老的收集器, 它的缺点是当Serial收集器想进行垃圾回收的时候, 必须暂停用户的所有进程, 即stop the world. 到现在为止, 
它依然在虚拟机运行在client模式下的默认新生代收集器. 与其他收集器相比, 对于限定在单个cpu的运行环境来说, Serial收集器由于没有线程交
互的开销, 专心做垃圾回收自然可以获得最高的单线程收集效率.
Serial old是Serial收集器的老年代版本, 它同样是一个单线程收集器, 使用标记-整理算法. 这个收集器的主要意义也是被Client模式下的虚拟机
使用. 在Server模式下, 它主要还有两大用途: 一个是jdk1.5及以前的版本中与Parallel Scanvenge收集器搭配使用, 另外一个就是作为CMS收集
器的后备预案, 在并发收集发生Concurrent Mode Failure的时候使用.
通过指定-UseSerialGC参数, 使用Serial + Serial Old的串行收集器组合进行内存回收.

### ParNew收集器
ParNew收集器是Serial收集器新生代的多线程实现, 注意在进行垃圾回收的时候依然会stop the world, 只是相比较Serial收集器而言它会运行多条线程进行垃圾回收.
ParNew收集器在单CPU的环境中绝对不会有比Serial收集器更好的效果, 甚至优于存在线程交互的开销, 该收集器在通过超线程技术实现的两个CPU的环境中都不能百分之百的保证能超越Serial收集器. 当然, 随着可以使用的CPU的数量的增加, 它对于GC时系统资源的利用还是很有好处的. 它默认开启的收集线程数与CPU的数量相同, 在CPU非常多(譬如32个, 现在CPU动辄4核加超线程, 服务器超过32个逻辑CPU的情况越来越多了)的环境下, 可以使用-XX:ParallelGCThreads参数来限制垃圾收集的线程数.
-UseParNewGC 打开此开关后, 使用ParNew + Serial Old的收集器组合进行内存回收, 这样新生代使用并行收集器, 老年代使用串行收集器.

### Parallel Scanvenge收集器
Parallel是采用复制算法的多线程新生代垃圾回收器, 似乎和ParNew收集器有很多相似的地方. 但是Parallel Scanvenge收集器的一个特点是它所关注的目标是吞吐量(Throughput). 所谓吞吐量就是CPU用于运行用户代码的时间与CPU总消耗时间的比值, 即吞吐量=运行用户代码时间/(运行用户代码时间 + 垃圾收集时间). 停顿时间越短就越适合需要与用户交互的程序, 良好的响应速度能够提升用户的体验, 而高吞吐量则可以最高效率地利用CPU时间, 尽快地完成程序的运算任务, 主要适合在后台运算而不需要太多交互的任务.
Parallel Old收集器是Parallel Scanvenge收集器的老年代版本, 采用多线程和标记-整理算法. 这个收集器是在jdk1.6中才开始提供的, 在此之前, 新生代的Parallel Scanvenge收集器一直处于比较尴尬的状态. 原因是如果新生代使用Parallel Scanvenge收集器, 那么老年代除了Serial Old(PS MarkSweep)收集器外别无选择. 由于单线程的老年代Serial Old收集器在服务端应用性能上的拖累. 即使使用了Parallel Scanvenge收集器也未必能在整体应用上获得吞吐量最大化的效果, 又因为老年代手机中无法充分利用服务器多CPU的处理能力, 在老年代很大而且硬件比较高级的环境中, 这种组合的吞吐量甚至还不一定有ParNew加CMS的组合给力. 知道Parallel Old收集器出现之后, 吞吐量优先 收集器终于有了比较名副其实的应用, 在注重吞吐量及CPU资源敏感的场合, 都可以优先考虑Parallel Scanvenge加Parallel Old收集器.
-UseParallelGC: 虚拟机运行在Server模式下的默认值, 打开此开关后, 使用Parallel Scanvenge 加 Serial Old的收集器组合进行内存回收. -UseParallelOldGC: 打开此开关后, 使用Parallel Scanvenge + Parallel Old的收集器组合进行垃圾回收.

### CMS收集器
CMS(Concurrent Mark Sweep)收集器是一个比较重要的回收器, 现在应用非常广泛, 我们重点来看一下.
CMS是一种以获取最短回收停顿时间为目标的收集器, 这使得它很适合用于和用户交互的业务. 从名字(Mark Sweep)就可以看出, CMS收集器是基于标记清除算法实现的. 它的收集过程分为四个步骤:
① 初始标记
② 并发标记
③ 重新标记
④ 并发清除
注意初始标记和重新标记还是会stop the world, 但是在好费时间更改的并发标记和并发清除两个阶段都可以和用户进程同时工作.
不过由于CMS收集器是基于标记清除算法实现的, 会导致有大量的空间碎片产生, 在为大对象分配内存的时候, 往往会出现老年代还有很大的空间剩余, 但是无法找到足够大的`连续空间来分配对象, 不得不提前开启一次Full GC. 为了解决这个问题, CMS收集器默认提供了一个 -XX:+UseCMSCompactAtFullCollection 收集开关参数(默认是开启的), 用于在CMS收集器进行Full GC后开启内存碎片的合并整理过程, 内存整理的过程是无法并发的, 这样内存碎片问题倒是没有了, 不过停顿时间不得不边长. 虚拟机设计者还提供了另外一个参数 -XX:CMSFullGCsBeforeCompaction 参数用于设置执行多少次不压缩的Full GC后跟着来一次带压缩的(默认值是0, 表示每次进入Full GC时都进行碎片整理).
不幸的是, 它作为老年代的收集器, 却无法与jdk1.4中已经存在的新生代手气Parallel Scanvenge配合工作, 所以在jdk1.5中使用cms来收集老年代的时候, 新生代只能选择ParNew或Serial收集器中的一个. ParNew收集器是使用 -XX: +UseConcMarkSweepGC选项启用CMS收集器之后的默认新生代收集器, 也可以使用 -XX:+UseParNewGC选项来强制指定它.
由于CMS收集器现在比较常用，下面我们再额外了解一下CMS算法的几个常用参数：
① UseCMSInitatingOccupancyOnly：表示只在到达阈值的时候，才进行 CMS 回收。
② CMS默认启动的回收线程数目是(ParallelGCThreads+3)/4，如果你需要明确设定，可以通过-XX:-- +ParallelCMSThreads来设定，其中-XX:+ParallelGCThreads代表的年轻代的并发收集线程数目。
③ CMSClassUnloadingEnabled： 允许对元类数据进行回收。
④ CMSInitatingPermOccupancyFraction：当永久区占用率达到这一百分比后，启动 CMS 回收 (前提是-XX:+CMSClassUnloadingEnabled 激活了)。
⑤ CMSIncrementalMode：使用增量模式，比较适合单 CPU。
⑥ UseCMSCompactAtFullCollection参数可以使 CMS 在垃圾收集完成后，进行一次内存碎片整理。内存碎片的整理并不是并发进行的。
⑦ UseFullGCsBeforeCompaction：设定进行多少次 CMS 垃圾回收后，进行一次内存压缩。
#### 一些建议
对于Native Memory:
① 使用了 NIO 或者 NIO 框架( Mina/Netty)
② 使用了 DirectByteBuffer 分配字节缓冲区
③ 使用了 MappedByteBuffer 做内存映射
④ 由于 Native Memory 只能通过 Full GC 回收, 所以除非你非常清楚这时真的有必要, 否则不要轻易调用 System.gc()
另外为了防止某些狂阶的 System.gc()调用(例如 NIO 框架, Java RMI), 建议在启动参数中加上 -XX:+DisableExplicitGC来禁用显示 GC. 这个参数有个巨大的坑, 如果你禁用了 System.gc(), 那么上面的3种场景下的内存就无法回收, 可能造成 OOM, 如果你使用了 CMS GC, 那么可以用这个参数替代: -XX:+ExplicitGCInvokesConcurrent.
此外除了 CMS 的 GC, 其实其他针对 old gen 的回收器都会在对 old gen 回收的同时使用 young gc.

### G1收集器
G1收集器是一款面向服务端应用的垃圾收集器. HotSpot 团队赋予它的使命是在未来替换掉 jdk1.5中发布的 CMS 收集器. 与其他 GC 收集器相比, G1具备如下特点:
① 并行和并发: G1能更充分的利用 GPU, 多核环境下的硬件优势来缩短 stop the world 的停顿时间.
② 分代收集: 和其他收集器一样, 分代的概念在 G1中依然存在, 不过 G1不需要其他的垃圾回收器的配合就可以独自管理整个 GC 堆.
③ 空间整合: G1收集器有利于程序长时间运行, 分配大对象时不会无法得到连续的空间而提前触发一次 Full GC.
可预测的非停顿: 这是 G1相比于 CMS 的另一大优势, 降低停顿时间是 G1和 CMS 共同的关注点, 能让使用者明确指定在一个长度为 M 毫秒的时间片段内, 消耗在垃圾收集上的时间不得超过 N 毫秒.
④ 在使用 G1收集器时, Java 堆得内存布局和其他收集器有很大的差别, 它将这个 Java 堆分为多个大小相等的独立区域, 虽然还保留新生代和老年代的概念, 但是新生代和老年代不再试物理隔离的了, 他们都是一部分 Region( 不需要连续)的集合.
虽然 G1看起来有很多优点, 实际上 CMS 还是主流.

#### 与 GC 相关的常用参数
除了上面提及的一些参数，下面补充一些和GC相关的常用参数：
Xmx: 设置堆内存的最大值。
Xms: 设置堆内存的初始值。
Xmn: 设置新生代的大小。
Xss: 设置栈的大小。
PretenureSizeThreshold: 直接晋升到老年代的对象大小，设置这个参数后，大于这个参数的对象将直接在老年代分配。
MaxTenuringThrehold: 晋升到老年代的对象年龄。每个对象在坚持过一次Minor GC之后，年龄就会加1，当超过这个参数值时就进入老年代。
UseAdaptiveSizePolicy: 在这种模式下，新生代的大小、eden 和 survivor 的比例、晋升老年代的对象年龄等参数会被自动调整，以达到在堆大小、吞吐量和停顿时间之间的平衡点。在手工调优比较困难的场合，可以直接使用这种自适应的方式，仅指定虚拟机的最大堆、目标的吞吐量 (GCTimeRatio) 和停顿时间 (MaxGCPauseMills)，让虚拟机自己完成调优工作。
SurvivorRattio: 新生代Eden区域与Survivor区域的容量比值，默认为8，代表Eden: Suvivor= 8: 1。
XX:ParallelGCThreads：设置用于垃圾回收的线程数。通常情况下可以和 CPU 数量相等。但在 CPU 数量比较多的情况下，设置相对较小的数值也是合理的。
XX:MaxGCPauseMills：设置最大垃圾收集停顿时间。它的值是一个大于 0 的整数。收集器在工作时，会调整 Java 堆大小或者其他一些参数，尽可能地把停顿时间控制在 MaxGCPauseMills 以内。
XX:GCTimeRatio:设置吞吐量大小，它的值是一个 0-100 之间的整数。假设 GCTimeRatio 的值为 n，那么系统将花费不超过 1/(1+n) 的时间用于垃圾收集。


## 11. 各种回收算法

### GC Roots
我们先来了解一下在Java中如何判断一个对象的生死的, 有些语言例如python是采用引用记数法来统计的, 但是这种做法可能会遇到循环引用的问题, Java以及C#等语言中是采用GC Roots来解决这个问题。如果一个对象和GC Roots之间没有链接，那么这个对象也可以被视作是一个可回收的对象。
Java中可以被作为GC Roots中的对象有：
① 虚拟机栈中引用的对象.
② 方法区中的类静态属性引用的对象
③ 方法区中的常量引用的对象
④ 本地方法栈即一般说的Native的引用对象

### 标记清除
标记-清除算法将垃圾回收分为两个阶段: 标记阶段和清除阶段. 在标记阶段首先通过根节点, 标记所有从根节点开始的对象, 未被标记的对象就是未被引用的垃圾对象. 然后在清除阶段, 清除所有未被标记的对象. 标记清除算法带来的一个问题是会存在大量的空间碎片, 因为回收的空间是不连续的, 这样给大对象分配内存的时候可能会提前触发full gc.
![标记清除](标记清除.png)
### 复制算法
将现有的内存空间分为两块, 每次只使用其中一块, 在垃圾回收将正在使用的内存中的存活对象复制到未被使用的内存块中, 之后, 清除正在使用的内存块中的所有对象, 交换两个内存的角色, 完成垃圾回收.
![复制算法](复制算法.png)
现有的商业虚拟机都采用这种收集算法来回收新生代, IBM研究表明新生代中的对象98%是朝生夕死的, 所以并不需要按照1:1的比例划分内存空间, 而是将内存分为一块较大的Eden空间和两个较小的Survivor空间, 每次使用Eden和其中的一块Survivor, 当回收时, 将Eden和Survivor中还存活着的对象一次性的拷贝到另一个Survivor空间上, 最后清理Eden和刚才用过的Survivor的空间. HotSpot虚拟机默认Eden和Survivor的大小比例是8:1(可以通过-SurvivorRattio来配置), 也就是每次新生代中可用内存空间为整个新生代容量的90%, 只有10%的内存会被浪费. 当然, 98%的对象可回收只是一般场景下的数据, 我们没有办法保证回收都只有不多于10%的对象存活, 当Survivor空间不够用时, 需要依赖其他内存(这里指老年代)进行分配担保. 

### 标记整理
复制算法的高效性是建立在存活对象少, 垃圾对象多的前提下的. 这种情况在新生代经常发生, 但是在老年代更常见的情况是大部分对象都是存活对象. 如果依然使用复制算法, 由于存活的对象较多, 复制的成本也将很高.
![标记整理](标记整理.png)
标记-压缩算法是一种老年代的回收算法, 它在标记-清除算法的基础上做了一些优化. 首先也需要从根节点开始对所有可达对象做一次标记, 但之后, 它并不简单地清理未标记的对象, 而是将所有的存活对象压缩到内存的一端. 之后, 清理边界所有的空间. 这种方法既避免了碎片的产生, 又不需要两块相同的内存空间, 因此, 其性价比比较高. 
### 增量算法
增量算法的基本思想是, 如果一次性将所有的垃圾进行处理, 需要造成系统长时间的停顿, 那么就可以让垃圾收集线程和应用程序线程交替执行. 每次, 垃圾收集线程只收集一片区域的内存空间, 接着切换到应用程序线程. 依次反复, 知道垃圾收集完成. 使用这种方式, 由于在垃圾回收过程中, 间断性地还执行了应用程序代码, 所以能减少系统的停顿时间. 但是因为线程切换和上下文转换的消耗, 会使得垃圾回收的总成本上升, 造成系统吞吐量的下降. 

## 12. OOM错误, stackoverflow错误, permgen space错误


## 13. ACID CAS CAP BASIC

数据库事务本质ACID: Atomicity 原子性, Consistency 一致性, Isolation 隔离性, Durability 耐久
数据库事务定义: 是指作为单个逻辑单元执行的一系列操作, 要么完全执行, 要不 

CAS: compare and sweep 比较和交换
有个问题 ABA, 可以通过版本号的方式解决.


CAP: 数据一致性 Consistency, 服务可用性 Availability, 分区容错性 Partition-tolerance
CAP是分布式系统、特别是分布式存储领域中被讨论最多的理论，“什么是CAP定理？”在Quora 分布式系统分类下排名 FAQ 的 No.1。CAP在程序员中也有较广的普及，它不仅仅是“C、A、P不能同时满足，最多只能3选2”，以下尝试综合各方观点，从发展历史、工程实践等角度讲述CAP理论。希望大家透过本文对CAP理论有更多地了解和认识。
#### 数据一致性(consistency)：如果系统对一个写操作返回成功，那么之后的读请求都必须读到这个新数据；如果返回失败，那么所有读操作都不能读到这个数据，对调用者而言数据具有强一致性(strong consistency) (又叫原子性 atomic、线性一致性 linearizable consistency)[5]
#### 服务可用性(availability)：所有读写请求在一定时间内得到响应，可终止、不会一直等待
#### 分区容错性(partition-tolerance)：在网络分区的情况下，被分隔的节点仍能正常对外服务

在某时刻如果满足AP，分隔的节点同时对外服务但不能相互通信，将导致状态不一致，即不能满足C；如果满足CP，网络分区的情况下为达成C，请求只能一直等待，即不满足A；如果要满足CA，在一定时间内要达到节点状态一致，要求不能出现网络分区，则不能满足P。

Partition字面意思是网络分区，即因网络因素将系统分隔为多个单独的部分，有人可能会说，网络分区的情况发生概率非常小啊，是不是不用考虑P，保证CA就好。要理解P，我们看回CAP证明中P的定义：
```
In order to model partition tolerance, the network will be allowed to lose arbitrarily many messages sent from one node to another.
```
网络分区的情况符合该定义，网络丢包的情况也符合以上定义，另外节点宕机，其他节点发往宕机节点的包也将丢失，这种情况同样符合定义。现实情况下我们面对的是一个不可靠的网络、有一定概率宕机的设备，这两个因素都会导致Partition，因而分布式系统实现中 P 是一个必须项，而不是可选项。
对于分布式系统工程实践，CAP理论更合适的描述是：在满足分区容错的前提下，没有算法能同时满足数据一致性和服务可用性：
```
In a network subject to communication failures, it is impossible for any web service to implement an atomic read/write shared memory that guarantees a response to every request.
```
C/A不是非此即彼, 根据一致性和可用性的不同等级, 放开一些约束后可以兼顾一致性和可用性.

CAP定理证明中的一致性指强一致性，强一致性要求多节点组成的被调要能像单节点一样运作、操作具备原子性，数据在时间、时序上都有要求。如果放宽这些要求，还有其他一致性类型：

序列一致性(sequential consistency)：不要求时序一致，A操作先于B操作，在B操作后如果所有调用端读操作得到A操作的结果，满足序列一致性
最终一致性(eventual consistency)：放宽对时间的要求，在被调完成操作响应后的某个时间点，被调多个节点的数据最终达成一致

可用性在CAP定理里指所有读写操作必须要能终止，实际应用中从主调、被调两个不同的视角，可用性具有不同的含义。当P(网络分区)出现时，主调可以只支持读操作，通过牺牲部分可用性达成数据一致。

工程实践中，较常见的做法是通过异步拷贝副本(asynchronous replication)、quorum/NRW，实现在调用端看来数据强一致、被调端最终一致，在调用端看来服务可用、被调端允许部分节点不可用(或被网络分隔)的效果

BASIC: 

## 14. JVM参数
-X: 表示 非标准 选项, 不是所有虚拟机都支持
-XX: 表示 不稳定的, 不建议随便使用的 选项
