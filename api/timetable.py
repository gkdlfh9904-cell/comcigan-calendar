from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta
import requests
import base64
import json


# ============================================================
# 컴시간 설정
# ============================================================

COMCI_ENDPOINT = "http://comci.net:4082/36179"

# 신일비즈니스고 내부 식별값
SCHOOL_ID_1 = "73629"
SCHOOL_ID_2 = "64358"

SCHOOL_NAME = "신일비즈니스고등학교"

GRADE = 3
CLASS_NUM = 7


# ============================================================
# 컴시간 URL 자동 생성
#
# 1 = 이번 주
# 2 = 다음 주
# ============================================================

def make_comci_url(week_num):

    raw = (
        f"{SCHOOL_ID_1}_"
        f"{SCHOOL_ID_2}_"
        f"0_"
        f"{week_num}"
    )

    token = base64.b64encode(
        raw.encode("utf-8")
    ).decode("ascii")

    return f"{COMCI_ENDPOINT}?{token}"


# ============================================================
# 응답 JSON 디코딩
# ============================================================

def decode_response(response):

    # 컴시간 데이터는 UTF-8
    text = response.content.decode(
        "utf-8",
        errors="replace"
    )

    # 혹시 뒤에 이상한 데이터가 붙어 있으면
    # 마지막 }까지만 사용
    last_brace = text.rfind("}")

    if last_brace == -1:
        raise ValueError(
            "컴시간 응답에서 JSON을 찾지 못했습니다."
        )

    text = text[:last_brace + 1]

    return json.loads(text)


# ============================================================
# 수업 코드 해석
#
# 예:
# 17022
#
# 17 = 과목 번호
# 022 = 교사 번호
#
# >17022 = 변경 표시
# ============================================================

def decode_lesson(
    raw_code,
    subjects,
    teachers
):

    if raw_code is None:
        return None

    changed = False


    if isinstance(
        raw_code,
        str
    ):

        if raw_code.startswith(">"):

            changed = True

            raw_code = raw_code[1:]


        if not raw_code.isdigit():
            return None


        code = int(raw_code)


    else:

        code = int(raw_code)


    if code == 0:
        return None


    subject_index = (
        code // 1000
    )

    teacher_index = (
        code % 1000
    )


    subject = ""

    teacher = ""


    if (
        0 <= subject_index <
        len(subjects)
    ):

        subject = subjects[
            subject_index
        ]


    if (
        0 <= teacher_index <
        len(teachers)
    ):

        teacher = teachers[
            teacher_index
        ]


    teacher = (
        teacher
        .rstrip("*")
        .strip()
    )


    return {

        "code": code,

        "subject": subject,

        "teacher": teacher,

        "changed": changed

    }


# ============================================================
# 교시 시작/종료 시간
# ============================================================

def parse_class_times(
    raw_times
):

    result = {}


    for item in raw_times:

        try:

            # 1(09:10)
            period_text, time_text = (
                item.split("(")
            )

            period = int(
                period_text
            )

            start = (
                time_text
                .replace(")", "")
            )


            start_dt = datetime.strptime(
                start,
                "%H:%M"
            )


            end_dt = (
                start_dt +
                timedelta(
                    minutes=50
                )
            )


            result[period] = {

                "start":
                    start,

                "end":
                    end_dt.strftime(
                        "%H:%M"
                    )

            }


        except Exception:

            continue


    return result


# ============================================================
# 한 주 시간표 파싱
# ============================================================

