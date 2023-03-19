// const timezones = require("/static/data/timezones.json");
// const dist = require("/static/iit/js/dist.js");

const TZ_MATCH_DIST = 3

function strMatch(s1, s2) {
  const us1 = s1.split('').map
}

function getQuerystring() {
  let output = {};
  if (window.location.search) {
    var queryParams = window.location.search.substring(1);
    var listQueries = queryParams.split("&");
    for (var query in listQueries) {
      if (listQueries.hasOwnProperty(query)) {
        var queryPair = listQueries[query].split("=");
        output[queryPair[0]] = decodeURIComponent(queryPair[1] || "");
      }
    }
  }
  return output;
}

$(document).ready(() => {
  const TZ_FILTER_LIST = $("#iit-timezone-filter-list")
  const baseUrl = $(TZ_FILTER_LIST).attr("iit-data-base-url");

  $.getJSON("/static/data/timezones.json", (data) => {


    const timezones = data;

    const qs = getQuerystring();
    if (!qs.timezone) {
      // Detect the timezone if not given
      // https://attacomsian.com/blog/javascript-current-timezone
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      console.log(timezone);
      window.location.replace(window.location + `?timezone=${timezone}`);
    }


    $("#timezone-filter").keyup((e) => {
      const searchVal = e.target.value.trim().toLowerCase();
      console.log(searchVal)

      const valid = searchVal ? timezones.map(tz => [tz.label, dist(tz.label, searchVal.toLowerCase())]).filter(([tzn, dist]) => dist > 0).sort((a, b) => a[1] > b[1]).map(([tz, d]) => tz) : timezones.map(tz => tz.label);


      $(TZ_FILTER_LIST).append(valid.map(validTz => {
        const li = document.createElement("li");
        $(li).attr("href", `${baseUrl}?timezone=${validTz}`)
      }));
    });
  })
});
