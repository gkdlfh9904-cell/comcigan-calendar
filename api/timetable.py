from http.server import BaseHTTPRequestHandler
from pycomcigan import TimeTable, get_school_code
import json


SCHOOL_NAME = "신일비즈니스고등학교"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. 학교 검색부터 확인
            schools = get_school_code("신일비즈니스")

            result = {
                "school_search": schools
            }

            # 2. 시간표 객체 생성
            timetable = TimeTable(
                SCHOOL_NAME,
                week_num=0
            )

            # 3. 전체 timetable 구조를 문자열로 확인
            result["timetable_type"] = str(type(timetable.timetable))
            result["timetable_raw"] = timetable.timetable

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    default=str
                ).encode("utf-8")
            )

        except Exception as e:
            self.send_response(500)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(
                    {
                        "success": False,
                        "error": str(e),
                        "type": type(e).__name__
                    },
                    ensure_ascii=False
                ).encode("utf-8")
            )
