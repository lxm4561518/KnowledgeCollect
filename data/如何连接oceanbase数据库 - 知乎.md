来源: 知乎
链接: https://www.zhihu.com/question/263391776/answer/2307916676



如何连接oceanbase数据库？ - 知乎
关注
推荐
热榜
专栏
圈子
New
付费咨询
知学堂
​
直答
消息
私信
数据库
如何连接oceanbase数据库？
如何连接oceanbase数据库-博客-云栖社区-阿里云
显示全部 
​
关注者
10
被浏览
10,466
关注问题
​
写回答
​
邀请回答
​
好问题
​
添加评论
​
分享
​
查看全部 7 个回答
OceanBase
海量记录  笔笔算数
1 资源管理
1.1 资源单元unit
#创建unit
CREATE RESOURCE UNIT unit1 max_cpu 1, max_memory '1G', max_iops 128,max_disk_size '10G', max_session_num 64, MIN_CPU=1, MIN_MEMORY='1G', MIN_IOPS=128;
#查看创建unit
MySQL [oceanbase]> select * from __all_unit_config\G
.......
*************************** 2. row ***************************gmt_create: 2021-09-17 10:43:21.476628gmt_modified: 2021-09-17 10:43:21.476628unit_config_id: 1003name: unit1   <=====max_cpu: 1min_cpu: 1max_memory: 1073741824min_memory: 1073741824max_iops: 128min_iops: 128max_disk_size: 10737418240
max_session_num: 64
2 rows in set (0.005 sec)

1.2 资源池pool
# 创建资源池pool 
CREATE RESOURCE POOL pool1 unit='unit1', unit_num=1, zone_list=('zone1','zone2','zone3');

#查看创建pool
MySQL [oceanbase]> select * from __all_resource_pool\G
.....
*************************** 2. row ***************************gmt_create: 2021-09-17 11:25:46.359917gmt_modified: 2021-09-17 11:25:46.359917resource_pool_id: 1002name: pool1unit_count: 1unit_config_id: 1003zone_list: zone1;zone2;zone3tenant_id: -1replica_type: 0
is_tenant_sys_pool: 0

#查看系统资源分布 资源池创建之后，系统会分配相应的资源
MySQL [oceanbase]> select * from __all_unit;
.....
*************************** 4. row ***************************gmt_create: 2021-09-17 11:25:46.367016gmt_modified: 2021-09-17 11:25:46.367016unit_id: 1004resource_pool_id: 1002group_id: 0zone: zone1svr_ip: 192.168.20.142svr_port: 2882migrate_from_svr_ip: 
migrate_from_svr_port: 0manual_migrate: 0status: ACTIVEreplica_type: 0
*************************** 5. row ***************************gmt_create: 2021-09-17 11:25:46.373779gmt_modified: 2021-09-17 11:25:46.373779unit_id: 1005resource_pool_id: 1002group_id: 0zone: zone2svr_ip: 192.168.20.143svr_port: 2882migrate_from_svr_ip: 
migrate_from_svr_port: 0manual_migrate: 0status: ACTIVEreplica_type: 0
*************************** 6. row ***************************gmt_create: 2021-09-17 11:25:46.377005gmt_modified: 2021-09-17 11:25:46.377005unit_id: 1006resource_pool_id: 1002group_id: 0zone: zone3svr_ip: 192.168.20.144svr_port: 2882migrate_from_svr_ip: 
migrate_from_svr_port: 0manual_migrate: 0status: ACTIVEreplica_type: 0
6 rows in set (0.002 sec)

1.3 租户tenant
#创建租户
CREATE TENANT IF NOT EXISTS test_tenant 
    charset='utf8mb4', 
    replica_num=3, 
    zone_list=('zone1','zone2','zone3'), 
    primary_zone='RANDOM', 
    resource_pool_list=('pool1')
    SET ob_tcp_invited_nodes='%'
;
#设置口令 mysql模式
[root@obcontrol ~]# obclient -h192.168.20.141 -uroot@test_tenant#ob_cluster -P2883 -A
MySQL [(none)]> set password=password('123456');

[root@obcontrol ~]# obclient -h192.168.20.141 -uroot@test_tenant#ob_cluster -P2883 -A -p
Enter password: 

#设置口令 oracle模式
[root@obcontrol ~]# obclient -h192.168.20.141 -usys@test_tenant#ob_cluster -P2883 -c --prompt "\u > "
SYS > alter user sys identified by oracle;