def parse_week(
    data,
    week_num
):

    subjects = data[
        "자료492"
    ]

    teachers = data[
        "자료446"
    ]


    class_times = (
        parse_class_times(
            data.get(
                "일과시간",
                []
            )
        )
    )


    timetable_data = (
        data.get(
            "자료147"
        )
    )


    if not timetable_data:

        raise ValueError(
            "자료147 시간표 데이터가 없습니다."
        )


    # 3학년
    grade_data = (
        timetable_data[
            GRADE
        ]
    )


    # 7반
    class_data = (
        grade_data[
            CLASS_NUM
        ]
    )


    start_date_string = (
        data.get(
            "시작일"
        )
    )


    if not start_date_string:

        raise ValueError(
            "시작일 정보가 없습니다."
        )


    week_start = (
        datetime.strptime(
            start_date_string,
            "%Y-%m-%d"
        )
    )


    weekdays = [
        "월",
        "화",
        "수",
        "목",
        "금"
    ]


    result = []


    # class_data 구조:
    #
    # [요일수, 월, 화, 수, 목, 금]
    #
    for day_index in range(
        1,
        6
    ):

        raw_day = (
            class_data[
                day_index
            ]
        )


        date = (
            week_start +
            timedelta(
                days=
                day_index - 1
            )
        )


        day_result = {

            "weekday":
                weekdays[
                    day_index - 1
                ],

            "date":
                date.strftime(
                    "%Y-%m-%d"
                ),

            "lessons":
                []

        }


        if not raw_day:

            result.append(
                day_result
            )

            continue


        # 첫 번째 숫자는
        # 해당 일자의 교시 수
        period_count = (
            raw_day[0]
        )


        if period_count == 0:

            result.append(
                day_result
            )

            continue


        lesson_codes = (
            raw_day[1:]
        )


        for period, raw_code in enumerate(
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


            time_info = (
                class_times.get(
                    period,
                    {
                        "start": "",
                        "end": ""
                    }
                )
            )


            day_result[
                "lessons"
            ].append({

                "period":
                    period,

                "start":
                    time_info[
                        "start"
                    ],

                "end":
                    time_info[
                        "end"
                    ],

                "subject":
                    lesson[
                        "subject"
                    ],

                "teacher":
                    lesson[
                        "teacher"
                    ],

                "changed":
                    lesson[
                        "changed"
                    ],

                "raw_code":
                    raw_code

            })


        result.append(
            day_result
        )


    return {

        "week":
            week_num,

        "week_start":
            week_start.strftime(
                "%Y-%m-%d"
            ),

        "timetable":
            result

    }


# ============================================================
# 컴시간 한 주 다운로드
# ============================================================

def fetch_week(
    week_num
):

    url = make_comci_url(
        week_num
    )


    headers = {

        "User-Agent":
            (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/134.0 Safari/537.36"
            ),

        "Referer":
            "http://comci.net/"

    }


    response = requests.get(

        url,

        headers=headers,

        timeout=15

    )


    response.raise_for_status()


    data = decode_response(
        response
    )


    return parse_week(
        data,
        week_num
    )


# ============================================================
# Vercel API
# ============================================================

class handler(
    BaseHTTPRequestHandler
):

    def do_GET(self):

        try:

            # -----------------------------
            # 이번 주
            # -----------------------------

            current_week = (
                fetch_week(1)
            )


            # -----------------------------
            # 다음 주
            # -----------------------------

            next_week = (
                fetch_week(2)
            )


            result = {

                "success":
                    True,

                "school":
                    SCHOOL_NAME,

                "grade":
                    GRADE,

                "class":
                    CLASS_NUM,

                "weeks": [

                    current_week,

                    next_week

                ]

            }


            body = json.dumps(

                result,

                ensure_ascii=False,

                indent=2

            ).encode(
                "utf-8"
            )


            self.send_response(
                200
            )


            self.send_header(

                "Content-Type",

                "application/json; charset=utf-8"

            )


            # 시간표 변경 때문에
            # 캐시하지 않도록 설정
            self.send_header(

                "Cache-Control",

                "no-store, no-cache, must-revalidate"

            )


            self.end_headers()


            self.wfile.write(
                body
            )


        except Exception as e:

            body = json.dumps(

                {

                    "success":
                        False,

                    "error":
                        str(e),

                    "type":
                        type(e).__name__

                },

                ensure_ascii=False,

                indent=2

            ).encode(
                "utf-8"
            )


            self.send_response(
                500
            )


            self.send_header(

                "Content-Type",

                "application/json; charset=utf-8"

            )


            self.end_headers()


            self.wfile.write(
                body
            )
