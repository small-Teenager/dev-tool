
#  redis 配置文件
#  执行指令创建集群 --cluster-replicas 0 表示没有从节点  --cluster-replicas 1 表示1主1从
#  redis-cli -p 7701 --cluster create 192.168.0.101:7701 192.168.0.101:7702 192.168.0.101:7703 192.168.0.101:7704 192.168.0.101:7705 192.168.0.101:7706 --cluster-replicas 1

## cluster 指令

Redis Cluster集群的一些常用指令包括：

CLUSTER INFO：打印集群的信息。
CLUSTER NODES：列出集群当前已知的所有节点(node)，以及这些节点的相关信息。
CLUSTER MEET <ip> <port>：将ip和port所指定的节点添加到集群当中，让它成为集群的一份子。
CLUSTER FORGET <node_id>：从集群中移除node_id指定的节点。
CLUSTER REPLICATE <master_node_id>：将当前从节点设置为node_id指定的master节点的slave节点。只能针对slave节点操作。
CLUSTER SAVECONFIG：将节点的配置文件保存到硬盘里面。
CLUSTER ADDSLOTS <slot> [slot ...]：将一个或多个槽(slot)指派(assign)给当前节点。
CLUSTER DELSLOTS <slot> [slot ...]：移除一个或多个槽对当前节点的指派。
CLUSTER FLUSHSLOTS：移除指派给当前节点的所有槽，让当前节点变成一个没有指派任何槽的节点。
CLUSTER SETSLOT NODE <node_id>：将槽slot指派给node_id指定的节点。
CLUSTER SETSLOT MIGRATING <node_id>：将本节点的槽slot迁移到node_id指定的节点中。
CLUSTER COUNTKEYSINSLOT <slot>：返回count个slot槽中的键。
CLUSTER GETKEYSINSLOT <slot> <count>：返回槽slot中count个键。
以上指令都是在redis客户端中执行的，需要先登录redis，然后使用相应的命令进行操作。这些指令可以帮助你管理Redis Cluster集群，包括添加节点、移除节点、指派槽等操作。


# Redis安全性最佳实践：保护数据免受攻击

## 密码认证
设置密码是保护Redis实例最基本的安全措施之一。通过在配置文件中设置requirepass参数，并配置一个强密码，可以防止未经授权的访问。

## 在redis.conf配置文件中设置密码
requirepass your_password


## 在redis.conf配置文件中设置IP绑定
IP绑定
限制Redis服务器只能监听特定的IP地址或网卡接口，可以有效防止外部网络的访问。在配置文件中设置bind参数，指定允许连接的IP地址。
bind 127.0.0.1
## 客户端限制
通过设置maxclients参数，限制Redis服务器同时接受的客户端连接数，可以防止DDoS（分布式拒绝服务）攻击。
在redis.conf配置文件中设置最大客户端连接数
maxclients 1000

网络隔离
安全组配置
使用防火墙或安全组配置，限制对Redis端口的访问，只允许特定的IP地址或IP地址范围访问Redis端口。

## 通过防火墙或安全组配置，限制对Redis端口的访问
iptables -A INPUT -p tcp --dport 6379 -s trusted_ip -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -j DROP
VPN隔离
将Redis实例部署在虚拟私有网络（VPN）中，并通过VPN隔离，限制只有内部网络或已授权的用户能够访问Redis。

TLS加密
使用TLS（传输层安全）协议对Redis的通信进行加密，确保数据在传输过程中的安全性和完整性。

## 配置Redis使用TLS加密
tls-port 6379
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key

监控和审计
日志记录
开启Redis的日志记录功能，并定期审查日志文件，及时发现异常操作和攻击行为。

## 在redis.conf配置文件中设置日志记录级别
loglevel verbose
logfile /path/to/redis.log
实时监控
使用监控工具或服务，实时监控Redis的性能和状态，发现异常访问和攻击行为。




Redis集群原理分析
Redis Cluster 将所有数据划分为 16384 个 slots(槽位)，每个节点负责其中一部分槽位。槽位的信息存储于每个节点中。