[root@obcontrol ~]# obclient -h192.168.20.141 -usys@test_tenant#ob_cluster -P2883 -c --prompt "\u > " -poracle
#查看创建租户
MySQL [oceanbase]> select * from __all_tenant\G
......
*************************** 2. row ***************************
                 gmt_create: 2021-09-17 13:40:01.450647
               gmt_modified: 2021-09-17 13:40:01.450647
                  tenant_id: 1002
                tenant_name: test_tenant
                replica_num: -1
                  zone_list: zone1;zone2;zone3
               primary_zone: RANDOM
                     locked: 0
             collation_type: 0
                       info: 
                  read_only: 0
      rewrite_merge_version: 0
                   locality: FULL{1}@zone1, FULL{1}@zone2, FULL{1}@zone3
        logonly_replica_num: 0
          previous_locality: 
     storage_format_version: 0
storage_format_work_version: 0
      default_tablegroup_id: -1
         compatibility_mode: 0
           drop_tenant_time: -1
                     status: TENANT_STATUS_NORMAL
              in_recyclebin: 0
2 rows in set (0.002 sec)

1.4 observer资源使用
# 以observer维度查看
SELECT
	zone,
	concat(svr_ip, ':', svr_port) observer,
	cpu_total,
	cpu_assigned,
	cpu_assigned_percent,
	round(mem_total/1024/1024/1024) mem_total,
	round(mem_assigned/1024/1024/1024) mem_assigned,
	mem_assigned_percent,
	unit_Num,
  leader_count 
FROM
	__all_virtual_server_stat
ORDER BY
	zone,
	svr_ip;

# 以资源池pool维度查看
select   t1.name resource_pool_name,   
	t2.`name` unit_config_name,   
	t2.max_cpu,   t2.min_cpu,   
	round(t2.max_memory / 1024 / 1024 / 1024) max_mem_gb,   
	round(t2.min_memory / 1024 / 1024 / 1024) min_mem_gb,   
	t3.unit_id,   t3.zone,   
	concat(t3.svr_ip, ':', t3.`svr_port`) observer,   
	t4.tenant_id,   
	t4.tenant_name 
from   __all_resource_pool t1   
join __all_unit_config t2 on (t1.unit_config_id = t2.unit_config_id)   
join __all_unit t3 on (t1.`resource_pool_id` = t3.`resource_pool_id`)   
left join __all_tenant t4 on (t1.tenant_id = t4.tenant_id) 
order by   t1.`resource_pool_id`,   t2.`unit_config_id`,   t3.unit_id;

1.5 unit 资源的分布
select pool.tenant_id, tenant.tenant_name,name as pool_name,unit_config_id, unit_count,
unit.unit_id,pool.zone_list, unit.svr_ip
from
__all_resource_pool pool inner join __all_tenant tenant on pool.tenant_id=tenant.tenant_id
inner join __all_unit unit on pool.resource_pool_id=unit.resource_pool_id
where pool.tenant_id>1000
order by tenant.tenant_name, zone_list;

2 数据库表使用
2.1 创建表
create database t1;
use t1;
create table t1 (c1 int,c2 int ) ;
create table t2 (c1 int,c2 int ) primary_zone='zone2' ;
create table t3 (c1 int,c2 int ) partition by hash (c1) partitions 3;

2.2 创建hash分区表
#mysql 模式的限制：分区表达式的结果必须是 int 类型
MySQL [t1]> create table t_p_hash (c1 varchar(20),c2 int, c3 varchar(20)) partition by hash(c1) partitions 3;
ERROR 1659 (HY000): Field 'c1' is of a not allowed type for this type of partitioning
MySQL [t1]>  create table t_p_hash (c1 varchar(20), c2 int,c3 varchar(20) ) partition by hash(c2+1) partitions 3;

2.3 创建key分区表
MySQL [t1]> create table t_p_key (c1 varchar(20),c2 int,c3 varchar(20)) partition by key (c2) partitions 3;

