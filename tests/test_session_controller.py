from localwhisper.session_controller import SessionController


class ImmediateScheduler:
    def __call__(self, callback):
        callback()


class DeferredScheduler:
    def __init__(self):
        self.callbacks = []

    def __call__(self, callback):
        self.callbacks.append(callback)

    def run_pending(self):
        while self.callbacks:
            self.callbacks.pop(0)()


def test_start_job_replaces_previous_identity():
    controller = SessionController()

    first = controller.start_job()
    second = controller.start_job()

    assert (first, second) == (1, 2)
    assert not controller.is_active(first)
    assert controller.is_active(second)


def test_cancelled_job_cannot_run_a_scheduled_callback():
    controller = SessionController()
    scheduler = DeferredScheduler()
    called = []
    job_id = controller.start_job()

    controller.schedule_if_active(job_id, scheduler, lambda: called.append("old"))
    controller.invalidate()
    scheduler.run_pending()

    assert called == []


def test_finish_callback_runs_once_and_retires_only_its_job():
    controller = SessionController()
    scheduler = DeferredScheduler()
    called = []
    job_id = controller.start_job()

    controller.finish_if_active(job_id, scheduler, lambda: called.append("done"))
    scheduler.run_pending()
    controller.finish_if_active(job_id, scheduler, lambda: called.append("ignored"))
    scheduler.run_pending()

    assert called == ["done"]
    assert controller.active_job_id is None


def test_finish_callback_does_not_retire_a_replacement_job():
    controller = SessionController()
    scheduler = DeferredScheduler()
    job_id = controller.start_job()
    controller.finish_if_active(job_id, scheduler, lambda: controller.start_job())

    scheduler.run_pending()

    assert controller.active_job_id == 2


def test_compatibility_setters_validate_and_restore_state():
    controller = SessionController()
    controller.set_next_job_id(4)
    controller.set_active_job(4)

    assert controller.next_job_id == 4
    assert controller.active_job_id == 4
