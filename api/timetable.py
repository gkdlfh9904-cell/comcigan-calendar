from http.server import BaseHTTPRequestHandler
from pycomcigan import TimeTable
import json


SCHOOL_NAME = "신일비즈니스고등학교"
GRADE = 3
CLASS_NUM = 7


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 이번 주 시간표
            timetable = TimeTable(
                SCHOOL_NAME,
                week_num=0
            )

            raw = timetable.timetable[GRADE][CLASS_NUM]

            weekdays = ["월", "화", "수", "목", "금"]

            result = []

            for day_index, day in enumerate(raw):
                lessons = []

                for period_index, lesson in enumerate(day):
                    if lesson is None:
                        continue

                    lessons.append({
                        "period": period_index + 1,
                        "raw": lesson
                    })

                result.append({
                    "weekday": weekdays[day_index],
                    "lessons": lessons
                })

            response = {
                "success": True,
                "school": SCHOOL_NAME,
                "grade": GRADE,
                "class": CLASS_NUM,
                "timetable": result
            }

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(
                    response,
                    ensure_ascii=False,
                    default=str
                ).encode("utf-8")
            )

        except Exception as e:
            response = {
                "success": False,
                "error": str(e),
                "type": type(e).__name__
            }

            self.send_response(500)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(
                    response,
                    ensure_ascii=False
                ).encode("utf-8")
            )