当 Redis Cluster 的客户端来连接集群时，它也会得到一份集群的槽位配置信息并将其缓存在客户端本地。这样当客户端要查找某个 key 时，可以直接定位到目标节点。同时因为槽位的信息可能会存在客户端与服务器不一致的情况，还需要纠正机制来实现槽位信息的校验调整。

1、槽位定位算法
Cluster 默认会对 key 值使用 crc16 算法进行 hash 得到一个整数值，然后用这个整数值对 16384 进行取模
来得到具体槽位。

HASH_SLOT = CRC16(key) mod 16384
2、跳转重定位
当客户端向一个错误的节点发出了指令，该节点会发现指令的 key 所在的槽位并不归自己管理，这时它会向客户端发送一个特殊的跳转指令携带目标操作的节点地址，告诉客户端去连这个节点去获取数据。

客户端收到指令后除了跳转到正确的节点上去操作，还会同步更新纠正本地的槽位映射表缓存，后续所有 key 将使用新的槽位映射表。

注意：这里连接cluster客户端的时候，如果设置了面，一定要在连接的使用-a 带上密码，否则可能出现以下问题 ：

这里通过hash计算出xue应当被分配到14854这个槽位上，而这个槽在8003节点上，所以自动重定位到了8003.。我们可以在8003上成功查出信息。

3、Redis集群节点间的通信机制
redis cluster节点间采取gossip协议进行通信。

维护集群的元数据(集群节点信息，主从角色，节点数量，各节点共享的数据等)有两种方式：集中式和gossip。

（1）集中式：

比如将节点信息保存到zookeeper.

优点在于元数据的更新和读取，时效性非常好，一旦元数据出现变更立即就会更新到集中式的存储中，其他节点读取的时候立即就可以立即感知到；

不足在于所有的元数据的更新压力全部集中在一个地方，可能导致元数据的存储压力。 很多中间件都会借助zookeeper集中式存储元数据。

（2）gossip：
gossip协议包含多种消息，包括ping，pong，meet，fail等等。

meet：某个节点发送meet给新加入的节点，让新节点加入集群中，然后新节点就会开始与其他节点进行通信；

ping ：每个节点都会频繁给其他节点发送ping，其中包含自己的状态还有自己维护的集群元数据，互相通过ping交换元数据(类似自己感知到的集群节点增加和移除，hash slot信息等)；

pong: 对ping和meet消息的返回，包含自己的状态和其他信息，也可以用于信息广播和更新；

fail: 某个节点判断另一个节点fail之后，就发送fail给其他节点，通知其他节点，指定的节点宕机了。

优点：gossip协议的优点在于元数据的更新比较分散，不是集中在一个地方，更新请求会陆陆续续，打到所有节点上去更新，有一定的延时，降低了压力；

缺点：在于元数据更新有延时可能导致集群的一些操作会有一些滞后。

4、gossip通信的10000端口
每个节点都有一个专门用于节点间gossip通信的端口，就是自己提供服务的端口号+10000，比如7001，那么用于节点间通信的就是17001端口。 每个节点每隔一段时间都会往另外几个节点发送ping消息，同时其他几点接收到ping消息之后返回pong消息。

5、网络抖动
真实世界的机房网络往往并不是风平浪静的，它们经常会发生各种各样的小问题。比如网络抖动就是非常常见的一种现象，突然之间部分连接变得不可访问，然后很快又恢复正常。

所以我们配置主从节点间的clusternodetimeou时间的时候，不能配置配置的太短（建议配置到5秒钟）！如果配置的太短，从节点很短的时间内无法与主节点通信，就认为主节点挂了，需要从新选举新的主节点。但事实上，通信信息只是因为网络抖动延迟了，如果重新选举出一个主节点，这时候这个集群节点上就会有两个主节点，会发生脑裂问题。

为解决这种问题，Redis Cluster 提供了一种选项clusternodetimeout，表示当某个节点持续 timeout的时间失联时，才可以认定该节点出现故障，需要进行主从切换。如果没有这个选项，网络抖动会导致主从频繁切换 (数据的重新复制)。

