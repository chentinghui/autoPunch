#coding: utf-8
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED, EVENT_JOB_EXECUTED

import traceback
import os,sys,time
import requests
import logging, pytz,random
import datetime
# 判断 2018年4月30号 是不是节假日
from chinese_calendar import is_workday

ISOTIMEFORMAT = '%m-%d %H:%M:%S'
JOB_DATE = "%Y-%m-%d %H:%M:%S"

mHour =8  #早上打卡时间  必须是数字
aHour =17  #下午打卡时间  必须是数字  *会报错
mState = "0"  #0带表没有打卡，1带表打卡成功
misfire_grace_time = 3600 #误差时间
timezone = pytz.timezone("Asia/Shanghai")
TOPICID = '148' #149.test   傅148 pro  唐2260
userMessages = '--test--'
if '2260' == TOPICID:
    userMessages = '---唐---'
elif '148' == TOPICID:
    userMessages = '---傅---'

executors = {
   'default': ThreadPoolExecutor(10),
   'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    "coalesce": False,  # 默认为新任务关闭合并模式   如果有多个相同的任务在运行，false不会合并在一起，true把相同的任务合并
    "max_instances": 10,  # 设置新任务的最大实例数为2
}

#D:\\workProject\\pthon\\autoPunch\\LOG\\log.log
scheduler = BlockingScheduler(executors=executors,job_defaults=job_defaults,timezone=timezone)
schedulerGround = BackgroundScheduler(executors=executors,job_defaults=job_defaults,timezone=timezone)
logging.basicConfig(filename='log.log',format='[%(asctime)s-%(filename)s-%(levelname)s:%(message)s]', level = logging.DEBUG,filemode="a",datefmt='%Y-%m-%d %I:%M:%S %p')

#监听日志
def job_listener(Event):
    job = scheduler.get_job(Event.job_id)
    if not Event.exception:
        logging.info("jobname=%s|jobtrigger=%s|jobtime=%s|retval=%s", job.name, job.trigger,
                    Event.scheduled_run_time, Event.retval)
    else:
        logging.error("jobname=%s|jobtrigger=%s|errcode=%s|exception=[%s]|traceback=[%s]|scheduled_time=%s", job.name,
                     job.trigger, Event.code,
                     Event.exception, Event.traceback, Event.scheduled_run_time)
    scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_EXECUTED)

def ResetPunch(args):#重设打卡
    if 'oneMorning' == args:
        scheduler.remove_job("oneMorning")
        oneMorning()
    elif 'oneAfternoon' == args:
        scheduler.remove_job("oneAfternoon")
        oneAfternoon()
    else:
        logging.warning(userMessages+"重设打卡异常")


def oneMorning():#设置早上打卡时间
    triggerMorning = CronTrigger(day_of_week='*', hour=mHour, minute=random.randint(0, 10),second=random.randint(0, 59))# 打卡时间范围是0-10
    scheduler.add_job(click, triggerMorning, id="oneMorning", replace_existing=False, args=['oneMorning'],misfire_grace_time=misfire_grace_time)
def oneAfternoon():#设置下午打卡时间
    triggerAfternoon = CronTrigger(day_of_week='*', hour=aHour, minute=random.randint(31, 40),second=random.randint(0, 59)) # 打卡时间范围是30-40
    scheduler.add_job(click, triggerAfternoon, id="oneAfternoon", replace_existing=False, args=['oneAfternoon'],misfire_grace_time=misfire_grace_time)
def workingDay():#初始化检查打卡时间
    workingDayMorning = CronTrigger(day_of_week='*', hour=mHour, minute=15, second=random.randint(0, 59))  # 打卡时间范围是0-10
    schedulerGround.add_job(everyRun, workingDayMorning, id="workingDayMorning", replace_existing=False,misfire_grace_time=misfire_grace_time)
    workingDayAfternoon = CronTrigger(day_of_week='*', hour=aHour, minute=45, second=random.randint(0, 59))  # 打卡时间范围是30-40
    schedulerGround.add_job(everyRun, workingDayAfternoon, id="workingDayAfternoon", replace_existing=False,misfire_grace_time=misfire_grace_time)
# 输出时间
def job():
    logging.info("-------程序已正常启动，请等待自动打卡-------")
    print("-------程序已正常启动，请等待自动打卡-------")
    pro()
    scheduler.print_jobs()
    schedulerGround.print_jobs()
    schedulerGround.start()
    scheduler.start()

def test():#测试
    print("---test--")
    newDate = datetime.datetime.now()
    # triggerMorning(newDate)
    # triggerAfternoon(newDate)


