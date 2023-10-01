from django.test import TestCase

# Create your tests here.


"""
celery消息队列的大致运行原理的伪代码
"""

# 生产者
class Broker:
    # 任务队列，存储的是函数引用对象
    broker_list = list()


# 消费者
class Worker:
    """
    发送短信的任务
        不是直接去运行
        把发送短信的任务添加到队列中
    """
    def run(self, broker, func):
        if func in broker.broker_list:
            func()
        else:
            return 'error'


# 中间人：负责去调度生产者和消费者
class Celery:
    def __init__(self):
        # 类的实例
        self.broker = Broker()
        self.worker = Worker()

    def add(self, func):
        self.broker.broker_list.append(func)

    def work(self, func):
        # 此方法其实就是消费者角色
        self.worker.run(self.broker, func)



# 创建发送短信的任务
def send_sms_code():
    print('消息发送成功...')


app = Celery()
app.add(send_sms_code)
app.work(send_sms_code)

"""
上述代码其实是一种软件的设计模式：生产者消费者模式

Broker 消息队列
Worker 消费者 处理任务的
Celery 中间人
Task 任务

中间人Celery将Task任务添加到Broker消息队列中
然后由中间人Celery去检测Broker消息队列中是否有任务Task
如果有，中间人Celery则会分配任务给Worker消费者


在项目根目录之下创建celery文件夹
"""