7、Redis集群选举原理分析
当slave发现自己的master变为FAIL状态时，便尝试进行Failover（故障转移）），以期成为新的master。由于挂掉的master可能会有多个slave，从而存在多个slave竞争成为master节点的过程， 其过程如下：

1.slave发现自己的master变为FAIL；

2.将自己记录的集群currentEpoch（选举周期）)加1，并广播FAILOVER_AUTH_REQUEST（故障转移请求） 信息；

3.其他节点收到该信息，只有其他节点的master响应，判断请求者的合法性，并发送FAILOVER_AUTH_ACK（故障转认证确认），对每一个epoch只发送一次ack；

4.尝试failover的slave收集master返回的FAILOVER_AUTH_ACK；

5.slave收到超过半数master的ack后变成新Master(这里解释了集群为什么至少需要三个主节点，如果只有两个，当其中一个挂了，只剩一个主节点是不能选举成功的)；

6.slave广播Pong消息通知其他集群节点。

从节点并不是在主节点一进入 FAIL 状态就马上尝试发起选举，而是有一定延迟，一定的延迟确保我们等待FAIL状态在集群中传播，slave如果立即尝试选举，其它masters或许尚未意识到FAIL状态，可能会拒绝投票。

•延迟计算公式：

DELAY = 500ms + random(0 ~ 500ms) + SLAVE_RANK * 1000ms
1
SLAVE_RANK表示此slave已经从master复制数据的总量的rank。Rank越小代表已复制的数据越新。这种方式下，持有最新数据的slave将会首先发起选举（理论上）。

8、集群脑裂数据丢失问题
redis集群没有过半机制会有脑裂问题，网络分区导致脑裂后多个主节点对外提供写服务，一旦网络分区恢复，会将其中一个主节点变为从节点，这时会有大量数据丢失

（因为大的集群只认新选举出的master节点，一旦旧的master节点恢复之后，就会别当做一个从节点。但是在那段时间中，有旧的master节点也可能会接收到新的数据。而此时要将其转化成一个从节点，就需要删除它里面的所有数据，然后全盘的去同步新master节点的数据，这样一来，就会导致数据丢失。）。

规避方法可以在redis配置里加上参数(这种方法不可能百分百避免数据丢失，参考集群leader选举机制)：

# 写数据成功最少同步的slave数量，这个数量可以模仿大于半数机制配置
# 比如集群总共三个节点可以配置1，加上leader就是2，超过了半数，说明至少一个master节点和一个slave节点都成功同步了数据
# 即主节点写的新数据，必须同步到至少一个从节点才可以算写成功！！！

min‐replicas‐to‐write 1

# 注意，配置的这个数必须满足：这个数+leader > 半数
1
2
3
4
5
6
7
假如我们的集群现在有三个节点，一个master，两个slave. 假设由于网路波动导致该集群产生脑裂，出现了两个master节点，一个旧的master节点，一个新的master节点。当我们配置了min‐replicas‐to‐write 1之后，就表示我的数据只有写入一个master结点并且也被同步到了至少一个从节点中，才说明这个数据添加成功。 此时对于新的master节点，自然是可以写成功。但是旧的master节点，数据虽然能写入到这个旧的master节点中，但是由于这个旧的master节点此时并没有对应的从节点，所以就会告诉客户端，本次数据写入失败！

这种配置其实是增强了一致性，但是牺牲了可用性。

注意：这个配置在一定程度上会影响集群的可用性，比如slave要是少于1个，这个集群就算leader正常也不能提供服务了，需要具体场景权衡选择。

在我们实际使用中，基本不会配置这个来解决脑裂问题，因为可用性对于我们来说更重要，redis中丢失数据，可以从数据库中查找。

9、集群是否完整才能对外提供服务
当redis.conf的配置cluster-require-full-coverage为no时，表示当负责一个插槽的主库下线且没有相应的从库进行故障恢复时，集群仍然可用，如果为yes则集群不可用。

如果cluster-require-full-coverage为yes时, 当redis的某个集群节点中没有master的时候，会导致整个集群架构崩溃！

