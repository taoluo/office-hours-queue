from django.db.models import Avg, F

from ohq.models import Question, QueueStatistic


def calculate_avg_queue_wait(queue, prev_sunday, coming_sunday):
    avg = Question.objects.filter(
        queue=queue,
        time_asked__date__range=[prev_sunday, coming_sunday],
        time_response_started__isnull=False,
    ).aggregate(avg_wait=Avg(F("time_response_started") - F("time_asked")))

    wait = avg["avg_wait"]

    QueueStatistic.objects.update_or_create(
        queue=queue,
        metric=QueueStatistic.METRIC_AVG_WAIT,
        date=prev_sunday,
        defaults={"value": wait.seconds if wait else 0},
    )


def calculate_avg_time_helping(queue, prev_sunday, coming_sunday):
    avg = Question.objects.filter(
        queue=queue,
        status=Question.STATUS_ANSWERED,
        time_response_started__date__range=[prev_sunday, coming_sunday],
        time_responded_to__isnull=False,
    ).aggregate(avg_time=Avg(F("time_responded_to") - F("time_response_started")))

    duration = avg["avg_time"]

    QueueStatistic.objects.update_or_create(
        queue=queue,
        metric=QueueStatistic.METRIC_AVG_TIME_HELPING,
        date=prev_sunday,
        defaults={"value": duration.seconds if duration else 0},
    )


def calculate_wait_time_heatmap(queue, weekday, hour):
    interval_avg = Question.objects.filter(
        queue=queue,
        time_asked__week_day=weekday,
        time_asked__hour=hour,
        time_response_started__isnull=False,
    ).aggregate(avg_wait=Avg(F("time_response_started") - F("time_asked")))

    interval_avg_wait = interval_avg["avg_wait"]

    QueueStatistic.objects.update_or_create(
        queue=queue,
        metric=QueueStatistic.METRIC_HEATMAP_WAIT,
        day=weekday,
        hour=hour,
        defaults={"value": interval_avg_wait.seconds if interval_avg_wait else 0},
    )


def calculate_num_questions_ans(queue, prev_sunday, coming_saturday):
    num_questions = Question.objects.filter(
        queue=queue,
        status=Question.STATUS_ANSWERED,
        time_responded_to__date__range=[prev_sunday, coming_saturday],
    ).count()

    QueueStatistic.objects.update_or_create(
        queue=queue,
        metric=QueueStatistic.METRIC_NUM_ANSWERED,
        date=prev_sunday,
        defaults={"value": num_questions},
    )


def calculate_num_students_helped(queue, prev_sunday, coming_saturday):
    num_students = (
        Question.objects.filter(
            queue=queue,
            status=Question.STATUS_ANSWERED,
            time_responded_to__date__range=[prev_sunday, coming_saturday],
        )
        .distinct("asked_by")
        .count()
    )

    QueueStatistic.objects.update_or_create(
        queue=queue,
        metric=QueueStatistic.METRIC_STUDENTS_HELPED,
        date=prev_sunday,
        defaults={"value": num_students},
    )


def calculate_questions_per_ta_heatmap(queue, weekday, hour):
    interval_questions = Question.objects.filter(
        queue=queue, time_asked__week_day=weekday, time_asked__hour=hour
    )

    num_tas = interval_questions.distinct("responded_to_by").count()

    num_questions = interval_questions.count()

    statistic = num_questions / num_tas if num_tas else num_questions

    QueueStatistic.objects.update_or_create(
        queue=queue,
        metric=QueueStatistic.METRIC_HEATMAP_QUESTIONS_PER_TA,
        day=weekday,
        hour=hour,
        defaults={"value": statistic},
    )