def everyRun():
    if is_workday(datetime.datetime.now()):
        schedulerGround.print_jobs()
        logging.info("everyRun前")
        global mState
        if mState == returnState():
            mState = "0"
            print("检查打卡成功！")
            logging.info("检查打卡成功！")
        else:
            click('everyRun')



def pro():#正式环境
    # triggerMorning = CronTrigger(day_of_week='0-4', hour=mHour, minute=1, second=random.randint(0, 59))
    # triggerAfternoon = CronTrigger(day_of_week='0-4', hour=aHour, minute=35, second=random.randint(0, 59))
    # scheduler.add_job(click, triggerMorning, id="oneMorning", replace_existing=False, args=['oneMorning'],misfire_grace_time=misfire_grace_time)
    # scheduler.add_job(click, triggerAfternoon, id="oneAfternoon", replace_existing=False,args=['oneAfternoon'],misfire_grace_time=misfire_grace_time)
    oneMorning()#设置早上打卡时间
    oneAfternoon()#设置下午打卡时间
    workingDay()#初始化检查打卡时间

def click(args):
    global mState
    if is_workday(datetime.datetime.now()) and mState != returnState():
            try:
                #打第一个卡
                print("-------打卡运行中-------")
                returnFlag =os.system('adb shell input keyevent 26')  # 点亮屏幕
                time.sleep(5)
                if(returnFlag != 0):#重新连接客户端
                    print("returnFlag=", returnFlag)
                    returnConnect= os.system('adb connect 192.168.20.102')
                    if(returnConnect != 0):
                        time.sleep(30)
                        returnConnect = os.system('adb connect 192.168.20.102')
                    print("connect=",returnConnect )
                    time.sleep(20)
                returnFlag = os.system('adb shell input keyevent 82')  # 点亮屏幕
                print("returnFlag22==", returnFlag)
                time.sleep(3)
                if (returnFlag != 0):
                    wxpusher(userMessages+'请注意,打卡异常')
                    sys.exit(0)
                os.system('adb shell input keyevent 82')  # 点亮屏幕
                time.sleep(2)
                os.system('adb shell am force-stop com.tencent.wework')  # 关闭微信
                time.sleep(2)
                os.system('adb shell input swipe 300 1000 300 500')  # 往上滑动
                time.sleep(2)
                os.system('adb shell input keyevent 3')  # 单击home键，回到主页
                time.sleep(2)
                os.system('adb shell input tap 1620 800')  # 点击企业微信
                time.sleep(8)
                os.system('adb shell input tap 678 1820')
                time.sleep(5)
                os.system('adb shell input tap 410 430')
                time.sleep(10)
                # os.system('adb shell input tap 599 1164') #点击打卡
                # time.sleep(5)
                os.system("adb shell input keyevent 4 ")# 返回
                time.sleep(2)
                os.system("adb shell am force-stop com.tencent.wework")  # 返回
                time.sleep(2)

                wxpusher(userMessages+"打卡成功")
                print(userMessages + "-------打卡完成-------")

                if ("everyRun" == args):
                    mState = "0"
                    print("第二次运行检查打卡成功")
                    logging.info("第二次运行检查打卡成功")
                else:
                    mState = returnState()
                    ResetPunch(args)  # 重设打卡
                logging.info(scheduler.print_jobs())
                print('打卡状态标识='+str(mState))
            except Exception as e:
                logging.debug('click===:\t'+repr(e))
                print('click===:\t'+repr(e))
                traceback.print_exc()
    else:
        logging.info(scheduler.print_jobs())
        print("节假日跳过打卡或已打卡无需重复打卡")
        logging.info("节假日跳过打卡或已打卡无需重复打卡")
def wxpusher(information):
    try:
        # 推送消息给微信，此处可以删除，仅为通知 AT_4HSc6sCPTFGitUoEkfe4gmntD3gvw19e
        theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
        url = 'http://wxpusher.zjiecode.com/api/send/message/?appToken=AT_4HSc6sCPTFGitUoEkfe4gmntD3gvw19e&content='+theTime+' '+information+'&topicId='+TOPICID;
        headers = {'Connection': 'close'}
        time.sleep(10)
        requests.get(url, headers=headers)
        # print("-------" + information + ",等待下一次打卡-------\r\n")
    except Exception as e:
        logging.debug("微信推送失败====:\t"+repr(e))
        print("微信推送失败:\t"+repr(e))

def returnState():#设置状态判断
    dt = datetime.datetime.now()
    mState = dt.strftime('%y%m%d%I')
    return mState

def main():
    try:
        job()
        logging.info('打卡成功===:\t\n')
    except Exception as e:
        print("main====:\t"+repr(e))
        logging.info("main====:\t"+repr(e))
        traceback.print_exc()




if __name__ == '__main__':
    main()