10、Redis集群为什么至少需要三个master节点，并且推荐节点数为奇数？
因为新master的选举需要大于半数的集群master节点同意才能选举成功，如果只有两个master节点，当其中一个挂了，是达不到选举新master的条件的（1 <= 1， 1不可能大于1，所以永远不会超过半数，会导致服务不可用，所以推荐使用奇数个服务）。

因为新master的选举需要大于半数的集群master节点同意才能选举成功，如果只有两个master节点，当其中一个挂了，是达不到选举新master的条件的。

比如我们现在是3个集群节点，这时候最多支持挂一个集群节点，挂了之后该集群中的从节点会向剩余的两个master节点发起投票请求，获得超过半数的那个从节点会成为新的master几点。即2个集群节点，最多允许挂一个节点。

而如果我们配置4个几点，虽然可以分担压力，但是并不会提升可用性。因为此时挂掉两个master几点，剩下的节点投票数最大是2，永远不会超过半数，就不会选举出新的master节点，这样会使得我们的整个redis服务不可用（ 如果redis的某个集群节点中没有master的时候，会导致整个集群架构崩溃！）。所以建议部署5奇数个几点。

11、Redis集群对批量操作命令的支持
对于类似mset，mget这样的多个key的原生批量操作命令，redis集群只支持所有key落在同一slot的情况，如果有多个key一定要用mset命令在redis集群上操作，则可以在key的前面加上{XX}，这样参数数据分片hash计算的只会是大括号里的值，这样能确保不同的key能落到同一slot里去，示例如下：

mset {user1}:1:name xiaoyan {user1}:1:age 18
1


假设name和age计算的hash slot值不一样，但是这条命令在集群下执行，redis只会用大括号里的 user1 做hash slot计算，所以算出来的slot值肯定相同，最后都能落在同一slot。

12、哨兵leader选举流程
当一个master服务器被某sentinel视为下线状态后，该sentinel会与其他sentinel协商选出sentinel的leader进行故障转移工作。

每个发现master服务器进入下线的sentinel都可以要求其他sentinel选自己为sentinel的leader，选举是先到先得。

同时每个sentinel每次选举都会自增配置纪元(选举周期)，每个纪元中只会选择一个sentinel的leader。如果所有超过一半的sentinel选举某sentinel作为leader。

之后该sentinel进行故障转移操作，从存活的slave中选举出新的master，这个选举过程跟集群的master选举很类似。

哨兵集群只有一个哨兵节点，redis的主从也能正常运行以及选举master，如果master挂了，那唯一的那个哨兵节点就是哨兵leader了，可以正常选举新master。

不过为了高可用一般都推荐至少部署三个哨兵节点。为什么推荐奇数个哨兵节点原理跟集群奇数个master节点类似。

五、使用Jedis连接Redis Cluster集群
借助redis的java客户端jedis可以操作以上集群，引用jedis版本的maven依赖如下：

<dependency>
    <groupId>redis.clients</groupId>
    <artifactId>jedis</artifactId>
    <version>2.9.0</version>
</dependency>
1
2
3
4
5
Java编写访问redis集群的代码如下所示：

package com.jihu.jedis.master_slave;

import redis.clients.jedis.HostAndPort;
import redis.clients.jedis.JedisCluster;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;

import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

public class JedisClusterTest {

    private static final String HOST = "192.168.131.171";

    public static void main(String[] args) throws IOException {
        JedisPoolConfig config = new JedisPoolConfig();
        config.setMaxTotal(20);
        config.setMaxIdle(10);
        config.setMinIdle(5);

        Set<HostAndPort> jedisClusterNodes = new HashSet<>();
        jedisClusterNodes.add(new HostAndPort(HOST, 8001));
        jedisClusterNodes.add(new HostAndPort(HOST, 8002));
        jedisClusterNodes.add(new HostAndPort(HOST, 8003));
        jedisClusterNodes.add(new HostAndPort(HOST, 8004));
        jedisClusterNodes.add(new HostAndPort(HOST, 8005));
        jedisClusterNodes.add(new HostAndPort(HOST, 8006));

        JedisCluster jedisCluster = null;

        try {
            jedisCluster = new JedisCluster(jedisClusterNodes, 6000, 5000, 10, "redisadmin", config);

            System.out.println(jedisCluster.set("cluster", "jihu"));
            System.out.println(jedisCluster.get("jihu"));
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (jedisCluster != null)
                jedisCluster.close();
        }
    }
}

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
执行一下看看结果：

