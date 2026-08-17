from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta
import requests
import json


COMCI_URL = "http://comci.net:4082/36179?NzM2MjlfNjQzNThfMF8x"

SCHOOL_NAME = "신일비즈니스고등학교"
GRADE = 3
CLASS_NUM = 7


def decode_comcigan_response(response):
    # 컴시간은 실제 UTF-8인데 requests가 ISO-8859-1로 오인하는 경우가 있음
    text = response.content.decode("utf-8", errors="replace")

    # JSON 뒤에 NUL 문자 등이 붙는 경우 제거
    last_brace = text.rfind("}")

    if last_brace == -1:
        raise ValueError("컴시간 응답에서 JSON을 찾지 못했습니다.")

    text = text[:last_brace + 1]

    return json.loads(text)


def decode_lesson(code, subjects, teachers):
    if code is None:
        return None

    # 변경된 수업은 >17022 같은 형태로 올 수 있음
    changed = False

    if isinstance(code, str):
        if code.startswith(">"):
            changed = True
            code = code[1:]

        if not code.isdigit():
            return None

        code = int(code)

    if code == 0:
        return None

    # 컴시간 코드:
    # 과목번호 * 1000 + 교사번호
    subject_index = code // 1000
    teacher_index = code % 1000

    subject = ""
    teacher = ""

    if 0 <= subject_index < len(subjects):
        subject = subjects[subject_index]

    if 0 <= teacher_index < len(teachers):
        teacher = teachers[teacher_index]

    # 교사 이름 뒤 * 제거
    teacher = teacher.rstrip("*").strip()

    return {
        "code": code,
        "subject": subject,
        "teacher": teacher,
        "changed": changed
    }


def parse_class_times(raw_times):
    result = {}

    for item in raw_times:
        # 예: 1(09:10)
        try:
            period_text, time_text = item.split("(")

            period = int(period_text)
            start = time_text.replace(")", "")

            start_dt = datetime.strptime(start, "%H:%M")
            end_dt = start_dt + timedelta(minutes=50)

            result[period] = {
                "start": start,
                "end": end_dt.strftime("%H:%M")
            }

        except Exception:
            continue

    return result


def parse_timetable(data):
    subjects = data["자료492"]
    teachers = data["자료446"]

    class_times = parse_class_times(
        data.get("일과시간", [])
    )

    # 자료147 = 현재 선택된 주의 실제/변경 시간표
    timetable_data = data.get("자료147")

    if not timetable_data:
        raise ValueError("자료147 시간표 데이터가 없습니다.")

    # 구조:
    # [학년수,
    #   [반수, 1반, 2반 ...],
    #   ...
    # ]
    grade_data = timetable_data[GRADE]

    class_data = grade_data[CLASS_NUM]

    # class_data:
    # [요일수, 월요일, 화요일, 수요일, 목요일, 금요일]
    weekdays = [
        "월",
        "화",
        "수",
        "목",
        "금"
    ]

    start_date_string = data.get("시작일")

    if not start_date_string:
        raise ValueError("시작일 정보가 없습니다.")

    week_start = datetime.strptime(
        start_date_string,
        "%Y-%m-%d"
    )

    result = []

    for day_index in range(1, 6):
        raw_day = class_data[day_index]

        date = week_start + timedelta(
            days=day_index - 1
        )

        weekday = weekdays[day_index - 1]

        day_result = {
            "weekday": weekday,
            "date": date.strftime("%Y-%m-%d"),
            "lessons": []
        }

        if not raw_day:
            result.append(day_result)
            continue

        # 첫 숫자는 그날 총 교시 수
        period_count = raw_day[0]

        if period_count == 0:
            result.append(day_result)
            continue

        lesson_codes = raw_day[1:]

        for index, raw_code in enumerate(
            lesson_codes,
            start=1
        ):
            lesson = decode_lesson(
                raw_code,
                subjects,
                teachers
            )

            if not lesson:
                continue

            time_info = class_times.get(
                index,
                {
                    "start": "",
                    "end": ""
                }
            )

            day_result["lessons"].append({
                "period": index,
                "start": time_info["start"],
                "end": time_info["end"],
                "subject": lesson["subject"],
                "teacher": lesson["teacher"],
                "changed": lesson["changed"],
                "raw_code": raw_code
            })

        result.append(day_result)

    return {
        "success": True,
        "school": SCHOOL_NAME,
        "grade": GRADE,
        "class": CLASS_NUM,
        "week_start": week_start.strftime(
            "%Y-%m-%d"
        ),
        "timetable": result
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/134.0 Safari/537.36"
                ),
                "Referer": "http://comci.net/"
            }

            response = requests.get(
                COMCI_URL,
                headers=headers,
                timeout=15
            )

            response.raise_for_status()

            raw_data = decode_comcigan_response(
                response
            )

            result = parse_timetable(
                raw_data
            )

            body = json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8")

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.send_header(
                "Cache-Control",
                "no-store"
            )

            self.end_headers()

            self.wfile.write(body)

        except Exception as e:
            body = json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "type": type(e).__name__
                },
                ensure_ascii=False,
                indent=2
            ).encode("utf-8")

            self.send_response(500)

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.end_headers()

            self.wfile.write(body)
