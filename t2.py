from threading import Thread
import time


class MyThread(Thread):
    def __init__(self, ctrl, id):
        self.id = id
        self.ctrl = ctrl
        super().__init__()
        self.start()

    def run(self):
        print("WORK START", self.id)
        time.sleep(10)
        print("WORK START", self.id)
        self.ctrl.work_finished(self)


class Controller:
    curr = 1
    cnt = 0

    def start_curr(self):
        print("START", self.curr)
        MyThread(self, self.curr)
        print("WAIT FOR ", self.curr)

    def work_finished(self, thread):
        print("FINISHED  ", thread.id)
        self.curr = 1 if thread.id == 2 else 2
        if self.cnt < 10:
            self.start_curr()
        self.cnt += 1


c = Controller()
c.start_curr()