2.4 创建rang分区表
CREATE TABLE t_p_range (id INT, gmt_create DATETIME, info VARCHAR(20), PRIMARY KEY (gmt_create))
PARTITION BY RANGE COLUMNS(gmt_create)
(PARTITION p0 VALUES LESS THAN ('2015-01-01 00:00:00'),
PARTITION p1 VALUES LESS THAN ('2016-01-01 00:00:00'),
PARTITION p2 VALUES LESS THAN ('2017-01-01 00:00:00'),
PARTITION p3 VALUES LESS THAN (MAXVALUE));
#range 分区表的最后 maxvalue 分区，我们尝试增加一个分区看是否可以
#可以看到最后是 maxvalue 分区的时候，add 分区不能成功
MySQL [t1]>  alter table t_p_range add partition (partition p4 values less than ('2018-01-01 00:00:00'));
ERROR 1493 (HY000): VALUES LESS THAN value must be strictly increasing for each partition
#先删除最后的 maxvalue 分区，然后再尝试刚才的 add 分区操作
MySQL [t1]>  alter table t_p_range drop partition (p3);
MySQL [t1]> alter table t_p_range add partition (partition p4 values less than ('2018-01-01 00:00:00'));

2.5 创建list分区表
# int字段list分区表
create table t_p_list (c1 varchar(20), c2 int) 
partition by list(c2) (
partition p0 values in (1,2,3),
partition p1 values in (4,5), 
partition p2 values in (default) );

# varchar字段list分区表
create table t_p_list (c1 varchar(20), c2 int) 
partition by list(c1) (
partition p0 values in (1,2,3),
partition p1 values in (4,5), 
partition p2 values in (default) );

2.6 表分区的分布情况
select tenant.tenant_name,meta.table_id, tab.table_name, partition_id,zone,concat(svr_ip, ':', svr_port) observer ,
case
when role=1 then 'leader'
when role=2 then 'follower'
else NULL
end as role,
tab.primary_zone
from __all_virtual_meta_table meta 
inner join __all_tenant tenant on meta.tenant_id=tenant.tenant_id
inner join __all_virtual_table tab on meta.tenant_id=tab.tenant_id and meta.table_id=tab.table_id
where tenant.tenant_id='1005'
order by tenant.tenant_name,table_name,partition_id,zone ;

2.7 查看表分区副本分布情况的统计
select tenant.tenant_name, zone, svr_ip,
case
when role=1 then 'leader'
when role=2 then 'follower'
else NULL
end as role,
count(1) as partition_cnt
from
__all_virtual_meta_table meta inner join __all_tenant tenant on meta.tenant_id=tenant.tenant_id
inner join __all_virtual_table tab on meta.tenant_id=tab.tenant_id and meta.table_id=tab.table_id
where tenant.tenant_id='1005'
group by tenant.tenant_name,zone,svr_ip,4
order by tenant.tenant_name,zone,svr_ip,role desc;

3 合并和转储
3.1 查看当前租户内存使用情况
select tenant_id, active/1024/1024/1024 active_gb, total/1024/1024/1024 total_gb,
freeze_trigger/1024/1024/1024 freeze_trigger_gb,total/freeze_trigger, mem_limit/1024/1024/1024 mem_limit_gb from v$memstore where
tenant_id>1000;

select tenant_id,ip, active/1024/1024/1024 active_gb, total/1024/1024/1024 total_gb,
freeze_trigger/1024/1024/1024 freeze_trigger_gb,total/freeze_trigger, mem_limit/1024/1024/1024 mem_limit_gb,freeze_cnt from gv$memstore
where tenant_id>1000;

3.2 使用 sysbench 对某个租户写入数据
cd /usr/sysbench/share/sysbench
/root/obtools/sysbench/sysbench-1.0.20/src/sysbench ./oltp_insert.lua --mysql-host=192.168.20.141 --mysql-db=t1 --mysql-port=2883 --mysql-user=root@obcp_t2#ob_cluster --mysql-password='123456' --tables=20 --table_size=30000 --report-interval=10 --db-driver=mysql --skip-trx=on --db-ps-mode=disable --create-secondary=off --mysql-ignore-errors=6002,6004,4012,2013,4016 --threads=10 --time=60 prepare

/root/obtools/sysbench/sysbench-1.0.20/src/sysbench ./oltp_insert.lua --mysql-host=192.168.20.141 --mysql-db=t1 --mysql-port=2883 --mysql-user=root@obcp_t2#ob_cluster --mysql-password='123456' --tables=20 --table_size=30000 --report-interval=10 --db-driver=mysql --skip-trx=on --db-ps-mode=disable --create-secondary=off --mysql-ignore-errors=6002,6004,4012,2013,4016 --threads=10 --time=60 run
相关参数介绍：
--mysql-host=192.168.20.141 --根据实际情况修改
--mysql-db=t1 - 使用这个租户下的那个 database，可以使用 test 这个
--mysql-port=2883  通过 obproxy 进行 Mysql 登录，默认端口是 2883
--mysql-user=root@obcp_t2#ob_cluster 根据实际情况修改登录用户信息
--mysql-password='123456' ---根据实际情况填写用户密码
--tables=20 --table_size=300000 -通过 sysbench 创建 20 张表，每个表数据 300000，可以根据实际情况调整
--time=60 prepare -先进行 prepare, 就是先完成表和数据的创建 （time 在后面运行的时候可以修改）

