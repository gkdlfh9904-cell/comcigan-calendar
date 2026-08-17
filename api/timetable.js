const Timetable = require("comcigan-parser");

module.exports = async function handler(req, res) {
  try {
    const timetable = new Timetable();

    await timetable.init({
      cache: 1000 * 60 * 5
    });

    // 학교 검색
    const schools = await timetable.search("신일비즈니스고등학교");

    const school = schools.find(
      s =>
        s.name === "신일비즈니스고등학교" &&
        s.region === "경기"
    );

    if (!school) {
      return res.status(404).json({
        error: "신일비즈니스고등학교를 찾지 못했습니다.",
        schools
      });
    }

    // 학교 지정
    timetable.setSchool(school.code);

    // 시간표 + 교시 시간
    const [allTimetable, classTimes] = await Promise.all([
      timetable.getTimetable(),
      timetable.getClassTime()
    ]);

    const grade = 3;
    const classNumber = 7;

    const target =
      allTimetable?.[grade]?.[classNumber];

    if (!target) {
      return res.status(404).json({
        error: "3학년 7반 시간표를 찾지 못했습니다."
      });
    }

    const weekdays = [
      "월",
      "화",
      "수",
      "목",
      "금"
    ];

    const result = target.map(
      (day, dayIndex) => {
        return {
          weekday: weekdays[dayIndex],
          lessons: day
            .filter(Boolean)
            .map(lesson => ({
              period: lesson.classTime,
              subject: lesson.subject,
              teacher: lesson.teacher || "",
              code: lesson.code || ""
            }))
        };
      }
    );

    return res.status(200).json({
      school: {
        name: school.name,
        region: school.region,
        code: school.code
      },

      grade,
      classNumber,

      classTimes,

      timetable: result
    });

  } catch (error) {
    console.error(error);

    return res.status(500).json({
      error: error.message,
      stack: error.stack
    });
  }
};