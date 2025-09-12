import threading
import queue
import logging

logger = logging.getLogger(__name__)

class TaskRunner:
    def __init__(self, view):
        self.view = view
        self.task_queue = queue.Queue()
        self.view.root.after(100, self.process_queue)

    def run_task(self, task_func, on_success=None, on_error=None, on_finally=None):
        thread = threading.Thread(target=self._execute_task, args=(task_func, on_success, on_error, on_finally))
        thread.daemon = True
        thread.start()

    def _execute_task(self, task_func, on_success, on_error, on_finally):
        try:
            result = task_func()
            if on_success:
                self.post_to_main_thread(on_success, result)
        except Exception as e:
            logger.error("An error occurred in the background task", exc_info=True)
            if on_error:
                self.post_to_main_thread(on_error, e)
        finally:
            if on_finally:
                self.post_to_main_thread(on_finally)

    def post_to_main_thread(self, callback, *args):
        self.task_queue.put((callback, args))

    def process_queue(self):
        try:
            while True:
                callback, args = self.task_queue.get_nowait()
                callback(*args)
                self.view.root.update_idletasks()
        except queue.Empty:
            pass
        finally:
            self.view.root.after(100, self.process_queue)