OK
jihu

Process finished with exit code 0
1
2
3
4
六、使用SrpingBoot连接Redis Cluster集群
1、引入相关依赖：

<dependency>
   <groupId>org.springframework.boot</groupId>
   <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>

<dependency>
   <groupId>org.apache.commons</groupId>
   <artifactId>commons-pool2</artifactId>
</dependency>
1
2
3
4
5
6
7
8
9
2、springboot项目核心配置：

server:
port: 8090


spring:
redis:
database: 0
timeout: 3000
#    sentinel:  # 哨兵模式
#      master: mymaster #主服务器所在集群名称
#      nodes: 192.168.131.171:26379, 192.168.131.171:26381, 192.168.131.171:26381

    password: redisadmin
    cluster:
      nodes: 192.168.131.171:8001,192.168.131.171:8002,192.168.131.171:8003,192.168.131.171:8004,192.168.131.171:8005, 192.168.131.171:8006
    lettuce:
      pool:
        max-idle: 50
        min-idle: 10
        max-active: 100
        max-wait: 1000
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
3、测试代码：

@SpringBootApplication
public class RedisApplication {
public static void main(String[] args) {
SpringApplication.run(RedisApplication.class, args);
}
}
1
2
3
4
5
6
package com.jihu.redis.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RedisClusterController {
@Autowired
private StringRedisTemplate stringRedisTemplate;

    @RequestMapping("/test_cluster")
    public void testCluster() {
        stringRedisTemplate.opsForValue().set("cn", "999");

        System.out.println("从redis获取值成功" + stringRedisTemplate.opsForValue().get("cn"));
    }
}
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
来看执行结果：


接下来我们测测高可用，重新写一个controller，这个方法会不断的向redis中写值，然后我们kill掉一个redis服务，来看看服务是否继续可用：

package com.jihu.redis.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class IndexForRedisClusterController {

    private static final Logger logger = LoggerFactory.getLogger(IndexForRedisClusterController.class);

    @Autowired
    private StringRedisTemplate stringRedisTemplate;


    @RequestMapping("/test_cluster_ha")
    public void testSentinel() throws InterruptedException {
        int i = 1;
        while (true){
            try {
                stringRedisTemplate.opsForValue().set("xiaoyan"+i, i+"");
                System.out.println("设置key："+ "xiaoyan" + i);
                i++;
                Thread.sleep(1000);
            }catch (Exception e){
                logger.error("错误：", e);
            }
        }
    }
}

8003之前是一个master节点，它的id是1efbd5a98b866cb516e8d63d0e55768d2a980442，我们在集群信心中可以查找，发现slave 8006的master节点是8003. 说明8006是8003的一个从节点。


接下来，我们关闭redis这个8003的master节点；

查看集群node信息：


发现8003这个节点状态已经是fail, 而之前8003的从节点8006已经被选举为了新的master节点，8006对应的槽位[10923-16384]也与之前8003对应的复合，这说明选举成功了。

我们再来看代码输出信息：

我们虽然关掉了一个master节点，但是后面的命令还是执行成功了。

现在我们不启动redis刚才挂的那个节点，重新项目调用一下这个方法，看看Redis服务是不是依然可用：

可以看到，虽然8003节点挂掉了，但是Redis服务依然是可用的。

深入思考：代码中的数据为何能准确的插入到服务端的redis中？
我们通过jedis或者springBoot使用Redis Cluster的时候，在启动的过程中，会将redis中生成的node.conf文件拉取到后端服务器上，里面有关于redis集群的节点信息，包括ip地址、端口以及主从信息等。

然后我们如果要查询或者新增数据的时候，代码中调用方法get或者set，我们来看看jedis源码：