3.3 合并的参数
mysql> show parameters like 'major_freeze_duty_%' ;
mysql> show parameters like 'minor_freeze%' ;

3.4 合并状态
select * from __all_zone where name like '%merge%';
查看合并进度
select * from __all_virtual_partition_sstable_image_info;

4 SQL 引擎
4.1 开启 SQL trace ,清空执行计划和 KV 缓存
#以 root 用户登录 sys 租户，清空执行计划和 KV 缓存
MySQL [oceanbase]> alter system flush plan cache global ;

MySQL [oceanbase]> alter system flush kvcache;
#root 用户登录 obcp_t2 租户，打开 SQL Trace
mysql> set ob_enable_trace_log=1;

4.2 执行一条 sql 错误语句
#执行一条 sql 错误语句，分析输出，查看 SQL 引擎的哪些模块参与了执行
MySQL [t1]> select * frm sbtest1;

MySQL [t1]>  show trace ;

4.3 执行一条 sql 语句
执行一条 sql 语句，查找不存在的对象或者列，查看 SQL 引擎的哪些模块参与了执行
在前面我们查看了 sbtest 等表的结构，现在我们查看这些表中“不存在的列“
MySQL [t1]> select zzzyyy from sbtest1;
ERROR 1054 (42S22): Unknown column 'zzzyyy' in 'field list'
MySQL [t1]>  show trace ;

5 集群参数
5.1 日志相关
MySQL [oceanbase]> alter system set enable_syslog_recycle=true;
MySQL [oceanbase]> show parameters like '%enable_syslog_recycle%';
MySQL [oceanbase]> alter system set max_syslog_file_count=4;
MySQL [oceanbase]> show parameters like '%max_syslog_file_count%';

5.2 内存相关
#ob集群 运行总内存限制
MySQL [oceanbase]> show parameters like 'memory_limit';
MySQL [oceanbase]> show parameters like 'memory_limit_percentage';
#ob集群 sys500租户使用内存
MySQL [oceanbase]> show parameters like 'system_memory';
#ob租户 MemStore内存百分比
MySQL [oceanbase]> show parameters like 'memstore_limit_percentage';
#ob租户 转存合并内存百分比
MySQL [oceanbase]> show parameters like 'freeze_trigger_percentage';

5.3 cpu相关
#observer运行总内存限制
MySQL [oceanbase]> show parameters like 'cpu_count';
#observer给操作系统的保留内存
MySQL [oceanbase]> show parameters like 'cpu_reserved';

5.4 合并参数
# 主合并时间
MySQL [oceanbase]> show parameters like 'major_freeze_duty_%' ;
# 小合并次数后，主合并
MySQL [oceanbase]> show parameters like 'minor_freeze%' ;
#ob租户 转存合并内存百分比
MySQL [oceanbase]> show parameters like 'freeze_trigger_percentage';

5.5 执行计划缓存
MySQL [oceanbase]>  show variables like '%ob_enable_plan_cache%' ;
MySQL [oceanbase]> show variables like '%plan_cache%' ;
ob_plan_cache_percentage：用于设置计划缓存可使用内存占租户内存的百分比 （最多可使用内存为：租户内存上限 * ob_plan_cache_percentage/100）
ob_plan_cache_evict_high_percentage：设置触发计划缓存淘汰的内存大小在内存上限绝对值的百分比
ob_plan_cache_evict_low_percentage：设置停止淘汰计划时内存大小在内存上限绝对值的百分比

5.6 负载均衡
MySQL [oceanbase]> show parameters like 'enable_rebalance';
MySQL [oceanbase]> show parameters like 'migrate_concurrency';
MySQL [oceanbase]> show parameters like 'data_copy_concurrency';
MySQL [oceanbase]> show parameters like 'server_data_copy_in_concurrency';
MySQL [oceanbase]> show parameters like 'server_data_copy_out_concurrency';
了解并试用OceanBase
编辑于 2025-05-22 16:18
・
浙江
​
赞同
​
​
添加评论
​
分享
​
收藏
​
喜欢
​
收起
​
查看全部 7 个回答