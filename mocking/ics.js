
const express = require('express')
const ics = require('ics');
const dayjs = require("dayjs")
var casual = require('casual');
const app = express()

function dateArray(date) {
	return [
		date.getYear(),
		date.getMonth(),
		date.getDay(),
		date.getHours(),
		date.getMinutes(),
	];
}

app.get('/test.ics', function (req, res) {
  // construct a series of events based on the current start time.
  const start = dayjs().startOf("day");
  const end = start.add(1, "month");
  let curr = start;
  let events = [];
  const duration = {hours: 1};
  while (curr <= end) {
	if (curr.day() == 0 || curr.day() == 6) {
		console.log("I'm off today!");
		curr = curr.add(1, "day");
		continue;
	}
	for (let i = 1; i <= 3; ++ i) {
		const title = `${casual.word} with ${casual.full_name}`
		events.push({
			title: title,
			start: [
				curr.get("year"),
				curr.get("month")+1,
				curr.get("day"),
				curr.get("hour"),
				curr.get("minute")
			],
			duration,
		});
	}
	curr = curr.add(1, "day");
	console.log('Moving to %s', curr);
  }
  const {error, value} = ics.createEvents(events);
  if (error) {
	console.error(error);
  }
  return res.header({
	"Content-Type": "application/ics",
  }).send(value);
})

app.listen(3000)